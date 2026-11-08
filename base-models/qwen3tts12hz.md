---
slug: qwen3tts12hz
hf_id: Qwen/Qwen3-TTS-12Hz-1.7B-Base
revision: TODO
family: codec-ar-tts
licence: TODO — check model card
status: candidate
recipe: recipes/codec-ar-tts.md
last_updated: 2026-11-08
---

# Qwen3-TTS 12Hz 1.7B Base (reference model)

The first base model, and the reference implementation of the recipe.

## Architecture
Talker (LoRA targets: `q_proj, k_proj, v_proj, o_proj, gate_proj, up_proj, down_proj`; 196 projections per
the blueprint), `code_predictor`, `speaker_encoder`. TODO: verify module names and counts against the
actual checkpoint, and record them here.

## Audio tokenizer
`Qwen/Qwen3-TTS-Tokenizer-12Hz`, 24 kHz, 12 Hz frames, RVQ. Minimum clip 3.0 s = 36 frames.

## Speaker and style conditioning
- 2048-d speaker embedding (`.spk`) from the speaker encoder
- ICL prompt (`.icl`): reference codes + transcript, which clones timbre and prosody
- `instruction` field (natural-language style)

**Keep `speaker_encoder.*` (and `code_predictor`) at export.** A previous third-party fine-tune
(`jmtl`) deleted them and lost cloning. It also trained on CV `yue` and got a PRD accent.

## Inference runtime
`qwen3-tts.cpp` (`libqwen3_tts_shared.so`) is relevant for Layer 3 and for RTF/TTFA. Record which runtime each metric used.

## Experiments
| ID | What | Result |
|---|---|---|
| (planned) `E####_qwen3tts12hz_baseline` | untouched model on test set v1 | |
| (planned) `E####_qwen3tts12hz_lang-adapt` | phase-1 LoRA, mix `tts-lang-phase1-v0` | |

## Porting notes
N/A (reference model).
