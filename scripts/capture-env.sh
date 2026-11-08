#!/usr/bin/env bash
# Capture the run environment into an experiment's env/ folder (see docs/methodology/logging-standard.md §3).
# Run it on the machine that does the work, from the environment it uses (venv active).
# Usage: scripts/capture-env.sh <experiment-dir> [-- <command that will be run>]
set -uo pipefail

dir="${1:?usage: $0 <experiment-dir> [-- <command>]}"; shift
env_dir="$dir/env"; mkdir -p "$env_dir"
[ "${1:-}" = "--" ] && shift
[ $# -gt 0 ] && printf 'cwd: %s\ncmd: %s\n' "$PWD" "$*" >> "$env_dir/command.txt"

repo="$(cd "$(dirname "$0")/.." && pwd)"
{
  echo "captured: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "ctts commit: $(git -C "$repo" rev-parse HEAD 2>/dev/null)"
  echo "ctts dirty files:"; git -C "$repo" status --porcelain 2>/dev/null
  echo "# add trainer fork commits below if any"
} > "$env_dir/git.txt"

{
  echo "host: $(hostname)"
  uname -a
  command -v nvidia-smi >/dev/null && nvidia-smi
  command -v python >/dev/null && python - <<'PY' 2>/dev/null
import sys; print("python", sys.version)
try:
    import torch; print("torch", torch.__version__, "cuda", torch.version.cuda, "gpus", torch.cuda.device_count())
except Exception as e: print("torch: n/a", e)
PY
} > "$env_dir/hardware.txt" 2>&1

if command -v uv >/dev/null && [ -n "${VIRTUAL_ENV:-}" ]; then uv pip freeze > "$env_dir/pip-freeze.txt" 2>/dev/null
elif command -v python >/dev/null; then python -m pip freeze > "$env_dir/pip-freeze.txt" 2>/dev/null
fi

[ -f "$env_dir/seeds.txt" ] || echo "# fill in: python / numpy / torch / data-shuffle seeds" > "$env_dir/seeds.txt"
echo "wrote $env_dir"
