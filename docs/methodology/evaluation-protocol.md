# Evaluation protocol (v0, draft)

All TTS experiments are scored the same way, so that numbers compare across base models and
over time. Changing this protocol means bumping its version, noting the change below, and
re-scoring the baselines.

**Status:** draft. P2 on the roadmap turns it into code and fixes v1.

## What we are trying to measure

| Property | Why it matters here | Primary metric | Secondary / human |
|---|---|---|---|
| Intelligibility | Speech must say the text | **Round-trip CER**: synthesise, then transcribe with a fixed ASR, then CER against the input | |
| HK accent (not PRD) | The core goal | Accent classifier score (to be built or chosen) | **A/B listening test**: "which sounds like a Hong Kong speaker?" |
| Colloquial fidelity | Particles and 口語 must be spoken naturally | CER on the particle-heavy subset | Listening notes |
| Code-switching | English terms inside Cantonese sentences | English-term accuracy on the code-switch subset | Listening notes |
| Naturalness | Avoid read-speech stiffness | Automatic MOS predictor (e.g. UTMOS) | MOS listening test |
| Speaker similarity | Zero-shot cloning must survive fine-tuning | Cosine similarity of speaker embeddings (e.g. WavLM-SV / ECAPA) between reference and output | |
| Robustness | No early EOS, babbling or truncation | Rate of failed utterances (duration-ratio outliers, CER > 50%) | |
| Speed | Real-time use in downstream voice apps | RTF, time-to-first-audio | |

## Round-trip CER: avoiding judge bias

The HK ASR model (`Qwen3-ASR-1.7B` Stage 2) was trained on overlapping data. Scoring with it alone
can reward outputs that match its own habits. Therefore:

- Report round-trip CER with **two** judges: our HK ASR **and** one independent ASR. Record both versions.
- Normalise text the same way for every judge: punctuation stripped, full-width/half-width unified,
  English lowercased, numbers kept as written in the prompt. Version the normaliser.

## Test set

Defined in `evals/test-sets/`. It is versioned and frozen, and is never used for training. It has
categories so that results can be broken down:

`colloquial` · `particles` · `code_switch` · `numbers_dates` · `names_places` · `long_form` · `questions_exclamations`

Every experiment also renders the same fixed **listening prompts** into `samples/`.

## Metrics file format

`experiments/<id>/metrics/<testset-version>.json`:

```json
{
  "experiment": "E0001_qwen3tts12hz_lang-adapt",
  "checkpoint": "step-12000",
  "test_set": "tts-test-v1",
  "protocol_version": "v0",
  "judges": {"asr_hk": "<model@rev>", "asr_independent": "<model@rev>", "sv": "<model@rev>", "mos": "<model@rev>"},
  "inference": {"temperature": 0.9, "top_p": null, "seed": 1234, "voice": "<ref clip id or preset>"},
  "overall": {"cer_hk": 0.0, "cer_indep": 0.0, "spk_sim": 0.0, "utmos": 0.0, "fail_rate": 0.0, "rtf": 0.0},
  "by_category": {"code_switch": {"cer_hk": 0.0}}
}
```

## Inference & Long-Form Chunking Rules

1. **Punctuation chunking (`max_chars = 42`):** Autoregressive codec TTS models (`Qwen3-TTS-12Hz`) skip entire clauses when fed >65–70 characters in a single forward pass. For `long_form` evaluation, the harness must split paragraphs at punctuation (`，。！？；：`) into chunks of $\le 42$ characters, synthesise each chunk with identical sampling parameters, and concatenate the resulting waveforms before computing round-trip CER.
2. **Sampling discipline:** Never evaluate codec-AR TTS models with greedy decoding (`temperature = 0.0`), which triggers runaway repetition loops. Use the model's standard stochastic settings (`temperature = 0.9, top_k = 50, top_p = 1.0, repetition_penalty = 1.05`) with a fixed, recorded random seed per draw (and average over 2 draws per prompt).

## Baselines (required before any fine-tune claim)

For every base model: score the **untouched** model on the current test set first. Make that its own
experiment, `E####_<base>_baseline`. Every fine-tune is reported as a change from that baseline. Also score `jmtl/hk-cantonese-cc0-qwen3-tts` (v0.0.5) as an external community reference (`E0002_qwen3tts12hz_jmtl-v005-ref`).

## Changelog

- v0 (2026-11-08): initial draft.
