# 0003. TTS first; ASR is a tool; S2S and Layer 3 later

- **Status:** accepted
- **Date:** 2026-11-08

## Context
The blueprint covers ASR, TTS, S2S and a voice-control API. HK ASR is already done (prior work).
The open problem is a model that *speaks* authentic HK Cantonese.

## Decision
- The research target is **TTS** (codec-AR family first: Qwen3-TTS-12Hz-1.7B-Base).
- The HK ASR model serves as a **tool**: labeller **Q** in tri-label arbitration, and a round-trip CER judge.
- S2S/Omni adaptation and the Layer 3 voice-studio are on the roadmap as *later*. Integration
  into downstream apps (e.g. a `VoiceProvider` adapter) belongs in each app's own repo.

## Consequences
- Evaluation must guard against judge bias, because the ASR judge shares training data (see evaluation protocol).
- Repo structure still leaves room for `studio/` and S2S recipes, so adding them later needs no restructure.
