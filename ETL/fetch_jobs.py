import os
import json
from datetime import datetime
from pathlib import Path
from collections import Counter
from supabase import create_client
import re

import requests
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

ADZUNA_APP_ID = os.getenv("ADZUNA_APP_ID")
ADZUNA_APP_KEY = os.getenv("ADZUNA_APP_KEY")

BASE_URL = "https://api.adzuna.com/v1/api/jobs"

def fetch_jobs(page = 1, what = "software engineer", results_per_page = 50, country="ca"):
    params = {
        "app_id": ADZUNA_APP_ID,
        "app_key": ADZUNA_APP_KEY,
        "results_per_page": results_per_page,
        "what": what,
        "content-type": "application/json"
    }

    url = f"{BASE_URL}/{country}/search/{page}"
    resp = requests.get(url, params=params, timeout=15)

    if resp.status_code != 200:
        raise RuntimeError(f"Adzuna API error: {resp.status_code} - {resp.text}")
    
    return resp.json()

def create_job_search(search_term, country):
    resp = supabase.table("job_searches").insert({
        "search_term":search_term,
        "country": country or "ca"
    }).execute()
    return resp.data[0]["id"]

def get_skill_id_map():
    resp = supabase.table("skills").select("id,name").execute()
    rows = resp.data or []
    
    skill_map = {}

    for r in rows:
        name = r["name"] 
        skill_id = r["id"]
        skill_map[name] = skill_id
    
    return skill_map

def upsert_search_skill_counts(search_id, normalized_jobs):
    skill_id_map = get_skill_id_map()

    skill_counts = Counter()

    for job in normalized_jobs:
        skills = set(job.get("skills") or [] )
        for skill in skills:
            skill_counts[skill] += 1
    
    rows = []
    for skill,count in skill_counts.items():
        if skill in skill_id_map:
            rows.append({
                "search_id": search_id,
                "skill_id": skill_id_map[skill],
                "count":count
            })

    if rows:
        supabase.table("search_skill_counts").upsert(
            rows,
            on_conflict="search_id,skill_id"
        ).execute()


def save_raw_results(data, search_term):
    os.makedirs("data/raw",exist_ok=True)
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    safe_term = search_term.replace(" ", "_").lower()
    filename = f"data/raw/{safe_term}_jobs_{timestamp}.json"

    with open(filename, "w") as f:
        json.dump(data,f,ensure_ascii=False, indent =2)

    return filename
    

SKILL_KEYWORDS = {

    # =====================
    # Programming Languages
    # =====================
    "python": ["python"],
    "java": ["java"],
    "javascript": ["javascript", "ecmascript", "js"],
    "typescript": ["typescript", "ts"],
    "c++": ["c++", "cpp"],
    "c#": ["c#", "c-sharp", "c sharp"],
    "go": ["golang", "go"],
    "rust": ["rust"],
    "scala": ["scala"],
    "kotlin": ["kotlin"],
    "swift": ["swift"],
    "r": ["r language", "r programming"],
    "matlab": ["matlab"],
    "bash": ["bash", "shell scripting"],
    "powershell": ["powershell"],

    # =====================
    # Frontend
    # =====================
    "react": ["react", "reactjs", "react.js"],
    "nextjs": ["next.js", "nextjs"],
    "angular": ["angular", "angularjs"],
    "vue": ["vue", "vuejs"],
    "svelte": ["svelte"],
    "html": ["html", "html5"],
    "css": ["css", "css3"],
    "tailwind": ["tailwind", "tailwindcss"],
    "bootstrap": ["bootstrap"],
    "mui": ["material ui", "mui"],

    # =====================
    # Backend / APIs
    # =====================
    "node": ["node", "nodejs", "node.js"],
    "express": ["express", "expressjs"],
    "fastapi": ["fastapi"],
    "flask": ["flask"],
    "django": ["django"],
    "spring": ["spring", "spring boot", "springboot"],
    "dotnet": [".net", "dotnet"],
    "nestjs": ["nestjs"],
    "graphql": ["graphql"],
    "rest": ["rest", "rest api", "restful"],
    "grpc": ["grpc"],

    # =====================
    # Databases
    # =====================
    "sql": ["sql"],
    "postgres": ["postgres", "postgresql"],
    "mysql": ["mysql"],
    "sqlite": ["sqlite"],
    "mongodb": ["mongodb", "mongo"],
    "redis": ["redis"],
    "dynamodb": ["dynamodb"],
    "cassandra": ["cassandra"],
    "elasticsearch": ["elasticsearch"],
    "neo4j": ["neo4j"],

    # =====================
    # Data / Analytics
    # =====================
    "pandas": ["pandas"],
    "numpy": ["numpy"],
    "scipy": ["scipy"],
    "matplotlib": ["matplotlib"],
    "seaborn": ["seaborn"],
    "plotly": ["plotly"],
    "jupyter": ["jupyter", "jupyter notebook"],
    "excel": ["excel"],
    "tableau": ["tableau"],
    "powerbi": ["power bi", "powerbi"],
    "looker": ["looker"],

    # =====================
    # Big Data / Streaming
    # =====================
    "spark": ["spark", "apache spark"],
    "pyspark": ["pyspark"],
    "hadoop": ["hadoop"],
    "hive": ["hive"],
    "kafka": ["kafka", "apache kafka"],
    "airflow": ["airflow", "apache airflow"],
    "dbt": ["dbt"],
    "snowflake": ["snowflake"],
    "redshift": ["redshift"],
    "bigquery": ["bigquery"],
    "databricks": ["databricks"],

    # =====================
    # ML / AI
    # =====================
    "machine learning": ["machine learning", "ml"],
    "deep learning": ["deep learning"],
    "tensorflow": ["tensorflow"],
    "pytorch": ["pytorch"],
    "scikit-learn": ["scikit-learn", "sklearn"],
    "xgboost": ["xgboost"],
    "nlp": ["nlp", "natural language processing"],
    "computer vision": ["computer vision"],
    "llm": ["llm", "large language model"],
    "rag": ["rag", "retrieval augmented generation"],
    "openai": ["openai"],
    "huggingface": ["hugging face", "huggingface"],

    # =====================
    # Cloud Platforms
    # =====================
    "aws": ["aws", "amazon web services"],
    "azure": ["azure", "microsoft azure"],
    "gcp": ["gcp", "google cloud"],
    "firebase": ["firebase"],
    "supabase": ["supabase"],

    # =====================
    # DevOps / Infra
    # =====================
    "docker": ["docker"],
    "kubernetes": ["kubernetes", "k8s"],
    "terraform": ["terraform"],
    "ansible": ["ansible"],
    "ci/cd": ["ci/cd", "continuous integration", "continuous deployment"],
    "github actions": ["github actions"],
    "jenkins": ["jenkins"],
    "gitlab ci": ["gitlab ci"],
    "linux": ["linux"],
    "nginx": ["nginx"],

    # =====================
    # Testing / Quality
    # =====================
    "unit testing": ["unit testing"],
    "integration testing": ["integration testing"],
    "pytest": ["pytest"],
    "jest": ["jest"],
    "cypress": ["cypress"],
    "selenium": ["selenium"],

    # =====================
    # Architecture / Concepts
    # =====================
    "microservices": ["microservices", "microservice"],
    "monolith": ["monolith"],
    "event-driven": ["event-driven", "event driven"],
    "distributed systems": ["distributed systems"],
    "system design": ["system design"],
    "scalability": ["scalability", "scalable"],
    "high availability": ["high availability"],
    "fault tolerance": ["fault tolerant", "fault tolerance"],
    "api design": ["api design"],
    "data pipelines": ["data pipeline", "etl", "elt"],
    "data warehousing": ["data warehouse", "data warehousing"],

    # =====================
    # Security
    # =====================
    "authentication": ["authentication", "auth"],
    "authorization": ["authorization"],
    "oauth": ["oauth", "oauth2"],
    "jwt": ["jwt", "json web token"],
    "encryption": ["encryption"],
}


BOUNDARY = r"[A-Za-z0-9_+#]"
SKILL_PATTERNS = {}

for skill, variants in SKILL_KEYWORDS.items():   # ← the OUTER for
    compiled = []
    for v in variants:                           # ← the INNER for
        pattern_text = rf"(?<!{BOUNDARY}){re.escape(v)}(?!{BOUNDARY})"
        compiled.append(re.compile(pattern_text, re.IGNORECASE))
    SKILL_PATTERNS[skill] = compiled


def extract_skills_from_description(description, patterns=SKILL_PATTERNS):
    if not description:
        return []

    found = set()
    for skill, pats in patterns.items():
        if any(p.search(description) for p in pats):
            found.add(skill)

    return sorted(found)

def normalize_job(raw_job):
    desc = raw_job.get("description", "") or ""
    location = raw_job.get("location", {}) or {}
    company = raw_job.get("company", {}) or {}
    category = raw_job.get("category", {}) or {}

    return{
        "id": raw_job.get("id"),
        "title": raw_job.get("title"),
        "company": company.get("display_name"),
        "location": location.get("display_name"),
        "created": raw_job.get("created"),
        "category": category.get("label"),
        "description": desc,
        "skills": extract_skills_from_description(desc),
    }

def _dedupe_key(job):
    """Identity of a job opening, ignoring cosmetic differences."""
    title = re.sub(r"\s+", " ", (job.get("title") or "")).strip().lower()
    company = re.sub(r"\s+", " ", (job.get("company") or "")).strip().lower()
    return (title, company)

def dedupe_jobs(jobs):
    """
    Collapse syndicated re-posts of the same opening.

    Adzuna gives every syndicated copy its own id, so one posting blasted
    across 85 cities arrives as 85 rows. Counting those separately lets a
    single employer dominate the skill counts, so we key on content
    (title + company) rather than on the id.

    Keeps the copy with the longest description and records how many raw
    rows collapsed into it as `posting_count`.
    """
    kept = {}

    for job in jobs:
        key = _dedupe_key(job)
        existing = kept.get(key)

        if existing is None:
            job = dict(job)
            job["posting_count"] = 1
            kept[key] = job
            continue

        existing["posting_count"] += 1

        if len(job.get("description") or "") > len(existing.get("description") or ""):
            promoted = dict(job)
            promoted["posting_count"] = existing["posting_count"]
            kept[key] = promoted

    return list(kept.values())


def parse_raw_file(path, out_path):

    os.makedirs(Path(out_path).parent, exist_ok=True)

    data = json.loads(Path(path).read_text())
    raw_results = data.get("results",[])


    normalized = [normalize_job(job) for job in raw_results]
    normalized = dedupe_jobs(normalized)
    Path(out_path).write_text(json.dumps(normalized, ensure_ascii= False, indent = 2))
    return normalized

def main():
    if not ADZUNA_APP_ID or not ADZUNA_APP_KEY:
        raise RuntimeError("Missing ADZUNA_APP_ID or ADZUNA_APP_KEY in .env")
    
    search_term = "software engineer intern"
    country = "ca"
    
    all_results = []
    num_pages = 3
    
    for i in range(num_pages):
        page = 1 + i
        print(f"Fetching page {page}...")
        try:
            data = fetch_jobs(page=page, what=search_term, results_per_page=50, country=country)
            results = data.get("results", [])
            all_results.extend(results)
            if len(results) < 50:
                break
        except Exception as e:
            print(f"Error on page {page}: {e}")
            break

    combined_data = {"results": all_results}
    raw_filename = save_raw_results(combined_data, search_term)

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    processed_filename = f"data/processed/parsed_jobs_{timestamp}.json"
    normalized_jobs = parse_raw_file(raw_filename, processed_filename)
    
    search_id = create_job_search(search_term, country)
    upsert_search_skill_counts(search_id, normalized_jobs)

    print(f"Done. Processed {len(normalized_jobs)} jobs.")

if __name__ == "__main__":
    main()

