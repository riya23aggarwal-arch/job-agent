import requests
from bs4 import BeautifulSoup
from datetime import datetime
import time, json, os

COMPANIES_PATH = os.path.join(os.path.dirname(__file__), "..", "config", "greenhouse_companies.json")
BASE_URL       = "https://boards-api.greenhouse.io/v1/boards/{slug}/jobs"
JOB_URL        = "https://boards-api.greenhouse.io/v1/boards/{slug}/jobs/{job_id}"
HEADERS        = {"User-Agent": "Mozilla/5.0 (compatible; job-agent/1.0)"}

def load_companies():
    with open(COMPANIES_PATH) as f:
        return json.load(f)

def clean_html(html):
    return BeautifulSoup(html or "", "html.parser").get_text(separator="\n").strip()

def fetch_company_jobs(slug):
    try:
        r = requests.get(BASE_URL.format(slug=slug), headers=HEADERS, timeout=10)
        r.raise_for_status()
        return r.json().get("jobs", [])
    except requests.exceptions.HTTPError:
        code = r.status_code if r else "?"
        print(f"[Greenhouse] {'Not found' if code==404 else f'HTTP {code}'}: {slug}")
        return []
    except Exception as e:
        print(f"[Greenhouse] Error {slug}: {e}")
        return []

def fetch_jd(slug, job_id):
    try:
        r = requests.get(JOB_URL.format(slug=slug, job_id=job_id), headers=HEADERS, timeout=10)
        r.raise_for_status()
        return clean_html(r.json().get("content", ""))
    except Exception as e:
        print(f"[Greenhouse] JD fetch error {job_id}: {e}")
        return ""

def greenhouse_jobs(pre_filter=None, companies=None):
    """
    Generator — yields one job at a time.
    Applies title + location pre-filter BEFORE fetching JD to save HTTP calls.
    """
    slugs = companies if companies else load_companies()
    print(f"[Greenhouse] Scraping {len(slugs)} companies...")

    for slug in slugs:
        jobs = fetch_company_jobs(slug)
        total   = len(jobs)
        passed  = 0
        skipped = 0

        for job in jobs:
            title    = job.get("title", "").strip()
            location = job.get("location", {}).get("name", "").strip()
            t_lower  = title.lower()
            l_lower  = location.lower()

            # ── title pre-filter (no JD fetch yet) ──
            if pre_filter:
                inc = pre_filter.get("title_must_include", [])
                blk = pre_filter.get("title_blocklist", [])
                if inc and not any(k in t_lower for k in inc):
                    skipped += 1
                    continue
                if any(b in t_lower for b in blk):
                    skipped += 1
                    continue

            # ── location pre-filter: USA only ──
            if pre_filter and location:
                usa = pre_filter.get("locations_usa_only", [])
                if usa and not any(u in l_lower for u in usa):
                    skipped += 1
                    continue

            # ── passed — now fetch full JD ──
            passed += 1
            jd = fetch_jd(slug, job.get("id"))
            print(f"[{slug}] ({passed}) {title} | {location or 'no location'}")

            yield {
                "title":      title,
                "company":    slug,
                "location":   location,
                "url":        job.get("absolute_url", "").strip(),
                "source":     "greenhouse",
                "date_found": datetime.utcnow().strftime("%Y-%m-%d"),
                "jd_text":    jd,
            }
            time.sleep(0.3)

        print(f"[Greenhouse] {slug}: {passed}/{total} passed filter, {skipped} skipped")
        time.sleep(1)
