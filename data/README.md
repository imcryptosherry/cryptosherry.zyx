# Daily Data Pipeline

## Files
- `daily_ai.json`: current day AI recommendation (1 item)
- `daily_ai_history.json`: AI history archive (used by homepage history cards)
- `daily_market.json`: current day market recommendations (Top 3)
- `override.json`: manual override for today's picks only

## Manual Run
```bash
cd /home/sherry/codex/HelloWorld
./site/scripts/generate_daily_data.py
python3 site/scripts/build_from_notion_export.py
```

Or run all-in-one:
```bash
./site/scripts/run_daily_pipeline.sh
```

## Schedule
Installed cron:
- `09:00` ET daily
- command: `/bin/bash /home/sherry/codex/HelloWorld/site/scripts/run_daily_pipeline.sh`

## Override Rules
- `override.json` only applies when `date` equals today's ET date.
- `ai` object replaces today's AI output fields.
- `market` list replaces market entries in order.
- AI history (`daily_ai_history.json`) is not rewritten by override logic.
