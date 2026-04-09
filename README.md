# Job Monitor

Watches 100+ tech companies for new job postings, filters by your criteria (role, location, seniority), and emails you only the new ones daily. Fully automated once set up.

## How It Works

Most companies use an ATS (Greenhouse, Lever, Ashby, etc.) that exposes a public JSON API with all open postings. This tool hits those endpoints directly, applies your filters, diffs against a local state file, and emails only postings it has never seen before.

**100+ companies included:** Anthropic, Stripe, Mistral AI, Cursor, Celonis, ElevenLabs, Helsing, and many more across AI labs, developer platforms, European tech, and DACH companies. See `companies_catalog.yaml` for the full list.

## Quickstart (with Claude Code)

The easiest way to set up. Claude Code walks you through everything interactively.

```bash
git clone https://github.com/dennisfleischer/job-monitor.git
cd job-monitor
claude
```

Then say: **"Richte den Jobscraper für mich ein"** (or "Set up the job scraper for me").

Claude Code will:
1. Install Python dependencies
2. Ask about your target roles, locations, and preferred companies
3. Generate a personalized `config.yaml`
4. Set up Gmail credentials
5. Run a test, fix any issues
6. Schedule daily execution

Takes about 10 minutes.

## Manual Setup

If you prefer to set things up yourself:

1. **Install dependencies:** `pip install -r requirements.txt`
2. **Create `.env`:** Copy `.env.example` to `.env`, add your Gmail address and [app password](https://myaccount.google.com/apppasswords)
3. **Create `config.yaml`:** Use `config.example.yaml` as a starting point, pick companies from `companies_catalog.yaml`
4. **Test:** `python job_monitor.py --dry-run`
5. **Run:** `python job_monitor.py`
6. **Schedule:** Windows Task Scheduler (`run.bat`) or cron (`run.sh`)

## Supported ATS Systems

| ATS | URL Pattern | Slug Source |
|---|---|---|
| Greenhouse | `boards.greenhouse.io/SLUG/...` | URL path |
| Lever | `jobs.lever.co/SLUG/...` | URL path |
| Ashby | `jobs.ashbyhq.com/SLUG/...` | URL path |
| SmartRecruiters | `jobs.smartrecruiters.com/SLUG/...` | URL path |
| Personio | `SLUG.jobs.personio.de` | Subdomain |
| Recruitee | `SLUG.recruitee.com` | Subdomain |
| Workday | `SLUG.wd{N}.myworkdayjobs.com` | Subdomain |

## File Layout

```
jobscraper/
├── job_monitor.py           Main script (do not modify)
├── companies_catalog.yaml   Full company catalog (100+ companies)
├── config.example.yaml      Example config format
├── config.yaml              Your personal config (generated, gitignored)
├── .env.example             Credential template
├── .env                     Your credentials (gitignored)
├── requirements.txt         Python dependencies
├── run.bat                  Windows Task Scheduler entry point
├── run.sh                   Mac/Linux cron entry point
├── work/                    State + logs (gitignored)
│   ├── seen_jobs.json       Which jobs have been emailed
│   └── last_run.log         Rolling log
└── output/                  Per-run snapshots (gitignored)
    └── run_*.json           New jobs + errors per run
```

## Adding Companies

Open any job posting on a company's careers page and check the URL to identify the ATS and slug. Add to your `config.yaml`:

```yaml
  - name: Company Name
    ats: greenhouse    # or lever, ashby, etc.
    slug: companyslug
```

Run `--dry-run` to verify.

## Troubleshooting

- **No results for a company:** Wrong slug. Check the careers page URL.
- **404 errors:** Slug changed or company switched ATS. Re-discover the slug.
- **Email not arriving:** Check `.env` credentials, ensure 2-Step Verification is enabled, check `work/last_run.log`.
- **Script crash on startup:** YAML indentation (spaces, not tabs) or `.env` in wrong location.
