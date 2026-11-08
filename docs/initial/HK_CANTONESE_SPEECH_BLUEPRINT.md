# Hong Kong Cantonese Speech Foundation & Adaptation Blueprint
## Model-Agnostic Data Curation, Training Methodology & Interface Spec (for Project Sunset & Future Speech Models)

**Document Version:** 1.0  
**Date:** 2026-11-08  
**Purpose:** A self-contained, model-agnostic technical handoff specification for an engineering agent to build or adapt **authentic Hong Kong Cantonese** speech-recognition (ASR), text-to-speech (TTS), and speech-to-speech (S2S / Omni) models, plus a unified Voice Cloning & Emotion Control interface.

---

## 1. Executive Summary & Core Problem

Most open-weight models claiming "Cantonese (`yue`)" support suffer from three structural defects when used in Hong Kong applications:
1. **Pearl River Delta / Guangzhou Accent Contamination ("珠三角鄉音"):** Public corpora such as Mozilla Common Voice `yue` contain **< 4% confirmed Hong Kong speakers**; the majority are Guangzhou, Foshan, or overseas Cantonese speakers. Models trained on unfiltered `yue` acquire Mainland Cantonese pitch contours and pronunciation.
2. **Written-Chinese (書面語) Transcript Mismatch:** Most public datasets pair spoken Cantonese audio with Standard Written Chinese subtitles (`今天我們去辦公室` instead of actual spoken `今日我哋返 office`), corrupting both ASR outputs and TTS text-to-phoneme mappings.
3. **Read-Speech Stiffness ("死板朗讀腔"):** Crowd-recorded single-sentence reading lacks natural Hong Kong conversational prosody, sentence-final particles (`㗎、囉、喎、啫、吖嘛`), and effortless **Cantonese–English technical code-switching** (`encoder`, `latent space`, `at least`, `office`).

### Our Proven Solution: Three-Layer Decoupled Architecture
To make our investment **100% reusable across future base models** (whether upgrading from `Qwen3` to `Qwen4`, `GLM-4-Voice`, `Moshi`, `Fish Speech`, or `CosyVoice`), we strictly separate the system into three layers:

```text
+-----------------------------------------------------------------------------------+
| LAYER 1: Model-Agnostic Golden HK Corpus (100% Pure HK Accent + Verbatim 口語)     |
|  - Tri-labelled conversational HK YouTube/stream audio + strict zh-HK datasets    |
|  - Stored as canonical (WAV 24kHz/16kHz + Verbatim HK Text + Emotion/Speaker Tag) |
+-----------------------------------------------------------------------------------+
                                         |
            +----------------------------+----------------------------+
            v                            v                            v
+-----------------------+    +-----------------------+    +-------------------------+
| LAYER 2A: ASR (Ears)  |    | LAYER 2B: TTS (Mouth) |    | LAYER 2C: S2S (Omni)    |
| - Qwen3-ASR 1.7B FT   |    | - Qwen3-TTS 12Hz 1.7B |    | - Qwen3-Omni Talker+MTP |
| - Lightweight CTC     |    | - Fish / CosyVoice    |    | - GLM-4-Voice / Moshi   |
+-----------------------+    +-----------------------+    +-------------------------+
            \                            |                            /
             +---------------------------+---------------------------+
                                         v
+-----------------------------------------------------------------------------------+
| LAYER 3: Unified Voice, Speaker-Clone & Emotion Control API / UI                  |
|  - OpenAI-compatible /v1/audio/speech & /v1/audio/transcriptions                  |
|  - Zero-shot Speaker Embedding (.spk) + Full ICL Emotion/Prosody Prompting (.icl) |
+-----------------------------------------------------------------------------------+
```

---

## 2. Layer 1 — The Model-Agnostic Hong Kong Cantonese Data Pipeline

**Golden Rule:** The dataset is the moat. Models change every 6 months; a clean, verbatim, accent-pure Hong Kong corpus can fine-tune any new model in hours.

### 2.1 Dataset Selection: What to Include vs. What to Strictly Exclude

| Dataset / Source | Role in Training | Inclusion / Filtering Rule | Volume |
|---|---|---|---|
| **1. Conversational HK YouTube & Live Streams** (`OrcinusOrca/YouTube-Cantonese` HK channels + HK creator highlights) | **Primary Prosody, Slang & Code-Switching Core** (Teaches natural HK cadence, particles, and English terms) | **Include only verified HK channels** (e.g., `mm.millmilk`, `pricehongkongofficial`, `unwire`, `ahju`, `bboblackboxoffice`, `mingjai14`, `thedoshow0909`, JFFT `床哥心事台`). **Filter out Mandarin/Japanese guests** via colloquial density score. | **100+ hours** (700+ hours raw available) |
| **2. Common Voice `zh-HK` (v23 / v27)** | Broad HK Speaker Diversity | Use the explicit **`zh-HK`** split, **NOT** the generic `yue` split (unless filtered by HK accent metadata). Convert written prompts where needed or use for acoustic diversity. | ~53 hours |
| **3. MDCC (Multi-Domain Cantonese Corpus)** | Clean Studio HK Read Speech | High-SNR Hong Kong audiobook speech; great for stabilizing character pronunciation. | ~57 hours |
| **4. MCE (`AlienKevin/mixed_cantonese_and_english_speech`)** | Heavy Cantonese–English Code-Switching | Crucial for technical tutoring (`Project Sunset`) where every sentence mixes Cantonese grammar with English terms. | ~25 hours |
| **5. ZoengJyutGaai (`CanCLID/zoengjyutgaai`) & LegCo** | Long-form Storytelling & Formal HK Register | Cap storytelling to ~40h per epoch so a single narrator does not dominate speaker priors. | ~40–180 hours |
| **❌ Unfiltered Common Voice `yue`** | **EXCLUDE from TTS/Accent Phase** | Contains >90% non-HK (Guangzhou / PRD) accents. Using it in TTS language adaptation directly causes "珠三角鄉音". | **0 hours in TTS** |

### 2.2 The "Tri-Label + Subtitle Arbiter" Pipeline (Solving Written Subtitles)

Hong Kong YouTubers upload **Standard Written Chinese subtitles** (`如果坐的士可以多睡20分鐘`), while actually speaking **colloquial HK Cantonese** (`如果搭的士嘅話可以瞓多四個字`). Feeding written subtitles as training targets ruins both ASR and TTS.

Furthermore, **never pass written subtitles as `context` into a Cantonese ASR model during labelling**—empirical testing proved that written-Chinese context contaminates the ASR into outputting written Chinese (`省了4,000蚊` instead of `慳咗四千蚊`).

Instead, run our proven **Tri-Label Arbitration Pipeline** on every raw audio segment (3–25 seconds):

1. **Candidate `G` (Teacher Multimodal LLM — e.g., Gemini Flash Audio):**
   - Input: Raw audio + creator subtitle (with explicit prompt: *"Subtitle is written Chinese and only for proper nouns/English spelling reference; transcribe verbatim spoken HK Cantonese using 嘅咗喺佢冇啲嘢噉"*).
2. **Candidate `Q` (Local Fine-Tuned HK ASR — e.g., our `Qwen3-ASR-1.7B-Cantonese-HK`):**
   - Input: Raw audio **only** (zero subtitle context, preventing written-Chinese contamination).
3. **Candidate `S` (Creator Subtitle):**
   - Used **only as an arbiter**, never selected directly unless already colloquial.
4. **Skeleton Consensus & Colloquial Selection (`merge` rule):**
   - Normalize spoken-to-written equivalents (`睇↔看, 瞓↔睡, 畀↔給, 搵↔找, 嚟↔來, 食↔吃`) and strip modal particles to compute pairwise **content skeleton similarity** $\text{sim}(X, Y)$.
   - **If $\text{CER}(G, Q) \le 15\%$ (`sync` — ~70% of clips):** Both models agree on the speech; pick the candidate with the higher **HK Colloquial Density Score** (count of `嘅咗喺佢冇啲嘢噉嚟唔係睇諗瞓攞畀搵` minus written markers `什麼/沒有/的/了/他/說/睡`).
   - **If $\text{CER}(G, Q) > 15\%$ (`sub` — ~25% of clips):** Use subtitle `S` as the tie-breaker! Whichever of `G` or `Q` has higher skeleton agreement with `S` wins (e.g., `G` correctly spells `ZenFone 10` / `120Hz` from the subtitle while keeping spoken Cantonese grammar).
   - **Auto-Reject (~4–5% of clips):** Drop clips where $\max \text{sim} < 0.60$ (heavy BGM/noise), clips containing Japanese kana, or clips where `G` has negative colloquial score (Putonghua guest speakers).

**Verified Yield:** On 80 hours (10,342 segments) across 7 HK YouTube channels, this pipeline automatically retained **95.7% clean verbatim HK speech** while catching and removing Putonghua/Japanese guests and noisy BGM.

### 2.3 Canonical Model-Agnostic Storage Format

Store the cleaned corpus once in a universal manifest format so **any future model** can consume it via a 50-line adapter script:

```json
{
  "id": "mm.millmilk_-3fikODBMs4_1-8",
  "audio_24k_wav": "corpus/wav24k/mm.millmilk/-3fikODBMs4_1-8.wav",
  "duration_s": 15.92,
  "text_verbatim_hk": "噉既然 office 有免費咖啡，雖然冇咁好飲，但係難飲嘅話咪仲提神，at least 我噉樣同自己講。",
  "jyutping": "gam2 gei3 jin4 office jau5 min5 fai3 gaa3 fe1 ...",
  "speaker_id": "yt-mm.millmilk-chucky",
  "accent": "zh-HK-native",
  "style_tag": "conversational_natural",
  "snr_db": 28.4
}
```

---

## 3. Layer 2 — How to Train Each Model Type (Targets & Recipes)

Clarifying the distinction asked in the group:
- **Up to this morning:** We trained **Speech-to-Text (ASR)** models (`Qwen3-ASR 1.7B Stage 2` and `EG2-Reader v6`), achieving state-of-the-art HK Cantonese recognition. Specifically, our **`Qwen3-ASR 1.7B Stage 2`** achieved:
  - `MDCC`: **2.49% CER** (vs. Base 4.25%, Whisper-large-v3 34.52%)
  - `CV Cantonese`: **3.86% CER** (vs. Base 5.46%, Whisper 36.44%)
  - `FLEURS`: **3.95% CER** (vs. Base 4.20%, Whisper 20.97%)
  - `CV zh-HK`: **5.09% CER** (vs. Base 7.65%, Whisper 41.76%)
  - `MCE (Cantonese-English Code-Switch)`: **5.62% CER** (vs. Base 11.74% — **error rate cut in half!**)
  - `LegCo`: **7.16% CER** (vs. Base 7.22%, Whisper 32.15%)
  - `HK YouTube / 床哥`: **11.07% CER** (vs. Base 14.07%, Whisper 38.08%)
- **Next Target (for Voice Output):** Training **Text-to-Speech (TTS)** and/or **Speech-to-Speech (S2S)** using the exact same 100h+ Golden HK Corpus so the AI *speaks* with an authentic Hong Kong voice and prosody.

Below is the reusable training recipe for all three model families:

### 3.1 Family A: Discrete-Codec Autoregressive TTS (e.g., `Qwen3-TTS-12Hz-1.7B-Base`, `Fish Speech`, `CosyVoice`)

**Why `jmtl` had a PRD accent & couldn't clone voices:** They trained on `CV yue` (96% non-HK) and deleted `speaker_encoder.*` at export.  
**Our Pure-HK Recipe (Two-Phase LoRA with Speaker Encoder Preserved):**

1. **Audio Tokenization Step:**
   - Resample Golden HK Corpus audio to 24 kHz mono.
   - Filter out clips $< 3.0\text{ s}$ (`min_frames = 36` at 12 Hz) to prevent rushed-speech / early-EOS collapse.
   - Trim leading silence to `0.10 s` and trailing silence to `0.30 s`.
   - Encode every clip into discrete RVQ `audio_codes` using the model's exact local tokenizer (`Qwen/Qwen3-TTS-Tokenizer-12Hz`).
2. **Phase 1 — Pure Hong Kong Language & Prosody Adaptation (`train-lang`):**
   - **Base Model:** `Qwen/Qwen3-TTS-12Hz-1.7B-Base`
   - **Data:** 96h HK YouTube (conversational) + 53h `CV zh-HK` + 57h `MDCC` (100% Hong Kong speakers; **0% Mainland `CV yue`**).
   - **Target Modules:** LoRA (`r=32, alpha=64`) on all 196 Talker attention/MLP projections (`q_proj, k_proj, v_proj, o_proj, gate_proj, up_proj, down_proj`).
   - **Crucial Flag:** **`--keep_speaker_encoder`** (freeze `speaker_encoder.*` and `code_predictor` so the model retains zero-shot voice cloning and multi-speaker conditioning while learning HK pronunciation and conversational rhythm!).
   - **Hyperparameters:** `lr = 5e-5` to `1e-4`, `warmup_ratio = 0.03`, `sub_talker_loss_weight = 0.0`, 1–2 epochs.
3. **Phase 2 — Curated HK Persona / Emotion Voices (`train-speaker` or Zero-Shot `.icl` Bank):**
   - Instead of baking a single rigid speaker and destroying the encoder, keep the model as a `base` / `voice_clone` checkpoint **or** bake multiple named HK speaker rows (`hk_female_anchor`, `hk_male_youtuber`, `hk_tsundere`) into `codec_embedding.weight` rows `3000..3010` while keeping the `speaker_encoder` intact.

### 3.2 Family B: End-to-End Speech-to-Speech / Omni Models (e.g., `Qwen3-Omni-30B-A3B`, `GLM-4-Voice-9B`, `Moshi`)

If you later switch to a native Speech-to-Speech model, the **exact same Golden HK Corpus** adapts it:
- **For `Qwen3-Omni` (`Thinker + Talker + MTP`):**
  - Encode the target HK audio into 16-layer RVQ tokens using **`kyutai/mimi`** (`MimiModel.from_pretrained("kyutai/mimi")`).
  - Apply LoRA simultaneously to **Thinker** (`lr=5e-6`, learns to understand HK speech and think in colloquial HK text), **Talker** (`lr=2e-5`, predicts layer-0 Mimi token), and **MTP `code_predictor`** (`lr=5e-5`, predicts layers 1–15), with $\mathcal{L} = \mathcal{L}_{\text{talker}} + 2.0 \cdot \mathcal{L}_{\text{mtp}}$.
- **For `GLM-4-Voice-9B`:**
  - Encode audio with `GLM-4-Voice-Tokenizer` (12.5 Hz) and run SFT on interleaved `(text_tokens, audio_tokens)` pairs.

### 3.3 Family C: Speech-to-Text / ASR Models (Already Completed & Proven)

- **Recipe proven on `Qwen3-ASR-1.7B` & `EG2-Reader`:**
  - Full-parameter SFT (`lr=2e-5` Stage 1, `1e-5` Stage 2 cosine) with `"language Cantonese<asr_text>" + verbatim_hk_text`.
  - For lightweight CTC readers on frozen encoders (`EmbeddingGemma-2`): extract multi-layer middle Conformer representations (`Layers 6, 9, 12, 0` projected via 256-d PCA + learned softmax layer weights) and add an auxiliary **Jyutping (粵拼) CTC loss (`weight=0.3`)** at intermediate layers.

---

## 4. Layer 3 — Custom Voice Cloning & Emotion/Tone Interface Specification

To let developers and end-users **change voices on the fly** and **control emotional tone/prosody**, the inference server (`qwen3-tts.cpp` C API + Python/TS wrapper) should expose three orthogonal controls:

### 4.1 Three Mechanisms for Voice & Emotion Control

1. **Zero-Shot Speaker Cloning (`.spk` — 2048-d Speaker Embedding):**
   - User uploads any 3–10s clean WAV file (`POST /v1/audio/voices/clone`).
   - Backend calls `qwen3_tts_extract_speaker_embedding(ctx, wav_path, spk_path)` (~30 ms).
   - Changes **who** is speaking (timbre/pitch) without changing speaking speed.
2. **Full ICL Prosody & Emotion Cloning (`.icl` — In-Context Audio + Text Prefix):**
   - User uploads a 3–8s reference WAV recorded in a specific **emotion/style** (e.g., *excited*, *gentle tutor*, *sarcastic/tsundere*, *whispering*) along with its transcript (auto-transcribed by our `Qwen3-ASR Stage 2`).
   - Backend calls `qwen3_tts_extract_icl_prompt(ctx, wav_path, ref_text, icl_path)`.
   - During synthesis (`qwen3_tts_synthesize_with_icl_prompt_streaming`), the model prepends the reference speech codes and tokens—**inheriting both the speaker's voice AND the exact emotional cadence/energy of the reference clip!**
3. **Natural-Language Style Instruction (`instruction` field):**
   - For models with instruction-tuned Talkers (or our dataset tagged with `[語氣：...]`), pass `"instruction": "用溫柔、耐性嘅教學語氣講，遇到英文術語自然過渡"` in the API payload (`qwen3_tts_params_t.instruction`).

### 4.2 Proposed REST / WebSocket API Contract (for Your Agent to Implement)

```http
### 1. List available voices & emotion presets
GET /v1/audio/voices
Response:
{
  "voices": [
    {"id": "hk_tutor_calm", "type": "icl_preset", "speaker": "hk_female_1", "emotion": "calm_explaining"},
    {"id": "hk_tutor_excited", "type": "icl_preset", "speaker": "hk_female_1", "emotion": "enthusiastic"},
    {"id": "custom_user_voice", "type": "spk_embedding", "speaker": "custom"}
  ]
}

### 2. Upload 3-10s audio to create a new Voice or Emotion Preset
POST /v1/audio/voices/clone
Content-Type: multipart/form-data
Fields:
  - file: <3-10s WAV/MP3>
  - voice_id: "my_hk_voice"
  - mode: "icl" | "embedding"   # "icl" copies both voice + emotional cadence; "embedding" copies timbre only
  - transcript: (optional; if omitted, auto-transcribed via local Qwen3-ASR-1.7B-Cantonese-HK)

### 3. Synthesize Speech (OpenAI-compatible + Emotion/Style extensions)
POST /v1/audio/speech
Content-Type: application/json
{
  "model": "qwen3-tts-hk",
  "input": "嗱，其實 Variational Autoencoder 最核心嘅概念呢，就係將張圖壓入去一個連續嘅 latent space 入面。",
  "voice": "my_hk_voice",
  "emotion": "calm_explaining",
  "instruction": "自然香港口語，解釋清晰",
  "temperature": 0.9,
  "stream": true,
  "response_format": "wav"
}
```

---

## 5. Actionable Scratch Tasks for Your Engineering Agent

You can hand the following checklist directly to your coding agent to start building the scratch components right now:

- [ ] **Task 1 — Build the Voice & Emotion Manager API + Web UI (`voice-studio`):**
  - Wrap `qwen3-tts.cpp` (`libqwen3_tts_shared.so`) with endpoints for `POST /v1/audio/voices/clone` (supporting both `.spk` embedding extraction and `.icl` full emotion-prompt extraction), `GET /v1/audio/voices`, and streaming `POST /v1/audio/speech`.
  - Build a clean React/HTML control panel where the user can:
    1. Record or drag-and-drop a 5s reference clip to clone a voice in one click;
    2. Create named **Emotion Presets** (e.g., `Calm Tutor`, `Tsundere`, `Casual Chat`, `Whisper`) per voice using `.icl` prompts;
    3. Test Cantonese + English code-switched sentences with real-time TTFA / RTF metrics.
- [ ] **Task 2 — Prepare the Pure-HK TTS Fine-Tuning Pipeline (`hk-tts-trainer`):**
  - Fork/adapt `Qwen3-TTS` 12Hz SFT (`sft_12hz.py`) with a strict **data-source separation config (`dataset_mix.yaml`)**:
    - `language_phase`: accept our cleaned HK YouTube JSONL (`13,023 clips / 96.3h`) + `CV zh-HK`, with `min_duration_s: 3.0`, `max_duration_s: 25.0`, and `--keep_speaker_encoder` enabled.
    - `emotion_tagging`: add an optional preprocessing step that tags each training clip with acoustic energy/pitch contour labels (`[calm]`, `[animated]`, `[questioning]`) so `params.instruction` is trained alongside audio codes.
- [ ] **Task 3 — Define the `Project Sunset` Voice Provider Interface:**
  - Implement a pluggable `VoiceProvider` TypeScript/Python interface in `Project Sunset` that supports:
    - **Path B (Modular Low-Latency Streaming):** `Silero VAD` → `Qwen3-ASR-1.7B-Cantonese-HK` (`TranscriptSpan` source of truth) + `LiquidAI/d1-2B` (10ms Capture Gate) → Streaming Tutor LLM (sentence-chunked on `，。！？`) → `Qwen3-TTS HK (.icl emotion)` stream.
    - **Path A+B Hybrid (Optional):** Native S2S voice model for conversation + parallel `Qwen3-ASR-1.7B-Cantonese-HK` shadow transcription for 100% accurate Cantonese-English wiki citations.
