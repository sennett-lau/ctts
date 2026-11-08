---
slug: <source-slug>
status: candidate | included | EXCLUDED | partial
role: <what this source teaches the model, e.g. conversational prosody / code-switching / studio clarity>
hours_raw: null
hours_used: null
clips_used: null
speakers: null
licence: <licence name + URL>
redistributable: unknown | yes | no
last_updated: YYYY-MM-DD
---

# <Source name>

## Origin
URL / HF id + revision. Who recorded it, and how (read vs spontaneous, studio vs phone).

## Why it is (or is not) HK Cantonese
Evidence for the accent and register: speaker metadata, channel provenance, manual spot checks (how many clips, and what you heard).

## Transcript type
Verbatim 口語 / written 書面語 / mixed. If not verbatim, how it is converted (link `data/pipelines/`).

## Filters applied
Duration bounds, SNR, language-ID, colloquial score, speaker caps, manual removals. Include thresholds.

## Stats
Hours / clips / speakers per split; duration histogram; colloquial score distribution. Link the build experiment.

## Licence and use
What we may do: train, publish samples, publish manifests. Cite the source as follows.

## Location
`host:path` or `hf://...@rev` + sha256 of the manifest.

## Known issues
