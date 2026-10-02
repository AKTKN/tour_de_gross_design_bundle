#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
command -v conda >/dev/null || { echo 'ERROR: conda is unavailable on PATH.' >&2; exit 1; }
# Run both orchestration and acceptance checks in the requested environment.
exec conda run --no-capture-output -n tour_de_gross python "$SCRIPT_DIR/codex_pipeline.py" "$@"
