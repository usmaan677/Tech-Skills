import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

SKILLS = [
    # Programming Languages
    "python",
    "java",
    "javascript",
    "typescript",
    "c++",
    "c#",
    "go",
    "rust",
    "scala",
    "kotlin",
    "swift",
    "r",
    "matlab",
    "bash",
    "powershell",

    # Frontend
    "react",
    "nextjs",
    "angular",
    "vue",
    "svelte",
    "html",
    "css",
    "tailwind",
    "bootstrap",
    "mui",

    # Backend / APIs
    "node",
    "express",
    "fastapi",
    "flask",
    "django",
    "spring",
    "dotnet",
    "nestjs",
    "graphql",
    "rest",
    "grpc",

    # Databases
    "sql",
    "postgres",
    "mysql",
    "sqlite",
    "mongodb",
    "redis",
    "dynamodb",
    "cassandra",
    "elasticsearch",
    "neo4j",

    # Data / Analytics
    "pandas",
    "numpy",
    "scipy",
    "matplotlib",
    "seaborn",
    "plotly",
    "jupyter",
    "excel",
    "tableau",
    "powerbi",
    "looker",

    # Big Data / Streaming
    "spark",
    "pyspark",
    "hadoop",
    "hive",
    "kafka",
    "airflow",
    "dbt",
    "snowflake",
    "redshift",
    "bigquery",
    "databricks",

    # ML / AI
    "machine learning",
    "deep learning",
    "tensorflow",
    "pytorch",
    "scikit-learn",
    "xgboost",
    "nlp",
    "computer vision",
    "llm",
    "rag",
    "openai",
    "huggingface",

    # Cloud Platforms
    "aws",
    "azure",
    "gcp",
    "firebase",
    "supabase",

    # DevOps / Infra
    "docker",
    "kubernetes",
    "terraform",
    "ansible",
    "ci/cd",
    "github actions",
    "jenkins",
    "gitlab ci",
    "linux",
    "nginx",

    # Testing / Quality
    "unit testing",
    "integration testing",
    "pytest",
    "jest",
    "cypress",
    "selenium",

    # Architecture / Concepts
    "microservices",
    "monolith",
    "event-driven",
    "distributed systems",
    "system design",
    "scalability",
    "high availability",
    "fault tolerance",
    "api design",
    "data pipelines",
    "data warehousing",

    # Security
    "authentication",
    "authorization",
    "oauth",
    "jwt",
    "encryption",
]


def seed_skills():
    for skill in SKILLS:
        supabase.table("skills").upsert(
            {"name": skill},
            on_conflict="name"
        ).execute()

if __name__ == "__main__":
    seed_skills()