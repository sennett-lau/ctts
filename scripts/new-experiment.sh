#!/usr/bin/env bash
# Create the next experiment folder from experiments/_TEMPLATE.
# Usage: scripts/new-experiment.sh <base-slug> <short-slug>
#   e.g. scripts/new-experiment.sh qwen3tts12hz lang-adapt  ->  experiments/E0001_qwen3tts12hz_lang-adapt/
set -euo pipefail

if [ $# -ne 2 ]; then
  echo "usage: $0 <base-slug> <short-slug>" >&2
  exit 1
fi
base="$1"; slug="$2"
case "$base$slug" in
  *[!a-z0-9.-]*) echo "slugs may only contain a-z 0-9 . -" >&2; exit 1 ;;
esac

root="$(cd "$(dirname "$0")/.." && pwd)"
exp_dir="$root/experiments"

last=$(find "$exp_dir" -maxdepth 1 -type d -name 'E[0-9][0-9][0-9][0-9]_*' -exec basename {} \; \
  | sed -E 's/^E([0-9]{4})_.*/\1/' | sort -n | tail -1)
next=$(printf 'E%04d' $(( 10#${last:-0} + 1 )))
id="${next}_${base}_${slug}"
dest="$exp_dir/$id"

cp -R "$exp_dir/_TEMPLATE" "$dest"
sed -i.bak "s/^id: .*/id: $id/; s/^# <ID>:/# $id:/" "$dest/README.md" && rm "$dest/README.md.bak"

echo "$dest"
echo "Next: fill in the hypothesis and setup in $id/README.md, add it to experiments/README.md, and commit before you run anything."
