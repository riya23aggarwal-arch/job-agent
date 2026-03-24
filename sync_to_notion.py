"""
sync_to_notion.py — syncs jobs.db results into your Notion Job Tracker database.
Run from inside job-agent/ folder:
  python sync_to_notion.py                  # sync apply + review jobs
  python sync_to_notion.py --decision apply # sync only apply jobs
  python sync_to_notion.py --all            # sync everything including skips

Requires:
  pip install anthropic requests
  ANTHROPIC_API_KEY in .env (not actually used here, but .env is loaded)
  NOTION_TOKEN in .env  ← add this: your Notion integration token
"""

import sqlite3, json, os, sys, argparse, requests
from dotenv import load_dotenv

load_dotenv()

DB_PATH          = os.path.join(os.path.dirname(__file__), "db", "jobs.db")
NOTION_TOKEN     = os.environ.get("NOTION_TOKEN", "")
NOTION_DB_ID     = "5a9fb78bda2482f4abcf01520b5e5da8"  # your Job Tracker DB
NOTION_API       = "https://api.notion.com/v1"
HEADERS          = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28",
}


def get_jobs(decision_filter=None):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    if decision_filter:
        rows = conn.execute(
            "SELECT * FROM jobs WHERE decision = ? ORDER BY score DESC",
            (decision_filter,)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM jobs WHERE decision IN ('apply','review') ORDER BY score DESC"
        ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_existing_urls():
    """Fetch all URLs already in Notion DB to avoid duplicates."""
    existing = set()
    url  = f"{NOTION_API}/databases/{NOTION_DB_ID}/query"
    body = {"page_size": 100}
    while True:
        r = requests.post(url, headers=HEADERS, json=body)
        data = r.json()
        for page in data.get("results", []):
            props = page.get("properties", {})
            u = props.get("URL", {}).get("url", "")
            if u:
                existing.add(u)
        if not data.get("has_more"):
            break
        body["start_cursor"] = data["next_cursor"]
    return existing


def build_notion_page(job: dict) -> dict:
    """Build Notion page properties from job dict."""
    def text(val):
        return {"rich_text": [{"text": {"content": str(val or "")[:2000]}}]}

    def num(val):
        return {"number": int(val) if val is not None else None}

    return {
        "Job Title":     {"title": [{"text": {"content": str(job.get("title", ""))}}]},
        "Company":       text(job.get("company", "").capitalize()),
        "Score":         num(job.get("score")),
        "Decision":      {"select": {"name": job.get("decision", "skip")}},
        "Location":      text(job.get("location", "")),
        "Matched Skills":text(job.get("matched_skills", "")),
        "Missing Skills":text(job.get("missing_skills", "")),
        "Red Flags":     text(job.get("red_flags", "")),
        "Role Score":    num(job.get("domain_score")),
        "Skills Score":  num(job.get("skills_score")),
        "Exp Score":     num(job.get("experience_score")),
        "Status":        {"select": {"name": "new"}},
        "URL":           {"url": job.get("url", "") or None},
        "Date Found":    {"date": {"start": job.get("date_found", "")} if job.get("date_found") else None},
    }


def create_notion_page(job: dict):
    payload = {
        "parent": {"database_id": NOTION_DB_ID},
        "properties": build_notion_page(job),
    }
    r = requests.post(f"{NOTION_API}/pages", headers=HEADERS, json=payload)
    if r.status_code == 200:
        return True, None
    return False, r.text


def main():
    parser = argparse.ArgumentParser(description="Sync jobs.db to Notion Job Tracker")
    parser.add_argument("--decision", choices=["apply", "review", "skip"], default=None)
    parser.add_argument("--all", action="store_true", help="Sync all decisions")
    args = parser.parse_args()

    if not NOTION_TOKEN:
        print("ERROR: NOTION_TOKEN not set in .env")
        print("Get your token from: https://www.notion.so/profile/integrations")
        print("Add to .env:  NOTION_TOKEN=secret_xxxx")
        sys.exit(1)

    decision = None if args.all else args.decision
    jobs = get_jobs(decision)
    print(f"Found {len(jobs)} jobs to sync...")

    existing = get_existing_urls()
    print(f"Already in Notion: {len(existing)} jobs")

    synced  = 0
    skipped = 0
    failed  = 0

    for job in jobs:
        url = job.get("url", "")
        if url in existing:
            skipped += 1
            continue

        ok, err = create_notion_page(job)
        if ok:
            synced += 1
            print(f"  ✓ {job['decision'].upper():6} score={job.get('score','?'):3} | {job['title']} @ {job['company']}")
        else:
            failed += 1
            print(f"  ✗ FAILED: {job['title']} — {err[:100]}")

    print(f"""
{'='*50}
  Synced  : {synced}
  Skipped : {skipped} (already in Notion)
  Failed  : {failed}
{'='*50}
""")
    if synced > 0:
        print(f"View results: https://www.notion.so/5a9fb78bda2482f4abcf01520b5e5da8")


if __name__ == "__main__":
    main()
