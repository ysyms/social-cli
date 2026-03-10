# Social CLI

A unified CLI tool for monitoring Discord and Telegram messages via a single HTTP API.

---

## Architecture

```
cli.py              # Entry point, interactive setup
├── discord_worker.py   # Discord polling + SQLite cache
├── tg_worker.py        # Telegram via Telethon (MTProto)
├── api.py              # Unified FastAPI server
└── config.py           # Config persistence
```

### Discord

Discord does not provide a real-time push API for user accounts, so the worker polls all guilds and channels every 10–15 minutes and caches messages in a local SQLite database (up to 72 hours). Queries against `/discord/messages` read from this cache.

### Telegram

This project uses [Telethon](https://github.com/LonamiWebs/Telethon) — a pure Python implementation of Telegram's **MTProto** protocol. After login, a session file stores the authorization key so subsequent startups skip authentication entirely. Messages are fetched in real time directly from Telegram servers on each API call; no local storage needed.

**API credentials**

No registration required. Use Telegram's own built-in client credentials directly:

```python
API_ID   = 2040
API_HASH = "b18441a1ff607e10a989891a5462e627"
```

These are already hardcoded in `tg_worker.py` — just run the CLI and log in with your phone number.

---

## Getting Discord Token

Requires a Discord **user token** (not a Bot token).

1. Open Discord in your browser
2. Press `F12` → go to the **Network** tab
3. Switch to a channel in Discord to trigger a messages request
4. Find a request matching `discord.com/api/v9/channels/*/messages`
5. Click it → **Request Headers** → find the `Authorization` field
6. Copy the value — that is your token

> ⚠️ Your user token grants full access to your Discord account. Never share it or commit it to version control.

---

## Installation

```bash
git clone https://github.com/ysyms/social-cli.git
cd social-cli
pip install -r requirements.txt
```

---

## Usage

### Interactive setup

```bash
python cli.py
```

Prompts for Discord token, then Telegram phone number + verification code.

### Import config file

```bash
# Print template
python cli.py --print-template

# Use config file
python cli.py --config myconfig.json
```

Config format:

```json
{
  "discord_token": "YOUR_DISCORD_TOKEN",
  "tg_session": "/path/to/tg_session.session"
}
```

### Import existing Telegram session

```bash
python cli.py --tg-session /path/to/tg.session
```

---

## API Reference

All endpoints require header: `x-password: 1314@YSYms`

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/discord/messages` | POST | Discord messages from cache |
| `/telegram/recent` | POST | Telegram messages (real-time) |
| `/telegram/dialogs` | GET | Telegram dialog list |
| `/health` | GET | Service health check |

**Examples**

```bash
# Discord
curl -X POST http://localhost:7790/discord/messages \
  -H "x-password: 1314@YSYms" \
  -H "Content-Type: application/json" \
  -d '{"hours": 24}'

# Telegram
curl -X POST http://localhost:7790/telegram/recent \
  -H "x-password: 1314@YSYms" \
  -H "Content-Type: application/json" \
  -d '{"hours": 24}'

# Health
curl http://localhost:7790/health
# {"discord": "ok", "telegram": "ok"}
```

---

## Security

- Credentials stored at `~/.social-monitor/config.json` — never committed to git
- Session files (`.session`) and databases (`.db`) are in `.gitignore`
- Change the default API password before production deployment

---

## 中文说明

<details>
<summary>点击展开</summary>

**架构**：Discord 通过轮询缓存消息到 SQLite，Telegram 通过 Telethon（MTProto）实时拉取。

**Discord Token 获取**：浏览器打开 Discord → F12 → Console → 执行 `localStorage.token`。

**Telegram 登录**：无需申请 API，使用内置凭证通过手机号 + 验证码登录，session 文件保存授权密钥。

</details>
