# Porting the method to a new base model

This is the reason the repo exists. When a better base model comes out, follow this checklist and
add to it whatever the port teaches you.

1. **Card the model.** Create `base-models/<slug>.md` from the template: HF id + revision, licence,
   architecture family, audio tokenizer (frame rate, codebooks, sample rate), text/prompt format,
   speaker conditioning (embedding? ICL? both?), language tags and how Cantonese is labelled.
2. **Pick the family recipe** in `recipes/`. If the model fits no family, write a new recipe first.
3. **Write the adapter.** Map the canonical manifest (`data/schemas/manifest.schema.json`) to the
   model's training format. **Do not change the corpus or the manifest to suit a model.** If the
   adapter needs a field the manifest lacks, add the field to the schema for every model (ADR + schema version bump).
4. **Baseline.** Run `E####_<slug>_baseline` on the current test set before any training.
5. **Reproduce the reference recipe first, unchanged** (same data mix, same epochs, matched LoRA
   targets as closely as the architecture allows). Only then tune. This separates "the method
   transfers" from "we tuned a lot".
6. **Record what did not transfer.** Note every hyperparameter or step you had to change, and why, in the
   base-model card under *Porting notes*. These notes are the report's portability section.
7. **Update `evals/leaderboard.md`** so the new model sits next to the old ones.

## Things that commonly break when porting

- Tokenizer frame rate changes the minimum-duration filter (the 3.0 s / 36 frames at 12 Hz rule).
  Re-derive it; do not copy it.
- Different sample rates (16 / 22.05 / 24 / 44.1 kHz). Resample from the corpus master, never from another derived copy.
- The language tag for Cantonese varies (`yue`, `zh-HK`, `Cantonese`, none). Record what was used.
- Exporting may drop the speaker encoder or code predictor by default. Check that cloning still works after export.
