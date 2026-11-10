"""YouTube creator-subtitle + Gemini verbatim-Cantonese pilot on OrcinusOrca segments.

usage: python data_yue/yt_gemini_pilot.py TAR N [--model gemini-3.8-flash] [--budget-usd 5]
For N random segments of TAR: send audio + creator subtitle to Gemini, ask for a verbatim colloquial-Cantonese
transcript; log tokens/cost; then run our yue_v3 reader on the same clips and report CER between the three texts.
Uses the paid key file (owner approved, budget capped). Writes data_yue/yt_pilot/<tar stem>.jsonl
"""

import argparse
import base64
import json
import os
import random
import tarfile
import threading
import time
import urllib.request
from pathlib import Path

STOP = threading.Event()

ROOT = Path(__file__).parent
KEY = os.environ.get("GEMINI_API_KEY") or Path(os.environ["GEMINI_API_KEY_FILE"]).read_text().strip()
PRICE_IN, PRICE_OUT = 0.75 / 1e6, 3.75 / 1e6  # gemini-3.8-flash standard tier, USD per token (to 2026-12-31)
PROMPT = (
    "下面係一段香港廣東話 YouTube 錄音，同埋 YouTuber 自己上載嘅字幕。字幕通常係書面語、可能刪減咗，只可以用嚟參考人名、"
    "專有名詞同英文字。請你聽錄音，逐字寫低佢實際講嘅廣東話口語（繁體中文，用粵語字例如 嘅 咗 喺 佢 冇 啲 嘢 噉），"
    "英文字保留英文，數字照讀音寫成中文字，唔好加任何解釋、標題或者時間碼，只輸出轉寫文字。\n\n字幕：{sub}"
)


def gemini(model, mp3: bytes, sub: str):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    body = {
        "contents": [{"parts": [{"text": PROMPT.format(sub=sub)}, {"inline_data": {"mime_type": "audio/mp3", "data": base64.b64encode(mp3).decode()}}]}],
        "generationConfig": {"temperature": 0, "thinkingConfig": {"thinkingBudget": 0}},
    }
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, data=json.dumps(body).encode(), headers={"Content-Type": "application/json", "x-goog-api-key": KEY})
            d = json.load(urllib.request.urlopen(req, timeout=180))
            text = "".join(p.get("text", "") for p in d["candidates"][0]["content"].get("parts", [])).strip()
            u = d.get("usageMetadata", {})
            return text, u.get("promptTokenCount", 0), u.get("candidatesTokenCount", 0) + u.get("thoughtsTokenCount", 0)
        except urllib.error.HTTPError as e:
            msg = e.read().decode()[:300]
            if "thinking" in msg.lower() and "thinkingConfig" in body["generationConfig"]:
                body["generationConfig"].pop("thinkingConfig")  # model rejects a zero thinking budget: retry without
                continue
            print("HTTP", e.code, msg, flush=True)
            if "spending cap" in msg:  # project spend cap hit: stop everything instead of retrying
                STOP.set()
                return "", 0, 0
        except Exception as e:  # noqa: BLE001
            print("retry", attempt, type(e).__name__, str(e)[:200], flush=True)
        time.sleep(5 * (attempt + 1))
    return "", 0, 0


def main():
    p = argparse.ArgumentParser()
    p.add_argument("tar")
    p.add_argument("n", type=int)
    p.add_argument("--model", default="gemini-3.8-flash")
    p.add_argument("--budget-usd", type=float, default=5.0)
    p.add_argument("--workers", type=int, default=8)
    a = p.parse_args()
    out_dir = ROOT / "yt_pilot"
    out_dir.mkdir(exist_ok=True)
    aud_dir = out_dir / "audio"
    aud_dir.mkdir(exist_ok=True)
    t = tarfile.open(a.tar)
    names = {m.name: m for m in t.getmembers()}
    segs = sorted(n[:-5] for n in names if n.endswith(".json"))
    random.Random(0).shuffle(segs)
    from concurrent.futures import ThreadPoolExecutor

    # resume: keep segments already transcribed (non-empty), redo the rest; write each row as soon as it is done
    out_path = out_dir / f"{Path(a.tar).stem}.jsonl"
    rows = []
    if out_path.exists():
        rows = [r for r in (json.loads(line) for line in open(out_path, encoding="utf-8")) if r["gemini"]]
    done = {r["seg"] for r in rows}
    spent, secs = sum(r["usd"] for r in rows), sum(r["seconds"] for r in rows)
    print(f"resume: {len(rows)} done, ${spent:.3f}", flush=True)
    with open(out_path, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    out = open(out_path, "a", encoding="utf-8")
    t0 = time.time()
    jobs = []
    for s in segs[: a.n]:
        if s in done:
            continue
        meta = json.load(t.extractfile(names[s + ".json"]))
        mp3 = t.extractfile(names[s + ".mp3"]).read()
        (aud_dir / f"{s}.mp3").write_bytes(mp3)
        jobs.append((s, meta, mp3))

    def run(job):
        s, meta, mp3 = job
        if spent > a.budget_usd or STOP.is_set():  # budget / spend-cap guard (checked before each request)
            return None
        text, tin, tout = gemini(a.model, mp3, meta["caption"])
        cost = tin * PRICE_IN + tout * PRICE_OUT
        return {"seg": s, "seconds": meta["clip_duration"], "sub": meta["caption"], "gemini": text, "tok_in": tin, "tok_out": tout, "usd": round(cost, 6)}

    failed = 0
    with ThreadPoolExecutor(a.workers) as ex:
        for r in ex.map(run, jobs):
            if r is None:
                continue
            spent += r["usd"]
            if not r["gemini"]:  # failed: leave it out so a rerun retries it
                failed += 1
                continue
            rows.append(r)
            secs += r["seconds"]
            out.write(json.dumps(r, ensure_ascii=False) + "\n")
            out.flush()
            if len(rows) % 200 == 0:
                print(f"{len(rows)} clips, {secs / 3600:.2f} h, ${spent:.3f}", flush=True)
    out.close()
    if spent > a.budget_usd:
        print("budget reached, stopped early", flush=True)
    if STOP.is_set():
        print("spending cap hit, stopped early", flush=True)
    print(f"failed (not written): {failed}", flush=True)
    print(json.dumps({"clips": len(rows), "audio_min": round(secs / 60, 1), "usd": round(spent, 4), "usd_per_audio_hour": round(spent / (secs / 3600), 3), "wall_s": round(time.time() - t0)}), flush=True)


if __name__ == "__main__":
    main()
