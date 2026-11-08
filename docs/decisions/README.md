# Decision records

One short file per decision that has trade-offs: `NNNN-<slug>.md`, numbered in order and never
renumbered. A superseded record stays. Set its status to `superseded by NNNN`. The report's
"design choices" section draws on these files.

Copy [`_TEMPLATE.md`](_TEMPLATE.md) to start one.

| # | Decision | Status |
|---|---|---|
| [0001](0001-three-layer-decoupled-architecture.md) | Three-layer decoupled architecture; the manifest is the model-agnostic boundary | accepted |
| [0002](0002-artefacts-outside-git.md) | Audio, weights and raw logs live outside git; the repo keeps pointers | accepted |
| [0003](0003-tts-first-scope.md) | TTS first; ASR is a tool; S2S and Layer 3 later | accepted |
