"""
Job Monitor — fetches new postings from target companies' ATS endpoints,
filters by criteria, diffs against last run, emails new matches.

Usage:
    python job_monitor.py [--config config.yaml] [--dry-run]

Env vars required for email:
    JOBMON_SMTP_USER     Gmail address (e.g. you@gmail.com)
    JOBMON_SMTP_PASS     Gmail app password (NOT your normal password)
    JOBMON_SMTP_TO       Recipient address (defaults to SMTP_USER)
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import smtplib
import sys
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from email.message import EmailMessage
from pathlib import Path
from typing import Iterable

import requests
import yaml

# Load .env from this script's own directory. Self-contained — no dependency
# on any parent project's .env file.
try:
    from dotenv import load_dotenv
    _env_file = Path(__file__).resolve().parent / ".env"
    if _env_file.exists():
        load_dotenv(_env_file)
except ImportError:
    pass

# Local input/work/output layout
SCRIPT_DIR = Path(__file__).parent
INPUT_DIR = SCRIPT_DIR / "input"
WORK_DIR = SCRIPT_DIR / "work"
OUTPUT_DIR = SCRIPT_DIR / "output"
STATE_FILE = WORK_DIR / "seen_jobs.json"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
log = logging.getLogger("job_monitor")

HTTP_TIMEOUT = 20
USER_AGENT = "JobMonitor/1.0 (+local)"


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class Job:
    company: str
    ats: str
    job_id: str
    title: str
    location: str
    department: str
    url: str
    posted_at: str  # ISO string or empty

    @property
    def key(self) -> str:
        return f"{self.company}::{self.job_id}"


# ---------------------------------------------------------------------------
# ATS adapters — each returns a list[Job] for one company
# ---------------------------------------------------------------------------

def _get(url: str, **kwargs) -> requests.Response:
    headers = kwargs.pop("headers", {})
    headers.setdefault("User-Agent", USER_AGENT)
    headers.setdefault("Accept", "application/json")
    return requests.get(url, headers=headers, timeout=HTTP_TIMEOUT, **kwargs)


def fetch_greenhouse(company: str, slug: str) -> list[Job]:
    url = f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs?content=true"
    r = _get(url)
    r.raise_for_status()
    data = r.json()
    out = []
    for j in data.get("jobs", []):
        out.append(Job(
            company=company,
            ats="greenhouse",
            job_id=str(j.get("id", "")),
            title=j.get("title", ""),
            location=(j.get("location") or {}).get("name", ""),
            department=", ".join(d.get("name", "") for d in j.get("departments", [])),
            url=j.get("absolute_url", ""),
            posted_at=j.get("updated_at", "") or "",
        ))
    return out


def fetch_lever(company: str, slug: str) -> list[Job]:
    url = f"https://api.lever.co/v0/postings/{slug}?mode=json"
    r = _get(url)
    r.raise_for_status()
    out = []
    for j in r.json():
        cats = j.get("categories", {}) or {}
        out.append(Job(
            company=company,
            ats="lever",
            job_id=str(j.get("id", "")),
            title=j.get("text", ""),
            location=cats.get("location", "") or "",
            department=cats.get("department", "") or cats.get("team", "") or "",
            url=j.get("hostedUrl", ""),
            posted_at=str(j.get("createdAt", "")),
        ))
    return out


def fetch_ashby(company: str, slug: str) -> list[Job]:
    url = f"https://api.ashbyhq.com/posting-api/job-board/{slug}"
    r = _get(url, params={"includeCompensation": "false"})
    r.raise_for_status()
    out = []
    for j in r.json().get("jobs", []):
        out.append(Job(
            company=company,
            ats="ashby",
            job_id=str(j.get("id", "")),
            title=j.get("title", ""),
            location=j.get("location", "") or "",
            department=j.get("department", "") or j.get("team", "") or "",
            url=j.get("jobUrl", ""),
            posted_at=j.get("publishedAt", "") or "",
        ))
    return out


def fetch_smartrecruiters(company: str, slug: str) -> list[Job]:
    url = f"https://api.smartrecruiters.com/v1/companies/{slug}/postings"
    r = _get(url, params={"limit": 100})
    r.raise_for_status()
    out = []
    for j in r.json().get("content", []):
        loc = j.get("location", {}) or {}
        loc_str = ", ".join(filter(None, [loc.get("city"), loc.get("country")]))
        out.append(Job(
            company=company,
            ats="smartrecruiters",
            job_id=str(j.get("id", "")),
            title=j.get("name", ""),
            location=loc_str,
            department=(j.get("department") or {}).get("label", "") or "",
            url=(j.get("ref") or "").replace("/postings/", "/jobs/")
                or f"https://jobs.smartrecruiters.com/{slug}/{j.get('id', '')}",
            posted_at=j.get("releasedDate", "") or "",
        ))
    return out


def fetch_personio(company: str, slug: str) -> list[Job]:
    """
    Personio exposes XML at https://{slug}.jobs.personio.de/xml
    Big in DACH — important for your target list.
    """
    import xml.etree.ElementTree as ET

    url = f"https://{slug}.jobs.personio.de/xml"
    r = _get(url, headers={"Accept": "application/xml"})
    r.raise_for_status()
    root = ET.fromstring(r.content)
    out = []
    for pos in root.findall(".//position"):
        def t(tag: str) -> str:
            el = pos.find(tag)
            return (el.text or "").strip() if el is not None and el.text else ""
        job_id = t("id")
        out.append(Job(
            company=company,
            ats="personio",
            job_id=job_id,
            title=t("name"),
            location=t("office"),
            department=t("department"),
            url=f"https://{slug}.jobs.personio.de/job/{job_id}",
            posted_at=t("createdAt"),
        ))
    return out


def fetch_recruitee(company: str, slug: str) -> list[Job]:
    url = f"https://{slug}.recruitee.com/api/offers/"
    r = _get(url)
    r.raise_for_status()
    out = []
    for j in r.json().get("offers", []):
        out.append(Job(
            company=company,
            ats="recruitee",
            job_id=str(j.get("id", "")),
            title=j.get("title", ""),
            location=", ".join(filter(None, [j.get("city"), j.get("country")])),
            department=j.get("department", "") or "",
            url=j.get("careers_url") or j.get("careers_apply_url", ""),
            posted_at=j.get("published_at", "") or "",
        ))
    return out


def fetch_workday(company: str, slug: str) -> list[Job]:
    """
    Workday format: slug = 'tenant/site' (e.g. 'sap/SAPCareers').
    Uses POST to the CXS endpoint. Tenant subdomain varies — see config notes.
    """
    if "/" not in slug:
        log.warning("[%s] workday slug must be 'tenant/site', got %r", company, slug)
        return []
    tenant, site = slug.split("/", 1)
    # Tenant subdomain pattern: usually {tenant}.wd{N}.myworkdayjobs.com — config can override
    # For simplicity, we try wd1, wd3, wd5 commonly seen
    base_candidates = [f"https://{tenant}.wd{n}.myworkdayjobs.com" for n in (1, 3, 5)]
    out = []
    for base in base_candidates:
        url = f"{base}/wday/cxs/{tenant}/{site}/jobs"
        try:
            r = requests.post(
                url,
                json={"limit": 100, "offset": 0, "searchText": ""},
                headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
                timeout=HTTP_TIMEOUT,
            )
            if r.status_code != 200:
                continue
            data = r.json()
            for j in data.get("jobPostings", []):
                ext = j.get("externalPath", "")
                out.append(Job(
                    company=company,
                    ats="workday",
                    job_id=ext.split("/")[-1] if ext else j.get("title", ""),
                    title=j.get("title", ""),
                    location=j.get("locationsText", "") or "",
                    department="",
                    url=f"{base}/{site}{ext}" if ext else "",
                    posted_at=j.get("postedOn", "") or "",
                ))
            return out
        except Exception as e:
            log.debug("[%s] workday %s failed: %s", company, base, e)
            continue
    log.warning("[%s] workday: no responsive subdomain found for tenant %s", company, tenant)
    return out


ADAPTERS = {
    "greenhouse": fetch_greenhouse,
    "lever": fetch_lever,
    "ashby": fetch_ashby,
    "smartrecruiters": fetch_smartrecruiters,
    "personio": fetch_personio,
    "recruitee": fetch_recruitee,
    "workday": fetch_workday,
}


# ---------------------------------------------------------------------------
# Filtering
# ---------------------------------------------------------------------------

def matches_filters(job: Job, filters: dict) -> bool:
    title_blob = f"{job.title} {job.department}".lower()
    loc = job.location.lower()

    include = [k.lower() for k in filters.get("include_keywords", []) or []]
    exclude = [k.lower() for k in filters.get("exclude_keywords", []) or []]
    locations = [l.lower() for l in filters.get("locations", []) or []]
    exclude_locations = [l.lower() for l in filters.get("exclude_locations", []) or []]

    if include and not any(k in title_blob for k in include):
        return False
    if exclude and any(k in title_blob for k in exclude):
        return False
    if locations and not any(l in loc for l in locations):
        return False
    if exclude_locations and any(l in loc for l in exclude_locations):
        return False
    return True


# ---------------------------------------------------------------------------
# State (which jobs we've already emailed about)
# ---------------------------------------------------------------------------

def load_state() -> dict:
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    return {"seen": {}, "last_run": None}


def save_state(state: dict) -> None:
    WORK_DIR.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")


# ---------------------------------------------------------------------------
# Email
# ---------------------------------------------------------------------------

def render_html(new_jobs: list[Job], errors: list[str]) -> str:
    by_company: dict[str, list[Job]] = {}
    for j in new_jobs:
        by_company.setdefault(j.company, []).append(j)

    parts = [
        "<html><body style='font-family:-apple-system,Segoe UI,Helvetica,Arial,sans-serif;font-size:14px;color:#222;'>",
        f"<h2 style='margin-bottom:4px;'>Job Monitor — {len(new_jobs)} new posting(s)</h2>",
        f"<p style='color:#666;margin-top:0;'>{datetime.now().strftime('%Y-%m-%d %H:%M')}</p>",
    ]
    if not new_jobs:
        parts.append("<p>No new matching jobs since last run.</p>")
    for company, jobs in sorted(by_company.items()):
        parts.append(f"<h3 style='margin-bottom:4px;border-bottom:1px solid #eee;'>{company} ({len(jobs)})</h3><ul style='padding-left:18px;'>")
        for j in jobs:
            loc = f" — {j.location}" if j.location else ""
            dept = f" <span style='color:#888;'>[{j.department}]</span>" if j.department else ""
            parts.append(
                f"<li style='margin-bottom:6px;'><a href='{j.url}'>{j.title}</a>{loc}{dept}</li>"
            )
        parts.append("</ul>")
    if errors:
        parts.append("<h3 style='color:#a00;'>Fetch errors</h3><ul>")
        for e in errors:
            parts.append(f"<li style='color:#a00;'>{e}</li>")
        parts.append("</ul>")
    parts.append("</body></html>")
    return "".join(parts)


def send_email(subject: str, html: str, cfg_email: dict | None = None) -> None:
    """
    Reads credentials from env vars in this priority order:
      1. GMAIL_ADDRESS / GMAIL_APP_PASSWORD  (from local .env in this folder)
      2. JOBMON_SMTP_USER / JOBMON_SMTP_PASS  (fallback OS env vars)
    Recipient priority: config.email.to > JOBMON_SMTP_TO > sender address.

    SMTP server defaults to Gmail (smtp.gmail.com:465, SSL).
    Override via config.yaml email section:
      email:
        smtp_host: smtp.office365.com
        smtp_port: 587
        smtp_ssl: false          # use STARTTLS instead of SSL
    """
    user = os.environ.get("GMAIL_ADDRESS") or os.environ.get("JOBMON_SMTP_USER")
    pwd = os.environ.get("GMAIL_APP_PASSWORD") or os.environ.get("JOBMON_SMTP_PASS")
    cfg = cfg_email or {}
    to = cfg.get("to") or os.environ.get("JOBMON_SMTP_TO") or user

    smtp_host = cfg.get("smtp_host", "smtp.gmail.com")
    smtp_port = int(cfg.get("smtp_port", 465))
    use_ssl = cfg.get("smtp_ssl", True)

    if not user or not pwd:
        log.warning(
            "No SMTP credentials found. Create a .env file in this folder with "
            "GMAIL_ADDRESS=... and GMAIL_APP_PASSWORD=... (see .env.example)."
        )
        return

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = user
    msg["To"] = to
    msg.set_content("HTML version required.")
    msg.add_alternative(html, subtype="html")
    if use_ssl:
        with smtplib.SMTP_SSL(smtp_host, smtp_port) as s:
            s.login(user, pwd)
            s.send_message(msg)
    else:
        with smtplib.SMTP(smtp_host, smtp_port) as s:
            s.ehlo()
            s.starttls()
            s.login(user, pwd)
            s.send_message(msg)
    log.info("Email sent to %s via %s:%d", to, smtp_host, smtp_port)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def run(config_path: Path, dry_run: bool) -> int:
    cfg = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    companies = cfg.get("companies", [])
    filters = cfg.get("filters", {})
    always_email = cfg.get("always_email", False)

    state = load_state()
    seen: dict = state.get("seen", {})

    all_fetched: list[Job] = []
    errors: list[str] = []

    for c in companies:
        name = c.get("name") or c.get("slug")
        ats = (c.get("ats") or "").lower()
        slug = c.get("slug")
        if c.get("disabled"):
            continue
        if ats not in ADAPTERS:
            errors.append(f"{name}: unknown ATS '{ats}'")
            continue
        try:
            log.info("Fetching %s (%s/%s)", name, ats, slug)
            jobs = ADAPTERS[ats](name, slug)
            log.info("  -> %d total postings", len(jobs))
            all_fetched.extend(jobs)
        except Exception as e:
            msg = f"{name} ({ats}/{slug}): {type(e).__name__}: {e}"
            log.error(msg)
            errors.append(msg)

    matched = [j for j in all_fetched if matches_filters(j, filters)]
    log.info("%d matched filters out of %d total", len(matched), len(all_fetched))

    new_jobs = [j for j in matched if j.key not in seen]
    log.info("%d are new since last run", len(new_jobs))

    # Update state
    now_iso = datetime.now(timezone.utc).isoformat()
    for j in matched:
        seen[j.key] = {"first_seen": seen.get(j.key, {}).get("first_seen", now_iso), "title": j.title}
    state["seen"] = seen
    state["last_run"] = now_iso

    # Write a snapshot for inspection
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    snapshot = OUTPUT_DIR / f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    snapshot.write_text(
        json.dumps({"new": [asdict(j) for j in new_jobs], "errors": errors}, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    log.info("Snapshot: %s", snapshot)

    if dry_run:
        log.info("DRY RUN — not sending email, not saving state")
        for j in new_jobs:
            print(f"  NEW {j.company:25} {j.title}  ({j.location})  {j.url}")
        return 0

    if new_jobs or always_email or errors:
        html = render_html(new_jobs, errors)
        subject = f"Job Monitor: {len(new_jobs)} new" + (f" ({len(errors)} errors)" if errors else "")
        send_email(subject, html, cfg.get("email"))

    save_state(state)
    return 0


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--config", default=str(SCRIPT_DIR / "config.yaml"))
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()
    sys.exit(run(Path(args.config), args.dry_run))


if __name__ == "__main__":
    main()
