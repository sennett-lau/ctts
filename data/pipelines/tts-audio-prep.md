# TTS audio preparation (from corpus master to model input)

Spec from blueprint §3.1. The parts tied to one model are marked **[model]**. Re-derive those for each base model.

1. Resample from the corpus master to the model's sample rate, mono. **[model]** (Qwen3-TTS: 24 kHz)
2. Drop clips shorter than the minimum duration. **[model]** (Qwen3-TTS-12Hz: 3.0 s = 36 frames. Shorter clips cause rushed speech / early-EOS collapse.)
3. Trim silence: leading to 0.10 s, trailing to 0.30 s. (Note from `jmtl` v0.0.5 recipe: if using Sidon restoration on noisy clips, restore the raw clip's loudness envelope contour afterwards so dynamics are not flattened; for single-speaker voice-bake clips only, pad trailing digital silence back to source length to prevent early-EOS text skipping.)
4. **Single-speaker & BGM gate (mandatory for YouTube/podcast sources):**
   - Compute speaker-embedding cosine similarity between the first half and second half of the clip (`single_speaker_sim`). Drop clips with `single_speaker_sim < 0.75` so multi-speaker interview turns or overlapping call-ins never enter TTS training.
   - Reject or vocal-isolate clips with heavy background music (`snr_db < 15`).
5. **Spoken-number & symbol normalisation check:** Reject or expand any row where `text_verbatim_hk` still contains raw Arabic digits (`0-9`, `%`, `$`), because digits in TTS transcripts cause fallback to Mandarin/written readings (`百分之十四` instead of spoken `十四個 percent`).
6. Encode to discrete codes with the model's **exact** tokenizer, matching its revision. **[model]** (`Qwen/Qwen3-TTS-Tokenizer-12Hz`)
7. Write the cache with a build record: tokenizer id + revision, input manifest sha256, clip counts in and out, and dropped clips by reason.

The codec cache is derived data. It is rebuildable, git-ignored, and never canonical (ADR 0001).
