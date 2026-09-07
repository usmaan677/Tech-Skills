import os
from dotenv import load_dotenv

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from supabase import create_client

# Reuse your existing pipeline functions from fetch_jobs.py
from fetch_jobs import (
    fetch_jobs,
    save_raw_results,
    parse_raw_file,
    create_job_search,
    upsert_search_skill_counts,
)

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
    raise RuntimeError("Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY in .env")

supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

app = FastAPI(title="Tech Skills ETL API")

# Allow your React dev server to call this backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite default
        "http://localhost:3000",  # (if you ever use CRA/Next dev)
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def find_recent_search(term: str, country: str):
    """
    Checks if we have run this search recently.
    Returns the search_id if found, else None.
    """
    # You might want to add a time filter here (e.g., created_at > 7 days ago)
    resp = (
        supabase.table("job_searches")
        .select("id")
        .eq("search_term", term)
        .eq("country", country)
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )
    if resp.data:
        return resp.data[0]["id"]
    return None


def get_search_results(search_id: int):
    """
    Helper to fetch skills for a given search_id
    """
    rows = (
        supabase.table("search_skill_counts")
        .select("count, skills(name)")
        .eq("search_id", search_id)
        .execute()
        .data
        or []
    )

    skills = []
    for r in rows:
        skill_obj = r.get("skills") or {}
        skills.append(
            {"skill": skill_obj.get("name", "unknown"), "count": r.get("count", 0)}
        )

    skills.sort(key=lambda x: x["count"], reverse=True)
    return skills


class SearchRequest(BaseModel):
    search_term: str = Field(min_length=2, max_length=120)
    country: str = Field(default="ca", min_length=2, max_length=10)
    page: int = Field(default=1, ge=1, le=50)
    results_per_page: int = Field(default=50, ge=1, le=50)


@app.get("/health")
def health():
    return {"ok": True}


@app.post("/search")
def run_search(req: SearchRequest):
    """
    Runs: Adzuna fetch -> parse -> insert job_searches -> upsert counts
    Returns: { search_id, search_term, skills: [{skill, count}, ...] }
    """
    try:
        # 1. Check if we already have this search
        existing_id = find_recent_search(req.search_term, req.country)
        if existing_id:
            print(f"Found existing search {existing_id} for '{req.search_term}'")
            skills = get_search_results(existing_id)
            return {
                "search_id": existing_id,
                "search_term": req.search_term,
                "country": req.country,
                "skills": skills,
            }

        # 2. If not, run the full pipeline
        all_results = []
        # Fetch 3 pages to get more jobs (approx 150 jobs)
        num_pages = 3
        
        for i in range(num_pages):
            current_page = req.page + i
            try:
                data = fetch_jobs(
                    page=current_page,
                    what=req.search_term,
                    results_per_page=req.results_per_page,
                    country=req.country,
                )
                page_results = data.get("results", [])
                all_results.extend(page_results)
                
                # If we got fewer results than requested, we probably reached the end
                if len(page_results) < req.results_per_page:
                    break
            except Exception as e:
                print(f"Error fetching page {current_page}: {e}")
                # If we have some results, we can continue, otherwise re-raise if it's the first page
                if not all_results:
                    raise e
                break

        # Combine results into a structure that matches what save_raw_results expects
        combined_data = {"results": all_results}

        raw_path = save_raw_results(combined_data, req.search_term)

        # Save parsed JSON (optional but nice for debugging)
        parsed_path = f"data/processed/parsed_jobs_{req.search_term.replace(' ', '_').lower()}.json"
        normalized_jobs = parse_raw_file(raw_path, parsed_path)

        # Write to DB
        search_id = create_job_search(req.search_term, req.country)
        upsert_search_skill_counts(search_id, normalized_jobs)

        # Read aggregated counts back (join to get skill names)
        skills = get_search_results(search_id)

        return {
            "search_id": search_id,
            "search_term": req.search_term,
            "country": req.country,
            "skills": skills,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/search/{search_id}")
def get_search(search_id: int):
    """
    Fetch previously computed results from Supabase without calling Adzuna again.
    """
    skills = get_search_results(search_id)
    return {"search_id": search_id, "skills": skills}
