# CTTS: Hong Kong Cantonese Text-to-Speech, as a reproducible method

CTTS is a research project to make text-to-speech models speak **authentic Hong Kong Cantonese**:
the HK accent rather than the Pearl River Delta accent, verbatim spoken 口語 rather than written
書面語, natural conversational prosody, and smooth Cantonese–English code-switching.

The deliverable is **the method, not one checkpoint.** Base models change every few months. This
repo records what data we used, how we cleaned it, how we trained, how we measured, and what
happened, including what failed. With that record we can:

1. re-run the same recipe on a newer base model (Qwen3-TTS today; CosyVoice, Fish Speech, an Omni model tomorrow) and expect similar gains;
2. compare base models fairly on one frozen evaluation;
3. publish the work later as a research-paper-style report or site, built from the records kept here.

## Architecture in one picture

```text
Layer 1  Golden HK corpus (model-agnostic)   data/       ← the moat; outlives every model
Layer 2  Per-model adaptation recipes        recipes/ base-models/ experiments/
Layer 3  Voice / emotion control API + UI    (later; see docs/roadmap.md)
```

The full rationale is in [`docs/initial/HK_CANTONESE_SPEECH_BLUEPRINT.md`](docs/initial/HK_CANTONESE_SPEECH_BLUEPRINT.md).

## Repository map

| Path | What lives there |
|---|---|
| [`docs/initial/`](docs/initial/) | Source documents (blueprint, agent brief). Frozen; never edited. |
| [`docs/roadmap.md`](docs/roadmap.md) | Phases and current status. **Start here to see progress.** |
| [`docs/methodology/`](docs/methodology/) | How we work: logging standard, evaluation protocol, porting to a new base model. |
| [`docs/decisions/`](docs/decisions/) | Architecture/decision records (ADRs): why we chose X over Y. |
| [`data/`](data/) | Data cards per source, the canonical manifest schema, dataset mixes, pipeline write-ups. **No audio.** |
| [`base-models/`](base-models/) | One card per base model: tokenizer, quirks, adapter notes, status. |
| [`recipes/`](recipes/) | Model-family training recipes (codec-AR TTS, S2S/Omni), independent of any one model. |
| [`experiments/`](experiments/) | One folder per training/eval run: config, environment, logs, metrics, samples, conclusion. |
| [`evals/`](evals/) | Frozen test sets and the cross-model leaderboard. |
| [`journal/`](journal/) | Dated lab notebook: observations, dead ends, surprises. |
| [`report/`](report/) | Draft of the research report / site, assembled from everything above. |
| [`scripts/`](scripts/) | Small repo helpers (e.g. scaffolding a new experiment). |
| `src/` | Implementation code (trainer, data adapters, eval harness). Not created yet; see [`CLAUDE.md`](CLAUDE.md). |

## What is not in git

Audio, codec tokens, model weights, and full training logs are large and in places not ours to
redistribute (the HK YouTube audio especially). They live outside the repo. Experiment folders
hold **pointers** to them (location + checksum) and small derived files (metrics, loss-curve CSVs,
a handful of listening samples). See [`data/README.md`](data/README.md) and
[`docs/methodology/logging-standard.md`](docs/methodology/logging-standard.md).

## Starting a new experiment

```bash
scripts/new-experiment.sh qwen3tts12hz lang-adapt     # creates experiments/E0001_qwen3tts12hz_lang-adapt/
```

Then fill in the card while you work, not afterwards. The rules are in
[`experiments/README.md`](experiments/README.md).

## Status

Project setup only. No data has been processed and no model trained in this repo yet. Prior
results (the HK ASR models) are summarised in the blueprint and listed as prior work in
[`docs/roadmap.md`](docs/roadmap.md).
