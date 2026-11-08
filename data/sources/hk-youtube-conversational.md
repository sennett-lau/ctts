---
slug: hk-youtube-conversational
status: included
role: primary conversational prosody, slang, sentence-final particles, Cantonese–English code-switching
hours_raw: 700            # "700+ hours raw available" (blueprint)
hours_used: 96.3          # cleaned set per agent brief; not yet verified in this repo
clips_used: 13023         # per agent brief; not yet verified in this repo
speakers: null
licence: third-party YouTube content (creator copyright)
redistributable: no
last_updated: 2026-11-08
---

# HK YouTube & live streams (conversational)

## Origin
`OrcinusOrca/YouTube-Cantonese` (HK channels only), plus HK creator highlights. Channels named in the
blueprint/brief: `mm.millmilk` (Mill MILK), `pricehongkongofficial` (Price.com.hk), `unwire`, `ahju`,
`bboblackboxoffice` (BBO), `mingjai14`, `thedoshow0909` (DoShow), JFFT `床哥心事台`.
TODO (P1): pin dataset revision; list the exact channel set used in the 96.3 h build.

## Why it is HK Cantonese
The channels were chosen as verified HK creators. Mandarin and Japanese guests are removed by the colloquial density score
and kana detection during arbitration.

## Transcript type
Creator subtitles are **written Chinese**. Targets come from tri-label arbitration
(`data/pipelines/tri-label-arbitration.md`), never from subtitles directly.

## Filters applied
Segments 3–25 s. Arbitration reject rules (max skeleton sim < 0.60, kana, negative colloquial score for G).
Blueprint figure: 95.7% retained on 80 h / 10,342 segments (not reproduced here).

## Stats
TODO (P1): build experiment with per-channel hours, speaker counts, sync/sub/reject buckets.

## Licence and use
Training use for research only. **Do not publish audio, manifests with transcripts, or samples cloned
from these speakers' voices.** Publish aggregate statistics only.

## Location
TODO (P1): locate the existing cleaned corpus (13,023 clips) and record host:path + manifest sha256.

## Known issues
One speaker per channel can dominate. Cap per speaker in mixes.
