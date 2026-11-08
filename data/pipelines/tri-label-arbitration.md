# Tri-label arbitration (verbatim HK labels from subtitled video)

**Status:** method described in the blueprint §2.2 and used in prior work. Not yet implemented in this repo.
This file is the spec. The implementation (`src/ctts/label/`) must match it, and any deviation needs an update here.

## Problem
HK creators speak colloquial Cantonese but subtitle in written Chinese. Subtitles as targets teach
書面語. Subtitles given as ASR *context* make the ASR output 書面語 too (e.g. `省了4,000蚊` instead of `慳咗四千蚊`).

## Inputs per segment (3–25 s)
| Candidate | Producer | Gets the subtitle? |
|---|---|---|
| **G** | Multimodal teacher LLM (e.g. Gemini Flash audio) | Yes, **for proper nouns / English spelling only**, with an explicit verbatim-口語 instruction |
| **Q** | Local fine-tuned HK ASR (`Qwen3-ASR-1.7B` Stage 2) | **No.** Audio only. |
| **S** | Creator subtitle | Used only as arbiter. Never chosen unless already colloquial. |

## Definitions
- **Skeleton normalisation:** map spoken↔written equivalents (睇↔看, 瞓↔睡, 畀↔給, 搵↔找, 嚟↔來, 食↔吃, ...), strip
  modal particles, then compare. `sim(X, Y)` = 1 − CER on skeletons.
- **Colloquial density score:** count of `嘅咗喺佢冇啲嘢噉嚟唔係睇諗瞓攞畀搵` minus count of written markers
  `什麼 / 沒有 / 的 / 了 / 他 / 說 / 睡`. (Version the marker lists. They are hyperparameters.)

## Decision rule
1. If `CER(G, Q) ≤ 15%` → **sync** (~70%): pick whichever of G/Q has the higher colloquial score.
2. Else → **sub** (~25%): pick whichever of G/Q has the higher skeleton similarity with S.
3. **Reject** (~4–5%): `max sim < 0.60` (BGM/noise), Japanese kana present, or G's colloquial score < 0 (Putonghua speaker).

## What to log for each run
Model versions for G and Q (and the G prompt text, verbatim), thresholds, marker-list versions, bucket counts, reject
counts by reason, and a random sample of 50 rows per bucket for manual audit, with the audit's
accuracy. Each row records its provenance in the manifest `labeling` object.

## Reported prior result (not reproduced here)
80 h / 10,342 segments / 7 channels → 95.7% retained as clean verbatim HK speech.
