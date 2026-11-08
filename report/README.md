# Report

Draft of the research-paper-style write-up / site. It is **assembled from** the rest of the repo, and
introduces no new facts:

| Report section | Pulls from |
|---|---|
| Data | `data/sources/`, build experiments, `data/pipelines/` |
| Method | `recipes/`, `docs/decisions/` |
| Experiments and results | `experiments/*/README.md`, `evals/leaderboard.md`, `logs/*.csv` for figures |
| Portability | `base-models/*/` → *Porting notes* |
| Lessons and failures | negative results in experiments, `journal/` |

- [`paper.md`](paper.md): the draft, one section per heading. Keep it in plain Markdown so any site generator can use it later (roadmap, *Open questions*).
- `figures/`: generated figures (PNG/SVG) plus the script or notebook cell that made each one, so every figure can be regenerated from committed CSVs.

Rules: every number cites an experiment ID. Every claim from the blueprint that we did not reproduce
says so.
