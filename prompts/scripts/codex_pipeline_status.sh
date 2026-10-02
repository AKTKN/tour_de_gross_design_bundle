#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd -- "$SCRIPT_DIR/../.." && pwd)"
SESSION="${CODEX_TMUX_SESSION:-codex-tour-de-gross}"
printf 'Repository: %s\nSession: %s\n' "$ROOT" "$SESSION"
if command -v tmux >/dev/null && tmux has-session -t "=$SESSION" 2>/dev/null; then
  tmux list-panes -t "=$SESSION:0" -F 'pane=#{pane_id} dead=#{pane_dead} exit=#{pane_dead_status} command=#{pane_current_command}'
else
  echo 'tmux session does not exist.'
fi
bash "$SCRIPT_DIR/run_codex_pipeline.sh" --status
printf '\nWorking tree:\n'
git -C "$ROOT" status --short
