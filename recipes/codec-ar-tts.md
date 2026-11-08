# Recipe: codec-AR TTS, HK Cantonese adaptation (v0)

**Status:** taken from blueprint §3.1. Not yet validated in this repo. Each step will link the experiments that confirm or change it.

## Preconditions
- Base-model card exists, and so does a baseline experiment on the current test set.
- Data mix built and checksummed (`data/mixes/`).

## Step 0: audio prep
`data/pipelines/tts-audio-prep.md` (resample, minimum duration from the frame rate, trim 0.10 s / 0.30 s, encode with the exact tokenizer).

## Step 1: language and accent adaptation (`train-lang`)
| Setting | v0 value | Why |
|---|---|---|
| Data | `tts-lang-phase1-v0` (HK YouTube + CV zh-HK + MDCC; 0% CV yue) | accent purity |
| Method | LoRA r=32, α=64 on all talker attention + MLP projections | |
| Frozen | speaker encoder, code predictor | keep zero-shot cloning |
| LR | 5e-5 to 1e-4, warmup ratio 0.03 | |
| Sub-talker loss weight | 0.0 | |
| Epochs | 1–2 | |

Checks: HK-accent A/B against the baseline, round-trip CER, speaker similarity **must not drop** against the baseline.

## Step 2: personas and emotion (`train-speaker` or zero-shot bank)
Choose one of:
- keep the adapted model as a voice-clone base and build an `.icl` / `.spk` preset bank; or
- bake named HK speakers into spare speaker rows (Qwen3-TTS: `codec_embedding.weight` rows 3000–3010) while keeping the speaker encoder.

Optional: emotion/style tagging of training clips (energy, pitch contour, giving `[calm] [animated] [questioning]`), trained through the `instruction` field.

## Ablations worth running (for the report)
- With vs without CV `yue` (does it really cause PRD drift?)
- With vs without MCE (effect on code-switching)
- LoRA rank 8 / 32 / 64; 1 vs 2 epochs
- Speaker encoder frozen vs trained vs dropped (effect on cloning)

## Changelog
- v0 (2026-11-08): transcribed from blueprint.
