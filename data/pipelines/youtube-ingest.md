# YouTube ingest and clean-up (channel → labelled clips → TTS-ready)

The full workflow for turning a YouTube channel into rows of `hk-youtube-conversational`, with the clean-up
rules, the open problems and where each channel stands. Two specs hold the details of single steps:
[`tri-label-arbitration.md`](tri-label-arbitration.md) (labelling rule) and [`tts-audio-prep.md`](tts-audio-prep.md)
(model input). The scripts that actually ran are in [`scripts/`](scripts/README.md).

**Mark progress in the [channel status](#channel-status) table** whenever a stage finishes for a channel, and
add a row to [clean-up problems](#clean-up-problems-and-directions) whenever a new kind of dirt shows up.

## Stages

| # | Stage | Action | Script | Output |
|---|---|---|---|---|
| 0 | Check | Is it HK Cantonese? Solo, interview or multi-speaker sketch? Public vs members-only hours. Creator subtitles in a sample. Share of music videos, games, shorts. | `channel_check.py` | numbers for the status table |
| 1 | Download | Route A: `OrcinusOrca/YouTube-Cantonese` tars (already cut on subtitle cues, creator subtitles included). Route B: `yt-dlp` audio only, 16 kHz mono mp3, rate-capped, creator subtitles `zh-HK`/`zh-Hant`/`zh-TW` (never auto captions). Skip members-only items. | A: `yt_tri_label.py extract`; B: `yt_dl_segment.py` (or `chong_pipeline.py` steps 1–2 for the 床哥 batch) | audio + subtitles outside git |
| 2 | Segment | Route A: subtitle-cue segments. Route B: consecutive subtitle cues joined while the gap ≤ 1.5 s and the span ≤ 25 s; videos without subtitles are cut at silences (`ffmpeg silencedetect`) into 3–25 s chunks. Segments under 3 s are dropped. | `yt_tri_label.py extract`, `yt_dl_segment.py` | segment list (`meta.jsonl`) |
| 3 | Label | G = Gemini Flash verbatim colloquial transcript (paid key, budget cap). Q = our fine-tuned Qwen3-ASR. S = creator subtitle, or burned-in caption OCR when there are no creator subtitles. Arbitrate per segment. | `yt_tri_label.py gemini/qwen/merge` (`yt_tri_chain.sh`); OCR route: `chong_ocr.py`, `qwen_label.py`, `chong_relabel.py` (`chong_quality_chain.sh`) | `merged.jsonl` (sync / sub / reject) |
| 4 | Manifest | Split by video (no video in two splits). Train rows: no `[?]`, no digits. | `build_yt_manifests.py` | `yt_{train,dev,test}.jsonl` + summary |
| 5 | TTS gate | 3–30 s, ≤ 15 h per channel, 24 kHz mono, single-speaker check (3 windows, min cosine ≥ 0.75; falls back to the median if fewer than 30 % pass), ≥ 36 codec frames. | `tts_build_set_e0003.py` | TTS train set + `stats.json` |
| 6 | Record | Update the data card hours and checksums, the [source list](../sources/README.md), and this page. | – | git |

What to log for stages 3–5: the counts in [`tri-label-arbitration.md`](tri-label-arbitration.md#what-to-log-for-each-run),
the Gemini spend, and the TTS gate's `stats.json` (pass rate, per-channel median similarity).

Reference numbers from the `yt_more` batch (2026-11-07/08; 9,944 segments, 76.92 h, 7 channels): 95.7 % kept
(sync 70.1 %, sub 25.7 %), 4.3 % rejected; Gemini cost US$11.10; processed clips about 23 MB per hour of audio.

## Clean-up problems and directions

| Problem | Seen in | What we do now | Direction (not done yet) |
|---|---|---|---|
| Members-only uploads | FHProductionHK (210 h of 228 h streams), mingjai14 (a few) | skip them (they cannot be downloaded) | – |
| No creator subtitles | FHProductionHK 0/6, The MultiTalk 0/4, mingjai14 3/5 without (2026-11-10 samples) | burned-in caption OCR as S (床哥 route) | Two-label mode (G + Q, keep `sync` only) for channels with no captions at all; measure how much it keeps on a pilot |
| BGM, sound effects, game audio | variety shows, streams | tri-label reject (best pair similarity < 0.60) | Vocal separation (Demucs) before labelling; check it does not hurt CER or speaker similarity |
| Music videos, singing | FHProductionHK | drop by title | Singing detector |
| Several speakers, overlaps, shouting | interview and sketch channels | TTS gate single-speaker check | Diarization before segmentation, so a clip never spans two speakers |
| Putonghua, Japanese, Korean or English guests | The Do Show (many overseas-star interviews) | merge rejects: colloquial score (Putonghua), kana (Japanese), hangul (Korean, added 2026-11-10), han share of G < 0.25 counting English words (English, added 2026-11-10) | Language-ID model |
| Exaggerated acting voices | sketch channels | nothing yet | Cap their share in TTS mixes; prefer interview channels (owner, 2026-11-10) |
| Many fillers (呃, 噉) | interviews | nothing yet | Observation, not verified: a filler-heavy reference clip made E0009 inference unstable (2026-11-10). Check whether fillers are in the labels |
| Digits | all | train rows with digits are dropped | Spoken-number normaliser, so those rows can be kept |
| `yt-dlp` breaks | 2026-11-10 | `--ignore-config` (a cookies file in the config caused `KeyError('INNERTUBE_CONTEXT')`), latest yt-dlp via `uvx`, `youtubetab:skip=authcheck` for channel tabs | Pin the yt-dlp version in each build record |

## Channel status

✅ done · 🟡 partly · ⬜ not started · – not applicable. "Left" = public hours on YouTube not yet in the corpus
(rough: public hours minus the OrcinusOrca hours; overlap not checked).

| Channel | Type | 0 Check | 1 Download | 2 Segment | 3 Label | 4 Manifest | 5 TTS gate | Left | Notes |
|---|---|---|---|---|---|---|---|---|---|
| ahju | solo | ✅ | 🟡 A | ✅ | ✅ | ✅ | ✅ | not checked | OrcinusOrca has 28.8 h, ~19 h used |
| bboblackboxoffice | multi-speaker | ✅ | 🟡 A | ✅ | ✅ | ✅ | ✅ | not checked | OrcinusOrca has 32.7 h, ~17 h used |
| mm.millmilk | interviews | ✅ | 🟡 A | ✅ | ✅ | ✅ | ✅ | not checked | OrcinusOrca has 271 h, only ~11 h used |
| mingjai14 | solo narrator | ✅ | 🟡 A | ✅ | ✅ | ✅ | ✅ | ~72 h | YouTube: 471 public videos / 106.1 h, 5 public streams / 10.4 h; subtitles 2/5 sampled |
| unwire | tech reviews | ✅ | 🟡 A | ✅ | ✅ | ✅ | ✅ | not checked | OrcinusOrca has 48.5 h, ~9 h used |
| thedoshow0909 | interviews | ✅ | 🟡 A, B running | 🟡 | 🟡 | ✅ (A) | ✅ (A) | ~29 h | YouTube: 73 public videos / 46.6 h; subtitles 3/4 sampled. 2026-11-10: the 50 videos not in OrcinusOrca (28.8 h) started through Route B (`yt_more2_chain.sh`) |
| pricehongkongofficial | tech reviews | ✅ | 🟡 A | ✅ | ✅ | ✅ | ✅ | not checked | OrcinusOrca has 132 h, ~8 h used |
| 床哥 highlights | call-in stream | ✅ | ✅ B | ✅ | ✅ OCR | ✅ | ✅ | – | see publication checklist |
| themultitalk | talk / podcast | ✅ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ~386 h | 488 public videos / 385.6 h; subtitles 0/4 sampled |
| fhproductionhk | sketches, variety | ✅ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ~98 h | public 80.3 h videos + 17.6 h streams; subtitles 0/6 sampled; owner prefers interview channels |

Next in line (2026-11-10): the rest of The Do Show (has subtitles), then mingjai14, then a small The MultiTalk pilot
to measure the no-subtitle route.
