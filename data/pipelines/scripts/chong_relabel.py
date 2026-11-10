"""床哥 data quality, pass 2: re-label every chunk with Gemini given the burned-in subtitle OCR and an independent Qwen3-ASR
transcript as hints, then score each chunk by agreement.

usage:
  python data_yue/chong_relabel.py hints               # chunk -> OCR subtitle text (needs chong/ocr/*.json)
  python data_yue/chong_relabel.py gemini [--budget-usd 5] [--workers 8]   # -> chong/gemini2.jsonl (resumable)
  python data_yue/chong_relabel.py score               # -> chong/quality.jsonl + summary
Inputs: chong/chong.jsonl (pass-1 Gemini, has start/seconds), chong/failed_qwen.jsonl (start/seconds of pass-1 failures),
chong/qwen.jsonl (qwen_label.py chong), chong/ocr/<video>.json (chong_ocr.py).
"""

import argparse
import base64
import json
import os
import sys
import threading
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).parent
D = ROOT / "chong"
KEY = os.environ.get("GEMINI_API_KEY") or Path(os.environ["GEMINI_API_KEY_FILE"]).read_text().strip()
PRICE_IN, PRICE_OUT = 0.75 / 1e6, 3.75 / 1e6
STOP = threading.Event()
PROMPT = (
    "下面係香港網台節目（床哥心事台，有 call-in、傾偈、講笑）精華片段嘅錄音。請逐字寫低實際講嘅廣東話口語"
    "（繁體中文，用粵語字例如 嘅 咗 喺 佢 冇 啲 嘢 噉 咩 嚟 㗎 撚，俗語、潮語、粗口照寫，唔好改做書面語），英文字保留英文，"
    "數字照讀音寫成中文字。聽唔清楚嘅位寫 [?]，唔好估。唔好加解釋、講者標記或者時間碼，只輸出轉寫。\n\n"
    "以下參考資料只係輔助，一切以錄音為準：\n"
    "1. 片上燒入字幕（OCR 讀出，可能有錯字同雜字；字幕會將粗口寫成 Diu、L、PK 之類、會改用書面字、會玩字，時間亦可能同錄音唔完全對齊）：{ocr}\n"
    "2. 另一個語音辨識系統嘅結果（可能有同音字錯、簡體字、人名錯）：{qwen}\n"
    "用字幕幫你確定人名、專有名詞、英文字同同音字；字幕同錄音唔同嘅時候，跟錄音。"
)


def jl(p):
    return [json.loads(line) for line in open(p, encoding="utf-8")] if Path(p).exists() else []


def chunk_table():
    rows = {r["chunk"]: r for r in jl(D / "chong.jsonl")}
    for r in jl(D / "failed_qwen.jsonl"):
        rows.setdefault(r["chunk"], {k: r[k] for k in ("chunk", "video", "channel", "title", "start", "seconds")} | {"hint": r["sub"], "text": ""})
    return rows


def cmd_hints():
    rows, cues = chunk_table(), {}
    out = open(D / "hints.jsonl", "w", encoding="utf-8")
    n = has = 0
    for c, r in sorted(rows.items()):
        v = r["video"]
        if v not in cues:
            p = D / "ocr" / f"{v}.json"
            cues[v] = json.loads(p.read_text(encoding="utf-8"))["cues"] if p.exists() else None
        s, e = r["start"], r["start"] + r["seconds"]
        ocr = [t for (cs, ce, t) in (cues[v] or []) if ce > s - 0.3 and cs < e + 0.3]
        ocr = [t for i, t in enumerate(ocr) if i == 0 or t != ocr[i - 1]]
        out.write(json.dumps({"chunk": c, "ocr": " / ".join(ocr), "ocr_video": cues[v] is not None, "creator_sub": r.get("hint", "")}, ensure_ascii=False) + "\n")
        n, has = n + 1, has + bool(ocr)
    print(f"{n} chunks, {has} with OCR subtitle text, {sum(v is None for v in cues.values())} videos without OCR", flush=True)


def gemini(mp3, prompt):
    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.8-flash:generateContent"
    body = {
        "contents": [{"parts": [{"text": prompt}, {"inline_data": {"mime_type": "audio/mp3", "data": base64.b64encode(mp3).decode()}}]}],
        "generationConfig": {"temperature": 0, "thinkingConfig": {"thinkingBudget": 0}},
        "safetySettings": [{"category": c, "threshold": "BLOCK_NONE"} for c in (
            "HARM_CATEGORY_HARASSMENT", "HARM_CATEGORY_HATE_SPEECH", "HARM_CATEGORY_SEXUALLY_EXPLICIT", "HARM_CATEGORY_DANGEROUS_CONTENT")],
    }
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, data=json.dumps(body).encode(), headers={"Content-Type": "application/json", "x-goog-api-key": KEY})
            d = json.load(urllib.request.urlopen(req, timeout=180))
            u = d.get("usageMetadata", {})
            usd = u.get("promptTokenCount", 0) * PRICE_IN + (u.get("candidatesTokenCount", 0) + u.get("thoughtsTokenCount", 0)) * PRICE_OUT
            c = (d.get("candidates") or [{}])[0]
            text = "".join(p.get("text", "") for p in c.get("content", {}).get("parts", [])).strip()
            block = None if text else (c.get("finishReason") or (d.get("promptFeedback") or {}).get("blockReason") or "EMPTY")
            if text or attempt == 2:
                return text, block, usd
        except urllib.error.HTTPError as e:
            msg = e.read().decode()[:300]
            print("HTTP", e.code, msg[:160], flush=True)
            if "spending cap" in msg:
                STOP.set()
                return "", "SPEND_CAP", 0.0
        except Exception as e:  # noqa: BLE001
            print("retry", attempt, type(e).__name__, str(e)[:120], flush=True)
        time.sleep(4 * (attempt + 1))
    return "", "FAILED", 0.0


def cmd_gemini(budget, workers):
    hints = {r["chunk"]: r for r in jl(D / "hints.jsonl")}
    qwen = {r["id"] + ".mp3": r["qwen"] for r in jl(D / "qwen.jsonl")}
    out_p = D / "gemini2.jsonl"
    done = {r["chunk"]: r for r in jl(out_p) if r["text"] or r["block"] not in ("FAILED", "SPEND_CAP")}
    spent = sum(r["usd"] for r in done.values())
    todo = [c for c in sorted(hints) if c not in done and c in qwen]
    print(f"{len(done)} done (${spent:.3f}), {len(todo)} to go, {len(hints) - len(qwen)} without qwen yet", flush=True)
    with open(out_p, "w", encoding="utf-8") as f:
        for r in done.values():
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    out = open(out_p, "a", encoding="utf-8")
    lock = threading.Lock()

    def run(c):
        nonlocal spent
        if STOP.is_set() or spent > budget:
            return None
        h = hints[c]
        ocr = " ".join(x for x in (h["ocr"], h["creator_sub"]) if x) or "（冇）"
        text, block, usd = gemini((D / "chunks" / c).read_bytes(), PROMPT.format(ocr=ocr, qwen=qwen[c] or "（冇）"))
        with lock:
            spent += usd
        return {"chunk": c, "text": text, "block": block, "usd": round(usd, 6)}

    n = 0
    with ThreadPoolExecutor(workers) as ex:
        for r in ex.map(run, todo):
            if r is None:
                continue
            out.write(json.dumps(r, ensure_ascii=False) + "\n")
            out.flush()
            n += 1
            if n % 200 == 0:
                print(f"{n} chunks, ${spent:.3f}", flush=True)
    out.close()
    print(json.dumps({"new": n, "usd_total": round(spent, 3), "budget_hit": spent > budget, "spend_cap": STOP.is_set()}), flush=True)


def cmd_score():
    sys.path.insert(0, str(ROOT.parent / "src"))
    import opencc

    from embed2asr.metrics import edit_distance
    from embed2asr.numnorm import norm_nn

    t2s = opencc.OpenCC("t2s")
    keep = set("abcdefghijklmnopqrstuvwxyz0123456789")

    def clean(s):
        s = t2s.convert(norm_nn(s.replace("[?]", ""), "zh")).lower().replace("噶", "㗎")
        return "".join(ch for ch in s if ch in keep or "\u3400" <= ch <= "\u9fff" or "\U00020000" <= ch <= "\U0002ffff")

    def cer(ref, hyp):
        r, h = clean(ref), clean(hyp)
        return edit_distance(list(r), list(h)) / max(len(r), 1) if r else (0.0 if not h else 1.0)

    rows = chunk_table()
    g1 = {c: r.get("text", "") for c, r in rows.items()}
    g2 = {r["chunk"]: r for r in jl(D / "gemini2.jsonl")}
    qw = {r["id"] + ".mp3": r["qwen"] for r in jl(D / "qwen.jsonl")}
    hints = {r["chunk"]: r for r in jl(D / "hints.jsonl")}
    out = open(D / "quality.jsonl", "w", encoding="utf-8")
    stats = {"good": [0, 0.0], "ok": [0, 0.0], "bad": [0, 0.0], "unk": [0, 0.0]}
    for c, r in sorted(rows.items()):
        t2 = g2.get(c, {}).get("text", "")
        q = qw.get(c, "")
        d = {"chunk": c, "seconds": r["seconds"], "gemini1": g1.get(c, ""), "gemini2": t2, "qwen": q, "ocr": hints.get(c, {}).get("ocr", ""),
             "block2": g2.get(c, {}).get("block")}
        if t2 and q:
            d["cer_g2_qwen"] = round(cer(t2, q), 3)
            d["cer_g2_g1"] = round(cer(t2, g1[c]), 3) if g1.get(c) else None
            unclear = t2.count("[?]")
            d["grade"] = "good" if d["cer_g2_qwen"] <= 0.15 and not unclear else "ok" if d["cer_g2_qwen"] <= 0.35 and unclear <= 1 else "bad"
        else:
            d["grade"] = "unk"
        stats[d["grade"]][0] += 1
        stats[d["grade"]][1] += r["seconds"] / 3600
        out.write(json.dumps(d, ensure_ascii=False) + "\n")
    print({k: (n, round(h, 2)) for k, (n, h) in stats.items()}, flush=True)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("cmd", choices=["hints", "gemini", "score"])
    p.add_argument("--budget-usd", type=float, default=5.0)
    p.add_argument("--workers", type=int, default=8)
    a = p.parse_args()
    {"hints": cmd_hints, "gemini": lambda: cmd_gemini(a.budget_usd, a.workers), "score": cmd_score}[a.cmd]()
