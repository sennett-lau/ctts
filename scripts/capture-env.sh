#!/usr/bin/env bash
# Capture the run environment into an experiment's env/ folder (see docs/methodology/logging-standard.md §3).
# Run it on the machine that does the work, from the environment it uses (venv active).
# Usage: CTTS_HOST_ALIAS=<alias> scripts/capture-env.sh <experiment-dir> [-- <command that will be run>]
# The repo is public: the real host name is never written. $HOME and the user name are masked.
set -uo pipefail

alias_name="${CTTS_HOST_ALIAS:?set CTTS_HOST_ALIAS to a neutral host alias, e.g. gpu-workstation-01 (see ADR 0004)}"
redact() { sed -e "s#${HOME}#~#g" -e "s#$(id -un)#<user>#g" -e "s#$(hostname)#${alias_name}#g"; }

dir="${1:?usage: $0 <experiment-dir> [-- <command>]}"; shift
env_dir="$dir/env"; mkdir -p "$env_dir"
[ "${1:-}" = "--" ] && shift
[ $# -gt 0 ] && printf 'cwd: %s\ncmd: %s\n' "$PWD" "$*" | redact >> "$env_dir/command.txt"

repo="$(cd "$(dirname "$0")/.." && pwd)"
{
  echo "captured: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "ctts commit: $(git -C "$repo" rev-parse HEAD 2>/dev/null)"
  echo "ctts dirty files:"; git -C "$repo" status --porcelain 2>/dev/null
  echo "# add trainer fork commits below if any"
} > "$env_dir/git.txt"

{
  echo "host: ${alias_name}"
  uname -srm
  command -v nvidia-smi >/dev/null && nvidia-smi
  command -v python >/dev/null && python - <<'PY' 2>/dev/null
import sys; print("python", sys.version)
try:
    import torch; print("torch", torch.__version__, "cuda", torch.version.cuda, "gpus", torch.cuda.device_count())
except Exception as e: print("torch: n/a", e)
PY
} 2>&1 | redact > "$env_dir/hardware.txt"

if command -v uv >/dev/null && [ -n "${VIRTUAL_ENV:-}" ]; then uv pip freeze 2>/dev/null | redact > "$env_dir/pip-freeze.txt"
elif command -v python >/dev/null; then python -m pip freeze 2>/dev/null | redact > "$env_dir/pip-freeze.txt"
fi

[ -f "$env_dir/seeds.txt" ] || echo "# fill in: python / numpy / torch / data-shuffle seeds" > "$env_dir/seeds.txt"
echo "wrote $env_dir"
