import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

SKILLS = [
    "python",
    "java",
    "javascript",
    "typescript",
    "c++",
    "c#",
    "go",
    "rust",

    "react",
    "angular",
    "vue",
    "node",
    "express",
    "spring",
    "django",
    "flask",

    "sql",
    "postgres",
    "mysql",
    "mongodb",
    "redis",

    "aws",
    "azure",
    "gcp",
    "docker",
    "kubernetes",

    "spa",
    "microservices",
    "rest",
    "graphql",

    "pandas",
    "numpy",
    "pyspark",
    "spark",
    "hadoop",
]

def seed_skills():
    for skill in SKILLS:
        supabase.table("skills").upsert(
            {"name": skill},
            on_conflict="name"
        ).execute()

if __name__ == "__main__":
    seed_skills()