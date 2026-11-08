# 0001. Three-layer decoupled architecture; the manifest is the boundary

- **Status:** accepted
- **Date:** 2026-11-08
- **Related:** `docs/initial/HK_CANTONESE_SPEECH_BLUEPRINT.md` §1–2

## Context
Base models turn over every few months. Earlier work spent most of its effort on data
(accent filtering, verbatim labelling), and that effort is lost if it is tied to one model's format.

## Options considered
1. Prepare data directly in each model's training format.
2. Keep one canonical corpus + manifest and write a thin adapter per model.

## Decision
Option 2. Layer 1 (corpus) is model-agnostic and stored once. Layer 2 holds the per-model
adapters and recipes. Layer 3 holds the serving and control interface. The canonical manifest
(`data/schemas/manifest.schema.json`) is the only contract between Layer 1 and Layer 2.

## Consequences
- A new base model needs an adapter, a base-model card and a baseline, and no change to the corpus.
- Changes to the schema are versioned and need an ADR.
- Model-specific derived data (codec tokens, resampled copies) is a cache: rebuildable and never canonical.
