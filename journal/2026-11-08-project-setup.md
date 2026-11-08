# 2026-11-08: project setup

Author: setup agent (Claude) · Related: ADR 0001–0003

- Repo created from `docs/initial/HK_CANTONESE_SPEECH_BLUEPRINT.md` and the agent task brief.
- Framed as a **method** project: the record of data, recipe, evaluation and outcomes is the deliverable.
  Checkpoints are by-products.
- Scope set to TTS first (ADR 0003). ASR is prior work and serves as a tool.
- No data downloaded, no code written, no training run. Implementation is handed to another agent,
  which should start with `CLAUDE.md` and `docs/roadmap.md` (P1 corpus, P2 eval harness and baselines).
- Numbers in the data cards (96.3 h, 13,023 clips, ~53 h, ~57 h, ~25 h) come from the source documents and are
  **unverified**. P1 replaces them with measured stats.
- The GitHub repo is public, so third-party audio, transcripts and voice prompts stay out of git (ADR 0002).
