# CLAUDE.md: instructions for agents working in this repo

Read this file in full before you change anything. `AGENTS.md` points here, so every agent gets the same rules.

## What this project is

CTTS builds **Hong Kong Cantonese TTS as a reproducible method**. A fine-tuned checkpoint is a
by-product. The real output is the record: which data, which cleaning, which recipe, which numbers,
and which failures. Someone must be able to switch to a new base model and repeat the work from
this repo alone. Later the record becomes a research-paper-style report (`report/`).

The background is in `docs/initial/`: the blueprint and the agent task brief. They are frozen
source documents. Never edit them. When reality differs from them, write a decision record
(`docs/decisions/`) and update the living docs.

## Scope

| In scope now | Later | Out of scope here |
|---|---|---|
| Layer 1 corpus records (data cards, manifest schema, mixes, pipeline write-ups) | Layer 3 voice/emotion API + UI (`voice-studio`) | The Project Sunset `VoiceProvider` adapter: that code belongs in the Project Sunset repo. Here we only document the contract it relies on. |
| Layer 2 TTS adaptation (codec-AR family first: Qwen3-TTS-12Hz-1.7B-Base) | S2S / Omni adaptation (Qwen3-Omni, GLM-4-Voice, Moshi) | |
| Evaluation harness and the frozen test set | | |
| HK ASR as a **tool** (labelling, round-trip CER), not as the research target | | |

`docs/roadmap.md` holds the current phase. Read it first and update it when a phase changes.

## Non-negotiable data rules (from the blueprint; breaking any of them is a bug)

1. **No unfiltered Common Voice `yue` in TTS training.** Most of its speakers are not from Hong Kong, and it causes a PRD accent. Use the `zh-HK` split.
2. **Never use written-Chinese subtitles as speech targets**, and **never pass them as context to an ASR** during labelling. New conversational data goes through tri-label arbitration (`data/pipelines/tri-label-arbitration.md`).
3. **Keep the speaker encoder.** Never drop `speaker_encoder.*` (or the equivalent in another model) at export. Zero-shot cloning must survive fine-tuning.
4. **Cap any single speaker or narrator** (e.g. ZoengJyutGaai at about 40 h per epoch) so it does not dominate the speaker prior.
5. **The test set is frozen.** Never train on `evals/test-sets/`, and never edit a released test-set version. Make a new version instead.

## Where things go

| You are producing... | Put it in | In git? |
|---|---|---|
| Audio, codec tokens, checkpoints, TensorBoard/W&B dirs, full raw logs | outside the repo (or the git-ignored `corpus/`, `artifacts/`, `runs/`) | **No.** Record location + sha256 in the experiment card. |
| A new data source | `data/sources/<slug>.md` from `_TEMPLATE.md` | yes |
| A corpus build (filtered, labelled manifest) | manifest outside git; stats + build recipe in `data/` | stats/recipe only |
| A mix of sources for training | `data/mixes/<name>.yaml` | yes |
| A new base model | `base-models/<slug>.md` from `_TEMPLATE.md` | yes |
| Any training or eval run, including failed and aborted ones | `experiments/E####_<base>_<slug>/` via `scripts/new-experiment.sh` | yes (small files) |
| Eval numbers worth comparing | the experiment's `metrics/` **and** a row in `evals/leaderboard.md` | yes |
| A decision with trade-offs (e.g. "drop MDCC from phase 1") | `docs/decisions/NNNN-<slug>.md` | yes |
| An observation, hunch or dead end without a run of its own | `journal/YYYY-MM-DD-<slug>.md` | yes |
| Implementation code | `src/` (see below) | yes |

Size limit for committed files: keep each under about 1 MB and each experiment folder under about 10 MB.
Listening samples are short `.ogg`/`.mp3` clips only. `.wav`, `.safetensors`, `.pt`, `.spk`, `.icl` and
similar files are git-ignored on purpose. Do not force-add them.

## Experiment discipline (what makes this a research project)

- **Create the experiment folder before the run starts**, and fill in the hypothesis and setup first.
  A run without a card did not happen as far as the report is concerned.
- **Copy configs** into `config/`. Do not link to a file that will change later.
- **Capture the environment** into `env/`: git commit (and dirty flag), exact command line, `pip freeze`,
  `nvidia-smi`, host name, CUDA/driver, seeds. `docs/methodology/logging-standard.md` has the full checklist.
- **Log negative results with the same care as positive ones.** "LoRA r=8 never lost the PRD accent" is a finding.
- **Change one thing at a time** against a named parent experiment (`parent:` in the card), so
  the report can attribute every gain.
- **Use the evaluation protocol unchanged** (`docs/methodology/evaluation-protocol.md`). If you
  need a new metric, add it to the protocol, then re-score the baselines.
- **Never invent numbers.** If a figure comes from the blueprint and was not reproduced here, label it
  "reported in blueprint, not reproduced".

## Code layout (to be created by the implementation agent)

No implementation code exists yet. When you add it, use this layout unless an ADR changes it:

```text
src/ctts/
  data/       # manifest I/O + validation against data/schemas/, filters, mix sampler, per-model adapters
  label/      # tri-label arbitration (G/Q/S), colloquial density score, skeleton similarity
  train/      # per-family trainers; base-model specifics behind an adapter interface
  eval/       # round-trip CER, speaker similarity, MOS predictors, listening-test export
studio/       # Layer 3 voice-studio API + UI (later)
tests/
```

Principles:
- **The model-agnostic boundary is the manifest** (`data/schemas/manifest.schema.json`). Everything
  model-specific (tokenizer, prompt format, LoRA targets) lives in a per-base-model adapter. Moving
  to a new base model should mean writing a new adapter, not editing the data pipeline.
- Every training/eval entry point takes a config file and writes its outputs into a run directory
  in the layout `experiments/_TEMPLATE/` expects. That way logging is automatic, not a chore.
- Python. Pin dependencies. Record the Python version in `env/`.

## Compute

Each run records its host. The likely GPU box is `sennett-pc` (RTX 3080 Ti, inside WSL). The
global `~/.claude/CLAUDE.md` describes SSH access and its quoting and backgrounding traps. Large
artefacts stay on the machine that produced them, or go to an external store (e.g. a private
Hugging Face repo). The experiment card records the pointer.

## Git and GitHub

- Remote: `https://github.com/sennett-lau/ctts` (**public**). Use the GitHub account `sennett-lau`.
- The repo is public. Never commit credentials, API keys, raw audio of real people, or full
  transcripts of third-party content whose licence does not allow redistribution (check the data card).
- **Commit small and often.** Each commit holds one logical change with a short, conventional
  message (`docs:`, `data:`, `exp:`, `eval:`, `feat:`, `fix:`, `chore:`). Prefer several small
  commits over one large one.
- An experiment's record may be committed in steps (card, then config, then results). Each step is its own commit.

## Before you finish a work session

1. The experiment cards you touched have a status and, if the run finished, results and a conclusion.
2. `evals/leaderboard.md` has any new comparable numbers.
3. `docs/roadmap.md` shows the current phase.
4. A journal entry covers anything surprising that is not recorded elsewhere.
