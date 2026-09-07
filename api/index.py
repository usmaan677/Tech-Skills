"""
FastAPI app, deployed as a Vercel Python serverless function.

Vercel's Python runtime looks for a module-level ASGI app named `app` in
files under api/, so this file's location and the name `app` both matter.

Run locally from the repo root:
    uvicorn api.index:app --reload --port 8000

Routes are prefixed /api so the path is identical in both places:
    local  http://localhost:8000/api/search
    prod   https://<project>.vercel.app/api/search

Nothing here touches the network or the environment at import time. A bad
config makes a request return a readable 503; it must never crash the module,
because a module that fails to import gives Vercel nothing to report but
FUNCTION_INVOCATION_FAILED.
"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from supabase import Client, create_client

# Local dev reads ETL/.env. On Vercel there is no .env file - the variables
# come from the project's environment settings - so this quietly does nothing.
load_dotenv(Path(__file__).resolve().parent.parent / "ETL" / ".env")


def _env(name: str) -> str:
    """
    Read a variable, tolerating whitespace.

    `KEY = value` in a .env file, or a value pasted into a dashboard field
    with a stray leading space, both arrive here with padding that would
    otherwise produce a malformed URL or a key that fails to authenticate.
    """
    return (os.getenv(name) or "").strip()


_client: Client | None = None


def db() -> Client:
    """
    Build the Supabase client on first use and reuse it afterwards.

    Lazy on purpose: a serverless container is reused across requests, so
    this cost is paid once per cold start, and a missing variable surfaces
    as a 503 on a request rather than an import-time crash.
    """
    global _client
    if _client is None:
        url, key = _env("SUPABASE_URL"), _env("SUPABASE_SERVICE_ROLE_KEY")
        if not url or not key:
            raise HTTPException(
                status_code=503,
                detail="Server is missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY.",
            )
        try:
            _client = create_client(url, key)
        except Exception as e:
            raise HTTPException(status_code=503, detail=f"Could not reach Supabase: {e}")
    return _client


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
    """
    Deployment diagnostics. Reports the shape of the config, never its values,
    so it is safe to hit from a browser on a public URL.
    """
    url = _env("SUPABASE_URL")
    key = _env("SUPABASE_SERVICE_ROLE_KEY")
    raw_url = os.getenv("SUPABASE_URL") or ""

    return {
        "ok": True,
        "python": sys.version.split()[0],
        "supabase_url_set": bool(url),
        "supabase_url_looks_valid": url.startswith("https://") and url.endswith(".supabase.co"),
        # True means the pasted value carried stray whitespace - the usual
        # cause of a URL that looks right in the dashboard but will not parse.
        "supabase_url_had_whitespace": raw_url != raw_url.strip(),
        "service_key_set": bool(key),
        "service_key_length": len(key),
        "allowed_origins": ALLOWED_ORIGINS,
    }


@app.get("/api/stats")
def stats():
    """
    Corpus totals for the masthead.

    Needs the corpus_stats() function in Postgres. If it isn't there this
    503s and the frontend just omits the corpus line - the page does not
    depend on it.
    """
    try:
        rows = db().rpc("corpus_stats", {}).execute().data or []
    except HTTPException:
        raise
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
    try:
        rows = db().rpc("search_skills", {"term": req.search_term}).execute().data or []
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"search_skills() failed: {e}")

    return {
        "search_term": req.search_term,
        # Denominator: how many postings matched the title at all.
        "job_count": rows[0]["job_count"] if rows else 0,
        "skills": [{"skill": r["skill"], "count": r["mentions"]} for r in rows],
    }
