"""
Phase 1 — Scrape + Score loop.
Greenhouse only. Static scoring. Zero API cost.
Set USE_LLM_SCORING = True later for Claude API scoring.
"""
import sqlite3, json, os
from dotenv import load_dotenv
from scrapers.greenhouse import greenhouse_jobs
from pipeline.static_scorer import score_job

load_dotenv()

USE_LLM_SCORING = False

BASE_DIR    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH     = os.path.join(BASE_DIR, "db", "jobs.db")
FILTER_PATH = os.path.join(BASE_DIR, "config", "pre_filter.json")


def load_filter():
    with open(FILTER_PATH) as f:
        return json.load(f)

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def already_in_db(url):
    conn = get_db()
    row  = conn.execute("SELECT id FROM jobs WHERE url = ?", (url,)).fetchone()
    conn.close()
    return row is not None

def save_job(job):
    conn = get_db()
    conn.execute("""
        INSERT OR IGNORE INTO jobs
        (title, company, location, url, source, date_found, jd_text,
         score, decision, confidence,
         skills_score, experience_score, domain_score, location_score, seniority_score,
         matched_skills, missing_skills, red_flags, reasoning, status)
        VALUES
        (:title, :company, :location, :url, :source, :date_found, :jd_text,
         :score, :decision, :confidence,
         :skills_score, :experience_score, :domain_score, :location_score, :seniority_score,
         :matched_skills, :missing_skills, :red_flags, :reasoning, :status)
    """, job)
    conn.commit()
    conn.close()

def passes_jd_filter(job, rules):
    """Second filter after JD is fetched — checks location in JD text too."""
    jd       = job.get("jd_text", "")
    location = job.get("location", "").lower()
    jd_lower = jd.lower()

    # JD too short to be useful
    if len(jd) < 100:
        return False, "JD too short"

    # Non-USA explicit mentions in JD
    non_usa = ["must be located in canada", "must reside in india",
               "must be based in uk", "must be in germany",
               "this role is based in mexico", "this role is in japan"]
    if any(k in jd_lower for k in non_usa):
        return False, "Non-USA location in JD"

    return True, ""

def scrape_and_score(limit=None, companies=None):
    """
    Main loop.
    limit:     stop after N apply-queue matches
    companies: list of slugs (overrides config)
    """
    rules      = load_filter()
    thresholds = rules.get("score_thresholds", {"apply": 75, "review": 55})
    stats      = {"scraped": 0, "duplicate": 0, "jd_filtered": 0,
                  "scored": 0, "apply": 0, "review": 0, "skip": 0}

    for job in greenhouse_jobs(pre_filter=rules, companies=companies):
        stats["scraped"] += 1

        # check apply limit
        if limit and stats["apply"] >= limit:
            print(f"\n[Limit] Reached {limit} apply matches — stopping.")
            break

        # dedup
        if already_in_db(job["url"]):
            stats["duplicate"] += 1
            continue

        # JD-level filter (after fetch)
        passed, reason = passes_jd_filter(job, rules)
        if not passed:
            stats["jd_filtered"] += 1
            continue

        # score
        if USE_LLM_SCORING:
            from pipeline.llm_scorer import score_with_claude
            result = score_with_claude(job["jd_text"], thresholds)
        else:
            result = score_job(job, thresholds)

        stats["scored"] += 1
        b = result.get("breakdown", {})

        job.update({
            "score":           result["score"],
            "decision":        result["decision"],
            "confidence":      result.get("confidence"),
            "skills_score":    b.get("skills"),
            "experience_score":b.get("experience"),
            "domain_score":    b.get("role_type"),
            "location_score":  b.get("location"),
            "seniority_score": b.get("seniority"),
            "matched_skills":  ", ".join(result.get("matched_skills", [])),
            "missing_skills":  ", ".join(result.get("missing_skills", [])),
            "red_flags":       ", ".join(result.get("red_flags", [])),
            "reasoning":       result.get("reasoning", ""),
            "status":          result["decision"],
        })
        save_job(job)
        stats[result["decision"]] += 1

        # format output line
        flags = f" 🚩 {', '.join(result['red_flags'])}" if result.get("red_flags") else ""
        bkd   = result["breakdown"]
        print(
            f"[{result['decision'].upper():6}] "
            f"score={result['score']:3} | "
            f"skills={bkd['skills']:3} role={bkd['role_type']:3} "
            f"exp={bkd['experience']:3} loc={bkd['location']:3} | "
            f"{job['title']} @ {job['company']}"
            f"{flags}"
        )

        # trigger Phase 3 for apply-queue jobs
        if result["decision"] == "apply":
            try:
                from pipeline.generator import generate_package
                generate_package(job)
            except ImportError:
                pass  # Phase 3 not built yet
            except Exception as e:
                print(f"[ERROR] Package gen: {e}")

    print(f"""
{'='*60}
  DONE
  Scraped      : {stats['scraped']}
  Duplicates   : {stats['duplicate']}
  JD filtered  : {stats['jd_filtered']}
  Scored       : {stats['scored']}
  → APPLY      : {stats['apply']}
  → REVIEW     : {stats['review']}
  → SKIP       : {stats['skip']}
{'='*60}
""")
    return stats

if __name__ == "__main__":
    scrape_and_score()
