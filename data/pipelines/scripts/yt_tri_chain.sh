#!/usr/bin/env bash
# 2026-11-07 decision A+B: wait for e2a-dl-yt-more -> extract ~80 h -> Gemini 3.8 (cap $12) and Qwen-FT in parallel -> merge.
# usage: systemd-run --user --unit=e2a-tri ... bash data_yue/yt_tri_chain.sh
set -u
cd "$(dirname "$0")/.."
D=data_yue/yt_more
L=$D/chain.log
while systemctl --user is-active -q e2a-dl-yt-more; do sleep 30; done
echo "=== $(date +%T) downloads done" >> $L
.venv/bin/python data_yue/yt_tri_label.py extract >> $L 2>&1
echo "=== $(date +%T) extract done" >> $L
.venv/bin/python data_yue/yt_tri_label.py gemini --budget-usd 12 >> $D/gemini.log 2>&1 &
G=$!
MIOPEN_FIND_MODE=FAST .venv-qft/bin/python data_yue/yt_tri_label.py qwen --bs 16 >> $D/qwen.log 2>&1 &
Q=$!
wait $G; echo "=== $(date +%T) gemini exit $?" >> $L
wait $Q; echo "=== $(date +%T) qwen exit $?" >> $L
.venv/bin/python data_yue/yt_tri_label.py merge > $D/merge.log 2>&1
echo "=== $(date +%T) TRI DONE" >> $L
