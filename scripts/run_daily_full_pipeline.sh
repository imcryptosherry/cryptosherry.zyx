#!/usr/bin/env bash
set -euo pipefail

ROOT="/home/sherry/codex/HelloWorld"
cd "$ROOT"

if [[ -f "$ROOT/.env" ]]; then
  # shellcheck disable=SC1091
  source "$ROOT/.env"
fi

LOG_DIR="$ROOT/site/data/logs"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/daily_full_pipeline_$(date -u +%Y%m%d).log"

{
  echo "[start] $(date -u +%FT%TZ)"
  echo "[step] generate daily ai+market data"
  "$ROOT/site/scripts/generate_daily_data.py" --mode all
  echo "[step] build site"
  python3 "$ROOT/site/scripts/build_from_notion_export.py"
  echo "[step] publish github pages"
  /bin/bash "$ROOT/site/scripts/publish_pages.sh"
  echo "[done] $(date -u +%FT%TZ)"
} >> "$LOG_FILE" 2>&1
