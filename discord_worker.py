import time, random, logging, httpx
import db

logger = logging.getLogger("discord")

BASE_URL   = "https://discord.com/api/v9"
TEXT_TYPES = {0, 5}
POLL_MIN   = 10
POLL_MAX   = 15

state = {"expired": False}
_token = ""

def init(token: str):
    global _token
    _token = token

def _headers():
    return {
        "Authorization": _token,
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
    }

def _snowflake_to_time(s): return ((int(s) >> 22) + 1420070400000) / 1000
def _time_to_snowflake(ts): return str((int(ts * 1000) - 1420070400000) << 22)

class TokenExpired(Exception): pass

def _get(url, params=None):
    r = httpx.get(url, headers=_headers(), params=params, timeout=15)
    if r.status_code == 401: raise TokenExpired()
    if r.status_code == 403: return None
    r.raise_for_status()
    return r.json()

def _get_last_id(channel_id: str) -> str | None:
    import sqlite3, os
    state_db = "/opt/social-monitor/discord_state.db"
    os.makedirs(os.path.dirname(state_db), exist_ok=True)
    with sqlite3.connect(state_db) as c:
        c.execute("CREATE TABLE IF NOT EXISTS channel_state (channel_id TEXT PRIMARY KEY, last_id TEXT)")
        r = c.execute("SELECT last_id FROM channel_state WHERE channel_id=?", (channel_id,)).fetchone()
    return r[0] if r else None

def _set_last_id(channel_id: str, last_id: str):
    import sqlite3
    state_db = "/opt/social-monitor/discord_state.db"
    with sqlite3.connect(state_db) as c:
        c.execute("INSERT OR REPLACE INTO channel_state VALUES (?,?)", (channel_id, last_id))

def _fetch_channel(cid, gname, cname, after, max_fetch=None):
    rows, cursor, total = [], after, 0
    while True:
        data = _get(f"{BASE_URL}/channels/{cid}/messages", {"after": cursor, "limit": 100})
        if not data: break
        for m in data:
            txt = m.get("content", "").strip()
            if txt:
                rows.append((
                    f"dc-{m['id']}", "dc",
                    f"{gname} / {cname}",
                    m["author"]["username"], txt,
                    _snowflake_to_time(m["id"])
                ))
        cursor = data[-1]["id"]
        total += len(data)
        if len(data) < 100 or (max_fetch and total >= max_fetch): break
        time.sleep(0.5)
    return rows, cursor

def _poll_once():
    for guild in (_get(f"{BASE_URL}/users/@me/guilds") or []):
        gid, gname = guild["id"], guild["name"]
        channels = _get(f"{BASE_URL}/guilds/{gid}/channels")
        if not channels: continue
        for ch in [c for c in channels if c.get("type") in TEXT_TYPES]:
            cid, cname = ch["id"], ch.get("name", "")
            last = _get_last_id(cid)
            after = last or _time_to_snowflake(time.time())
            try:
                rows, newest = _fetch_channel(cid, gname, cname, after, None)
                if rows: db.insert(rows)
                _set_last_id(cid, newest if rows else (after if not last else last))
            except TokenExpired: raise
            except Exception as e: logger.warning(f"频道 {cname}: {e}")
            time.sleep(0.3)

def run_poller():
    db.init()
    logger.info("Discord poller 启动")
    while True:
        try:
            _poll_once()
            db.cleanup()
        except TokenExpired:
            logger.error("Discord token 过期")
            state["expired"] = True
            return
        except Exception as e:
            logger.error(f"轮询异常: {e}")
        interval = random.randint(POLL_MIN * 60, POLL_MAX * 60)
        logger.info(f"下次轮询 {interval//60}m 后")
        time.sleep(interval)
