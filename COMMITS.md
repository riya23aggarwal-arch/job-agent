# Git commit guide

```bash
git init
git remote add origin https://github.com/YOUR_USERNAME/job-agent.git

# Commit 1 — skeleton
git add .gitignore .env.example requirements.txt README.md COMMITS.md
git add db/schema.sql db/init_db.py
git commit -m "chore: project skeleton"

# Commit 2 — config
git add config/
git commit -m "feat(config): greenhouse companies + pre-filter rules (USA only, no ML/data/frontend)"

# Commit 3 — scraper
git add scrapers/
git commit -m "feat(phase1): Greenhouse JSON API scraper with early title+location filter"

# Commit 4 — scorer (tested 10/10)
git add pipeline/static_scorer.py pipeline/__init__.py
git commit -m "feat(phase1): static scorer tailored to Riya's resume

- role_type 35%: systems/platform/SRE=high, ML/data/frontend=near-zero
- core_skills 30%: grouped (systems, python/auto, debug, tools)
- experience 20%: 5.2 yoe, open to new grad + senior
- location 10%: USA only, non-USA hard block
- seniority 5%: SWE/SWE-II/Senior preferred
- tested 10/10 cases passing"

# Commit 5 — pipeline
git add pipeline/scrape_and_score.py
git commit -m "feat(phase1): merged scrape+score loop with --limit and --company flags"

# Commit 6 — scheduler
git add scheduler.py
git commit -m "feat(phase1): scheduler with --once --limit --company flags"

git branch -M main
git push -u origin main
```
