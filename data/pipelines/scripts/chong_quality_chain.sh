#!/usr/bin/env bash
# Wait for subtitle OCR (e2a-chong-ocr) and the Qwen pass over 床哥 chunks, then hints -> Gemini pass 2 -> score.
set -uo pipefail
cd "$(dirname "$0")/.."
log() { echo "=== $(date +%T) $*"; }
log "waiting for OCR + qwen"
until grep -q "OCR DONE" data_yue/chong_ocr.log 2>/dev/null && grep -q "QWEN DONE" data_yue/qwen_label.log 2>/dev/null; do sleep 60; done
log "hints"
.venv/bin/python data_yue/chong_relabel.py hints
log "gemini pass 2"
.venv/bin/python data_yue/chong_relabel.py gemini --budget-usd 5 --workers 8
log "score"
.venv/bin/python data_yue/chong_relabel.py score
log "CHAIN DONE"
