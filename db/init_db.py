import sqlite3, os

DB_PATH     = os.path.join(os.path.dirname(__file__), "jobs.db")
SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "schema.sql")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    with open(SCHEMA_PATH) as f:
        conn.executescript(f.read())
    conn.commit()
    conn.close()
    print(f"[DB] Initialised: {DB_PATH}")

if __name__ == "__main__":
    init_db()
