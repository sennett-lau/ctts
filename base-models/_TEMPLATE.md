---
slug: <short-slug used in experiment ids, e.g. qwen3tts12hz>
hf_id: <org/name>
revision: <commit hash>
family: codec-ar-tts | s2s-omni | asr | other
licence: <licence>
status: candidate | baseline-done | adapted | retired
recipe: recipes/<family>.md
last_updated: YYYY-MM-DD
---

# <Model name>

## Architecture
Sizes, sub-modules (text LM / talker / code predictor / speaker encoder / vocoder).

## Audio tokenizer
Name + revision, sample rate, frame rate, codebooks. Minimum-duration rule derived from it.

## Text and prompt format
How text, language tag (what does it call Cantonese?), speaker and instruction are fed in.

## Speaker and style conditioning
Embedding? ICL prompt? Instruction? Which modules must be kept at export so cloning still works?

## Adapter
Path to the manifest → model-format adapter in `src/` and anything it has to work around.

## Experiments
| ID | What | Result |
|---|---|---|

## Porting notes
Everything that did not transfer unchanged from the reference recipe, and why.
