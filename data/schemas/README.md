# Schemas

- [`manifest.schema.json`](manifest.schema.json) (v0.1.0): one row per clip, JSONL. This is the **only**
  contract between the corpus and model adapters (ADR 0001).

Example row (made up for illustration; real rows stay off the public repo):

```json
{"schema_version":"0.1.0","id":"ch06_vid0001_0007","audio_24k_wav":"wav24k/ch06/vid0001_0007.wav","duration_s":6.84,"text_verbatim_hk":"呢部手機個 battery 其實頂得幾耐，不過叉電就慢咗少少囉。","jyutping":"ni1 bou6 sau2 gei1 go3 battery kei4 sat6 ding2 dak1 gei2 noi6 ...","speaker_id":"yt-ch06-spk01","accent":"zh-HK-native","style_tag":"conversational_natural","snr_db":27.1,"source":"hk-youtube-conversational","split":"train","language_mix":"yue+en","labeling":{"method":"tri_label","bucket":"sync","winner":"G"}}
```

Rules:
- Paths are relative to the corpus root, so the corpus can move between machines.
- Adapters may read extra fields (`additionalProperties` is allowed), but must not require any field
  that the schema does not define. Add it to the schema first.
- The implementation agent should add a validator (`src/ctts/data/`) that every build runs.
