#!/usr/bin/env bash
set -euo pipefail

UNIT_DIR="${HOME}/.config/systemd/user"
mkdir -p "${UNIT_DIR}"

SERVICE="${UNIT_DIR}/daily-full-pipeline.service"
TIMER="${UNIT_DIR}/daily-full-pipeline.timer"

cat > "${SERVICE}" <<'EOF'
[Unit]
Description=Run CryptoSherry Daily AI+Market pipeline and publish

[Service]
Type=oneshot
WorkingDirectory=/home/sherry/codex/HelloWorld
ExecStart=/bin/bash /home/sherry/codex/HelloWorld/site/scripts/run_daily_full_pipeline.sh
EOF

cat > "${TIMER}" <<'EOF'
[Unit]
Description=Run CryptoSherry Daily pipeline at 10:00 America/New_York

[Timer]
OnCalendar=*-*-* 10:00:00 America/New_York
Persistent=true
Unit=daily-full-pipeline.service
AccuracySec=1min

[Install]
WantedBy=timers.target
EOF

# Remove legacy cron entries to avoid duplicate runs.
CURRENT="$(crontab -l 2>/dev/null || true)"
CLEANED="$(printf '%s\n' "$CURRENT" | grep -v 'run_daily_pipeline.sh' | grep -v 'site/scripts/run_daily_pipeline.sh' | grep -v '^CRON_TZ=America/New_York$' || true)"
printf '%s\n' "$CLEANED" | sed '/^$/N;/^\n$/D' | crontab -

systemctl --user daemon-reload

# Disable and remove old timer/service units if they exist.
for name in daily-ai-pipeline.timer daily-ai-pipeline.service \
            daily-market-pipeline.timer daily-market-pipeline.service \
            daily-pipeline.timer daily-pipeline.service; do
  systemctl --user disable --now "$name" >/dev/null 2>&1 || true
  rm -f "${UNIT_DIR}/${name}"
done
systemctl --user daemon-reload

systemctl --user enable --now daily-full-pipeline.timer

echo "Installed timer (Persistent=true):"
echo "- daily-full-pipeline.timer @ 10:00 America/New_York"
systemctl --user list-timers --all --no-pager | rg 'daily-full-pipeline|NEXT|LAST'
