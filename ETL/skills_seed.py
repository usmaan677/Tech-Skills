import os
from dotenv import load_dotenv
from supabase import create_client
from skills import SKILL_KEYWORDS

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)




def seed_skills():
    for skill in SKILL_KEYWORDS:
        supabase.table("skills").upsert(
            {"name": skill},
            on_conflict="name"
        ).execute()

if __name__ == "__main__":
    seed_skills()