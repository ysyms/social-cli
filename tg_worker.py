import asyncio, logging
from datetime import datetime, timezone, timedelta
from telethon import TelegramClient
from telethon.tl.types import User, Chat, Channel

logger = logging.getLogger("telegram")

API_ID   = 2040
API_HASH = "b18441a1ff607e10a989891a5462e627"
SESSION  = "/opt/social-monitor/tg_session"
CST      = timezone(timedelta(hours=8))

_client: TelegramClient = None

async def init_client():
    global _client
    _client = TelegramClient(SESSION, API_ID, API_HASH)
    await _client.connect()
    return _client

async def get_dialogs():
    dialogs = await _client.get_dialogs()
    result = {"private": [], "groups": []}
    for d in dialogs:
        item = {"id": d.id, "name": d.name, "unread": d.unread_count}
        if isinstance(d.entity, User):
            result["private"].append(item)
        elif isinstance(d.entity, (Chat, Channel)):
            result["groups"].append(item)
    return result

async def get_recent(hours: float):
    from telethon.tl.types import PeerChannel, PeerChat, PeerUser
    cutoff = datetime.now(tz=timezone.utc).timestamp() - hours * 3600
    dialogs = await _client.get_dialogs()
    result = {}
    for d in dialogs:
        msgs = []
        async for msg in _client.iter_messages(d.entity, limit=100):
            if msg.date.timestamp() < cutoff: break
            if not msg.text: continue
            sender = getattr(msg.sender, "first_name", None) or getattr(msg.sender, "title", "Unknown") if msg.sender else "Unknown"
            dt = msg.date.astimezone(CST).strftime("UTC+8 %m/%d %H:%M")
            msgs.append([sender, dt, msg.text])
        if msgs:
            result[d.name] = msgs
    return result
