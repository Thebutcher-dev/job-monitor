@echo off
REM Job Monitor — Task Scheduler entry point
REM Reads GMAIL_ADDRESS and GMAIL_APP_PASSWORD from a local .env file
REM in this same folder (see .env.example for the template).

cd /d "%~dp0"
python job_monitor.py --config config.yaml >> work\last_run.log 2>&1
