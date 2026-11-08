# Glossary

| Term | Meaning in this repo |
|---|---|
| **HK Cantonese** | Cantonese as spoken by Hong Kong natives (`zh-HK`). Distinct from Guangzhou/PRD Cantonese in accent and vocabulary. |
| **PRD accent / 珠三角鄉音** | The Pearl River Delta (Guangzhou, Foshan, ...) accent. Models trained on unfiltered CV `yue` drift towards it. A failure mode for us. |
| **口語 / verbatim spoken text** | Text written exactly as spoken, using colloquial characters (嘅咗喺佢冇啲嘢噉嚟). The only acceptable training target. |
| **書面語 / written Chinese** | Standard written Chinese (的了他沒有什麼). Common in subtitles. **Never a speech target.** |
| **Code-switching** | Mixing English words into Cantonese sentences (`office`, `latent space`, `at least`). |
| **SFP** | Sentence-final particles (㗎、囉、喎、啫、吖嘛). Hard to synthesise naturally. |
| **Golden HK corpus** | The cleaned, accent-pure, verbatim-labelled corpus (Layer 1). Model-agnostic. |
| **Canonical manifest** | JSONL describing the corpus in the model-agnostic schema (`data/schemas/manifest.schema.json`). |
| **Data mix** | A YAML naming which sources, filters and caps form one training set (`data/mixes/`). |
| **Tri-label arbitration** | Labelling method: G (multimodal LLM) + Q (HK ASR, no subtitle context) + S (creator subtitle, arbiter only). |
| **G / Q / S** | The three candidates above. |
| **sync / sub / reject** | Arbitration buckets: G and Q agree / subtitle breaks the tie / dropped. |
| **Colloquial density score** | Count of colloquial markers minus written markers. Used to pick the more 口語 candidate and to detect Putonghua speakers. |
| **Skeleton similarity** | Similarity after normalising spoken↔written equivalents and stripping particles. Compares *content* regardless of register. |
| **Codec-AR TTS** | TTS family that predicts discrete audio codec tokens autoregressively (Qwen3-TTS, CosyVoice, Fish Speech). |
| **Talker / Thinker / MTP / code predictor** | Sub-modules of Qwen3 speech models: Thinker = text LLM; Talker = predicts the first codec layer; MTP / code predictor = predicts the remaining codec layers. |
| **Speaker encoder** | The module that turns reference audio into a speaker embedding. Must be kept for zero-shot cloning. |
| **`.spk`** | Saved speaker embedding (timbre only). |
| **`.icl`** | Saved in-context prompt (reference audio codes + transcript). Carries timbre **and** prosody/emotion. |
| **Round-trip CER** | Synthesise, then ASR, then character error rate against the input text. |
| **RTF / TTFA** | Real-time factor / time-to-first-audio. |
| **Experiment ID** | `E####_<base>_<slug>`, e.g. `E0003_qwen3tts12hz_lang-adapt-r32`. Stable reference used in the report. |
