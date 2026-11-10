#!/usr/bin/env python3
"""Route B for the tri-label pipeline: download YouTube videos that are NOT in OrcinusOrca, cut them into 3-25 s
segments, and write the same meta.jsonl that `yt_tri_label.py extract` writes, so gemini / qwen / merge run unchanged
(YT_TRI_OUT=<out dir>).  2026-11-10: the rest of The Do Show (owner: "用返之前個方法，ASR + Gemini + 字幕").

usage: python data_yue/yt_dl_segment.py --channel thedoshow0909 --ids IDS.tsv [--out yt_more2] [--rate 5M]
  IDS.tsv: first column = video id (e.g. from channel_check / yt-dlp --flat-playlist), one per line

Per video:
  1. yt-dlp (YTDLP env, default "uvx --from yt-dlp[default]@latest yt-dlp", always --ignore-config) audio only,
     16 kHz mono mp3, rate-capped; creator subtitles zh-HK / zh-Hant / zh-TW as vtt (never auto captions)
  2. with subtitles: consecutive cues form one segment while the gap is <= 1.5 s and the span <= 25 s;
     the joined cue text is the segment's `sub` (arbiter S, and Gemini's hint for names only)
     without subtitles: cut at silences (ffmpeg silencedetect) into 3-25 s chunks, `sub` = ""
  3. segments shorter than 3 s are dropped; each is re-encoded to <out>/audio/<seg>.mp3
Resumable: finished videos (all segments on disk) are skipped. Videos held out in manifests/yt_{dev,test} are skipped.
"""
import argparse
import json
import os
import re
import shlex
import subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).parent
YTDLP = shlex.split(os.environ.get("YTDLP", "uvx --from yt-dlp[default]@latest yt-dlp")) + ["--ignore-config"]
MIN_S, MAX_S, MAX_GAP = 3.0, 25.0, 1.5
PAD_L, PAD_R = 0.15, 0.25
TS = re.compile(r"(\d+):(\d\d):(\d\d)[.,](\d{3})\s*-->\s*(\d+):(\d\d):(\d\d)[.,](\d{3})")


def jl(p):
    return [json.loads(x) for x in open(p, encoding="utf-8") if x.strip()] if Path(p).exists() else []


def secs(h, m, s, ms):
    return int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000


def parse_vtt(p):
    cues, cur = [], None
    for line in open(p, encoding="utf-8"):
        line = line.strip()
        m = TS.search(line)
        if m:
            g = m.groups()
            cur = [secs(*g[:4]), secs(*g[4:]), []]
            cues.append(cur)
        elif line and cur is not None and not line.startswith(("WEBVTT", "Kind:", "Language:", "NOTE")):
            cur[2].append(re.sub(r"<[^>]+>", "", line))
        elif not line:
            cur = None
    out = []
    for s, e, t in cues:
        t = " ".join(x for x in t if x).strip()
        if not t or e <= s:
            continue
        if out and t == out[-1][2] and s - out[-1][1] < 0.05:  # rolling duplicates
            out[-1][1] = e
            continue
        out.append([s, e, t])
    return out


def segs_from_cues(cues, total):
    segs, cur = [], None
    for s, e, t in cues:
        if cur and (s - cur[1] <= MAX_GAP) and (e - cur[0] <= MAX_S):
            cur[1], cur[2] = e, cur[2] + [t]
        else:
            if cur:
                segs.append(cur)
            cur = [s, e, [t]]
    if cur:
        segs.append(cur)
    out = []
    for s, e, ts in segs:
        s, e = max(0.0, s - PAD_L), min(total, e + PAD_R)
        if MIN_S <= e - s <= MAX_S + PAD_L + PAD_R:
            out.append((s, e, " ".join(ts)))
    return out


def segs_from_silence(mp3, total):
    p = subprocess.run(["ffmpeg", "-nostdin", "-i", str(mp3), "-af", "silencedetect=noise=-35dB:d=0.35", "-f", "null", "-"],
                       capture_output=True, text=True)
    starts = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", p.stderr)]
    ends = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", p.stderr)]
    cuts = sorted({0.0, total, *[(a + b) / 2 for a, b in zip(starts, ends)]})
    out, s = [], cuts[0]
    for c in cuts[1:]:
        if c - s < 6.0 and c < total:
            continue
        while c - s > MAX_S:  # no silence for too long: hard split
            out.append((s, s + 20.0, ""))
            s += 20.0
        if c - s >= MIN_S:
            out.append((s, c, ""))
        s = c
    return out


def duration(mp3):
    p = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(mp3)],
                       capture_output=True, text=True)
    return float(p.stdout.strip() or 0)


def cut(job):
    src, s, e, dst = job
    if dst.exists():
        return True
    p = subprocess.run(["ffmpeg", "-nostdin", "-loglevel", "error", "-y", "-ss", f"{s:.3f}", "-to", f"{e:.3f}", "-i", str(src),
                        "-ac", "1", "-ar", "16000", "-c:a", "libmp3lame", "-b:a", "64k", str(dst)])
    return p.returncode == 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--channel", required=True)
    ap.add_argument("--ids", required=True)
    ap.add_argument("--out", default="yt_more2")
    ap.add_argument("--rate", default="5M")
    ap.add_argument("--workers", type=int, default=6)
    a = ap.parse_args()
    out = ROOT / a.out
    raw, aud = out / "raw", out / "audio"
    raw.mkdir(parents=True, exist_ok=True)
    aud.mkdir(parents=True, exist_ok=True)
    held = {r["video"] for s in ("dev", "test") for r in jl(ROOT / "manifests" / f"yt_{s}.jsonl")}
    meta = {r["seg"]: r for r in jl(out / "meta.jsonl")}
    ids = [line.split("\t")[0].strip() for line in open(a.ids, encoding="utf-8") if line.strip()]
    ids = [i for i in ids if re.fullmatch(r"[\w-]{11}", i)]
    tot_sub = tot_sil = 0
    for n, vid in enumerate(ids, 1):
        key = f"{a.channel}:{vid}"
        if key in held:
            print(f"[{n}/{len(ids)}] {vid} held out, skip", flush=True)
            continue
        mp3 = raw / f"{vid}.mp3"
        if not mp3.exists():
            p = subprocess.run(YTDLP + ["-f", "ba/b", "-x", "--audio-format", "mp3", "--postprocessor-args", "ffmpeg:-ac 1 -ar 16000",
                                        "--write-subs", "--sub-langs", "zh-HK,zh-Hant,zh-TW", "--sub-format", "vtt",
                                        "-r", a.rate, "-o", str(raw / "%(id)s.%(ext)s"), f"https://www.youtube.com/watch?v={vid}"],
                               capture_output=True, text=True)
            if not mp3.exists():
                print(f"[{n}/{len(ids)}] {vid} DOWNLOAD FAILED: {(p.stderr or p.stdout)[-300:]}", flush=True)
                continue
        total = duration(mp3)
        vtts = sorted(raw.glob(f"{vid}.*.vtt"), key=lambda q: [".zh-HK.", ".zh-Hant.", ".zh-TW."].index(
            next((x for x in [".zh-HK.", ".zh-Hant.", ".zh-TW."] if x in q.name), ".zh-TW.")))
        cues = parse_vtt(vtts[0]) if vtts else []
        segs = segs_from_cues(cues, total) if cues else segs_from_silence(mp3, total)
        route = "B-sub" if cues else "B-sil"
        jobs, rows = [], []
        for i, (s, e, t) in enumerate(segs):
            seg = f"{vid}_b{i:04d}"
            jobs.append((mp3, s, e, aud / f"{seg}.mp3"))
            rows.append({"seg": seg, "channel": a.channel, "video": key, "seconds": round(e - s, 3), "sub": t,
                         "start": round(s, 3), "route": route})
        with ThreadPoolExecutor(a.workers) as ex:
            ok = list(ex.map(cut, jobs))
        for r, k in zip(rows, ok):
            if k:
                meta[r["seg"]] = r
        h = sum(r["seconds"] for r, k in zip(rows, ok) if k) / 3600
        tot_sub, tot_sil = tot_sub + (h if cues else 0), tot_sil + (0 if cues else h)
        print(f"[{n}/{len(ids)}] {vid} {total / 60:.0f} min, {route}, {sum(ok)} segs {h:.2f} h", flush=True)
        with open(out / "meta.jsonl", "w", encoding="utf-8") as f:
            for r in meta.values():
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
    hrs = sum(r["seconds"] for r in meta.values()) / 3600
    print(f"SEGMENT DONE meta {len(meta)} segs {hrs:.2f} h (this run: subtitle route {tot_sub:.2f} h, silence route {tot_sil:.2f} h)",
          flush=True)


if __name__ == "__main__":
    main()
