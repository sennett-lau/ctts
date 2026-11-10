#!/usr/bin/env bash
# 2026-11-10 owner approved ("CAN 用返之前個方法 ASR + gemini + 字幕"): the 50 public The Do Show videos not in
# OrcinusOrca -> Route B download + segment -> Gemini (cap $6) and Qwen-FT Stage 2 in parallel -> merge.
# usage: systemd-run --user --unit=e2a-tri2 ... bash data_yue/yt_more2_chain.sh
set -u
cd "$(dirname "$0")/.."
D=data_yue/yt_more2
mkdir -p $D
L=$D/chain.log
export YT_TRI_OUT=$PWD/$D YT_TRI_QFT=$PWD/qwen_ft/colab_out2/final
echo "=== $(date +%T) download + segment" >> $L
.venv/bin/python data_yue/yt_dl_segment.py --channel thedoshow0909 --ids data_yue/yt_more2_ids.tsv --out yt_more2 >> $L 2>&1
echo "=== $(date +%T) segment exit $?" >> $L
.venv/bin/python data_yue/yt_tri_label.py gemini --budget-usd 6 >> $D/gemini.log 2>&1 &
G=$!
MIOPEN_FIND_MODE=FAST .venv-qft/bin/python data_yue/yt_tri_label.py qwen --bs 16 >> $D/qwen.log 2>&1 &
Q=$!
wait $G; echo "=== $(date +%T) gemini exit $?" >> $L
wait $Q; echo "=== $(date +%T) qwen exit $?" >> $L
.venv/bin/python data_yue/yt_tri_label.py merge > $D/merge.log 2>&1
echo "=== $(date +%T) TRI2 DONE" >> $L
