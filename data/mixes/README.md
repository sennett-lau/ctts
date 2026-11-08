# Data mixes

A mix is a YAML file naming exactly which sources, filters, caps and weights make up one training
set. Experiments refer to a mix by file name and copy it into their `config/`. Once an experiment
has used a mix, **never edit that mix.** Create `<name>-v2.yaml` instead.

- [`_TEMPLATE.yaml`](_TEMPLATE.yaml): all fields, commented
- [`tts-lang-phase1-v0.yaml`](tts-lang-phase1-v0.yaml): blueprint's phase-1 language/accent mix (proposed, not yet built)
