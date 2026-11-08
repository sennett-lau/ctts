# Recipes

A recipe is the training method for a model **family**, written so that it applies to any member
of the family. Model-specific values go in `base-models/<slug>.md`. Recipes are versioned: when
experiments change the method, bump the version and log the change at the bottom.

| Recipe | Family | Status |
|---|---|---|
| [codec-ar-tts.md](codec-ar-tts.md) | Discrete-codec autoregressive TTS (Qwen3-TTS, CosyVoice, Fish Speech) | v0, from blueprint, unvalidated |
| [s2s-omni.md](s2s-omni.md) | End-to-end speech-to-speech (Qwen3-Omni, GLM-4-Voice, Moshi) | v0 stub, later |
