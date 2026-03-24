"""
Static job scorer — built precisely for Riya Aggarwal's resume.

WHO RIYA IS:
  - Systems/platform engineer: Linux kernel, firmware, device drivers, BSP, C
  - Python automation engineer: PyATS, Pytest, shell scripting
  - Debugger/tools engineer: GDB, ADB, log analysis, root cause analysis
  - 5.2 years total (Cognizant/Google AR-VR, Cisco x2) — left Cognizant March 2026
  - MS CS UC Santa Cruz 2025 — open to new grad AND senior roles
  - San Jose CA — Bay Area, Remote, Hybrid, USA only

SCORING DIMENSIONS (weights sum to 1.0):
  role_type    35%  — is this the RIGHT kind of engineering role?
  core_skills  30%  — do her actual skills match the JD?
  experience   20%  — does YOE fit?
  location     10%  — USA only
  seniority     5%  — level fit
"""
import re

YOUR_YOE = 5.2

# ── Skill groups: broad keyword clusters so JD phrasing variations still match ──

SKILLS_SYSTEMS = [
    # Linux & kernel
    "linux", "kernel", "linux kernel", "linux internals", "linux system",
    "linux-based", "unix", "posix",
    # Boot & runtime
    "boot", "bsp", "platform initialization", "bring-up", "bringup",
    "bootloader", "u-boot", "uefi", "bios",
    # Firmware & drivers
    "firmware", "device driver", "driver development", "embedded system", "embedded software",
    "hardware bring", "fpga", "fpd",
    # Low-level
    "memory management", "multithreading", "concurrency", "ipc",
    "interrupt", "dma", "hardware abstraction",
]

SKILLS_PYTHON_AUTO = [
    "python", "pytest", "pyats", "automation", "shell script",
    "bash", "shell scripting", "scripting",
    "automated test", "test automation", "regression test",
    "test framework", "test infrastructure",
]

SKILLS_DEBUG = [
    "debugging", "debug", "gdb", "adb", "root cause",
    "failure triage", "triage", "log analysis", "log parsing",
    "troubleshoot", "postmortem", "incident",
]

SKILLS_TOOLS = [
    "git", "build system", "makefile", "cmake", "bazel",
    "ci/cd", "jenkins", "github actions",
]

# Bonus: in resume indirectly, worth partial credit
BONUS_SKILLS = [
    "docker", "kubernetes", "aws", "gcp", "cloud",
    "distributed system", "api", "rest api",
    "networking", "ethernet", "tcp", "protocol",
    "c programming", " c ", "c++",
]

ALL_CORE_GROUPS = [SKILLS_SYSTEMS, SKILLS_PYTHON_AUTO, SKILLS_DEBUG, SKILLS_TOOLS]

# ── Role type: title + JD signals ────────────────────────────────────────
ROLE_STRONG_TITLES = [
    "platform engineer", "systems engineer", "systems software",
    "infrastructure engineer", "embedded engineer", "firmware engineer",
    "linux engineer", "kernel engineer", "bsp engineer",
    "automation engineer", "tools engineer", "test engineer",
    "site reliability engineer", "sre", "production engineer",
    "driver engineer", "hardware software",
]

ROLE_OK_TITLES = [
    "software engineer", "backend engineer", "python engineer",
    "devops", "build engineer", "release engineer",
    "developer tools", "tooling", "performance engineer",
    "network engineer", "storage engineer",
]

ROLE_WRONG_TITLES = [
    "machine learning engineer", "ml engineer", "ai engineer",
    "data engineer", "data scientist", "research engineer",
    "research scientist", "data platform",
    "frontend", "full stack", "web engineer",
    "mobile engineer", "ios", "android",
]

# JD body signals (check opening 800 chars)
JD_STRONG_SIGNALS = [
    "linux kernel", "device driver", "firmware", "embedded system",
    "bsp", "platform engineering", "boot", "bare metal",
    "hardware bring", "kernel module", "kernel space",
    "automation framework", "test infrastructure", "pyats",
]
JD_WRONG_SIGNALS = [
    "machine learning", "deep learning", "neural network", "pytorch",
    "tensorflow", "model training", "llm", "data pipeline",
    "react", "angular", "vue.js", "node.js",
    "django", "django rest", "rails", "spring boot",
    "payment api", "checkout", "storefront",
]

# ── Location ─────────────────────────────────────────────────────────────
BAY_AREA = [
    "san jose", "san francisco", " sf,", "bay area",
    "santa clara", "sunnyvale", "mountain view",
    "palo alto", "menlo park", "redwood city",
    "fremont", "oakland", "cupertino",
]
USA_OK = [
    "remote", "hybrid", "united states", "us-based", "us only",
    "work from anywhere", "anywhere in us",
    "seattle", "new york", "nyc", "austin", "denver",
    "chicago", "boston", "los angeles", ", ca", ", ny",
    ", wa", ", tx", ", co", ", ma", ", il", ", ga", ", or",
]
NON_USA = [
    "canada", "toronto", "vancouver", "montreal",
    "mexico", "brazil", "argentina",
    "united kingdom", " uk,", "london",
    "germany", "berlin", "france", "paris",
    "india", "bangalore", "bengaluru", "hyderabad", "mumbai", "pune",
    "japan", "tokyo", "singapore", "australia", "sydney",
    "ireland", "dublin", "netherlands", "amsterdam",
    "poland", "sweden", "norway", "denmark", "spain", "israel",
]


def score_role_type(title: str, jd: str) -> int:
    t        = title.lower()
    jd_open  = jd[:800].lower()

    # title is authoritative
    if any(k in t for k in ROLE_WRONG_TITLES):
        return 8   # wrong domain — near zero regardless of Python in JD
    if any(k in t for k in ROLE_STRONG_TITLES):
        return 95  # exactly Riya's domain

    if any(k in t for k in ROLE_OK_TITLES):
        # ok title — check JD for domain signals
        if any(s in jd_open for s in JD_STRONG_SIGNALS):
            return 82  # ok title + systems JD → good fit
        if any(s in jd_open for s in JD_WRONG_SIGNALS):
            return 30  # ok title but wrong-domain JD
        return 58      # generic ok title, no strong signals

    # no title match — rely on JD
    if any(s in jd_open for s in JD_WRONG_SIGNALS):
        return 15
    if any(s in jd_open for s in JD_STRONG_SIGNALS):
        return 75
    return 42


def score_core_skills(jd: str) -> tuple:
    jd_lower = jd.lower()

    # count matched skills per group
    group_scores = []
    all_matched  = []
    all_missing  = []

    for group in ALL_CORE_GROUPS:
        matched = [s for s in group if s in jd_lower]
        missing = [s for s in group if s not in jd_lower]
        # each group scored 0-100 based on coverage, then averaged
        coverage = len(matched) / max(len(group), 1)
        # diminishing returns: first few matches worth most
        group_score = min(100, int(coverage * 120))
        group_scores.append(group_score)
        all_matched.extend(matched)
        all_missing.extend(missing[:3])  # top 3 missing per group

    # average group scores (so no single group dominates)
    base_score = int(sum(group_scores) / len(group_scores))

    # bonus skills
    bonus_count = sum(1 for s in BONUS_SKILLS if s in jd_lower)
    bonus_score = min(20, bonus_count * 3)

    total = min(100, base_score + bonus_score)

    # deduplicate display lists
    display_matched = list(dict.fromkeys(s.strip() for s in all_matched if len(s.strip()) > 2))[:8]
    display_missing = list(dict.fromkeys(s.strip() for s in all_missing if len(s.strip()) > 3))[:6]

    return total, display_matched, display_missing


def score_experience(jd: str) -> int:
    jd_lower = jd.lower()

    if any(k in jd_lower for k in ["new grad", "entry level", "entry-level",
                                     "0-1 year", "0-2 year", "recent graduate",
                                     "university grad", "fresh graduate"]):
        return 65

    patterns = [
        r"(\d+)\s*\+\s*years?\s+of\s+(?:relevant\s+)?(?:industry\s+)?experience",
        r"(\d+)\s*\+\s*years?\s+experience",
        r"(\d+)\s*-\s*(\d+)\s*years?\s+(?:of\s+)?experience",
        r"minimum\s+of?\s*(\d+)\s*years?",
        r"at\s+least\s+(\d+)\s*years?",
        r"(\d+)\s*years?\s+of\s+(?:software|systems|platform|engineering)\s+experience",
    ]
    for p in patterns:
        m = re.search(p, jd_lower)
        if m:
            req = float(m.group(1))
            if req <= 2:   return 78
            elif req <= 4: return 88
            elif req <= 6: return 95
            elif req <= 8: return 70
            else:          return 35

    return 78


def score_location(location: str, jd: str) -> tuple:
    loc      = location.lower()
    combined = loc + " " + jd[:400].lower()

    if any(k in combined for k in NON_USA):
        return 0, False
    if any(k in loc for k in BAY_AREA):
        return 100, True
    if not location or not location.strip():
        return 72, True
    if any(k in combined for k in USA_OK):
        return 88, True
    return 20, False


def score_seniority(title: str) -> int:
    t = title.lower()
    if any(x in t for x in ["senior software", "senior engineer", "sr. software",
                              "swe ii", "software engineer ii", "software engineer 2",
                              "mid-level", "mid level"]):
        return 95
    if any(x in t for x in ["new grad", "entry level", "associate engineer",
                              "junior engineer", "university grad"]):
        return 70
    if any(x in t for x in ["staff engineer", "principal engineer", "lead engineer"]):
        return 48
    if any(x in t for x in ["engineering manager", "director"]):
        return 5
    return 85


def detect_red_flags(jd: str) -> list:
    flags  = []
    jd_low = jd.lower()
    checks = [
        ("clearance required",  ["security clearance", "secret clearance", "ts/sci"]),
        ("us citizenship only", ["us citizen only", "citizenship required", "must be a us citizen"]),
        ("contract only",       ["1099 only", "contract only", "w2 contract"]),
        ("10+ yoe required",    ["10+ years", "12+ years", "15+ years"]),
        ("phd required",        ["phd required", "doctorate required"]),
    ]
    for name, keywords in checks:
        if any(k in jd_low for k in keywords):
            flags.append(name)
    return flags


def score_job(job: dict, thresholds: dict) -> dict:
    title    = job.get("title", "")
    location = job.get("location", "")
    jd       = job.get("jd_text", "")

    loc_score, is_usa = score_location(location, jd)

    if not is_usa and loc_score == 0:
        return {
            "score": 0, "decision": "skip", "confidence": 99,
            "breakdown": {"role_type": 0, "skills": 0, "experience": 0,
                          "location": 0, "seniority": 0},
            "matched_skills": [], "missing_skills": [],
            "reasoning": f"Non-USA: '{location}'",
            "red_flags": ["non-usa location"],
        }

    role_score               = score_role_type(title, jd)
    skills_score, matched, missing = score_core_skills(jd)
    exp_score                = score_experience(jd)
    seniority_score          = score_seniority(title)

    final = int(
        role_score      * 0.35 +
        skills_score    * 0.30 +
        exp_score       * 0.20 +
        loc_score       * 0.10 +
        seniority_score * 0.05
    )

    apply_t  = thresholds.get("apply", 68)
    review_t = thresholds.get("review", 50)

    if final >= apply_t:
        decision = "apply"
    elif final >= review_t:
        decision = "review"
    else:
        decision = "skip"

    return {
        "score":    final,
        "decision": decision,
        "confidence": 88,
        "breakdown": {
            "role_type":  role_score,
            "skills":     skills_score,
            "experience": exp_score,
            "location":   loc_score,
            "seniority":  seniority_score,
        },
        "matched_skills": matched,
        "missing_skills": missing,
        "reasoning": (
            f"role={role_score} skills={skills_score} "
            f"exp={exp_score} loc={loc_score} sen={seniority_score} → {final}"
        ),
        "red_flags": detect_red_flags(jd),
    }
