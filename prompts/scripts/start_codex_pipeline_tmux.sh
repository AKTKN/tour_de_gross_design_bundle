#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd -- "$SCRIPT_DIR/../.." && pwd)"
SESSION="${CODEX_TMUX_SESSION:-codex-tour-de-gross}"
STATE_DIR="$ROOT/.codex-pipeline/tour-de-gross"
RUNNER="$SCRIPT_DIR/run_codex_pipeline.sh"
# Read-only diagnostics run immediately, without leaving a tmux session behind.
for arg in "$@"; do
  case "$arg" in --list|--dry-run|--preflight|--status|-h|--help) exec bash "$RUNNER" "$@" ;; esac
done
command -v tmux >/dev/null || { echo 'ERROR: tmux is unavailable.' >&2; exit 1; }
[[ "$SESSION" =~ ^[A-Za-z0-9_-]+$ ]] || { echo 'ERROR: invalid tmux session name.' >&2; exit 2; }
if tmux has-session -t "=$SESSION" 2>/dev/null; then
  echo "ERROR: tmux session already exists: $SESSION. Inspect or attach before starting another." >&2
  exit 1
fi
# Ensure CLI, auth and environment work before detaching. This makes no model call.
bash "$RUNNER" --preflight
mkdir -p "$STATE_DIR"
LAUNCHER="$(mktemp "$STATE_DIR/tmux-launch-XXXXXXXX.sh")"
{
  printf '#!/usr/bin/env bash\nset -o pipefail\nexport PATH=%q\ncd %q\n' "$PATH" "$ROOT"
  printf 'bash %q' "$RUNNER"
  for arg in "$@"; do printf ' %q' "$arg"; done
  printf ' 2>&1 | tee -a %q\n' "$STATE_DIR/pipeline.log"
  printf 'rc=${PIPESTATUS[0]}\necho "Pipeline exit code: $rc"\nexit "$rc"\n'
} > "$LAUNCHER"
# Set remain-on-exit before the runner starts, so even an early failure is visible.
# tmux takes a command plus separate arguments: no argument re-parsing by our launcher.
rm -f -- "$STATE_DIR/exit-code"
tmux new-session -d -s "$SESSION" -c "$ROOT" \; set-option -w -t "=$SESSION:0" remain-on-exit on \; respawn-pane -k -t "=$SESSION:0.0" bash "$LAUNCHER"
printf 'Started session: %s\nAttach: tmux attach -t %s\nLog: %s\nDetach: Ctrl-b d\n' "$SESSION" "$SESSION" "$STATE_DIR/pipeline.log"
