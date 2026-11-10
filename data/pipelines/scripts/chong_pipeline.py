"""床哥心事台 highlight clips -> verbatim Cantonese training data via gemini-3.8-flash.

usage: python data_yue/chong_pipeline.py [--hours 15] [--budget-usd 3] [--workers 8]
1. pick fan highlight videos (cands.tsv from yt-dlp search; title contains 床, 5-67 min) up to --hours
2. yt-dlp audio only, capped at 5 MB/s, 16 kHz mono mp3; creator subtitles (zh-HK / zh-Hant, not auto) if any
3. cut at silences (ffmpeg silencedetect) into 3-25 s chunks; overlapping subtitle cues become a hint
4. Gemini verbatim colloquial transcript per chunk (paid key, budget-capped) -> data_yue/chong/chong.jsonl
Audio stays local (personal research use; never pushed to any repo).
"""

import argparse
import base64
import json
import os
import random
import re
import subprocess
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import threading
import urllib.error

STOP = threading.Event()
D = Path(__file__).parent / "chong"
KEY = os.environ.get("GEMINI_API_KEY") or Path(os.environ["GEMINI_API_KEY_FILE"]).read_text().strip()
PRICE_IN, PRICE_OUT = 0.75 / 1e6, 3.75 / 1e6
PROMPT = (
    "下面係一段香港網台直播節目（床哥心事台，有 call-in、傾偈、講笑）嘅錄音片段。請逐字寫低實際講嘅廣東話口語"
    "（繁體中文，用粵語字例如 嘅 咗 喺 佢 冇 啲 嘢 噉 咩 嚟，俗語、潮語、粗口照寫，唔好改做書面語），英文字保留英文，"
    "數字照讀音寫成中文字。聽唔清楚嘅位寫 [?]，唔好估。唔好加解釋、講者標記、時間碼或者標點以外嘅符號，只輸出轉寫。"
)


def sh(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, **kw)


def vtt_cues(path: Path):
    cues = []
    for block in path.read_text(encoding="utf-8", errors="ignore").split("\n\n"):
        m = re.search(r"(\d+):(\d+):(\d+)[.,](\d+) --> (\d+):(\d+):(\d+)[.,](\d+)", block)
        if not m:
            continue
        g = [int(x) for x in m.groups()]
        a = g[0] * 3600 + g[1] * 60 + g[2] + g[3] / 1000
        b = g[4] * 3600 + g[5] * 60 + g[6] + g[7] / 1000
        text = " ".join(line for line in block.splitlines()[1:] if "-->" not in line).strip()
        text = re.sub(r"<[^>]+>", "", text)
        if text:
            cues.append((a, b, text))
    return cues


def chunks_for(mp3: Path, dur: float):
    for thr in (-35, -30, -26, -22, -18):  # background music: raise the threshold until pauses show up (~1 per 12 s)
        out = sh(["ffmpeg", "-hide_banner", "-nostats", "-i", str(mp3), "-af", f"silencedetect=noise={thr}dB:d=0.25", "-f", "null", "-"]).stderr
        mids = sorted((float(a) + float(b)) / 2 for a, b in re.findall(r"silence_start: ([\d.]+).*?silence_end: ([\d.]+)", out, re.S))
        if len(mids) >= dur / 12:
            break
    cuts, start, last = [], 0.0, None  # greedy: cut at the last silence that keeps the chunk <= 25 s
    for m in mids + [dur]:
        while m - start > 25:
            end = last if (last is not None and last - start >= 3) else start + 25
            cuts.append((start, end))
            start, last = end, None
        last = m
    if dur - start >= 3:
        cuts.append((start, dur))
    return [(s, e) for s, e in cuts if e - s >= 3]


def gemini(mp3: bytes, hint: str):
    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.8-flash:generateContent"
    text = PROMPT + (f"\n\n參考字幕（可能係書面語或者唔完整，只用嚟參考人名同英文字）：{hint}" if hint else "")
    body = {
        "contents": [{"parts": [{"text": text}, {"inline_data": {"mime_type": "audio/mp3", "data": base64.b64encode(mp3).decode()}}]}],
        "generationConfig": {"temperature": 0, "thinkingConfig": {"thinkingBudget": 0}},
    }
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, data=json.dumps(body).encode(), headers={"Content-Type": "application/json", "x-goog-api-key": KEY})
            d = json.load(urllib.request.urlopen(req, timeout=180))
            out = "".join(p.get("text", "") for p in d["candidates"][0]["content"].get("parts", [])).strip()
            u = d.get("usageMetadata", {})
            return out, u.get("promptTokenCount", 0), u.get("candidatesTokenCount", 0) + u.get("thoughtsTokenCount", 0)
        except urllib.error.HTTPError as e:
            msg = e.read().decode()[:300]
            print("HTTP", e.code, msg[:160], flush=True)
            if "spending cap" in msg:  # project spend cap hit: stop everything instead of retrying
                STOP.set()
                return "", 0, 0
            time.sleep(5 * (attempt + 1))
        except Exception as e:  # noqa: BLE001
            print("retry", attempt, type(e).__name__, str(e)[:160], flush=True)
            time.sleep(5 * (attempt + 1))
    return "", 0, 0


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--hours", type=float, default=15)
    p.add_argument("--budget-usd", type=float, default=3.0)
    p.add_argument("--workers", type=int, default=8)
    a = p.parse_args()
    vids = [line.rstrip("\n").split("\t") for line in open(D / "cands.tsv", encoding="utf-8")]
    vids = [v for v in vids if len(v) >= 4 and v[1].replace(".", "").isdigit() and 300 < float(v[1]) < 4000 and "床" in v[3]]
    random.Random(0).shuffle(vids)
    pick, tot = [], 0.0
    for v in vids:
        if tot >= a.hours * 3600:
            break
        pick.append(v)
        tot += float(v[1])
    print(f"picked {len(pick)} videos, {tot / 3600:.1f} h", flush=True)
    (D / "audio").mkdir(exist_ok=True)
    (D / "chunks").mkdir(exist_ok=True)
    jobs = []
    for vid, dur, chan, title in pick:
        mp3 = D / "audio" / f"{vid}.mp3"
        if not mp3.exists():
            # --ignore-config: the user config's account cookies make YouTube return a broken page (KeyError INNERTUBE_CONTEXT)
            sh(["yt-dlp", "--ignore-config", "--sleep-requests", "1", "--socket-timeout", "30", "-q", "-r", "5M", "-f", "bestaudio", "-x", "--audio-format", "mp3", "--postprocessor-args", "ffmpeg:-ac 1 -ar 16000 -b:a 48k",
                "--write-subs", "--sub-langs", "zh-HK,zh-Hant", "--sub-format", "vtt", "-o", str(D / "audio" / "%(id)s.%(ext)s"), f"https://www.youtube.com/watch?v={vid}"])
        if not mp3.exists():
            print("download failed", vid, flush=True)
            continue
        subs = sorted((D / "audio").glob(f"{vid}*.vtt"))
        cues = vtt_cues(subs[0]) if subs else []
        for i, (s, e) in enumerate(chunks_for(mp3, float(dur))):
            c = D / "chunks" / f"{vid}_{i:04d}.mp3"
            if not c.exists():
                sh(["ffmpeg", "-v", "error", "-y", "-ss", f"{s:.2f}", "-to", f"{e:.2f}", "-i", str(mp3), "-c:a", "libmp3lame", "-b:a", "48k", str(c)])
            hint = " ".join(t for (cs, ce, t) in cues if ce > s and cs < e)
            jobs.append({"chunk": c.name, "video": vid, "channel": chan, "title": title, "start": round(s, 2), "seconds": round(e - s, 2), "hint": hint})
    print(f"{len(jobs)} chunks, {sum(j['seconds'] for j in jobs) / 3600:.2f} h, {sum(bool(j['hint']) for j in jobs)} with subtitle hint", flush=True)
    # resume: keep chunks already transcribed (non-empty), redo the rest; write each row as soon as it is done
    out_path = D / "chong.jsonl"
    kept = []
    if out_path.exists():
        kept = [r for r in (json.loads(line) for line in open(out_path, encoding="utf-8")) if r["text"]]
    done = {r["chunk"] for r in kept}
    spent = sum(r["usd"] for r in kept)
    with open(out_path, "w", encoding="utf-8") as f:
        for r in kept:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    jobs = [j for j in jobs if j["chunk"] not in done]
    print(f"resume: {len(kept)} done, ${spent:.3f}; {len(jobs)} to go", flush=True)
    out = open(out_path, "a", encoding="utf-8")

    def run(j):
        if spent > a.budget_usd or STOP.is_set():
            return None
        text, tin, tout = gemini((D / "chunks" / j["chunk"]).read_bytes(), j["hint"])
        return {**j, "text": text, "usd": round(tin * PRICE_IN + tout * PRICE_OUT, 6)}

    n = failed = 0
    with ThreadPoolExecutor(a.workers) as ex:
        for r in ex.map(run, jobs):
            if r is None:
                continue
            spent += r["usd"]
            if not r["text"]:  # failed: leave it out so a rerun retries it
                failed += 1
                continue
            n += 1
            out.write(json.dumps(r, ensure_ascii=False) + "\n")
            out.flush()
            if n % 200 == 0:
                print(f"{n} chunks, ${spent:.3f}", flush=True)
    out.close()
    print(json.dumps({"chunks": n + len(kept), "failed": failed, "usd": round(spent, 3), "budget_hit": spent > a.budget_usd, "spend_cap_hit": STOP.is_set()}), flush=True)


if __name__ == "__main__":
    main()
