"""
FastAPI app, deployed as a Vercel Python serverless function.

Vercel's Python runtime looks for a module-level ASGI app named `app` in
files under api/, so this file's location and the name `app` both matter.

Run locally from the repo root:
    uvicorn api.index:app --reload --port 8000

Routes are prefixed /api so the path is identical in both places:
    local  http://localhost:8000/api/search
    prod   https://<project>.vercel.app/api/search

IMPORT DISCIPLINE
Importing this module must not be able to fail. It needs only fastapi and
pydantic; supabase and dotenv are imported lazily inside the functions that
use them, and their absence is reported by /api/health rather than raised.
A module that fails to import gives Vercel nothing to show but
FUNCTION_INVOCATION_FAILED, with the real reason buried in the runtime log.
"""

# Keeps `X | None` style annotations from being evaluated at import time, so
# this file parses and runs on Python 3.9 as well as 3.12.
from __future__ import annotations

import os
import sys

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Local dev reads ETL/.env; on Vercel there is no .env file and the variables
# come from project settings. Guarded so a missing python-dotenv cannot break
# the deployment - it is only needed on a laptop.
_DOTENV_ERROR = None
try:
    from pathlib import Path

    from dotenv import load_dotenv

    load_dotenv(Path(__file__).resolve().parent.parent / "ETL" / ".env")
except Exception as e:  # pragma: no cover - local convenience only
    _DOTENV_ERROR = f"{type(e).__name__}: {e}"


def _env(name):
    """
    Read a variable, tolerating whitespace.

    `KEY = value` in a .env file, or a value pasted into a dashboard field
    with a stray leading space, both arrive here with padding that would
    otherwise produce a malformed URL or a key that fails to authenticate.
    """
    return (os.getenv(name) or "").strip()


_client = None


def db():
    """
    Build the Supabase client on first use and reuse it afterwards.

    The supabase import lives here rather than at module scope so that a
    dependency problem surfaces as a 503 with a real message instead of an
    import-time crash.
    """
    global _client
    if _client is None:
        try:
            from supabase import create_client
        except Exception as e:
            raise HTTPException(
                status_code=503, detail=f"supabase package unavailable: {type(e).__name__}: {e}"
            )

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
    Deployment diagnostics. Reports the shape of the config and which optional
    imports resolved - never any secret value - so it is safe on a public URL.
    """
    url = _env("SUPABASE_URL")
    key = _env("SUPABASE_SERVICE_ROLE_KEY")
    raw_url = os.getenv("SUPABASE_URL") or ""

    try:
        import supabase

        supabase_import = getattr(supabase, "__version__", "installed")
    except Exception as e:
        supabase_import = f"FAILED: {type(e).__name__}: {e}"

    return {
        "ok": True,
        "python": sys.version.split()[0],
        "supabase_import": supabase_import,
        "dotenv_error": _DOTENV_ERROR,
        "supabase_url_set": bool(url),
        "supabase_url_looks_valid": url.startswith("https://") and url.endswith(".supabase.co"),
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
