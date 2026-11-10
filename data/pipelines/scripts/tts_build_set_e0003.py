#!/usr/bin/env python3
"""E0003 data build (runs on Colab): HK-only manifests -> filters -> 24 kHz mono FLAC -> single-speaker check (YouTube)
-> 12 Hz audio codes -> /content/tts/train.jsonl (the recipe trainer's format) + stats.json + refs.json (eval voices).

Mix (ctts data/mixes/tts-lang-phase1-v0, 0% CV yue): HK YouTube (all that pass, <=15 h per channel), CV zh-HK
(<=30k clips, <=1500 per contributor), MDCC (<=30k clips), MCE (all). 3-30 s, no digits, no [?].
"""
import json
import os
import random
import re
import subprocess
import sys
import time
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
import soundfile as sf
import torch

B = Path("/content/e0003")
W = Path("/content/tts")
WAV = W / "wav24"
BASE = "/content/base"
SEED = 4242
LIMITS = {"yt": None, "cvhk": 30000, "mdcc": 30000, "mce": None}
CVHK_PER_SPK = 1500
YT_SPK_CAP_H = 15.0
MIN_S, MAX_S = 3.0, 30.0
SIM_MIN = 0.75
NPROC = os.cpu_count() or 8


def log(*a):
    print(time.strftime("%H:%M:%S"), *a, flush=True)


def jl(p):
    return [json.loads(x) for x in open(p, encoding="utf-8") if x.strip()]


rng = random.Random(SEED)
rows = []
for src, fn in (("yt", "yt_train"), ("cvhk", "cvhk_train"), ("mdcc", "mdcc_train"), ("mce", "mce_train")):
    rs = jl(B / "manifests" / f"{fn}.jsonl")
    n0 = len(rs)
    rs = [r for r in rs if r["text"].strip() and "[?]" not in r["text"] and not re.search(r"\d", r["text"])]
    rs = [r for r in rs if Path(r["audio"]).exists()]
    n_exist = len(rs)
    rs = [r for r in rs if not r.get("seconds") or MIN_S <= r["seconds"] <= MAX_S]
    rng.shuffle(rs)
    if src == "cvhk":
        per, keep = Counter(), []
        for r in rs:
            if per[r["speaker_id"]] < CVHK_PER_SPK:
                per[r["speaker_id"]] += 1
                keep.append(r)
        rs = keep
    if src == "yt":
        per, keep = Counter(), []
        for r in rs:
            if per[r["speaker_id"]] + r["seconds"] <= YT_SPK_CAP_H * 3600:
                per[r["speaker_id"]] += r["seconds"]
                keep.append(r)
        rs = keep
    if LIMITS[src] and len(rs) > LIMITS[src]:
        rs = rs[: LIMITS[src]]
    for r in rs:
        r["src"] = src
    log(f"{src}: manifest {n0}, audio present {n_exist}, after filters/caps {len(rs)}")
    if n_exist < 0.5 * n0:
        log(f"WARNING {src}: only {n_exist}/{n0} audio files present")
    rows += rs

# ---------------------------------------------------------------- 24 kHz mono FLAC
def conv(item):
    i, r = item
    out = WAV / r["src"] / f"{i:06d}.flac"
    if not out.exists():
        out.parent.mkdir(parents=True, exist_ok=True)
        p = subprocess.run(["ffmpeg", "-nostdin", "-loglevel", "error", "-y", "-i", r["audio"], "-ac", "1", "-ar", "24000",
                            "-sample_fmt", "s16", str(out)])
        if p.returncode:
            return None
    try:
        return str(out), sf.info(str(out)).duration
    except Exception:
        return None


log(f"converting {len(rows)} clips to 24 kHz FLAC with {NPROC} workers")
with ThreadPoolExecutor(NPROC) as ex:
    res = list(ex.map(conv, enumerate(rows), chunksize=64))
ok = []
for r, x in zip(rows, res):
    if x and MIN_S <= x[1] <= MAX_S:
        r["wav"], r["dur"] = x
        ok.append(r)
log(f"converted {len(ok)}/{len(rows)} within {MIN_S}-{MAX_S} s")
rows = ok

# ---------------------------------------------------------------- model (speaker encoder + speech tokenizer)
from qwen_tts import Qwen3TTSModel  # noqa: E402

tts = Qwen3TTSModel.from_pretrained(BASE, dtype=torch.float32, device_map="cuda:0", attn_implementation="sdpa")
m = tts.model


@torch.inference_mode()
def spk(w):
    return m.extract_speaker_embedding(audio=np.ascontiguousarray(w, dtype=np.float32), sr=24000).float()


def sim3(path):
    w, sr = sf.read(path, dtype="float32")
    n = len(w)
    L = min(int(6 * sr), n // 3)
    if L < int(1.5 * sr):
        return None
    mid = (n - L) // 2
    e = torch.nn.functional.normalize(torch.stack([spk(w[:L]), spk(w[mid:mid + L]), spk(w[n - L:])]), dim=-1)
    c = e @ e.T
    return float(min(c[0, 1], c[0, 2], c[1, 2]))


yt = [r for r in rows if r["src"] == "yt"]
log(f"single-speaker check on {len(yt)} YouTube clips (3 windows, min cosine)")
t0 = time.time()
for k, r in enumerate(yt):
    r["spk_sim"] = sim3(r["wav"])
    if k % 2000 == 0:
        log(f"  {k}/{len(yt)} ({time.time() - t0:.0f} s)")
sims = np.array([r["spk_sim"] for r in yt if r["spk_sim"] is not None])
pct = {p: round(float(np.percentile(sims, p)), 3) for p in (5, 10, 25, 50, 75, 90)} if len(sims) else {}
thr = SIM_MIN
pass_rate = float((sims >= SIM_MIN).mean()) if len(sims) else 1.0
if pass_rate < 0.30:
    thr = float(np.percentile(sims, 50))
    log(f"WARNING pass rate {pass_rate:.2f} at {SIM_MIN}; using the median {thr:.3f} instead")
by_ch = defaultdict(list)
for r in yt:
    if r["spk_sim"] is not None:
        by_ch[r["speaker_id"]].append(r["spk_sim"])
ch_stats = {c: {"n": len(v), "median": round(float(np.median(v)), 3), "pass": round(float((np.array(v) >= thr).mean()), 3)}
            for c, v in sorted(by_ch.items())}
log(f"sim percentiles {pct}; threshold {thr:.3f}; per channel {json.dumps(ch_stats, ensure_ascii=False)}")
with open(W / "spk_sim.jsonl", "w", encoding="utf-8") as f:
    for r in yt:
        f.write(json.dumps({"audio": r["audio"], "speaker_id": r["speaker_id"], "sim": r["spk_sim"], "dur": r["dur"]},
                           ensure_ascii=False) + "\n")
rows = [r for r in rows if r["src"] != "yt" or r["spk_sim"] is None or r["spk_sim"] >= thr]

# ---------------------------------------------------------------- eval reference voices (held-out yt_dev, single speaker)
dev = [r for r in jl(B / "manifests" / "yt_dev.jsonl") if Path(r["audio"]).exists()]
cands = defaultdict(list)
for i, r in enumerate(dev):
    out = W / "refs_src" / f"dev{i:04d}.flac"
    out.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["ffmpeg", "-nostdin", "-loglevel", "error", "-y", "-i", r["audio"], "-ac", "1", "-ar", "24000",
                    "-sample_fmt", "s16", str(out)])
    if not out.exists():
        continue
    d = sf.info(str(out)).duration
    if d < 10:
        continue
    s = sim3(str(out))
    if s is not None:
        cands[r["speaker_id"]].append((s, str(out), r["text"]))
refs = []
for ch, c in sorted(cands.items(), key=lambda kv: -max(x[0] for x in kv[1])):
    s, p, t = max(c)
    w, sr = sf.read(p, dtype="float32")
    w = w[: 12 * sr]
    name = f"ref{len(refs) + 1}"
    dst = W / "refs" / f"{name}.wav"
    dst.parent.mkdir(parents=True, exist_ok=True)
    sf.write(str(dst), w, sr)
    refs.append({"name": name, "path": str(dst), "channel": ch, "sim": round(s, 3)})
    if len(refs) == 3:
        break
json.dump(refs, open(W / "refs.json", "w"), ensure_ascii=False, indent=1)
log(f"eval refs: {refs}")

# ---------------------------------------------------------------- 12 Hz codes (length-sorted batches)
tok = m.speech_tokenizer
order = sorted(range(len(rows)), key=lambda k: rows[k]["dur"])
BS = 16


def read(k):
    return sf.read(rows[k]["wav"], dtype="float32")[0]


log(f"encoding {len(rows)} clips, batch {BS}")
t0 = time.time()
with ThreadPoolExecutor(16) as ex:
    for bi in range(0, len(order), BS):
        b = order[bi: bi + BS]
        wavs = list(ex.map(read, b))
        enc = tok.encode(wavs, sr=24000)
        for k, c in zip(b, enc.audio_codes):
            rows[k]["codes"] = c.cpu().numpy().astype(np.int16)
        if (bi // BS) % 500 == 0:
            log(f"  {bi}/{len(rows)} ({time.time() - t0:.0f} s)")

# batched vs single-clip codes, on 40 random clips
chk = random.Random(1).sample(range(len(rows)), min(40, len(rows)))
same = []
for k in chk:
    c1 = tok.encode(read(k), sr=24000).audio_codes[0].cpu().numpy().astype(np.int16)
    c0 = rows[k]["codes"]
    n = min(len(c0), len(c1))
    same.append(float((c0[:n] == c1[:n]).mean()) if n else 0.0)
    if abs(len(c0) - len(c1)) > 1:
        log(f"WARNING length mismatch batched {len(c0)} vs single {len(c1)} for {rows[k]['wav']}")
log(f"batched-vs-single code agreement: mean {np.mean(same):.4f}, min {np.min(same):.4f}")

fr = np.array([len(r["codes"]) / r["dur"] for r in rows])
log(f"frames per second: median {np.median(fr):.2f} (expect ~12)")
rows = [r for r in rows if len(r["codes"]) >= 36]
random.Random(SEED).shuffle(rows)
with open(W / "train.jsonl", "w", encoding="utf-8") as f:
    for r in rows:
        f.write(json.dumps({"audio": r["wav"], "text": r["text"].strip(), "ref_audio": r["wav"], "speaker_id": r["src"],
                            "duration_sec": round(r["dur"], 3), "audio_codes": r["codes"].tolist()},
                           ensure_ascii=False) + "\n")
st = {"rows": len(rows), "hours": round(sum(r["dur"] for r in rows) / 3600, 2),
      "by_src": {s: {"rows": sum(1 for r in rows if r["src"] == s),
                     "hours": round(sum(r["dur"] for r in rows if r["src"] == s) / 3600, 2)} for s in LIMITS},
      "spk_threshold": thr, "spk_pass_rate_at_0.75": round(pass_rate, 3), "spk_percentiles": pct, "spk_by_channel": ch_stats,
      "code_agreement_mean": round(float(np.mean(same)), 4), "frames_per_s_median": round(float(np.median(fr)), 2),
      "refs": refs}
json.dump(st, open(W / "stats.json", "w"), ensure_ascii=False, indent=1)
log(f"STATS {json.dumps(st, ensure_ascii=False)}")
log("BUILD DONE")
