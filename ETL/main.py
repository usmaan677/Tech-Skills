import os
from dotenv import load_dotenv

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from supabase import create_client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
    raise RuntimeError("Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY in .env")

supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

app = FastAPI(title="Tech Skills API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite default
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class SearchRequest(BaseModel):
    search_term: str = Field(min_length=2, max_length=120)


@app.get("/health")
def health():
    return {"ok": True}


@app.get("/stats")
def stats():
    """
    Corpus totals for the masthead.

    Needs the corpus_stats() function in Postgres (see README). If it isn't
    there yet this 503s, and the frontend just omits the corpus line - the
    page does not depend on it.
    """
    try:
        rows = supabase.rpc("corpus_stats", {}).execute().data or []
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"corpus_stats() unavailable: {e}")

    if not rows:
        raise HTTPException(status_code=503, detail="corpus_stats() returned no rows")

    return rows[0]


@app.post("/search")
def run_search(req: SearchRequest):
    """
    Aggregate skills across every stored posting whose title matches the term.

    No fetching happens here. The Greenhouse corpus is loaded offline by
    load_jobs.py, so this is one grouped query - which is why the request-time
    caching the Adzuna version needed is gone.
    """
    rows = supabase.rpc("search_skills", {"term": req.search_term}).execute().data or []

    return {
        "search_term": req.search_term,
        # Denominator: how many postings matched the title at all.
        "job_count": rows[0]["job_count"] if rows else 0,
        "skills": [{"skill": r["skill"], "count": r["mentions"]} for r in rows],
    }
