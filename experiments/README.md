# Experiments

One folder per run: training, evaluation, baseline, data build or labelling run. **Failed and aborted
runs get folders too.** These folders are the raw material for the report.

## Naming

`E####_<base-slug>_<short-slug>`, e.g. `E0001_qwen3tts12hz_baseline`, `E0002_qwen3tts12hz_lang-adapt`.
Use `data` as the base slug for corpus builds (`E0003_data_hk-youtube-v1`). IDs are sequential, never
reused and never renumbered. Create the folder with:

```bash
scripts/new-experiment.sh <base-slug> <short-slug>
```

## Layout (copied from `_TEMPLATE/`)

```text
E0002_qwen3tts12hz_lang-adapt/
  README.md     card: hypothesis, setup, results, conclusion, artefact pointers
  config/       exact configs + data mix, copied
  env/          command, git commit, pip freeze, hardware, seeds   (scripts/capture-env.sh)
  logs/         train_scalars.csv, eval_scalars.csv, stdout_tail.log, events.md
  metrics/      <test-set>.json (+ per-utterance CSV)
  samples/      <prompt-id>.ogg for the fixed listening prompts
```

What goes in each folder is set by [`docs/methodology/logging-standard.md`](../docs/methodology/logging-standard.md).

## Lifecycle (`status:` in the card)

`planned` → `running` → `done` | `failed` | `aborted`. Then `superseded` if a later run replaces it.

Commit at each stage. A card with only a hypothesis is a valid, useful commit.

## Index

| ID | Base | What | Status | Headline result |
|---|---|---|---|---|
| (none yet) | | | | |
