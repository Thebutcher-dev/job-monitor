# Job Monitor -- Claude Code Setup Guide

This project scrapes ATS endpoints (Greenhouse, Lever, Ashby, SmartRecruiters, Personio, Recruitee, Workday) for job postings, filters by the user's criteria, and emails only new matches via Gmail.

The user has cloned this repo and wants you to set it up for them. Follow the steps below IN ORDER. This is an interactive process: ask the user questions and generate a personalized config from their answers.

## Ground Rules

- DO NOT modify `job_monitor.py`. It is complete and working.
- DO NOT modify `companies_catalog.yaml`. It is a reference catalog.
- You WILL generate two files: `config.yaml` and `.env`. These are personal and gitignored.
- NEVER echo back passwords or credentials after writing them.
- NEVER commit `.env` or `config.yaml` to git.
- ASK before making changes. Show the user what you plan to generate.
- Match the user's language. If they write German, respond in German. If English, respond in English.
- Keep responses concise. No over-explaining.
- If anything fails unexpectedly, STOP and ask. Do not improvise fixes to `job_monitor.py`.

---

## Step 1: Environment Check

1. Detect the OS (Windows / Mac / Linux).
2. Check Python 3.8+:
   - Windows: try `python --version`, then `py --version`
   - Mac/Linux: try `python3 --version`, then `python --version`
3. If Python is not found, tell the user:
   - Windows: install from https://www.python.org/downloads/ (check "Add to PATH")
   - Mac: `brew install python3` or https://www.python.org/downloads/
   - Linux: `sudo apt install python3 python3-pip` (or equivalent)
   - STOP here until they confirm Python is installed.
4. Install dependencies:
   ```
   python -m pip install --upgrade pip
   python -m pip install -r requirements.txt
   ```
   (Use `python3` or `py` as appropriate for the OS.)
5. Confirm all three packages installed (requests, PyYAML, python-dotenv). If not, debug.

---

## Step 2: Profile Interview

Ask the user these questions to build their personal config. You can batch them or ask one at a time depending on the conversation flow.

### Question 1: What roles are you looking for?

Ask: "What kind of roles are you looking for? For example: Product Management, Partnerships, Engineering, Marketing, Design, Data/Analytics, Operations, Sales..."

Map their answer to `include_keywords` using the role families below as reference. Combine multiple families if the user mentions several areas. Let them confirm and refine.

**Role Families Reference:**

- **partnerships_bd**: partnerships, partner manager, partner management, alliance, alliances, ecosystem, business development, biz dev, channel partner, partner marketing, partner operations, partner enablement, partner development
- **product**: product manager, product lead, product marketing, head of product, director of product, vp product, chief product, product strategy, platform product
- **devrel**: developer relations, devrel, developer advocate, developer experience, developer marketing, developer success, developer engagement
- **engineering**: software engineer, senior engineer, staff engineer, engineering manager, frontend engineer, backend engineer, full stack engineer, devops engineer, site reliability, mobile engineer
- **design**: product designer, ux designer, ui designer, design lead, head of design, design manager
- **marketing**: marketing manager, growth marketing, content marketing, brand marketing, performance marketing, demand generation, marketing lead, head of marketing
- **sales**: account executive, enterprise sales, sales manager, sales director, head of sales, revenue, commercial
- **data**: data scientist, data analyst, data engineer, analytics, machine learning, ml engineer, research scientist, ai researcher
- **operations**: operations manager, strategy and operations, chief of staff, strategic initiatives, go-to-market, gtm, program manager, project manager
- **finance**: finance manager, financial analyst, controller, head of finance, fp&a
- **people_hr**: recruiter, talent acquisition, people operations, hr business partner, people partner

If their role doesn't map to any family above, just ask for specific job titles they'd search for and use those directly.

### Question 2: What should be excluded?

Ask: "Any roles or seniority levels you want to filter OUT? Common exclusions: internships, junior roles, engineering (if not relevant), pure sales, HR/recruiting..."

Map to `exclude_keywords`. Suggest sensible defaults based on their role:
- Almost everyone wants to exclude: intern, internship, working student, werkstudent, praktikant, praktikum, trainee, junior, entry level, entry-level, graduate program, new grad
- If they're NOT looking for engineering: add the engineering family keywords
- If they're NOT looking for sales: add account executive, inside sales, field sales, sdr, bdr, sales development
- If they're NOT looking for design: add the design family keywords

### Question 3: Where are you looking?

Ask: "What locations or regions interest you? Examples: Germany, DACH region, all of Europe, Remote, specific cities like Berlin or London..."

Map to `locations` and `exclude_locations`:

**If they say "DACH" or "Germany/Austria/Switzerland":**
```
locations: germany, deutschland, berlin, munich, münchen, hamburg, frankfurt, cologne, köln, düsseldorf, stuttgart, vienna, austria, zurich, switzerland, dach, remote, emea, europe, european
exclude_locations: united states, usa, canada, india, singapore, hong kong, japan, china, australia, apac, latam, us-remote, remote us, remote-us, us remote
```

**If they say "Europe" (broader):**
Add to the DACH set: london, united kingdom, amsterdam, netherlands, paris, france, dublin, ireland, stockholm, sweden, copenhagen, denmark, helsinki, finland, oslo, norway, barcelona, madrid, spain, milan, italy, prague, czech, warsaw, poland, lisbon, portugal

**If they say "US" or specific US cities:** do NOT add US to exclude_locations.

**If they include "Remote":** always add the standard US/APAC excludes to prevent "Remote - US only" matches (unless they actually want US).

### Question 4: Which company categories?

Read `companies_catalog.yaml` and present the categories with company counts and examples. Format like:

```
Here are the available company categories:

1. Developer Platforms (11 companies)
   Stripe, Notion, Datadog, Cloudflare, Vercel, Figma, Supabase...

2. Frontier AI Labs (4 active + 2 manual-only)
   Anthropic, Mistral AI, Cohere, Perplexity

3. AI Applications (18 companies)
   ElevenLabs, Cursor, Replit, Cognition (Devin), Harvey, Clay...

4. AI Infrastructure (20 companies)
   Pinecone, Scale AI, LangChain, Together AI, Modal Labs...

5. European AI (13 companies)
   Helsing (Munich), Langfuse (Berlin), Black Forest Labs (Freiburg),
   Lovable (Stockholm), Dust (Paris)...

6. AI Rising Stars (24 companies)
   Suno, Pika, Descript, World Labs, Twelve Labs, Tessl...

7. Social Media & Creator Tools (4 companies)
   Canva, Hootsuite, Sprout Social, Later

8. DACH Tech (5 companies)
   Celonis (Munich), GetYourGuide, N26, Trade Republic, Mollie

Which categories? (e.g. "1, 2, 5" or "all" or "AI labs and European AI")
```

Collect all companies from selected categories where `status: active`. For `status: no_adapter` companies, mention them: "Note: [Company] uses [ATS] which we don't support yet. You'd need to check their careers page manually."

### Question 5: Email address

Ask: "What Gmail address should receive the job alerts?"

Validate it looks like a Gmail address. If not Gmail, warn: "This tool sends email via Gmail SMTP. You need a Gmail account as the sender. The recipient can be any address, but the sender must be Gmail."

---

## Step 3: Generate config.yaml

Before writing, show the user a summary:

```
I'll create your config.yaml with:
- X include keywords: [list first 5...]
- Y exclude keywords: [list first 5...]
- Z location terms (focused on [region])
- N companies across [selected categories]
- Alerts sent to: their@email.com

Look good?
```

After confirmation, write `config.yaml` using the format from `config.example.yaml`. Include a comment header noting it was generated by Claude Code with the date.

---

## Step 4: Set Up Email Credentials

First ask: "Do you have a Gmail account you can use as the sender for job alerts?
Gmail is the easiest option. If not, we can also set up Outlook, GMX, Yahoo, or
any other email provider."

### Path A: Gmail (recommended)

1. Check if `.env` already exists. If yes, read it and confirm GMAIL_ADDRESS is set.
2. If `.env` does not exist, copy `.env.example` to `.env`.
3. Ask the user for their Gmail address.
4. Guide them through creating a Gmail App Password:
   ```
   To send emails, you need a Gmail App Password (not your regular password):
   1. Go to https://myaccount.google.com/apppasswords
      (2-Step Verification must be enabled first)
   2. Create an app password (name it e.g. "Job Monitor")
   3. Copy the 16-character code and paste it here
   ```
5. Write `GMAIL_ADDRESS` and `GMAIL_APP_PASSWORD` into `.env`.
6. No changes needed to `config.yaml` email section (Gmail is the default).

### Path B: Other email provider

If the user does not have Gmail, walk them through their provider step by step.

1. Ask which provider they use.
2. Look up their SMTP settings from the table below:

   | Provider | smtp_host | smtp_port | smtp_ssl |
   |---|---|---|---|
   | Gmail | smtp.gmail.com | 465 | true |
   | Outlook / Hotmail | smtp.office365.com | 587 | false |
   | GMX | mail.gmx.net | 587 | false |
   | Yahoo | smtp.mail.yahoo.com | 465 | true |
   | iCloud | smtp.mail.me.com | 587 | false |
   | Proton Mail | (not supported, no SMTP access on free plan) | - | - |

   For providers not listed, ask the user to google "{provider} SMTP settings"
   and provide host, port, and whether it uses SSL or STARTTLS.

3. Add the SMTP settings to the `email` section of `config.yaml`:
   ```yaml
   email:
     to: recipient@example.com
     smtp_host: smtp.office365.com
     smtp_port: 587
     smtp_ssl: false
   ```
   (Only needed for non-Gmail. Gmail users don't need these lines.)

4. Copy `.env.example` to `.env`.
5. Guide the user through getting an app password for their provider:
   - **Outlook/Hotmail**: Go to https://account.microsoft.com/security
     → "Advanced security options" → "App passwords" → Create one
   - **GMX**: Go to GMX Settings → POP3/IMAP → Enable POP3/IMAP,
     note down the password shown
   - **Yahoo**: Go to https://login.yahoo.com/account/security
     → "Generate app password"
   - **iCloud**: Go to https://appleid.apple.com → "Sign-In and Security"
     → "App-Specific Passwords" → Generate
   - **Other**: Ask the user to look up how to create an app password
     for their provider.

6. Write `GMAIL_ADDRESS` (used as env var name for any provider) and
   `GMAIL_APP_PASSWORD` into `.env` with the user's email and app password.
7. Confirm saved. Do NOT echo the password back.

---

## Step 5: First Dry Run

Run:
```
python job_monitor.py --dry-run
```

This fetches all companies, applies filters, and prints matches without sending email or saving state. Takes 30-120 seconds depending on company count.

Parse the output and report:
1. **Successful fetches:** X companies returned Y total postings
2. **Failed fetches:** list each error (404 = wrong slug, timeout, etc.)
3. **Matches:** Z postings passed your filters
4. **New since last run:** (will be same as matches on first run since no state exists)

**If matches = 0:** Filters are too strict. Suggest loosening (broader keywords, more locations). Ask before changing.

**If matches > 300:** Filters are too broad. Suggest adding exclude_keywords or narrowing locations. Ask before changing.

---

## Step 6: Fix Broken Slugs

For each company that returned a fetch error in Step 5:

1. Try common slug variations:
   - With/without hyphens: `company` vs `company-ai`
   - With suffixes: `companycareers`, `companyjobs`
   - Lowercase vs mixed case
2. Test variations by fetching the API endpoint directly (curl or python).
3. Update `config.yaml` with any working slugs.
4. Re-run `--dry-run` and report.

For persistently broken slugs, tell the user:
```
To find the correct slug, open the company's careers page in your browser,
click any job posting, and check the URL:
  boards.greenhouse.io/SLUG/...     -> ats: greenhouse
  jobs.lever.co/SLUG/...            -> ats: lever
  jobs.ashbyhq.com/SLUG/...         -> ats: ashby
  jobs.smartrecruiters.com/SLUG/... -> ats: smartrecruiters
  SLUG.jobs.personio.de             -> ats: personio
  SLUG.recruitee.com                -> ats: recruitee
```

Remove companies that can't be resolved and note them for manual tracking.

---

## Step 7: Sanity Check Matches

Show the user the first 15-20 matches from the dry run, formatted as a table:

```
Company          | Title                        | Location
-----------------+------------------------------+---------
Stripe           | Partner Manager, EMEA        | London
Anthropic        | Product Manager, API         | London
...
```

Ask: "Do these look relevant? Any false positives to filter out? Any types of roles missing?"

If changes needed: suggest specific keyword edits, confirm, apply, re-run dry run. Repeat until they're satisfied.

---

## Step 8: First Real Run

Warn the user:
```
The first real run will send a large email with ALL current matches
(since the state file is empty, everything counts as "new").
After this, future runs only email genuinely new postings. Ready?
```

Run:
```
python job_monitor.py
```

Confirm: "Check your inbox (and spam folder) for an email from your Gmail address. Subject will be 'Job Monitor: X new'. Did it arrive?"

**If no email:**
- Check `work/last_run.log` for SMTP errors
- Wrong app password -> re-enter in `.env`
- 2FA not enabled -> guide user to enable it
- Email in spam -> mark as not spam

---

## Step 9: Set Up Daily Scheduling

Detect the OS and guide:

### Windows (Task Scheduler)

Walk through creating a scheduled task:
1. Open Task Scheduler (search "Task Scheduler" in Start)
2. Click "Create Basic Task"
3. Name: "Job Scraper"
4. Trigger: Daily at their preferred time (suggest 07:00)
5. Action: "Start a program"
6. Program/script: full path to `run.bat` (e.g. `C:\Users\...\jobscraper\run.bat`)
7. "Start in": the jobscraper folder path
8. Finish, then open Properties and check "Run whether user is logged on or not"

### Mac (cron)

```bash
chmod +x run.sh
crontab -e
```
Add line: `0 7 * * * cd /path/to/jobscraper && ./run.sh`

### Linux (cron)

```bash
chmod +x run.sh
crontab -e
```
Add line: `0 7 * * * cd /path/to/jobscraper && ./run.sh`

After setup, tell the user to wait for the next scheduled run or trigger manually to verify.

---

## Step 10: Summary

Give a short recap:
- N companies being tracked
- State file: `work/seen_jobs.json`
- Run logs: `work/last_run.log`
- Snapshots: `output/run_*.json`

Quick reference:
- Preview new matches: `python job_monitor.py --dry-run`
- Send email now: `python job_monitor.py`
- Add companies: edit `config.yaml`, add `name/ats/slug`, run `--dry-run`
- Adjust filters: edit `config.yaml` filters section, run `--dry-run`
- Check catalog: see `companies_catalog.yaml` for all available companies

Then stop. Do not volunteer additional features or improvements.
