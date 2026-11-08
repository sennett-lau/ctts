---
slug: hk-youtube-conversational
status: included
role: primary conversational prosody, slang, sentence-final particles, Cantonese–English code-switching
hours_raw: 700            # 45 tars (~41.0 GB) across 14 HK channels in OrcinusOrca/YouTube-Cantonese + live-stream highlights
hours_used: 96.28         # verified train split (13,023 clips across 1,181 videos) + 0.88h dev + 1.82h test
clips_used: 13023         # verified train clips (plus 136 dev, 279 test = 13,438 total split clips)
speakers: 8               # 8 channel-level speaker groups (per-clip diarization needed before TTS Phase 1)
licence: third-party YouTube content (creator copyright)
redistributable: no
last_updated: 2026-11-08
---

# HK YouTube & live streams (conversational)

## Origin
HK channels from `OrcinusOrca/YouTube-Cantonese`, plus highlights from one HK call-in live stream.
Individual channels are referred to by alias in this public repo. Maintainers keep the alias → channel
map privately (`private/data/hk-youtube-channel-map.md`, git-ignored).

The 8 sources in the 96.28 h train split:

| Alias | Train h | Dev h | Test h | Style |
|---|---|---|---|---|
| ch01 | 19.07 | 0.18 | 0.52 | solo speaker, high SNR, finance & lifestyle |
| ch02 | 16.85 | 0.21 | 0.49 | multi-speaker travel / lifestyle |
| ch03 | 12.41 | 0.49 | 0.81 | call-in live stream, heavy slang (callers are members of the public) |
| ch04 | 11.02 | | | street interviews & feature stories, multi-speaker |
| ch05 | 10.60 | | | solo narrator, storytelling & HK culture |
| ch06 | 9.40 | | | tech & gadget reviews, heavy Cantonese–English code-switching |
| ch07 | 9.38 | | | celebrity interviews, multi-speaker (Putonghua guests filtered out) |
| ch08 | 7.55 | | | consumer tech reviews, heavy English model names |

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

## Stats (verified on the corpus host)
- **Total split clips:** 13,438 (1,206 distinct videos; deterministic video-level split so no video spans splits)
  - `train`: 13,023 clips / **96.28 h** / 1,181 videos (`sha256: 94ca6f5dc17fb7316316595faef0c4795fb5c56f5e5fcf0aba535112a4d01174`)
  - `dev`: 136 clips / **0.88 h** / 7 videos (`sha256: 690e9c928fa53162221196bd708b85002cbc2041080c707bc0f21d473d9e013e`)
  - `test`: 279 clips / **1.82 h** / 18 videos (`sha256: 22bdc124a894b08a609bd674af20fdc8e8c1335846652c4f06d0d132cc9b9698`)
- **Tri-label merged output (`yt_more/merged.jsonl`):** 9,944 rows (`sha256: b3a864f364afc10aee3229ae4ae820f7c7b800cae6242c3bcafe225e940860f3`)

## Licence and use
Training use for research only. **Do not publish audio, manifests with transcripts, or samples cloned
from these speakers' voices.** Publish aggregate statistics only.

## Location
On the corpus host (`gpu-workstation-01`, see ADR 0004), under the corpus root:
- train/dev/test manifests: `data_yue/manifests/yt_{train,dev,test}.jsonl` (sha256 above; same paths as `data/mixes/`)
- tri-label audit log: `data_yue/yt_more/merged.jsonl`, `data_yue/yt_more/merge_summary.json`
- audio: MP3 files per batch. Exact paths are in the private notes.

## Known issues
1. **Multi-speaker clips in interview and call-in channels (ch02, ch03, ch04, ch07):** fine for ASR, but **must be filtered for single-speaker consistency (`single_speaker_cos_sim >= 0.75`)** before TTS training so the Talker does not switch voices mid-utterance.
2. One speaker per solo channel (ch01, ch05) can dominate; cap per speaker in mixes.
3. **Privacy:** ch03 callers are private individuals talking about personal matters. Never publish their audio, transcripts, or any voice cloned from them, even as a demo.
