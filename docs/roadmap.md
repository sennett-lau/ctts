# Roadmap and progress

This is the single place to see where the project stands. Update it when a phase starts, finishes
or changes, and link the evidence (experiment IDs, decision records, journal entries).

Status values: `todo` · `active` · `done` · `blocked` · `dropped`

| Phase | Goal | Status | Evidence |
|---|---|---|---|
| P0 Setup | Repo structure, conventions, agent instructions | done | this commit history |
| P1 Corpus v1 | Data cards for every source; canonical manifest built and validated; corpus stats | todo | `data/` |
| P2 Eval harness | Frozen test set v1; metrics implemented; **baselines of the untouched base models** | todo | `evals/` |
| P3 TTS language/accent adaptation | Phase 1 LoRA on Qwen3-TTS-12Hz-1.7B-Base, speaker encoder kept | todo | |
| P4 Personas and emotion | Phase 2: named HK voices / `.icl` emotion bank; optional style-instruction tags | todo | |
| P5 Portability check | Repeat P3 on a second base model (e.g. CosyVoice or Fish Speech) using only this repo | todo | |
| P6 Report | Research-style write-up / site from the records | todo | `report/` |
| Later: Layer 3 | voice-studio API + UI (`/v1/audio/speech`, `/v1/audio/voices/clone`) | todo | |
| Later: S2S | Omni / GLM-4-Voice adaptation on the same corpus | todo | |

P2 comes before P3 on purpose. Without base-model baselines on a frozen test set, no later
claim of improvement can be checked.

## Prior work (before this repo)

These come from earlier work and the blueprint. They have **not been reproduced in this repo**. Cite them
as prior work, not as results of this project.

- **HK ASR, `Qwen3-ASR-1.7B` Stage 2** (full SFT), CER as reported in the blueprint:
  MDCC 2.49% · CV Cantonese 3.86% · FLEURS 3.95% · CV zh-HK 5.09% · MCE 5.62% · LegCo 7.16% · HK YouTube 11.07%.
  This model is used here as **Q** in tri-label arbitration and as a round-trip CER judge.
- **Tri-label arbitration** on 80 h / 10,342 HK YouTube segments: 95.7% retained as clean verbatim HK speech (blueprint figure).
- **Cleaned HK YouTube corpus**: 13,023 clips / 96.3 h across 7+ HK channels (agent brief). It exists
  outside this repo. P1 must locate it, write its data card, and record its checksum.

## Open questions

- Where do corpus audio and checkpoints live long-term (local disk on `sennett-pc`, a private HF repo, other)?
- Which site generator for `report/` (MkDocs Material, Quarto, Astro)? Content stays plain Markdown until decided.
- Licence and redistribution status of each source. Settle it before any manifest or sample is made public.
- Which second base model for P5?
