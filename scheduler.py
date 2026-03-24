"""
Entry point.

Usage:
  python scheduler.py                                   # run now + schedule daily 7AM
  python scheduler.py --once                            # run once, all companies
  python scheduler.py --once --limit 5                  # stop after 5 apply matches
  python scheduler.py --once --company stripe           # one company only
  python scheduler.py --once --company stripe --limit 3 # one company, 3 matches max
  python scheduler.py --once --company stripe notion    # multiple companies
"""
import sys, argparse
from datetime import datetime
from pipeline.scrape_and_score import scrape_and_score

def parse_args():
    p = argparse.ArgumentParser(description="Job Agent — Phase 1")
    p.add_argument("--once",    action="store_true", help="Run once and exit")
    p.add_argument("--limit",   type=int, default=None, help="Stop after N apply matches")
    p.add_argument("--company", nargs="+", default=None, help="Company slugs to scrape")
    return p.parse_args()

def run(limit=None, companies=None):
    print(f"\n{'='*60}")
    print(f"  Job Agent — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    if limit:     print(f"  Limit    : {limit} apply matches")
    if companies: print(f"  Companies: {', '.join(companies)}")
    print(f"{'='*60}\n")
    scrape_and_score(limit=limit, companies=companies)

if __name__ == "__main__":
    args = parse_args()
    if args.once:
        run(limit=args.limit, companies=args.company)
    else:
        run(limit=args.limit, companies=args.company)
        from apscheduler.schedulers.blocking import BlockingScheduler
        s = BlockingScheduler()
        s.add_job(run, "cron", hour=7, minute=0,
                  kwargs={"limit": args.limit, "companies": args.company})
        print("[Scheduler] Daily at 7:00 AM. Ctrl+C to stop.\n")
        try:
            s.start()
        except KeyboardInterrupt:
            print("\n[Scheduler] Stopped.")
