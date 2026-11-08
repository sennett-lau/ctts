# 0004. Multi-host compute & private artefact synchronisation

- **Status:** accepted
- **Date:** 2026-11-08
- **Related:** ADR 0002

## Context
Two compute environments collaborate on CTTS:
1. **Primary Corpus & Large-Memory Host (`gpu-workstation-01` + Colab G4 96 GB):** Holds the cleaned 96.28 h Hong Kong YouTube corpus (`yt_train.jsonl`, 13,023 clips), `CV zh-HK`, `MDCC`, `MCE`, the fine-tuned `Qwen3-ASR-1.7B-Cantonese-HK` Stage 2 judge, and the compiled `qwen3-tts.cpp` (`libqwen3_tts_shared.so`) runtime.
2. **Local RTX Workstation (`sennett-pc`, RTX 3080 Ti 12 GB WSL):** Used by the partner engineering agent for development, evaluation, and single-GPU runs.

Because 12 GB VRAM requires `batch_size = 1` (~7–8 hours per epoch on `Qwen3-TTS-12Hz-1.7B-Base`), whereas 96 GB / 124 GB unified memory runs `batch_size = 16–32` in under 1 hour, both machines must be able to run the exact same `src/ctts/` scripts and record results into `experiments/`.

## Decision
1. **Code & experiment records sync via this GitHub repo (`sennett-lau/ctts`).**
2. **Large artefacts (pre-encoded 12 Hz codec JSONLs, LoRA checkpoints, GGUF exports) sync via Private Hugging Face repos** (or direct `rsync` over Tailscale between hosts), with exact `sha256` digests committed in `experiments/<id>/README.md` and `data/sources/*.md`.
3. **PII / Host Hygiene:** Never commit personal names, phone numbers, or private Tailscale IPs into this public repository. Use neutral host aliases (`gpu-workstation-01`, `sennett-pc`, `colab-g4`) in `env/hardware.txt`.
