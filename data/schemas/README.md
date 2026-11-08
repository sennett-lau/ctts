# Schemas

- [`manifest.schema.json`](manifest.schema.json) (v0.1.0): one row per clip, JSONL. This is the **only**
  contract between the corpus and model adapters (ADR 0001).

Example row (from the blueprint, with the provenance fields added):

```json
{"schema_version":"0.1.0","id":"mm.millmilk_-3fikODBMs4_1-8","audio_24k_wav":"wav24k/mm.millmilk/-3fikODBMs4_1-8.wav","duration_s":15.92,"text_verbatim_hk":"噉既然 office 有免費咖啡，雖然冇咁好飲，但係難飲嘅話咪仲提神，at least 我噉樣同自己講。","jyutping":"gam2 gei3 jin4 office jau5 min5 fai3 gaa3 fe1 ...","speaker_id":"yt-mm.millmilk-chucky","accent":"zh-HK-native","style_tag":"conversational_natural","snr_db":28.4,"source":"hk-youtube-conversational","split":"train","language_mix":"yue+en","labeling":{"method":"tri_label","bucket":"sync","winner":"G"}}
```

Rules:
- Paths are relative to the corpus root, so the corpus can move between machines.
- Adapters may read extra fields (`additionalProperties` is allowed), but must not require any field
  that the schema does not define. Add it to the schema first.
- The implementation agent should add a validator (`src/ctts/data/`) that every build runs.
