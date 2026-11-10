"""Independent Qwen3-ASR-1.7B transcripts (forced Cantonese, no hints) for the YouTube-derived sets, for cross-checking
the Gemini labels. Resumable: ids already in the output are skipped.

usage: MIOPEN_FIND_MODE=FAST python data_yue/qwen_label.py {chong|yt} [--bs 16]
  chong -> data_yue/chong/chunks/*.mp3            -> data_yue/chong/qwen.jsonl
  yt    -> data_yue/yt_pilot/audio/*.mp3 (labelled) -> data_yue/yt_pilot/qwen.jsonl
"""

import argparse
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))
import eval_baselines as eb  # noqa: E402


def main():
    a = argparse.ArgumentParser()
    a.add_argument("which", choices=["chong", "yt"])
    a.add_argument("--bs", type=int, default=16)
    a = a.parse_args()
    if a.which == "chong":
        files = sorted((ROOT / "chong" / "chunks").glob("*.mp3"))
        out = ROOT / "chong" / "qwen.jsonl"
    else:
        segs = {json.loads(line)["seg"] for f in (ROOT / "yt_pilot").glob("*_000.jsonl") for line in open(f, encoding="utf-8")}
        files = sorted(p for p in (ROOT / "yt_pilot" / "audio").glob("*.mp3") if p.stem in segs)
        out = ROOT / "yt_pilot" / "qwen.jsonl"
    done = {json.loads(line)["id"] for line in open(out, encoding="utf-8")} if out.exists() else set()
    files = [f for f in files if f.stem not in done]
    print(f"{len(done)} done, {len(files)} to go", flush=True)
    asr = eb.Qwen3ASR()
    with ThreadPoolExecutor(8) as ex:
        wavs = list(ex.map(lambda f: eb.load_audio(str(f)), files))
    order = sorted(range(len(files)), key=lambda i: len(wavs[i]))
    t0 = time.time()
    with open(out, "a", encoding="utf-8") as f:
        for b in range(0, len(order), a.bs):
            idx = order[b : b + a.bs]
            for i, h in zip(idx, asr([wavs[i] for i in idx])):
                f.write(json.dumps({"id": files[i].stem, "qwen": h.strip()}, ensure_ascii=False) + "\n")
            f.flush()
            if (b // a.bs) % 20 == 0:
                print(f"{b + len(idx)}/{len(files)} {time.time() - t0:.0f}s", flush=True)
    print("QWEN DONE", flush=True)


if __name__ == "__main__":
    main()
