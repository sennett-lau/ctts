---
slug: cv-yue
status: EXCLUDED
role: none (TTS / accent phases)
hours_raw: null
hours_used: 0
clips_used: 0
speakers: null
licence: CC0-1.0 (Mozilla Common Voice)
redistributable: yes
last_updated: 2026-11-08
---

# Common Voice `yue`: EXCLUDED from TTS training

## Why excluded
Per the blueprint, fewer than 4% of speakers are confirmed Hong Kong. The rest are from Guangzhou, Foshan, the wider PRD, or overseas. A previous
third-party fine-tune (`jmtl`) trained on it acquired a **PRD accent (珠三角鄉音)**.

## Allowed uses
- ASR evaluation (it was an ASR test set in prior work: "CV Cantonese" 3.86% CER).
- TTS only if filtered by HK accent metadata. That needs an ADR and an ablation experiment showing no accent drift.

## Possible ablation (for the report)
Phase 1 with vs without CV `yue`, scored on the HK-accent A/B test. This would turn the blueprint's claim into a measured result.
