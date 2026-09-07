import json
import os
import re
import html 
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor
from skills import extract_skills_from_description

import requests

BOARDS = [
    "stripe", "figma", "databricks", "discord", "coinbase", "vercel", "anthropic",
    "asana", "gitlab", "reddit", "airtable", "samsara", "affirm", "robinhood",
    "brex", "instacart", "dropbox", "twilio", "cloudflare", "mongodb", "elastic",
    "datadog", "gusto", "checkr", "flexport", "faire", "chime", "carta", "mercury",
    "duolingo", "lyft", "pinterest", "squarespace", "okta", "amplitude",
    "launchdarkly", "pagerduty", "netlify", "fivetran", "sigmacomputing", "scaleai",
]

BOARD_URL = "https://boards-api.greenhouse.io/v1/boards/{token}/jobs?content=true"

def strip_html(raw):
    """Greenhouse returns content double-escaped: unescape BEFORE removing tags."""
    text = html.unescape(raw or "")
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", text).strip()

def fetch_board(token):
    try:
        resp = requests.get(BOARD_URL.format(token=token), timeout = 30)
    except requests.RequestException as e:
        print(f"  {token}: {type(e).__name__}")
        return []
    if resp.status_code != 200:
        print(f"  {token}: HTTP {resp.status_code}")
        return []
    return resp.json().get("jobs", [])

def normalize_greenhouse_job(raw_job, token):
    """Shape a greenhouse job like normalize_job() does, so the rest of the pipeline works."""
    location = raw_job.get("location") or {}
    departments = raw_job.get("departments") or []
    desc = strip_html(raw_job.get("content"))

    return {
        "source": "greenhouse",
        "source_job_id": str(raw_job.get("id")),
        "title": raw_job.get("title"),
        "company": raw_job.get("company_name") or token,
        "location": location.get("name"),
        "department": ", ".join(d.get("name", "") for d in departments),
        "url": raw_job.get("absolute_url"),
        "posted_at": raw_job.get("first_published") or raw_job.get("updated_at"),
        "description": desc,
        "skills": extract_skills_from_description(desc),
    }

def fetch_all_boards(boards = BOARDS):
    jobs = []

    with ThreadPoolExecutor(max_workers = 8) as pool:
        results = pool.map(lambda t: (t,fetch_board(t)), boards)

        for token, raw_jobs in results:
            for raw_job in raw_jobs:
                jobs.append(normalize_greenhouse_job(raw_job,token))
    return jobs

def save_raw_greenhouse(jobs):
    os.makedirs("data/raw", exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    filename = f"data/raw/greenhouse_jobs_{timestamp}.json"

    with open(filename, "w") as f:
        json.dump({"results": jobs}, f, ensure_ascii=False, indent=2)

    return filename


def main():
    print(f"Fetching {len(BOARDS)} boards...")
    jobs = fetch_all_boards()

    path = save_raw_greenhouse(jobs)

    companies = len({j["company"] for j in jobs})
    avg_len = sum(len(j["description"]) for j in jobs) / max(len(jobs), 1)

    print(f"\n{len(jobs)} jobs from {companies} companies -> {path}")
    print(f"avg description: {avg_len:.0f} chars")


if __name__ == "__main__":
    main()