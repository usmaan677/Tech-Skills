# Tech-Skills

A data pipeline that answers a simple question: **which skills are employers actually asking for right now?**

Tech-Skills pulls live job postings from the [Adzuna API](https://developer.adzuna.com/), extracts the technical skills mentioned in each description, and aggregates them into per-skill and per-location counts stored in Supabase. A companion analysis script ranks the most in-demand skills and top hiring locations, and a React + Vite frontend (with a FastAPI service) surfaces the results in the browser.

## How it works

The core is a classic **ETL pipeline**:

1. **Extract** — `fetch_jobs.py` queries the Adzuna jobs API for a given search term (e.g. `software engineer intern`) and country, and saves the raw response to `data/raw/`.
2. **Transform** — each posting is normalized to a consistent shape (title, company, location, category, description) and run through a keyword matcher that detects known skills in the description. The normalized records are written to `data/processed/`.
3. **Load** — skill counts are aggregated per search and upserted into Supabase tables (`job_searches`, `skills`, `search_skill_counts`), so results accumulate across runs.
4. **Analyze** — `analyze_skills.py` reads the latest processed file and prints the top 20 skills and top 10 hiring locations.

Skill detection is driven by a keyword dictionary covering languages (Python, Java, JavaScript, TypeScript, C++, C#, Go, Rust), frameworks (React, Angular, Vue, Node, Express, Spring, Django, Flask), databases (SQL, Postgres, MySQL, MongoDB, Redis), cloud & infra (AWS, Azure, GCP, Docker, Kubernetes), and data tools (pandas, NumPy, Spark, Hadoop, PySpark).

## Architecture

```
Adzuna API
    │  (fetch_jobs.py)
    ▼
data/raw/*.json            ← raw API responses
    │  normalize + extract skills
    ▼
data/processed/*.json      ← cleaned, skill-tagged postings
    │
    ├──► Supabase (job_searches, skills, search_skill_counts)
    │
    └──► analyze_skills.py  ← top skills & locations
              │
              ▼
        Web/ (React + Vite frontend, FastAPI service)
```

## Project structure

```
Tech-Skills/
├── ETL/
│   ├── fetch_jobs.py       # Extract from Adzuna, normalize, load counts into Supabase
│   ├── analyze_skills.py   # Rank top skills and locations from processed data
│   ├── skills_seed.py      # Seed the skills reference table
│   └── data/
│       ├── raw/            # Raw Adzuna responses
│       └── processed/      # Normalized, skill-tagged postings
└── Web/                    # React + Vite frontend (FastAPI service)
```

## Getting started

### Prerequisites

- Python 3.10+
- A free [Adzuna API](https://developer.adzuna.com/) app ID and key
- A [Supabase](https://supabase.com/) project (URL + service role key)
- Node.js 18+ (for the web frontend)

### 1. Configure environment

Create a `.env` file in the `ETL/` directory:

```env
ADZUNA_APP_ID=your-adzuna-app-id
ADZUNA_APP_KEY=your-adzuna-app-key
SUPABASE_URL=your-supabase-url
SUPABASE_SERVICE_ROLE_KEY=your-supabase-service-role-key
```

### 2. Install dependencies

```bash
cd ETL
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install requests supabase python-dotenv
```

### 3. Seed the skills table

```bash
python skills_seed.py
```

### 4. Run the pipeline

```bash
python fetch_jobs.py
```

This fetches a batch of postings, saves the raw and processed JSON, and upserts skill counts into Supabase.

### 5. Analyze the results

```bash
python analyze_skills.py
```

Example output:

```
Top 20 skills:
python          42
aws             31
react           28
sql             25
...

Top 10 locations:
Toronto, ON     18
Vancouver, BC   12
...
```

## Tech stack

**Data / Backend:** Python, Adzuna API, Supabase (Postgres), FastAPI
**Frontend:** React, Vite
**Libraries:** requests, supabase-py, python-dotenv

## Roadmap

- Web dashboard to visualize skill trends over time
- Support for multiple search terms and countries in a single run
- Scheduled runs to build a historical trend dataset

---

*Built by [Usmaan Sayed](https://github.com/usmaan677).*
