#!/usr/bin/env bash
# Job Monitor -- cron / launchd entry point (Mac/Linux)
# Equivalent of run.bat for Windows Task Scheduler.
cd "$(dirname "$0")"
mkdir -p work
python3 job_monitor.py --config config.yaml >> work/last_run.log 2>&1
