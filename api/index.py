"""
FastAPI app, deployed as a Vercel Python serverless function.

Vercel's Python runtime looks for a module-level ASGI app named `app` in
files under api/, so this file's location and the name `app` both matter.

Run locally from the repo root:
    uvicorn api.index:app --reload --port 8000

Routes are prefixed /api so the path is identical in both places:
    local  http://localhost:8000/api/search
    prod   https://<project>.vercel.app/api/search
"""

import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from supabase import create_client

# Local dev reads ETL/.env. On Vercel there is no .env file - the variables
# come from the project's environment settings - so this quietly does nothing.
load_dotenv(Path(__file__).resolve().parent.parent / "ETL" / ".env")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
    raise RuntimeError("Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

app = FastAPI(title="Tech Skills API")

# In production the site and the API share an origin, so no CORS is needed.
# Locally the Vite dev server is on :5173 and this is on :8000, which is
# cross-origin - hence the default. Override with a comma-separated list.
ALLOWED_ORIGINS = [
    o.strip()
    for o in os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(",")
    if o.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class SearchRequest(BaseModel):
    search_term: str = Field(min_length=2, max_length=120)


@app.get("/api/health")
def health():
    return {"ok": True}


@app.get("/api/stats")
def stats():
    """
    Corpus totals for the masthead.

    Needs the corpus_stats() function in Postgres. If it isn't there this
    503s and the frontend just omits the corpus line - the page does not
    depend on it.
    """
    try:
        rows = supabase.rpc("corpus_stats", {}).execute().data or []
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"corpus_stats() unavailable: {e}")

    if not rows:
        raise HTTPException(status_code=503, detail="corpus_stats() returned no rows")

    return rows[0]


@app.post("/api/search")
def run_search(req: SearchRequest):
    """
    Aggregate skills across every stored posting whose title matches the term.

    No fetching happens here. The Greenhouse corpus is loaded offline by the
    daily GitHub Actions run, so this is one grouped query.
    """
    rows = supabase.rpc("search_skills", {"term": req.search_term}).execute().data or []

    return {
        "search_term": req.search_term,
        # Denominator: how many postings matched the title at all.
        "job_count": rows[0]["job_count"] if rows else 0,
        "skills": [{"skill": r["skill"], "count": r["mentions"]} for r in rows],
    }
