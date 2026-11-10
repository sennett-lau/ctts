# Pipeline scripts (as run)

Copies of the scripts that built `hk-youtube-conversational` and the E0003 TTS set, kept so the workflow in
[`../youtube-ingest.md`](../youtube-ingest.md) can be repeated and audited. They are **snapshots**, not the
package: the plan is to fold them into `src/ctts/data/` and `src/ctts/label/` (see CLAUDE.md, *Code layout*).

Changes from the originals: the Gemini key comes from `GEMINI_API_KEY` (or a file named by `GEMINI_API_KEY_FILE`),
and people's names were removed from comments. Nothing else, so paths still assume the corpus host layout:
each script sits in `data_yue/` of the ASR corpus repo, writes next to itself, and imports helpers from that repo
(`embed2asr.metrics`, `embed2asr.numnorm`). `tts_build_set_e0003.py` ran on Colab with paths under `/content/`.

| Script | Stage | What it does |
|---|---|---|
| `channel_check.py` | 0 | Public vs members-only hours per tab, title keywords, creator subtitles in a sample (new, 2026-11-10) |
| `yt_gemini_pilot.py` | 3 | Gemini Flash labels for OrcinusOrca segments (pilot; also holds the prompt and prices `yt_tri_label.py` reuses) |
| `yt_tri_label.py` | 1–3 | `extract` (pick segments from OrcinusOrca tars), `gemini`, `qwen`, `merge` (arbitration) |
| `yt_tri_chain.sh` | 1–3 | Runs the four `yt_tri_label.py` stages in order (Gemini and Qwen in parallel) |
| `yt_dl_segment.py` | 1–2 | Route B for videos not in OrcinusOrca: `yt-dlp` audio + creator vtt, subtitle-cue segments (silence cuts when there are no subtitles), writes the `meta.jsonl` that `yt_tri_label.py gemini/qwen/merge` read via `YT_TRI_OUT` |
| `yt_more2_chain.sh` | 1–3 | 2026-11-10 run: the 50 The Do Show videos not in OrcinusOrca → Route B → tri-label (Gemini cap US$6, Qwen-FT Stage 2) |
| `chong_pipeline.py` | 1–3 | Route B: pick videos, `yt-dlp` audio + subtitles, silence cuts, Gemini pass 1 |
| `qwen_label.py` | 3 | Independent Qwen3-ASR transcripts (forced Cantonese, no hints) to cross-check the Gemini labels |
| `chong_failed_qwen.py` | 3 | Chunks Gemini returned nothing for: asks Gemini for the block reason, then transcribes them with Qwen3-ASR |
| `chong_ocr.py` | 3 | Burned-in caption OCR (RapidOCR): finds the subtitle band, OCRs each change, drops overlays and speaker tags |
| `chong_sub_strips.py` | 3 | Stacks subtitle-band crops of hard chunks into one image for manual reading |
| `chong_relabel.py` | 3 | Gemini pass 2 with OCR + Qwen hints, then agreement scoring |
| `chong_quality_chain.sh` | 3 | Waits for OCR + Qwen, then runs `chong_relabel.py` hints → gemini → score |
| `build_yt_manifests.py` | 4 | Video-level split, grades, digit-free train rows → `yt_{train,dev,test}.jsonl` |
| `tts_build_set_e0003.py` | 5 | TTS gate and codec encoding for E0003 (filters, caps, single-speaker check, 12 Hz codes) |

Environments: the Qwen3-ASR steps ran in the ASR repo's `.venv-qft`, OCR in `.venv-ocr`, the rest in `.venv`.
Record the yt-dlp version in every build.
