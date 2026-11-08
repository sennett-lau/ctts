# Recipe: end-to-end S2S / Omni (v0 stub, *later*)

From blueprint §3.2. Not in current scope (ADR 0003). Kept so the corpus design accounts for it.

- **Qwen3-Omni (Thinker + Talker + MTP):** encode targets with `kyutai/mimi` (16 codebooks). LoRA on Thinker
  (lr 5e-6), Talker (2e-5, layer-0 token) and MTP code predictor (5e-5, layers 1–15). Loss = L_talker + 2.0·L_mtp.
- **GLM-4-Voice-9B:** encode with GLM-4-Voice-Tokenizer (12.5 Hz), SFT on interleaved text/audio tokens.

Uses the same canonical manifest. It needs no corpus changes, only adapters.
