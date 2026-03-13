#!/usr/bin/env bash
set -euo pipefail

echo "Deprecated: cron cannot catch up missed runs when machine is off."
echo "Use systemd timer instead:"
echo "  /home/sherry/codex/HelloWorld/site/scripts/setup_daily_timer.sh"
