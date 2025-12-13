import os
import json
from datetime import datetime
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()
ADZUNA_APP_ID = os.getenv("ADZUNA_APP_ID")
ADZUNA_APP_KEY = os.getenv("ADZUNA_APP_KEY")

BASE_URL = "https://api.adzuna.com/v1/api/jobs/ca/search"

def fetch_jobs(page = 1, what = "software engineer", results_per_page = 50,):
    params = {
        "app_id": ADZUNA_APP_ID,
        "app_key": ADZUNA_APP_KEY,
        "results_per_page": results_per_page,
        "what": what,
        "content-type": "application/json"
    }

    url = f"{BASE_URL}/{page}"
    resp = requests.get(url, params=params, timeout=15)

    if resp.status_code != 200:
        raise RuntimeError(f"Adzuna API error: {resp.status_code} - {resp.text}")
    
    return resp.json()

def save_raw_results(data, search_term):
    os.makedirs("data/raw",exist_ok=True)
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    safe_term = search_term.replace(" ", "_").lower()
    filename = f"data/raw/{safe_term}_jobs_{timestamp}.json"

    with open(filename, "w") as f:
        json.dump(data,f,ensure_ascii=False, indent =2)

    return filename
    

SKILL_KEYWORDS = {
    "python": ["python", "py"],
    "java": ["java"],
    "javascript": ["javascript", "js", "ecmascript"],
    "typescript": ["typescript", "ts"],
    "c++": ["c++", "cpp"],
    "c#": ["c#", "c-sharp", "c sharp"],
    "go": ["go", "golang"],
    "rust": ["rust"],

    "react": ["react", "reactjs", "react.js"],
    "angular": ["angular", "angularjs", "angular.js"],
    "vue": ["vue", "vuejs", "vue.js"],
    "node": ["node", "nodejs", "node.js"],
    "express": ["express", "expressjs", "express.js"],
    "spring": ["spring", "springboot", "spring boot"],
    "django": ["django"],
    "flask": ["flask"],

    "sql": ["sql"],
    "postgres": ["postgres", "postgresql", "psql"],
    "mysql": ["mysql"],
    "mongodb": ["mongodb", "mongo"],
    "redis": ["redis"],

    "aws": ["aws", "amazon web services"],
    "azure": ["azure", "microsoft azure"],
    "gcp": ["gcp", "google cloud", "google cloud platform"],
    "docker": ["docker"],
    "kubernetes": ["kubernetes", "k8s"],

    "spa": ["spa", "single page application"],
    "microservices": ["microservices", "microservice"],
    "rest": ["rest", "restful", "rest api"],
    "graphql": ["graphql", "graph ql"],

    "pandas": ["pandas"],
    "numpy": ["numpy", "np"],
    "pyspark": ["pyspark"],
    "spark": ["spark", "apache spark"],
    "hadoop": ["hadoop", "apache hadoop"],
}


def extract_skills_from_description(description, skills= SKILL_KEYWORDS):
    if not description:
        return[]
    
    text = description.lower()
    found = set()

    for skill, variants in skills.items():
        for v in variants:
            if v in text:
                found.add(skill)
                break
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

def parse_raw_file(path, out_path):

    os.makedirs(Path(out_path).parent, exist_ok=True)

    data = json.loads(Path(path).read_text())
    raw_results = data.get("results",[])


    normalized = [normalize_job(job) for job in raw_results]
    Path(out_path).write_text(json.dumps(normalized, ensure_ascii= False, indent = 2))

def main():
    if not ADZUNA_APP_ID or not ADZUNA_APP_KEY:
        raise RuntimeError("Missing ADZUNA_APP_ID or ADZUNA_APP_KEY in .env")
    
    search_term = "software engineer intern"
    page = 1

    data = fetch_jobs(page =page, what=search_term, results_per_page=50)
    raw_filename = save_raw_results(data,search_term)

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    processed_filename = f"data/processed/parsed_jobs_{timestamp}.json"
    parse_raw_file(raw_filename, processed_filename)

    results = data.get("results",[])

if __name__ == "__main__":
    main()

