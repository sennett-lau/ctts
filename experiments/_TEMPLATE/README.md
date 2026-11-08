---
id: E####_<base>_<slug>
status: planned            # planned | running | done | failed | aborted | superseded
type: train | eval | baseline | data-build | labelling
base_model: base-models/<slug>.md
recipe: recipes/<family>.md (version)
data_mix: data/mixes/<mix>.yaml
parent: null               # experiment this one changes ONE thing from
changed: null              # that one thing
test_sets: [tts-test-v1]
host: null
started: null
finished: null
gpu_hours: null
owner: null                # human or agent that ran it
---

# <ID>: <one-line title>

## Hypothesis
What we expect, and what result would show we were wrong.

## Setup
- Base model + revision:
- Data: mix, manifest sha256, hours / clips / speakers after filtering
- Method and key hyperparameters (full config in `config/`):
- Difference from parent:
- Command: see `env/command.txt`

## Run notes
Anything notable during the run (full timeline in `logs/events.md`).

## Results
| Test set | CER (HK ASR) | CER (indep.) | Spk sim | UTMOS | Fail rate | RTF |
|---|---|---|---|---|---|---|
| | | | | | | |

Compared with parent / baseline:

Listening notes (accent, particles, code-switching, rhythm, artefacts), referring to `samples/<prompt-id>.ogg`:

## Conclusion
Supported / refuted / inconclusive, with numbers. What we learned.

## Next
Follow-up experiment(s) and what they change.

## Artefacts (outside git)
| Name | Location | Size | sha256 | Keep? |
|---|---|---|---|---|
| | | | | |
