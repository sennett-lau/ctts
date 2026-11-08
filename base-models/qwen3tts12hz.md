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

## Language Token ID & Operational Constraints
- **Language ID strategy (critical ablation):**
  - Upstream `config.json` maps `chinese -> 2055`, `english -> 2050`, etc., with no dedicated `cantonese` ID.
  - **Option A (`jmtl` style):** Train under `language_id = 2055` (`chinese`) so the LoRA adapter shifts `chinese` to Hong Kong Cantonese.
  - **Option B (`hon9kon9ize` style):** Inject `cantonese -> 2072` into `config.json` and initialize `codec_embedding` row `2072` from row `2055`, keeping Mandarin (`2055`) intact while dedicating `2072` to pure Hong Kong Cantonese.
- **Chunk ceiling (<= 42–45 characters):** At >= 70 characters without punctuation splitting, the 12 Hz Talker skips whole clauses. Always split long text at punctuation (`，。！？；：`) into chunks of <= 42 characters during both inference and evaluation (`long_form`).
- **Sampling constraints:** Keep stochastic sampling (`temperature = 0.9, top_k = 50, top_p = 1.0, repetition_penalty = 1.05`). Greedy decoding (`temperature = 0`) and very low temperatures cause runaway codec loops.

## Inference runtime
`qwen3-tts.cpp` (commit `16bb5afcd06311031c72a8488f8d59660dc2fb46`, compiled as `libqwen3_tts_shared.so`) is used for Layer 3 and for RTF/TTFA benchmarking. Record which runtime (PyTorch BF16 vs `qwen3-tts.cpp` Q8_0) each metric used.

## Experiments
| ID | What | Result |
|---|---|---|
| (planned) `E####_qwen3tts12hz_baseline` | untouched model on test set v1 | |
| (planned) `E####_qwen3tts12hz_lang-adapt` | phase-1 LoRA, mix `tts-lang-phase1-v0` | |

## Porting notes
N/A (reference model).
