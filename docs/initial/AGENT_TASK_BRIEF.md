# Agent Task Brief: Hong Kong Cantonese Speech Adaptation & Voice/Emotion Studio (Project Sunset)

> Source document, kept verbatim as received on 2026-11-08. It is the brief handed to the
> implementation agent alongside `HK_CANTONESE_SPEECH_BLUEPRINT.md`. Do not edit it; record
> changes of plan in `docs/decisions/` instead.

Please read the attached HK_CANTONESE_SPEECH_BLUEPRINT.md for full architectural details. We are building a model-agnostic Hong Kong Cantonese speech stack (ASR + TTS + future S2S) and integrating it into Project Sunset.

## Core Design Principles (Model-Agnostic Separation)
1. *Layer 1 — Canonical Golden HK Corpus (Data Layer, separated from model weights):*
   - *Include ONLY pure Hong Kong accents & conversational prosody:* Our tri-labelled HK YouTube corpus (96.3h, 13,023 clips across 7 HK channels: Mill MILK, Price.com.hk, Unwire, MingJai, AhJu, DoShow, BBO + JFFT), Common Voice zh-HK, MDCC, and MCE (Cantonese-English code-switching).
   - *STRICTLY EXCLUDE unfiltered Common Voice yue* from TTS/Accent training (it is >96% Mainland/PRD Cantonese and causes non-HK accent drift).
   - *Tri-Label Arbitration for new data:* Never use raw written-Chinese subtitles as speech targets, and never pass written subtitles into ASR context prompts (causes written-Chinese output contamination). Use Gemini Audio (G) + Local Fine-Tuned Qwen3-ASR (Q) + Subtitle Arbiter (S) with skeleton-similarity consensus and HK colloquial density scoring (嘅咗喺佢冇啲嘢噉).

2. *Layer 2 — Reusable Fine-Tuning Recipe (Target: Authentic HK TTS & Future S2S):*
   - *For Discrete-Codec TTS (Qwen/Qwen3-TTS-12Hz-1.7B-Base, Fish Speech, CosyVoice):*
     - Filter clips to 3.0s - 25.0s (>=36 frames at 12Hz) to prevent rushed-speech collapse; trim edges (0.10s lead, 0.30s trail).
     - Encode audio into discrete RVQ codes using the model's exact local tokenizer (Qwen3-TTS-Tokenizer-12Hz).
     - Run Language/Accent LoRA (r=32, alpha=64) on Talker projections WITH *--keep_speaker_encoder* enabled (do NOT drop speaker_encoder.* tensors—preserve zero-shot voice cloning!).
   - *For End-to-End S2S (Qwen3-Omni Talker+MTP or GLM-4-Voice):*
     - Same Golden HK Corpus, encoded via kyutai/mimi (16 codebooks) or GLM-4-Voice-Tokenizer (12.5Hz), training Thinker + Talker + MTP via LoRA.

3. *Layer 3 — Voice Cloning & Emotion/Prosody Control Interface (qwen3-tts.cpp / API):*
   - Build a clean API + Web UI on top of qwen3-tts.cpp (libqwen3_tts_shared.so) supporting three controls:
     a) *Zero-shot Speaker Cloning (.spk):* Upload 3–10s WAV -> qwen3_tts_extract_speaker_embedding -> instant custom timbre.
     b) *Full ICL Emotion & Prosody Cloning (.icl):* Upload 3–8s WAV + transcript (auto-transcribed by our Qwen3-ASR-1.7B-Cantonese-HK) -> qwen3_tts_extract_icl_prompt -> clones both voice AND emotional cadence (e.g., calm_tutor, excited, tsundere, whisper).
     c) *Style Instruction (params.instruction):* Pass natural-language tone tags trained from acoustic energy/pitch labels.

## Immediate Scratch Tasks for You (Agent)
1. *Design & scaffold the voice-studio API + UI* (POST /v1/audio/voices/clone, GET /v1/audio/voices, POST /v1/audio/speech with voice, emotion, and instruction fields).
2. *Design the modular hk-tts-trainer config & scripts* so we can plug in the 96.3h HK YouTube manifest and swap base models (Qwen3-TTS, Qwen3-Omni, GLM-4-Voice, CosyVoice) without rewriting the data pipeline.
3. *Write a technical report / implementation plan* on how you will structure the repo, the .spk / .icl preset manager, and the VoiceProvider adapter for Project Sunset so we can review and run the training on GPU.
