"""Tri-label extra OrcinusOrca YouTube segments: Gemini 3.8 Flash + our fine-tuned Qwen3-ASR + the creator subtitle.

Decision 2026-11-07: label with both Gemini and the local Qwen-FT; where they disagree look at the subtitle; of the three
keep the result closest to spoken Cantonese.

usage (from the repo root; every stage resumes, rows keyed by segment id):
  .venv/bin/python     data_yue/yt_tri_label.py extract [--limit N]      # pick ~80 h over 7 channels -> yt_more/
  .venv/bin/python     data_yue/yt_tri_label.py gemini [--budget-usd 12]
  .venv-qft/bin/python data_yue/yt_tri_label.py qwen [--bs 16]
  .venv/bin/python     data_yue/yt_tri_label.py merge [--examples 0]

merge rule per segment, candidates Q (Qwen-FT), G (Gemini), S (subtitle, if any):
  sim(X, Y)  = 1 - edit distance / longer length, on content characters only (colloquial words mapped to their
               written form, particles / function characters dropped, t2s, numbers normalised, no punctuation)
  support(X) = mean sim(X, each other candidate)   -> when Q and G disagree, the subtitle tips the balance
  eligible   = support >= best support - MARGIN
  pick       = the most colloquial eligible text (Cantonese markers minus written-only words, per character;
               texts with Arabic digits are penalised because train manifests drop them); candidates within
               COL_TOL of the most colloquial count as a tie, broken by support (subtitle-backed names/terms win)
  status     = sync (full-text CER(Q, G) <= SYNC) / sub (subtitle decided) / reject (Qwen empty, Gemini empty or
               answered with meta text, kana in Q/G = Japanese speech, Gemini text more written than colloquial =
               probably Putonghua speech, or the pick agrees with no other candidate: best pair sim < MIN_AGREE)
Skips segments already labelled in yt_pilot/ and every video held out in manifests/yt_{dev,test}.jsonl.
"""

import argparse
import json
import random
import re
import sys
import tarfile
import time
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).parent
OO = ROOT / "raw_dl" / "OrcinusOrca__YouTube-Cantonese"
OUT = ROOT / "yt_more"
QFT = ROOT.parent / "qwen_ft" / "colab_out" / "final"
TARGET_H = {"ahju": 10, "bboblackboxoffice": 10, "mm.millmilk": 14, "pricehongkongofficial": 12, "unwire": 12,
            "mingjai14": 12, "thedoshow0909": 10}
SYNC, MARGIN, COL_TOL, MIN_AGREE = 0.15, 0.05, 0.03, 0.6
BAD_G = re.compile(r"(?i)the user|transcription|subtitle|verbatim|here is|字幕：")
KANA = re.compile(r"[\u3040-\u30ff]")
MANDARIN = -0.03  # Gemini text with more written-only words than Cantonese markers (per char) -> probably Putonghua

YUE = set("嘅咗喺佢冇啲嘢噉嚟哋唔係嗰咩乜啱嘞喎囉㗎吖嘛噃咪睇諗瞓攞畀俾搵揾晒咁嗌啖嚿冚攰揸嗮")
WRITTEN = ["什麼", "甚麼", "怎麼", "東西", "沒有", "的", "了", "他", "她", "它", "沒", "這", "那", "們", "睡", "說",
           "看", "給", "吃", "喝", "很", "在", "是", "不", "吧", "嗎"]
WRITTEN_OK = ["的士", "的確", "目的", "了解", "為了", "除了", "現在", "存在", "實在", "自在", "在於", "但是", "於是",
              "是否", "凡是", "不過", "不如", "不斷", "不同", "不少", "不錯", "不論", "不管", "不停", "不再", "不但",
              "不僅", "不足", "不得", "不安", "不良", "看法", "看好", "看來", "小說", "說明", "說服", "據說", "睡眠",
              "供給", "給予", "那麼多"]
FUNC = set("嘅的咗了喺在佢他她它冇沒啲些嘢噉這那咁呢嗰係是唔不啦呀喎囉吖嘛噃咪啊哦唉嗯呃誒哎噢喇嘞㗎咩乜吓哇咯們哋嗎吧")
TO_WRITTEN = str.maketrans({"睇": "看", "瞓": "睡", "講": "說", "畀": "給", "俾": "給", "嚟": "來", "返": "回",
                            "搵": "找", "揾": "找", "攞": "拿", "食": "吃", "飲": "喝", "同": "和", "跟": "和",
                            "啱": "對", "諗": "想"})


def jl(p):
    return [json.loads(line) for line in open(p, encoding="utf-8")] if Path(p).exists() else []


def wjl(p, rows):
    with open(p, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


# ---------------------------------------------------------------- extract
def cmd_extract(a):
    held = {r["video"] for s in ("dev", "test") for r in jl(ROOT / "manifests" / f"yt_{s}.jsonl")}
    used = {r["seg"] for f in (ROOT / "yt_pilot").glob("*_000.jsonl") for r in jl(f)}
    (OUT / "audio").mkdir(parents=True, exist_ok=True)
    meta = {r["seg"]: r for r in jl(OUT / "meta.jsonl")}
    for ch, hours in TARGET_H.items():
        tp = OO / ch / f"{ch}_000.tar"
        if not tp.exists():
            print("MISSING", tp, flush=True)
            continue
        t = tarfile.open(tp)
        names = {m.name: m for m in t.getmembers()}
        segs = sorted(n[:-5] for n in names if n.endswith(".json") and n[:-5] + ".mp3" in names)
        random.Random(1).shuffle(segs)
        took, secs, skipped = 0, 0.0, 0
        for s in segs:
            if secs >= hours * 3600 or (a.limit and took >= a.limit):
                break
            vid = f"{ch}:{s.rsplit('_', 1)[0]}"
            if s in used or vid in held:
                skipped += 1
                continue
            m = json.load(t.extractfile(names[s + ".json"]))
            dur = float(m["clip_duration"])
            if not 1.0 <= dur <= 40.0:
                continue
            mp3 = OUT / "audio" / f"{s}.mp3"
            if not mp3.exists():
                mp3.write_bytes(t.extractfile(names[s + ".mp3"]).read())
            meta[s] = {"seg": s, "channel": ch, "video": vid, "seconds": round(dur, 3), "sub": (m.get("caption") or "").strip()}
            took, secs = took + 1, secs + dur
        print(f"{ch}: {took} segs {secs / 3600:.2f} h (skipped used/held-out {skipped}, tar has {len(segs)})", flush=True)
    wjl(OUT / "meta.jsonl", meta.values())
    print(f"meta: {len(meta)} segs {sum(r['seconds'] for r in meta.values()) / 3600:.2f} h", flush=True)


# ---------------------------------------------------------------- gemini
def cmd_gemini(a):
    sys.path.insert(0, str(ROOT))
    import yt_gemini_pilot as ygp

    meta = jl(OUT / "meta.jsonl")
    outp = OUT / "gemini.jsonl"
    old = jl(outp)
    rows = [r for r in old if r["gemini"] and not BAD_G.search(r["gemini"])]
    wjl(outp, rows)  # drop earlier failures / meta answers so they are retried (their cost still counts)
    ledger = OUT / "gemini_dropped_usd.txt"  # cost of dropped rows, so the budget stays honest across reruns
    dropped = float(ledger.read_text()) if ledger.exists() else 0.0
    dropped += sum(r["usd"] for r in old) - sum(r["usd"] for r in rows)
    ledger.write_text(f"{dropped:.6f}")
    rows_usd = sum(r["usd"] for r in rows) + dropped
    done = {r["seg"] for r in rows}
    spent = [rows_usd]
    # round-robin over channels so a budget stop still leaves a balanced mix
    by_ch = defaultdict(list)
    for m in meta:
        if m["seg"] not in done:
            by_ch[m["channel"]].append(m)
    todo = []
    queues = [list(v) for v in by_ch.values()]
    while any(queues):
        for q in queues:
            if q:
                todo.append(q.pop(0))
    print(f"gemini: {len(rows)} done (${spent[0]:.3f}), {len(todo)} to go, budget ${a.budget_usd}", flush=True)

    def run(m):
        if spent[0] > a.budget_usd or ygp.STOP.is_set():
            return None
        mp3 = (OUT / "audio" / f"{m['seg']}.mp3").read_bytes()
        tin = tout = 0
        for _ in range(2):  # one retry when Gemini answers with meta text instead of a transcript
            text, i, o = ygp.gemini(a.model, mp3, m["sub"])
            tin, tout = tin + i, tout + o
            if not BAD_G.search(text):
                break
        return {"seg": m["seg"], "gemini": text, "tok_in": tin, "tok_out": tout, "usd": round(tin * ygp.PRICE_IN + tout * ygp.PRICE_OUT, 6)}

    t0, n, failed = time.time(), 0, 0
    with open(outp, "a", encoding="utf-8") as f, ThreadPoolExecutor(a.workers) as ex:
        for r in ex.map(run, todo):
            if r is None:
                continue
            spent[0] += r["usd"]
            if not r["gemini"]:
                failed += 1
                continue
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
            f.flush()
            n += 1
            if n % 200 == 0:
                print(f"gemini {n}/{len(todo)} ${spent[0]:.3f} {time.time() - t0:.0f}s", flush=True)
    stop = "budget" if spent[0] > a.budget_usd else "spending cap" if ygp.STOP.is_set() else "none"
    print(f"GEMINI DONE new={n} failed={failed} spent=${spent[0]:.3f} early_stop={stop}", flush=True)


# ---------------------------------------------------------------- qwen
def cmd_qwen(a):
    import librosa
    import torch
    from qwen_asr import Qwen3ASRModel

    meta = jl(OUT / "meta.jsonl")
    outp = OUT / "qwenft.jsonl"
    done = {r["seg"] for r in jl(outp)}
    todo = sorted((m for m in meta if m["seg"] not in done), key=lambda m: m["seconds"])
    print(f"qwen-ft: {len(done)} done, {len(todo)} to go", flush=True)
    if not todo:
        print("QWEN DONE", flush=True)
        return
    asr = Qwen3ASRModel.from_pretrained(str(QFT), dtype=torch.bfloat16, device_map="cuda:0",
                                        max_inference_batch_size=a.bs, max_new_tokens=400)
    load = lambda m: (librosa.load(str(OUT / "audio" / f"{m['seg']}.mp3"), sr=16000, mono=True)[0], 16000)  # noqa: E731
    t0, step = time.time(), a.bs * 4
    with open(outp, "a", encoding="utf-8") as f, ThreadPoolExecutor(8) as ex:
        for b in range(0, len(todo), step):
            chunk = todo[b : b + step]
            res = asr.transcribe(audio=list(ex.map(load, chunk)), language="Cantonese")
            for m, r in zip(chunk, res):
                f.write(json.dumps({"seg": m["seg"], "qwenft": r.text.strip()}, ensure_ascii=False) + "\n")
            f.flush()
            if (b // step) % 10 == 0:
                print(f"qwen-ft {b + len(chunk)}/{len(todo)} {time.time() - t0:.0f}s", flush=True)
    print("QWEN DONE", flush=True)


# ---------------------------------------------------------------- merge
def colloquial(text, digit_penalty=0.5):
    t = text
    for w in WRITTEN_OK:
        t = t.replace(w, "")
    n_written = 0
    for w in WRITTEN:
        n_written += t.count(w)
        t = t.replace(w, "")
    n_han = sum(1 for c in text if "\u3400" <= c <= "\u9fff") or 1
    n_yue = sum(1 for c in text if c in YUE)
    return (n_yue - n_written) / n_han - (digit_penalty if re.search(r"\d", text) else 0.0)


def cmd_merge(a):
    sys.path.insert(0, str(ROOT.parent / "src"))
    import opencc

    from embed2asr.metrics import edit_distance
    from embed2asr.numnorm import norm_nn

    t2s = opencc.OpenCC("t2s")
    keep = set("abcdefghijklmnopqrstuvwxyz0123456789")

    def plain(s):
        s = t2s.convert(norm_nn(s.replace("[?]", ""), "zh")).lower()
        return "".join(c for c in s if c in keep or "\u3400" <= c <= "\u9fff" or "\U00020000" <= c <= "\U0002ffff")

    def content(s):
        s = "".join(c for c in s.translate(TO_WRITTEN) if c not in FUNC)
        return plain(s)

    def sim(x, y):
        return 1 - edit_distance(list(x), list(y)) / max(len(x), len(y), 1)

    meta = {r["seg"]: r for r in jl(OUT / "meta.jsonl")}
    gem = {r["seg"]: r["gemini"] for r in jl(OUT / "gemini.jsonl")}
    qft = {r["seg"]: r["qwenft"] for r in jl(OUT / "qwenft.jsonl")}
    out, examples = [], defaultdict(list)
    for seg, m in meta.items():
        if seg not in gem or seg not in qft:
            continue
        cand = {"Q": qft[seg].strip(), "G": re.sub(r"\s+", " ", gem[seg]).strip()}
        if m["sub"]:
            cand["S"] = re.sub(r"\s+", " ", m["sub"]).strip()
        pq, pg = plain(cand["Q"]), plain(cand["G"])
        cer_qg = edit_distance(list(pg), list(pq)) / max(len(pg), 1)
        g_bad = not cand["G"] or bool(BAD_G.search(cand["G"]))
        con = {k: content(v) for k, v in cand.items()}
        pair = {(x, y): sim(con[x], con[y]) for x in cand for y in cand if x < y}
        ps = lambda x, y: pair[(min(x, y), max(x, y))]  # noqa: E731
        live = [k for k in cand if not (k == "G" and g_bad)]
        sup = {k: sum(ps(k, o) for o in live if o != k) / max(len(live) - 1, 1) for k in live}
        col = {k: colloquial(v) for k, v in cand.items()}
        best = max(sup.values())
        elig = [k for k in live if sup[k] >= best - MARGIN]
        top = max(col[k] for k in elig)
        # among the (about) equally colloquial ones, take the one the others agree with most
        pick = max((k for k in elig if col[k] >= top - COL_TOL), key=lambda k: (sup[k], k == "G"))
        agree = max((ps(pick, o) for o in live if o != pick), default=0.0)
        reason = ("qwen_empty" if not cand["Q"] else "gemini_bad" if g_bad else
                  "japanese" if KANA.search(cand["Q"] + cand["G"]) else
                  "mandarin?" if colloquial(cand["G"], 0) < MANDARIN else  # Gemini writes verbatim: written text = Putonghua speech
                  "no_agreement" if agree < MIN_AGREE else "")
        status = "reject" if reason else "sync" if cer_qg <= SYNC else "sub"
        r = {"seg": seg, "channel": m["channel"], "video": m["video"], "seconds": m["seconds"],
             "audio": str(OUT / "audio" / f"{seg}.mp3"), "text": cand[pick], "pick": pick, "status": status,
             "reason": reason, "cer_qg": round(cer_qg, 3), "agree": round(agree, 3),
             "pair": {f"{x}{y}": round(v, 3) for (x, y), v in pair.items()},
             "support": {k: round(v, 3) for k, v in sup.items()},
             "colloq": {k: round(v, 3) for k, v in col.items()}, "cand": cand}
        out.append(r)
        examples[(status, pick)].append(r)
    wjl(OUT / "merged.jsonl", out)

    hours = lambda rs: round(sum(r["seconds"] for r in rs) / 3600, 2)  # noqa: E731
    summ = {"segs": len(out), "hours": hours(out),
            "status": {s: {"segs": len(v), "hours": hours(v)} for s in ("sync", "sub", "reject") for v in [[r for r in out if r["status"] == s]]},
            "pick_kept": dict(Counter(r["pick"] for r in out if r["status"] != "reject")),
            "reject_reason": dict(Counter(r["reason"] for r in out if r["status"] == "reject")),
            "per_channel": {}}
    for ch in TARGET_H:
        rs = [r for r in out if r["channel"] == ch]
        if rs:
            summ["per_channel"][ch] = {"segs": len(rs), "hours": hours(rs), "kept_h": hours([r for r in rs if r["status"] != "reject"]),
                                       "sync%": round(100 * sum(r["status"] == "sync" for r in rs) / len(rs), 1),
                                       "pick": dict(Counter(r["pick"] for r in rs if r["status"] != "reject"))}
    (OUT / "merge_summary.json").write_text(json.dumps(summ, ensure_ascii=False, indent=1))
    print(json.dumps(summ, ensure_ascii=False, indent=1))
    for key, rs in sorted(examples.items()):
        for r in random.Random(0).sample(rs, min(a.examples, len(rs))):
            print(f"\n=== {key} {r['seg']} {r['reason']} cer_qg={r['cer_qg']} pair={r['pair']} sup={r['support']} col={r['colloq']}")
            for k, v in r["cand"].items():
                print(f"  {k}{'*' if k == r['pick'] else ' '}: {v[:150]}")


def main():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)
    e = sub.add_parser("extract")
    e.add_argument("--limit", type=int, default=0, help="max segments per channel (pilot)")
    g = sub.add_parser("gemini")
    g.add_argument("--model", default="gemini-3.8-flash")
    g.add_argument("--budget-usd", type=float, default=12.0)
    g.add_argument("--workers", type=int, default=8)
    q = sub.add_parser("qwen")
    q.add_argument("--bs", type=int, default=16)
    mg = sub.add_parser("merge")
    mg.add_argument("--examples", type=int, default=0)
    a = p.parse_args()
    {"extract": cmd_extract, "gemini": cmd_gemini, "qwen": cmd_qwen, "merge": cmd_merge}[a.cmd](a)


if __name__ == "__main__":
    main()
