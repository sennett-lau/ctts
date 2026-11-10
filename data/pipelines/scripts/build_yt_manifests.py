"""YouTube-derived Cantonese sets (床哥 highlights + OrcinusOrca ahju/bbo) -> manifests yt_{train,dev,test}.jsonl.

usage: python data_yue/build_yt_manifests.py
Labels: 床哥 = Gemini pass 2 (audio + burned-in subtitle OCR + Qwen hint, chong/quality.jsonl); OrcinusOrca = Gemini
(audio + creator subtitle hint, yt_pilot/<tar>.jsonl). Grade = CER of the label vs an independent Qwen3-ASR transcript
(t2s + numnorm, punctuation dropped): good <= 0.15, ok <= 0.35, else bad.
Split by VIDEO (no video in two splits): test ~1.5 h, dev ~0.6 h, rest train.
  train: grade good/ok, no [?], no digits (same rule as every other train set)
  dev/test: every held-out row with a label and no [?] (no agreement filter: it would favour Qwen-like outputs)
Writes data_yue/manifests/yt_*.jsonl and data_yue/manifests/yt_summary.json.
"""

import hashlib
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT.parent / "src"))
import opencc  # noqa: E402

from embed2asr.metrics import edit_distance  # noqa: E402
from embed2asr.numnorm import norm_nn  # noqa: E402

MAN = ROOT / "manifests"
t2s = opencc.OpenCC("t2s")
KEEP = set("abcdefghijklmnopqrstuvwxyz0123456789")


def jl(p):
    return [json.loads(line) for line in open(p, encoding="utf-8")] if Path(p).exists() else []


def clean_cmp(s):
    s = t2s.convert(norm_nn(s.replace("[?]", ""), "zh")).lower().replace("噶", "㗎")
    return "".join(ch for ch in s if ch in KEEP or "\u3400" <= ch <= "\u9fff" or "\U00020000" <= ch <= "\U0002ffff")


def cer(ref, hyp):
    r, h = clean_cmp(ref), clean_cmp(hyp)
    return edit_distance(list(r), list(h)) / max(len(r), 1) if r else (0.0 if not h else 1.0)


def grade(c):
    return "good" if c <= 0.15 else "ok" if c <= 0.35 else "bad"


def tidy(t):
    t = re.sub(r"[「」『』“”\"]", "", t)
    return re.sub(r"\s+", " ", t).strip()


def hkey(s):
    return hashlib.md5(s.encode()).hexdigest()


rows = []
# 床哥
meta = {r["chunk"]: r for r in jl(ROOT / "chong" / "chong.jsonl")}
for r in jl(ROOT / "chong" / "failed_qwen.jsonl"):
    meta.setdefault(r["chunk"], r)
for q in jl(ROOT / "chong" / "quality.jsonl"):
    m = meta.get(q["chunk"])
    if not m or not q.get("gemini2"):
        continue
    rows.append({"audio": str(ROOT / "chong" / "chunks" / q["chunk"]), "text": tidy(q["gemini2"]), "lang": "yue",
                 "speaker_id": f"chong-{m['channel']}", "seconds": q["seconds"], "video": "chong:" + q["chunk"][:-4].rsplit("_", 1)[0],
                 "src": "chong", "cer_qwen": q.get("cer_g2_qwen")})
# OrcinusOrca
qy = {r["id"]: r["qwen"] for r in jl(ROOT / "yt_pilot" / "qwen.jsonl")}
for f in sorted((ROOT / "yt_pilot").glob("*_000.jsonl")):
    ch = f.stem.rsplit("_", 1)[0]
    for r in jl(f):
        if not r["gemini"]:
            continue
        q = qy.get(r["seg"])
        rows.append({"audio": str(ROOT / "yt_pilot" / "audio" / f"{r['seg']}.mp3"), "text": tidy(r["gemini"]), "lang": "yue",
                     "speaker_id": f"yt-{ch}", "seconds": r["seconds"], "video": f"{ch}:" + r["seg"].rsplit("_", 1)[0],
                     "src": ch, "cer_qwen": round(cer(r["gemini"], q), 3) if q else None})

for r in rows:
    r["grade"] = "unk" if r["cer_qwen"] is None else grade(r["cer_qwen"])

# split by video, deterministic: hash order within each source, fill test then dev per source proportional to its hours
by_src = defaultdict(lambda: defaultdict(list))
for r in rows:
    by_src[r["src"]][r["video"]].append(r)
tot_h = sum(r["seconds"] for r in rows) / 3600
split_of = {}
for src, vids in by_src.items():
    src_h = sum(r["seconds"] for v in vids.values() for r in v) / 3600
    want_test, want_dev = 1.5 * src_h / tot_h, 0.6 * src_h / tot_h
    th = dh = 0.0
    for v in sorted(vids, key=hkey):
        h = sum(r["seconds"] for r in vids[v]) / 3600
        if th < want_test:
            split_of[v], th = "test", th + h
        elif dh < want_dev:
            split_of[v], dh = "dev", dh + h
        else:
            split_of[v] = "train"

out = {"train": [], "dev": [], "test": []}
for r in rows:
    s = split_of[r["video"]]
    if "[?]" in r["text"] or not r["text"]:
        continue
    if s == "train" and (r["grade"] not in ("good", "ok") or any(c.isdigit() for c in r["text"])):
        continue
    out[s].append(r)

# Extra tri-labelled YouTube segments (data_yue/yt_more/merged.jsonl): train-only, dev/test stay identical
held_vids = {v for v, sp in split_of.items() if sp in ("dev", "test")}
seen_audio = {r["audio"] for rs in out.values() for r in rs}
tri_added = []
for m in jl(ROOT / "yt_more" / "merged.jsonl"):
    if m.get("status") == "reject" or m["video"] in held_vids or m["audio"] in seen_audio:
        continue
    t = tidy(m["text"])
    if not t or "[?]" in t or any(c.isdigit() for c in t):
        continue
    row = {"audio": m["audio"], "text": t, "lang": "yue", "speaker_id": f"yt-{m['channel']}",
           "seconds": m["seconds"], "video": m["video"], "src": m["channel"],
           "grade": "good" if m["status"] == "sync" else "ok"}
    out["train"].append(row)
    tri_added.append(row)
    seen_audio.add(m["audio"])
    by_src[m["channel"]][m["video"]].append(row)

summary = {"all_rows": len(rows) + len(tri_added), "all_hours": round(tot_h + sum(r["seconds"] for r in tri_added) / 3600, 2),
           "tri_added_rows": len(tri_added), "tri_added_hours": round(sum(r["seconds"] for r in tri_added) / 3600, 2)}
for g in ("good", "ok", "bad", "unk"):
    sel = [r for r in rows if r["grade"] == g]
    summary[f"grade_{g}"] = {"rows": len(sel), "hours": round(sum(r["seconds"] for r in sel) / 3600, 2)}
for s, rs in out.items():
    with open(MAN / f"yt_{s}.jsonl", "w", encoding="utf-8") as f:
        for r in rs:
            f.write(json.dumps({k: r[k] for k in ("audio", "text", "lang", "speaker_id", "seconds", "video", "grade")}, ensure_ascii=False) + "\n")
    summary[s] = {"rows": len(rs), "hours": round(sum(r["seconds"] for r in rs) / 3600, 2), "videos": len({r["video"] for r in rs}),
                  "by_src": {src: round(sum(r["seconds"] for r in rs if r["src"] == src) / 3600, 2) for src in by_src}}
(MAN / "yt_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1), encoding="utf-8")
print(json.dumps(summary, ensure_ascii=False, indent=1))
