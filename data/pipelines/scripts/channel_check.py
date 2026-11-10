#!/usr/bin/env python3
"""Stage 0 of youtube-ingest.md: size up a YouTube channel before downloading anything.

usage: python channel_check.py HANDLE [HANDLE ...] [--sample 5] [--seed 0] [--json out.json]
  HANDLE is the part after "@" in https://www.youtube.com/@HANDLE

For each channel, per tab (videos, streams): item count and hours, split into public vs members-only
(members-only cannot be downloaded), how many items are >= 10 min, and a few title keywords.
Then it samples --sample public videos >= 10 min and reports which have creator subtitles
(zh-HK / zh-Hant / yue), because tri-label arbitration needs them as the third label.

yt-dlp: set YTDLP to the command to run (default: "uvx --from yt-dlp[default]@latest yt-dlp").
--ignore-config is always passed: on 2026-11-10 a cookies file in the yt-dlp config made every per-video
extraction fail with KeyError('INNERTUBE_CONTEXT'). Channel tabs also need
--extractor-args youtubetab:skip=authcheck.
"""
import argparse
import json
import os
import random
import re
import shlex
import subprocess
from collections import Counter

YTDLP = shlex.split(os.environ.get("YTDLP", "uvx --from yt-dlp[default]@latest yt-dlp")) + ["--ignore-config"]
SUB_LANGS = ("zh-HK", "zh-Hant", "zh-TW", "yue")


def run(args, timeout=600):
    p = subprocess.run(YTDLP + args, capture_output=True, text=True, timeout=timeout)
    return p.stdout


def tab(handle, name):
    out = run(["--extractor-args", "youtubetab:skip=authcheck", "--flat-playlist",
               "--print", "%(id)s\t%(availability)s\t%(duration)s\t%(title)s",
               f"https://www.youtube.com/@{handle}/{name}"])
    rows = []
    for line in out.splitlines():
        parts = line.split("\t")
        if len(parts) < 4:
            continue
        vid, avail, dur, title = parts[0], parts[1], parts[2], parts[3]
        rows.append({"id": vid, "members_only": avail == "subscriber_only",
                     "seconds": float(dur) if dur not in ("NA", "None", "") else None, "title": title})
    return rows


def summarise(rows):
    def hours(rs):
        return round(sum(r["seconds"] or 0 for r in rs) / 3600, 1)
    pub = [r for r in rows if not r["members_only"]]
    mem = [r for r in rows if r["members_only"]]
    long_pub = [r for r in pub if (r["seconds"] or 0) >= 600]
    return {"items": len(rows), "public": len(pub), "public_h": hours(pub), "members_only": len(mem),
            "members_only_h": hours(mem), "public_ge_10min": len(long_pub), "public_ge_10min_h": hours(long_pub)}


def subtitles(vid):
    out = run(["--skip-download", "--dump-json", f"https://www.youtube.com/watch?v={vid}"], timeout=180)
    try:
        d = json.loads(out)
    except json.JSONDecodeError:
        return None
    return sorted(k for k in d.get("subtitles", {}) if k != "live_chat")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("handles", nargs="+")
    ap.add_argument("--sample", type=int, default=5)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--json")
    a = ap.parse_args()
    report = {}
    for h in a.handles:
        vids, streams = tab(h, "videos"), tab(h, "streams")
        shows = Counter(re.split(r"[｜|]", r["title"])[0].strip()[:30] for r in vids)
        pool = [r for r in vids if not r["members_only"] and (r["seconds"] or 0) >= 600]
        picks = random.Random(a.seed).sample(pool, min(a.sample, len(pool)))
        subs = {r["id"]: subtitles(r["id"]) for r in picks}
        with_subs = sum(1 for s in subs.values() if s and any(x in SUB_LANGS for x in s))
        report[h] = {"videos": summarise(vids), "streams": summarise(streams),
                     "top_title_prefixes": shows.most_common(8),
                     "subtitle_sample": {"checked": len(subs), "with_creator_zh_subs": with_subs, "per_video": subs}}
        v, s = report[h]["videos"], report[h]["streams"]
        print(f"@{h}: videos public {v['public']} / {v['public_h']} h (members-only {v['members_only']} / "
              f"{v['members_only_h']} h); streams public {s['public']} / {s['public_h']} h (members-only "
              f"{s['members_only']} / {s['members_only_h']} h); creator zh subtitles in {with_subs}/{len(subs)} sampled")
    if a.json:
        with open(a.json, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
