# `tts-test-v1` (Frozen Evaluation Prompts v1)

- **Frozen Date:** 2026-11-08
- **Total Prompts:** 35 (5 per category across all 7 categories)
- **Listening Subset (`listening.txt`):** 10 prompts rendered into `experiments/<id>/samples/` for every experiment.
- **Rules:**
  1. All numbers are written out in spoken Hong Kong Cantonese words (`四個字`, `十四個 percent`) so TTS models are evaluated on pronunciation and prosody rather than regex number preprocessors.
  2. For `long_form` (`lng-001` .. `lng-005`), the evaluation harness must split at punctuation (`，。！？；：`) into chunks of $\le 42$ characters before synthesis.
