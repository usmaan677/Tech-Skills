import json
from pathlib import Path
from collections import Counter

def get_latest_processed(pattern = "data/processed/*.json"):
    files = list(Path("data/processed").glob("*.json"))
    if not files:
        raise FileNotFoundError("There are no processed files to take a look at")
    
    files.sort(key=lambda p: p.stat().st_mtime)
    return files[-1]


def main():
    processed_path = get_latest_processed()
    print(f"Using processed file: {processed_path}")

    jobs = json.loads(processed_path.read_text(encoding="utf-8"))
    print(f"Loaded {len(jobs)} jobs.")

    skill_counter = Counter()
    title_counter = Counter()
    location_counter = Counter()

    for job in jobs:
        skills = job.get("skills") or []
        skill_counter.update(skills)

        location = job.get("location") or "Unknown"
        location_counter.update([location])


    print("\nTop 20 skills:")
    for skill,count in skill_counter.most_common(20):
        print(f"{skill:15} {count}")
    
    print(f"\nTop 10 locations:")
    for loc, count in location_counter.most_common(10):
        print(f"{loc:30} {count}")


if __name__ == "__main__":
    main()