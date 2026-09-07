import re

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

for skill, variants in SKILL_KEYWORDS.items():
    compiled = []
    for v in variants:
        pattern_text = rf"(?<!{BOUNDARY}){re.escape(v)}(?!{BOUNDARY})"
        compiled.append(re.compile(pattern_text, re.IGNORECASE))
    SKILL_PATTERNS[skill] = compiled


def extract_skills_from_description(description, patterns=SKILL_PATTERNS):
    if not description:
        return []

    found = set()
    for skill, pats in patterns.items():
        # any() short-circuits on the first varianops
        # after matching and never tries "reactjs" / "react.js".
        if any(p.search(description) for p in pats):
            found.add(skill)

    # Sorted so the output is deterministic - same input always produces the
    # same ordering, which keeps your parsed JSON s.
    return sorted(found)