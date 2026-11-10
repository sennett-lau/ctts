"""Burned-in subtitle strips for some 床哥 chunks: download the video span, sample frames, crop the subtitle band,
drop near-duplicate crops, stack them into one tall image per chunk (for reading the hard subtitles).

usage: python data_yue/chong_sub_strips.py CHUNK [CHUNK ...]   (names as in data_yue/chong/failed_qwen.jsonl)
Writes data_yue/chong/substrips/<chunk>.jpg
"""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image

D = Path(__file__).parent / "chong"
OUT = D / "substrips"
OUT.mkdir(exist_ok=True)
rows = {json.loads(line)["chunk"]: json.loads(line) for line in open(D / "failed_qwen.jsonl", encoding="utf-8")}

for name in sys.argv[1:]:
    r = rows[name]
    s, e = r["start"], r["start"] + r["seconds"]
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        subprocess.run(["yt-dlp", "--ignore-config", "-q", "-f", "bv*[height<=480][ext=mp4]/bv*[height<=480]",
                        "--download-sections", f"*{s:.1f}-{e:.1f}", "-o", str(td / "v.%(ext)s"),
                        f"https://www.youtube.com/watch?v={r['video']}"], check=False)
        vids = list(td.glob("v.*"))
        if not vids:
            print(name, "download failed")
            continue
        subprocess.run(["ffmpeg", "-v", "error", "-i", str(vids[0]), "-vf", "fps=3", str(td / "f_%04d.png")], check=True)
        crops, last = [], None
        for f in sorted(td.glob("f_*.png")):
            im = Image.open(f).convert("RGB")
            w, h = im.size
            c = im.crop((int(w * 0.12), int(h * 0.82), int(w * 0.88), int(h * 0.985)))
            a = np.asarray(c.convert("L"), dtype=np.float32)
            if last is not None and np.abs(a - last).mean() < 6:  # same subtitle as previous kept crop
                continue
            last = a
            crops.append(c)
        W = max(c.width for c in crops)
        sheet = Image.new("RGB", (W, sum(c.height + 4 for c in crops)), "white")
        y = 0
        for c in crops:
            sheet.paste(c, (0, y))
            y += c.height + 4
        sheet.save(OUT / f"{name[:-4]}.jpg", quality=90)
        print(name, len(crops), "strips", sheet.size)
