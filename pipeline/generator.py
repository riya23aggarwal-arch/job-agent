"""
Phase 3 — Application package generation.
Reads apply-queue jobs from DB, builds package from profile.json + base_resume.txt.

TODOs (Claude API integration later):
  - TODO: generate tailored resume summary via Claude API
  - TODO: generate cover letter via Claude API
  - TODO: generate "why this company" answer via Claude API + web search
  - TODO: send email alert after package is ready
"""
import sqlite3, json, os, re
from dotenv import load_dotenv

load_dotenv()

BASE_DIR     = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH      = os.path.join(BASE_DIR, "db", "jobs.db")
RESUME_PATH  = os.path.join(BASE_DIR, "base_resume.txt")
PROFILE_PATH = os.path.join(BASE_DIR, "profile.json")
APP_DIR      = os.path.join(BASE_DIR, "applications")

DEFAULT_PROFILE = {
    "name":               {"first": "Riya", "last": "Aggarwal"},
    "email":              "riya23aggarwal@gmail.com",
    "phone":              "+18318694225",
    "location":           "San Jose, CA",
    "linkedin":           "https://linkedin.com/in/ragrwl",
    "work_authorization": "Authorized to work in the United States",
    "require_sponsorship":"No",
    "start_date":         "Immediately",
    "salary_expectation": "Open to discussion based on total compensation",
    "years_of_experience":"5",
    "eeo": {
        "gender":    "Decline to self-identify",
        "ethnicity": "Decline to self-identify",
        "veteran":   "I am not a protected veteran",
        "disability":"I don't wish to answer"
    }
}

def load_profile():
    if os.path.exists(PROFILE_PATH):
        with open(PROFILE_PATH) as f:
            return json.load(f)
    return DEFAULT_PROFILE

def load_resume():
    if os.path.exists(RESUME_PATH):
        with open(RESUME_PATH) as f:
            return f.read()
    return ""

def save_package(job, profile, resume):
    os.makedirs(APP_DIR, exist_ok=True)
    slug = re.sub(r'[^a-z0-9]+', '_',
                  f"{job.get('company','')}_{job.get('title','')}".lower())[:60]
    path = os.path.join(APP_DIR, f"{slug}.json")

    name = profile.get("name", {})
    package = {
        "job_id":   job.get("id"),
        "title":    job.get("title"),
        "company":  job.get("company"),
        "location": job.get("location"),
        "url":      job.get("url"),
        "score":    job.get("score"),
        "generated": {
            "resume_summary": "TODO: generate via Claude API",
            "cover_letter":   "TODO: generate via Claude API",
            "why_company":    "TODO: generate via Claude API + web search",
        },
        "standard_answers": {
            "first_name":          name.get("first", ""),
            "last_name":           name.get("last", ""),
            "email":               profile.get("email", ""),
            "phone":               profile.get("phone", ""),
            "location":            profile.get("location", ""),
            "linkedin":            profile.get("linkedin", ""),
            "work_authorization":  profile.get("work_authorization", ""),
            "require_sponsorship": profile.get("require_sponsorship", "No"),
            "start_date":          profile.get("start_date", "Immediately"),
            "salary_expectation":  profile.get("salary_expectation", ""),
            "years_of_experience": profile.get("years_of_experience", ""),
        },
        "eeo":    profile.get("eeo", DEFAULT_PROFILE["eeo"]),
        "resume": resume,
        "status": "ready"
    }

    with open(path, "w") as f:
        json.dump(package, f, indent=2)
    return path

def update_db(job_id, path):
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "UPDATE jobs SET package_path=?, status='package_ready' WHERE id=?",
        (path, job_id)
    )
    conn.commit()
    conn.close()

def generate_package(job):
    """Called by scrape_and_score.py when a job hits apply queue."""
    profile = load_profile()
    resume  = load_resume()
    path    = save_package(job, profile, resume)
    if job.get("id"):
        update_db(job["id"], path)
    print(f"[Phase 3] ✓ {path}")
    return path

def generate_all_pending():
    """Standalone — generate packages for all apply jobs without one."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    jobs = conn.execute(
        "SELECT * FROM jobs WHERE decision='apply' "
        "AND (package_path IS NULL OR package_path='') ORDER BY score DESC"
    ).fetchall()
    conn.close()

    if not jobs:
        print("[Phase 3] No pending jobs.")
        return

    profile = load_profile()
    resume  = load_resume()
    print(f"[Phase 3] Generating {len(jobs)} packages...")

    for job in [dict(j) for j in jobs]:
        print(f"  {job['title']} @ {job['company']} (score={job['score']})")
        path = save_package(job, profile, resume)
        update_db(job["id"], path)
        print(f"  ✓ {path}")

    print("\n[Phase 3] Done. Check applications/ folder.")

if __name__ == "__main__":
    generate_all_pending()
