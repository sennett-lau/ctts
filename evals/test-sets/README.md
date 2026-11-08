# Test sets

**Status:** none built yet. Building `tts-test-v1` is roadmap phase P2.

## Rules
- Versioned (`tts-test-v1`, `tts-test-v2`, ...). **A released version is never edited.**
- Never used for training. Every data build checks that no test text or speaker leaks into training.
- Every prompt has an id and a category, so results can be broken down.
- Prompts are written or picked to be publishable (no third-party transcripts).

## Planned `tts-test-v1` layout
```text
tts-test-v1/
  prompts.jsonl        {"id": "cs-001", "category": "code_switch", "text": "...", "notes": "..."}
  references.jsonl     reference voices for cloning tests: {"id": "ref-f1", "audio": "<pointer>", "transcript": "...", "licence": "..."}
  listening.txt        ids of the fixed listening prompts rendered into every experiment's samples/
  README.md            how it was built, counts per category, frozen date
```

## Categories
| Category | Tests | Example shape |
|---|---|---|
| `colloquial` | everyday 口語 | 我今日好攰，唔想出街喇 |
| `particles` | sentence-final particles, intonation | ...㗎嘛 / ...咩？ / ...囉喎 |
| `code_switch` | English terms in Cantonese grammar | 呢個 encoder 嘅 output 會入去 latent space |
| `numbers_dates` | numbers, prices, times, dates | |
| `names_places` | HK place and proper names | 旺角、銅鑼灣、將軍澳 |
| `long_form` | 30 s+ paragraphs (stability, early EOS) | |
| `questions_exclamations` | prosody of questions and exclamations | |

Reference voices for cloning tests must be voices we are allowed to use and publish (consenting speakers or CC0).
