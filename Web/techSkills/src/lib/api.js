/**
 * Every network call the frontend makes lives here. Nothing else in src/
 * touches fetch(), so this file is the whole API surface.
 *
 * Backend: ETL/main.py (FastAPI), default http://localhost:8000
 */

// Falls back to localhost so the app still runs if .env.local is missing.
const API_BASE = import.meta.env.VITE_API_BASE?.trim() || "http://localhost:8000";

/** Thrown for any non-2xx response, carrying the status for the UI to branch on. */
export class ApiError extends Error {
  constructor(message, status) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

async function request(path, { signal, ...init } = {}) {
  let resp;
  try {
    resp = await fetch(`${API_BASE}${path}`, {
      headers: { "Content-Type": "application/json" },
      signal,
      ...init,
    });
  } catch (err) {
    // AbortError means we cancelled it deliberately; let the caller ignore it.
    if (err?.name === "AbortError") throw err;
    throw new ApiError(`Can't reach the API at ${API_BASE}.`, 0);
  }

  if (!resp.ok) {
    // FastAPI puts a human-readable reason in `detail` for both HTTPException
    // and 422 validation errors, so prefer it over the raw status line.
    let detail = "";
    try {
      const body = await resp.json();
      detail = typeof body?.detail === "string" ? body.detail : "";
    } catch {
      /* non-JSON error body; fall through to the status code */
    }
    throw new ApiError(detail || `Request failed (HTTP ${resp.status}).`, resp.status);
  }

  return resp.json();
}

/**
 * POST /search — aggregate skills across every stored posting whose title
 * matches `term`. One grouped query against the search_skills() RPC; no
 * fetching happens at request time.
 *
 * Returns { search_term, job_count, skills: [{ skill, count }] }
 * where `count` is how many of those `job_count` postings mention the skill.
 */
export function searchSkills(term, { signal } = {}) {
  return request("/search", {
    method: "POST",
    body: JSON.stringify({ search_term: term }),
    signal,
  });
}

/**
 * GET /stats — corpus totals for the masthead. Optional: the UI renders
 * fine without it, so callers should swallow failures rather than surface them.
 *
 * Returns { job_count, company_count, skill_count, last_fetched }
 */
export function getCorpusStats({ signal } = {}) {
  return request("/stats", { signal });
}
