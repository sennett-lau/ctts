"""Burned-in subtitle OCR for the 床哥 highlight videos -> timestamped cues (run with .venv-ocr, RapidOCR).

usage: .venv-ocr/bin/python data_yue/chong_ocr.py [--workers 6] [VIDEO_ID ...]
Per video (data_yue/chong/video/<id>.mp4, 480p):
  1. band: OCR 40 evenly spaced full frames; text that shows up in >=30% of them is a static overlay (title, logo);
     the subtitle band is the densest y-region of the remaining (changing) text boxes
  2. decode the band at 3 fps (ffmpeg crop), start a new segment whenever the crop changes, OCR each segment once
  3. drop static lines, speaker tags (short lines repeated in many segments) and low-score lines; merge repeats
Writes data_yue/chong/ocr/<id>.json = {"band": [...], "static": [...], "tags": [...], "cues": [[start, end, text], ...]}
"""

import argparse
import json
import os
import re
import subprocess
from collections import Counter
from multiprocessing import Pool
from pathlib import Path

import numpy as np

D = Path(__file__).parent / "chong"
OUT = D / "ocr"
FPS = 2


def probe(p):
    o = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height:format=duration",
                        "-of", "json", str(p)], capture_output=True, text=True).stdout
    j = json.loads(o)
    return j["streams"][0]["width"], j["streams"][0]["height"], float(j["format"]["duration"])


def frame_at(p, t, w, h):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.2f}", "-i", str(p), "-frames:v", "1", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                         capture_output=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(h, w, 3) if len(raw) == w * h * 3 else None


def norm(t):
    return re.sub(r"\s+", "", t)


CHAT = re.compile(r"@|^[A-Za-z0-9_.\-]{3,}\s*[:：]|[\u4e00-\u9fff]{1,8}\s*[：]")


def is_chat(t):
    """Live-chat overlay line ('@user: ...', 'name：...'), not a subtitle."""
    return bool(CHAT.search(t))


def ocr_lines(eng, img, min_score=0.6):
    r = eng(img)
    if r.boxes is None:
        return []
    out = []
    for box, txt, sc in zip(r.boxes, r.txts, r.scores):
        if sc >= min_score and norm(txt):
            ys = [pt[1] for pt in box]
            xs = [pt[0] for pt in box]
            out.append((min(ys), max(ys), min(xs), max(xs), txt.strip()))
    return out


def find_band(eng, p, w, h, dur):
    samples = [frame_at(p, dur * (i + 0.5) / 40, w, h) for i in range(40)]
    lines = [ocr_lines(eng, f) for f in samples if f is not None]
    cnt = Counter(norm(t) for ls in lines for t in {x[4] for x in ls})
    static = {t for t, c in cnt.items() if c >= 0.3 * len(lines)}
    # subtitles are horizontally centred; live-chat / comment overlays sit at the sides and change just as often
    boxes = [b for ls in lines for b in ls
             if norm(b[4]) not in static and len(norm(b[4])) >= 3 and abs((b[2] + b[3]) / 2 - w / 2) < 0.15 * w and not is_chat(b[4])]
    low = [b for b in boxes if (b[0] + b[1]) / 2 >= 0.55 * h]  # subtitles normally sit in the lower part: prefer it
    boxes = low if len(low) >= 8 else boxes
    if len(boxes) < 5:
        return None, static
    bins = Counter(int(((b[0] + b[1]) / 2) / h * 20) for b in boxes)  # 5%-of-height bins of box centres
    peak, pc = bins.most_common(1)[0]
    keep = {peak}
    for step in (1, -1):  # grow over adjacent bins that are still busy
        k = peak + step
        while bins.get(k, 0) >= 0.2 * pc:
            keep.add(k)
            k += step
    sel = [b for b in boxes if int(((b[0] + b[1]) / 2) / h * 20) in keep]
    y0 = max(0, int(min(b[0] for b in sel)) - 6)
    y1 = min(h, int(max(b[1] for b in sel)) + 6)
    x0 = max(0, int(min(b[2] for b in sel)) - 20)
    x1 = min(w, int(max(b[3] for b in sel)) + 20)
    y0 -= y0 % 2
    x0 -= x0 % 2
    return (x0, y0, (x1 - x0) // 2 * 2, (y1 - y0) // 2 * 2), static


def segments(p, band):
    x, y, bw, bh = band
    proc = subprocess.Popen(["ffmpeg", "-v", "error", "-i", str(p), "-vf", f"fps={FPS},crop={bw}:{bh}:{x}:{y}", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                            stdout=subprocess.PIPE)
    n, cur, cur_m, start = 0, None, None, 0
    size = bw * bh * 3
    while True:
        buf = proc.stdout.read(size)
        if len(buf) < size:
            break
        f = np.frombuffer(buf, np.uint8).reshape(bh, bw, 3)
        # subtitle text is near-white or yellow; compare that mask only, so moving video behind the text is ignored
        r, g, b = f[..., 0].astype(np.int16), f[..., 1].astype(np.int16), f[..., 2].astype(np.int16)
        m = ((r > 200) & (g > 200) & (b > 200)) | ((r > 190) & (g > 160) & (b < 110))
        if cur_m is None or (m ^ cur_m).sum() > 0.2 * max(1, (m | cur_m).sum()):
            if cur is not None:
                yield start / FPS, n / FPS, cur
            cur, cur_m, start = f, m, n
        n += 1
    if cur is not None:
        yield start / FPS, n / FPS, cur
    proc.wait()


def work(vid):
    from rapidocr import RapidOCR

    # det default (limit_type min, 736) upscales a 124 px high band to 736 px: ~1 s per call; cap the long side instead
    eng = RapidOCR(params={"Global.log_level": "error", "Global.use_cls": False, "EngineConfig.onnxruntime.intra_op_num_threads": 2,
                           "Det.limit_type": "max", "Det.limit_side_len": 960})
    p = D / "video" / f"{vid}.mp4"
    w, h, dur = probe(p)
    full = RapidOCR(params={"Global.log_level": "error", "Global.use_cls": False, "EngineConfig.onnxruntime.intra_op_num_threads": 2})
    band, static = find_band(full, p, w, h, dur)  # default det sizing: slower but finds small subtitle text on full frames
    if band is None:
        res = {"band": None, "static": sorted(static), "tags": [], "cues": []}
    else:
        segs = []
        for s, e, crop in segments(p, band):
            if crop.std() < 12:  # flat band: no text
                continue
            segs.append((s, e, [t for (_, _, _, _, t) in ocr_lines(eng, crop)]))
        cnt = Counter(norm(t) for _, _, ls in segs for t in set(ls))
        tags = {t for t, c in cnt.items() if len(t) <= 4 and c >= max(5, 0.1 * len(segs))}
        # logo / name-plate words that ride along with the subtitle line (e.g. 'MANFT') repeat across many segments
        tok = Counter(x for _, _, ls in segs for x in {y for t in ls for y in t.split()})
        junk = {x for x, c in tok.items() if len(x) <= 12 and c >= max(5, 0.08 * len(segs))}
        cues = []
        for s, e, ls in segs:
            ls = [" ".join(y for y in t.split() if y not in junk) for t in ls]
            text = " ".join(t for t in ls if t and norm(t) not in static and norm(t) not in tags and not is_chat(t))
            if not text:
                continue
            if cues and norm(cues[-1][2]) == norm(text) and s - cues[-1][1] < 0.7:
                cues[-1][1] = e
            else:
                cues.append([round(s, 2), round(e, 2), text])
        res = {"band": band, "static": sorted(static), "tags": sorted(tags), "cues": cues}
    (OUT / f"{vid}.json").write_text(json.dumps(res, ensure_ascii=False), encoding="utf-8")
    return vid, band, len(res["cues"])


def main():
    a = argparse.ArgumentParser()
    a.add_argument("ids", nargs="*")
    a.add_argument("--workers", type=int, default=6)
    a = a.parse_args()
    OUT.mkdir(exist_ok=True)
    ids = a.ids or sorted(p.stem for p in (D / "video").glob("*.mp4") if not (OUT / f"{p.stem}.json").exists())
    os.environ.setdefault("OMP_NUM_THREADS", "2")
    with Pool(a.workers) as pool:
        for vid, band, n in pool.imap_unordered(work, ids):
            print(vid, band, n, "cues", flush=True)
    print("OCR DONE", flush=True)


if __name__ == "__main__":
    main()
