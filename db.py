"""Shared SQLite storage for both Discord and Telegram messages."""
import sqlite3, os

DB_PATH = "/opt/social-monitor/messages.db"
RETENTION_DAYS = 7

def _conn():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    return sqlite3.connect(DB_PATH)

def init():
    with _conn() as c:
        c.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id       TEXT PRIMARY KEY,
                platform TEXT NOT NULL,   -- 'tg' or 'dc'
                group_name TEXT NOT NULL, -- dialog/guild+channel
                sender   TEXT NOT NULL,
                text     TEXT NOT NULL,
                ts       REAL NOT NULL
            )
        """)
        c.execute("CREATE INDEX IF NOT EXISTS idx_ts ON messages(ts)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_platform ON messages(platform)")

def insert(rows: list[tuple]):
    """rows: [(id, platform, group_name, sender, text, ts), ...]"""
    if not rows: return
    with _conn() as c:
        c.executemany("INSERT OR IGNORE INTO messages VALUES (?,?,?,?,?,?)", rows)

def query(start_ts: float, end_ts: float, platform: str = None) -> list[tuple]:
    sql = "SELECT platform,group_name,sender,text,ts FROM messages WHERE ts>=? AND ts<=?"
    params = [start_ts, end_ts]
    if platform:
        sql += " AND platform=?"
        params.append(platform)
    sql += " ORDER BY ts ASC"
    with _conn() as c:
        return c.execute(sql, params).fetchall()

def cleanup():
    import time
    cutoff = time.time() - RETENTION_DAYS * 86400
    with _conn() as c:
        c.execute("DELETE FROM messages WHERE ts<?", (cutoff,))
