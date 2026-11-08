# Data (Layer 1): records only, no audio

This folder describes the Golden HK corpus. It does not contain it. Audio, manifests that carry
third-party transcripts, and derived caches live outside git (ADR 0002).

| Path | Contents |
|---|---|
| `sources/` | One **data card** per source: origin, licence, HK-accent rationale, filters, stats, location. |
| `schemas/` | `manifest.schema.json`: the canonical, model-agnostic clip format (ADR 0001). |
| `mixes/` | Training mixes: which sources, filters, caps and weights make one training set. |
| `pipelines/` | How a source becomes manifest rows (tri-label arbitration, filtering, normalisation). |

## Rules

1. **Every source used in any run has a data card.** No card, no training.
2. **Inclusion is decided per source, with a reason.** Excluded sources get a card too (marked `EXCLUDED`),
   so the report can explain what was left out and why.
3. **The corpus master is the highest-quality copy.** Every resampled or tokenised copy is a cache
   derived from the master, and its build is recorded.
4. **Record every build.** Each corpus or manifest build records: input checksums, filter funnel (in → kept, dropped by reason),
   output checksum, hours/clips/speakers per source and split. Builds are run as experiments
   (`experiments/E####_data_<slug>/`), so they follow the same logging standard.
5. **Splits are speaker-disjoint** where speaker IDs exist, and no evaluation clip ever enters training.

## Where the data physically lives

Not decided yet (roadmap, *Open questions*). Until then, each data card's *Location* section records host + path
+ checksum.
