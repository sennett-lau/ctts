# Logging standard: what every run must record

The report can only state what was recorded. This is the minimum for any run: training, encoding,
labelling or evaluation. The paths are relative to the experiment folder (`experiments/E####_.../`).
For a failed or aborted run, record everything up to the point of failure, plus the failure itself.

## 1. Before the run (card `README.md` → *Hypothesis* and *Setup*)

- [ ] Hypothesis: one sentence, and what result would refute it
- [ ] `parent:` experiment it differs from, and **the one thing changed**
- [ ] Base model: HF id **and revision/commit hash** (`base-models/<slug>.md`)
- [ ] Data mix: `data/mixes/<name>.yaml` + manifest checksum(s) + resulting hours / clips / speakers
- [ ] Planned evaluation: test-set version(s) and metrics (from `docs/methodology/evaluation-protocol.md`)

## 2. Config (`config/`)

- [ ] Exact training config(s) **copied**, not linked
- [ ] The resolved config after CLI overrides (dump it from the program if possible)
- [ ] Data mix file copied in as it was at run time

## 3. Environment (`env/`)

| File | Contents |
|---|---|
| `command.txt` | Exact command line(s), with working directory |
| `git.txt` | `git rev-parse HEAD` for this repo **and** any trainer fork; `git status --porcelain` (dirty flag) |
| `pip-freeze.txt` | `pip freeze` (or `uv pip freeze`), plus `python --version` |
| `hardware.txt` | Host name, `nvidia-smi`, CUDA / driver / torch versions, GPU count, RAM |
| `seeds.txt` | Every seed: python, numpy, torch, data shuffling |

## 4. During and after training (`logs/`)

- [ ] `train_scalars.csv`: step, epoch, lr, every loss component, grad-norm, tokens/s, GPU memory.
      Export TensorBoard/W&B scalars to CSV. The CSV is the source of truth for report figures.
- [ ] `eval_scalars.csv`: validation metrics per checkpoint
- [ ] `stdout_tail.log`: last ~500 lines of the console log (the full log stays outside git; give its pointer)
- [ ] `events.md`: timestamped notes on anything notable (loss spike at step N, OOM, restart from a checkpoint, early stop and why)
- [ ] Wall-clock time and GPU-hours

## 5. Results (`metrics/`, `samples/`)

- [ ] `metrics/<testset-version>.json`: one file per test set, in the format in `evaluation-protocol.md`
- [ ] Per-utterance results (`metrics/<testset-version>.per_utt.csv`) if small, to support error analysis
- [ ] `samples/`: **the same fixed prompts in every experiment** (listed in `evals/test-sets/`), as short `.ogg`
      files named `<prompt-id>.ogg`. Same prompts every time, so you can compare across runs by ear.
- [ ] A row in `evals/leaderboard.md`

## 6. Artefact pointers (card → *Artefacts*)

For each large output (checkpoint, LoRA adapter, codec cache, full log):

```text
name | location (host:path or hf://repo@rev) | size | sha256 | keep? (yes / delete after N)
```

## 7. Conclusion (card → *Conclusion*)

- [ ] Was the hypothesis supported? Answer with numbers.
- [ ] What you heard in listening checks (accent, particles, code-switching, rhythm, artefacts)
- [ ] Next step, and the `parent:` for the follow-up experiment

## Data-pipeline runs

Corpus builds and labelling runs follow the same rules. Also record:

- input manifest(s) + checksum, output manifest checksum
- counts at every filter stage (in → kept → dropped, **by reason**). This becomes a funnel figure in the report.
- for tri-label arbitration: `sync` / `sub` / `reject` bucket sizes and the thresholds used
- the external model/API versions (e.g. which Gemini model and date, which Qwen3-ASR checkpoint)
