import os
import glob
import json
import argparse
from datetime import datetime, timezone

from dotenv import load_dotenv
from supabase import create_client

from fetch_jobs import dedupe_jobs, get_skill_id_map

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)


JOB_COLUMNS = [
    "source", "source_job_id", "company", "title",
    "location", "department", "url", "description", "posted_at",
]

CHUNK = 500

def newest_raw_file(pattern="data/raw/greenhouse_jobs_*.json"):
    """Most recent fetch file. The timestamped names sort chronologically."""
    files = sorted(glob.glob(pattern))
    if not files:
        raise FileNotFoundError(f"no files match {pattern} - run fetch_greenhouse.py first")
    return files[-1]

def chunked(items, size=CHUNK):
    """Yield successive `size`-length slices of `items`."""
    for i in range(0, len(items), size):
        yield items[i:i + size]

def load_normalized(path):
    """Read a raw fetch file and collapse duplicate postings of the same role."""
    jobs = json.loads(open(path).read())["results"]

    # Greenhouse gives every city-variant of a role its own unique id, so the
    # DB constraint can't catch them - 7,764 rows collapse to ~6,200 openings.
    # Without this, a role posted in 19 cities votes 19 times on skill counts.
    return dedupe_jobs(jobs)

def upsert_jobs(jobs, fetched_at):
    """
    Write jobs, then read their ids back with an explicit SELECT.

    We deliberately do NOT trust the upsert response. PostgREST doesn't
    reliably return a representation for every row on large batched upserts,
    and when it comes back empty you get a silent failure: every job written,
    zero skills linked, no error raised. Reading the ids back costs a few
    extra requests and cannot silently under-report.
    """
    for batch in chunked(jobs):
        rows = []
        for job in batch:
            row = {col: job.get(col) for col in JOB_COLUMNS}
            row["fetched_at"] = fetched_at
            rows.append(row)

        supabase.table("jobs").upsert(rows, on_conflict="source,source_job_id").execute()
        print(f"  wrote {len(rows)} jobs")

    # Page through every row: PostgREST caps a single response at 1000 rows,
    # so a plain .select() would silently return only the first 1000 of your
    # 6,224 jobs - the same class of silent truncation that caused this bug.
    id_map = {}
    start = 0
    while True:
        page = (
            supabase.table("jobs")
            .select("id,source,source_job_id")
            .range(start, start + 999)
            .execute()
            .data
        )
        if not page:
            break
        for row in page:
            id_map[(row["source"], row["source_job_id"])] = row["id"]
        start += 1000

    return id_map

def build_skill_pairs(jobs, id_map, skill_id_map):
    """Turn each job's skill names into (job_id, skill_id) rows for job_skills."""
    pairs = []
    unknown = set()

    for job in jobs:
        job_id = id_map.get((job.get("source"), job.get("source_job_id")))
        if job_id is None:
            continue  # never got an id back; already warned above

        # set() guards against a skill name appearing twice - job_skills has a
        # composite primary key, and one duplicate  one duplicate pair fails the whole insert.
        for name in set(job.get("skills") or []):
            skill_id = skill_id_map.get(name)
            if skill_id is None:
                unknown.add(name)
                continue
            pairs.append({"job_id": job_id, "skill_id": skill_id})

    if unknown:
        print(f"  WARNING: {len(unknown)} skills missing from `skills` table: {sorted(unknown)}")
        print("           run skills_seed.py to sync the vocabulary")

    return pairs

def replace_job_skills(job_ids, pairs):
    """
    Delete then re-insert, rather than upsert.

    An upsert would add new pairs but never remove ones that no longer apply -
    edit a description to drop Java and the old row lives forever. Clearing
    each touched job first makes the table a true reflection of the current
    descriptions on every run.
    """
    for batch in chunked(list(job_ids)):
        supabase.table("job_skills").delete().in_("job_id", batch).execute()

    for batch in chunked(pairs, 1000):  # tiny rows, so a bigger chunk is fine
        supabase.table("job_skills").insert(batch).execute()

def main():
    parser = argparse.ArgumentParser(description="Load a raw fetch file into Supabase")
    parser.add_argument("path", nargs="?", help="raw JSON file (default: newest)")
    parser.add_argument("--limit", type=int, help="only load the first N jobs")
    args = parser.parse_args()

    path = args.path or newest_raw_file()
    jobs = load_normalized(path)
    if args.limit:
        jobs = jobs[:args.limit]

    print(f"{path} -> {len(jobs)} jobs after dedupe")

    # One timestamp for the whole run: it records when this BATCH was fetched,
    # not when each individual row happened to get written.
    fetched_at = datetime.now(timezone.utc).isoformat()

    id_map = upsert_jobs(jobs, fetched_at)
    pairs = build_skill_pairs(jobs, id_map, get_skill_id_map())

    if len(id_map) != len(jobs):
        raise RuntimeError(f"resolved {len(id_map)} ids for {len(jobs)} jobs")

    print(f"linking {len(pairs)} job-skill pairs...")
    replace_job_skills(id_map.values(), pairs)

    with_skills = sum(1 for j in jobs if j.get("skills"))
    print(f"\ndone. {len(id_map)} jobs, {len(pairs)} skill links")
    print(f"{with_skills}/{len(jobs)} jobs had at least one skill")


if __name__ == "__main__":
    main()
