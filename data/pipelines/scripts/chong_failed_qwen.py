"""床哥 chunks that Gemini returned nothing for: ask Gemini once more for the block reason, then transcribe with Qwen3-ASR.

usage: MIOPEN_FIND_MODE=FAST python data_yue/chong_failed_qwen.py
Writes data_yue/chong/failed_qwen.jsonl (chunk, video, title, start, seconds, subtitle hint, gemini block info, qwen text).
"""

import base64
import json
import subprocess
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import chong_pipeline as cp  # noqa: E402

D = cp.D
done = {json.loads(line)["chunk"] for line in open(D / "chong.jsonl", encoding="utf-8")}
failed = sorted(p.name for p in (D / "chunks").glob("*.mp3") if p.name not in done)
meta = {v[0]: v for v in (line.rstrip("\n").split("\t") for line in open(D / "cands.tsv", encoding="utf-8")) if len(v) >= 4}
print(len(failed), "failed chunks", flush=True)

rows, cuts_cache = [], {}
for name in failed:
    vid, i = name[:-4].rsplit("_", 1)
    mp3 = D / "audio" / f"{vid}.mp3"
    if vid not in cuts_cache:
        cuts_cache[vid] = cp.chunks_for(mp3, float(meta[vid][1]))
    s, e = cuts_cache[vid][int(i)]
    subs = sorted((D / "audio").glob(f"{vid}*.vtt"))
    cues = cp.vtt_cues(subs[0]) if subs else []
    hint = " ".join(t for (cs, ce, t) in cues if ce > s and cs < e)
    rows.append({"chunk": name, "video": vid, "channel": meta[vid][2], "title": meta[vid][3], "start": round(s, 1), "seconds": round(e - s, 1), "sub": hint})


def gemini_reason(mp3: bytes, hint: str):
    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.8-flash:generateContent"
    text = cp.PROMPT + (f"\n\n參考字幕（可能係書面語或者唔完整，只用嚟參考人名同英文字）：{hint}" if hint else "")
    body = {
        "contents": [{"parts": [{"text": text}, {"inline_data": {"mime_type": "audio/mp3", "data": base64.b64encode(mp3).decode()}}]}],
        "generationConfig": {"temperature": 0, "thinkingConfig": {"thinkingBudget": 0}},
    }
    req = urllib.request.Request(url, data=json.dumps(body).encode(), headers={"Content-Type": "application/json", "x-goog-api-key": cp.KEY})
    try:
        d = json.load(urllib.request.urlopen(req, timeout=180))
    except Exception as ex:  # noqa: BLE001
        return {"error": str(ex)[:200]}
    c = (d.get("candidates") or [{}])[0]
    out = "".join(p.get("text", "") for p in c.get("content", {}).get("parts", []))
    return {"promptFeedback": d.get("promptFeedback"), "finishReason": c.get("finishReason"), "text": out[:300]}


for r in rows:
    r["gemini_retry"] = gemini_reason((D / "chunks" / r["chunk"]).read_bytes(), r["sub"])
    print(r["chunk"], json.dumps(r["gemini_retry"], ensure_ascii=False)[:200], flush=True)

import torch  # noqa: E402

import eval_baselines as eb  # noqa: E402

asr = eb.Qwen3ASR()
wavs = [eb.load_audio(str(D / "chunks" / r["chunk"])) for r in rows]
for b in range(0, len(rows), 8):
    for r, h in zip(rows[b : b + 8], asr(wavs[b : b + 8])):
        r["qwen"] = h.strip()
with open(D / "failed_qwen.jsonl", "w", encoding="utf-8") as f:
    for r in rows:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")
print("DONE", flush=True)
