# Authentic Hong Kong Cantonese TTS: a reproducible, model-agnostic adaptation method

> Draft skeleton. Each section lists what it needs. Fill it only from records in this repo, and cite experiment IDs.

## Abstract
_Needs: headline result from the leaderboard, plus the portability result (P5)._

## 1. Introduction
The three failure modes of "Cantonese" TTS in Hong Kong use: PRD accent, written-register targets,
read-speech stiffness. Why we treat the method, not the checkpoint, as the contribution.

## 2. Related work
Open Cantonese corpora (Common Voice zh-HK / yue, MDCC, MCE, ZoengJyutGaai), codec-AR TTS models,
prior HK ASR work (ours, cited as prior).

## 3. Data: the Golden HK corpus
_Needs: per-source table (data cards), filter funnel figure (build experiments), tri-label bucket stats and audit accuracy, exclusion rationale (CV yue)._

## 4. Method
_Needs: recipe version, design decisions (ADRs), adapter boundary._

## 5. Evaluation protocol
_Needs: test-set v1 description, metrics, judge-bias mitigation, listening-test design._

## 6. Experiments and results
_Needs: baselines, phase-1 adaptation, ablations (CV yue, MCE, LoRA rank, speaker encoder)._

## 7. Portability across base models
_Needs: P5 results and porting notes._

## 8. Limitations and ethics
Voice cloning consent, third-party audio, accent bias of the judges, small listening panels.

## 9. Reproducibility statement
Pointers to configs, environment captures, artefact checksums.
