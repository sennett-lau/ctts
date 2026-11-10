# Pipelines

Specs for turning raw sources into canonical manifest rows and model inputs. Each spec says
what must be logged when it runs.

- [`tri-label-arbitration.md`](tri-label-arbitration.md): verbatim HK labels from subtitled video (G/Q/S)
- [`tts-audio-prep.md`](tts-audio-prep.md): resample, filter, trim, tokenise for codec-AR TTS
- [`youtube-ingest.md`](youtube-ingest.md): the whole YouTube workflow (check → download → segment → label →
  manifest → TTS gate), clean-up problems and directions, and per-channel status
- [`scripts/`](scripts/README.md): the scripts that actually ran (snapshots)
