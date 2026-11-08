# 0002. Audio, weights and raw logs live outside git

- **Status:** accepted
- **Date:** 2026-11-08

## Context
The GitHub repo is public. The corpus contains third-party audio (HK YouTube creators) that we
must not redistribute. Checkpoints are several GB. Raw training logs are large and noisy.

## Options considered
1. Git LFS for everything.
2. Keep artefacts outside git; commit pointers (location + sha256), small derived files and short samples.

## Decision
Option 2. `.gitignore` blocks audio, weights, codec caches and `.spk`/`.icl` files. Experiment
folders commit configs, environment captures, scalar CSVs, metrics JSON and a few compressed
listening samples, and record pointers to everything else.

## Consequences
- Reproducing a run needs access to the external artefact store. Data cards and experiment
  cards must state where things are.
- Publishing listening samples of models trained on third-party voices needs a per-source
  licence check (data card → *Licence*).
- Long-term artefact storage is not decided yet (see roadmap, *Open questions*).
