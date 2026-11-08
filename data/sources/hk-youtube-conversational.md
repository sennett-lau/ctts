---
slug: hk-youtube-conversational
status: included
role: primary conversational prosody, slang, sentence-final particles, Cantonese–English code-switching
hours_raw: 700            # 45 tars (~41.0 GB) across 14 HK channels in OrcinusOrca/YouTube-Cantonese + JFFT highlights
hours_used: 96.28         # verified train split (13,023 clips across 1,181 videos) + 0.88h dev + 1.82h test
clips_used: 13023         # verified train clips (plus 136 dev, 279 test = 13,438 total split clips)
speakers: 8               # 8 channel-level speaker groups (per-clip diarization needed before TTS Phase 1)
licence: third-party YouTube content (creator copyright)
redistributable: no
last_updated: 2026-11-08
---

# HK YouTube & live streams (conversational)

## Origin
`OrcinusOrca/YouTube-Cantonese` (HK channels only), plus JFFT `床哥心事台` highlight channels.
The 8 verified sources in the 96.28 h train split:
- `ahju` (19.07 h train / 0.18 h dev / 0.52 h test) — solo speaker, high SNR, financial & lifestyle
- `bboblackboxoffice` (16.85 h train / 0.21 h dev / 0.49 h test) — multi-speaker travel/lifestyle
- `chong` / JFFT highlights (12.41 h train / 0.49 h dev / 0.81 h test) — call-in live stream, heavy slang
- `mm.millmilk` (11.02 h train) — HK street interviews & feature stories (multi-speaker)
- `mingjai14` (10.60 h train) — solo narrator, storytelling & HK culture
- `unwire` (9.40 h train) — tech & gadget reviews, heavy Cantonese–English code-switching
- `thedoshow0909` (9.38 h train) — celebrity interviews (multi-speaker; Putonghua guests filtered out)
- `pricehongkongofficial` (7.55 h train) — consumer tech reviews, heavy English model names

## Why it is HK Cantonese
The channels were chosen as verified HK creators. Mandarin and Japanese guests are removed by the colloquial density score
and kana detection during arbitration.

## Transcript type
Creator subtitles are **written Chinese**. Targets come from tri-label arbitration
(`data/pipelines/tri-label-arbitration.md`), never from subtitles directly. All train rows are strictly digit-free (numbers written out as spoken Cantonese words).

## Filters applied
Segments 3–25 s. Arbitration reject rules (max skeleton sim < 0.60, kana, negative colloquial score for G).
On the 9,944-segment `yt_more` tri-label batch (76.92 h):
- **Retained:** 9,521 segments (**73.69 h**, **95.7%**)
  - `sync` ($\text{CER}(G, Q) \le 15\%$): 6,969 segments (**54.05 h**, **70.1%**)
  - `sub` (subtitle-arbitrated): 2,552 segments (**19.64 h**, **25.7%**)
  - Winner breakdown: `G` = 6,522 (68.5%), `Q` = 2,984 (31.3%), `S` = 15 (0.2%)
- **Rejected:** 423 segments (**3.23 h**, **4.3%**) — `no_agreement`: 319, `mandarin?`: 44, `japanese`: 36, `gemini_bad`: 24.

## Stats (Verified on `gpu-workstation-01`)
- **Total split clips:** 13,438 (1,206 distinct videos; deterministic video-level split so no video spans splits)
  - `train`: 13,023 clips / **96.28 h** / 1,181 videos (`sha256: 94ca6f5dc17fb7316316595faef0c4795fb5c56f5e5fcf0aba535112a4d01174`)
  - `dev`: 136 clips / **0.88 h** / 7 videos (`sha256: 690e9c928fa53162221196bd708b85002cbc2041080c707bc0f21d473d9e013e`)
  - `test`: 279 clips / **1.82 h** / 18 videos (`sha256: 22bdc124a894b08a609bd674af20fdc8e8c1335846652c4f06d0d132cc9b9698`)
- **Tri-label merged output (`yt_more/merged.jsonl`):** 9,944 rows (`sha256: b3a864f364afc10aee3229ae4ae820f7c7b800cae6242c3bcafe225e940860f3`)

## Licence and use
Training use for research only. **Do not publish audio, manifests with transcripts, or samples cloned
from these speakers' voices.** Publish aggregate statistics only.

## Location
Stored on the primary GPU workstation (`embed2asr/data_yue/`):
- Train/dev/test manifests: `data_yue/manifests/yt_{train,dev,test}.jsonl`
- Tri-label audit log: `data_yue/yt_more/merged.jsonl` and `data_yue/yt_more/merge_summary.json`
- Audio files: `data_yue/yt_pilot/audio/*.mp3`, `data_yue/yt_more/audio/*.mp3`, `data_yue/chong/chunks/*.mp3`

## Known issues
1. **Multi-speaker clips in interview channels (`mm.millmilk`, `thedoshow0909`, `bboblackboxoffice`, `chong`):** fine for ASR, but **must be filtered for single-speaker consistency (`single_speaker_cos_sim >= 0.75`)** before TTS training so the Talker does not switch voices mid-utterance.
2. One speaker per solo channel (`ahju`, `mingjai14`) can dominate; cap per speaker in mixes.
