# TTS audio preparation (from corpus master to model input)

Spec from blueprint §3.1. The parts tied to one model are marked **[model]**. Re-derive those for each base model.

1. Resample from the corpus master to the model's sample rate, mono. **[model]** (Qwen3-TTS: 24 kHz)
2. Drop clips shorter than the minimum duration. **[model]** (Qwen3-TTS-12Hz: 3.0 s = 36 frames. Shorter clips cause rushed speech / early-EOS collapse.)
3. Trim silence: leading to 0.10 s, trailing to 0.30 s.
4. Encode to discrete codes with the model's **exact** tokenizer, matching its revision. **[model]** (`Qwen/Qwen3-TTS-Tokenizer-12Hz`)
5. Write the cache with a build record: tokenizer id + revision, input manifest sha256, clip counts in and out, and dropped clips by reason.

The codec cache is derived data. It is rebuildable, git-ignored, and never canonical (ADR 0001).
