# Social Monitor

A unified CLI tool for monitoring Discord and Telegram messages via a single HTTP API.

Discord 与 Telegram 消息监控的统一 CLI 工具，通过单一 HTTP API 提供服务。

---

## Architecture / 架构

```
cli.py              # Entry point, interactive setup / 入口，交互式配置
├── discord_worker.py   # Discord polling + SQLite cache / 轮询 + 缓存
├── tg_worker.py        # Telegram via Telethon (MTProto) / MTProto 实时拉取
├── api.py              # Unified FastAPI server / 统一 API 服务
└── config.py           # Config persistence / 配置持久化
```

### Discord

Discord does not provide a real-time push API for user accounts, so the worker polls all guilds and channels every 10–15 minutes and caches messages in a local SQLite database (up to 72 hours). Queries against `/discord/messages` read from this cache.

Discord 没有用户账号的实时推送 API，因此 worker 每 10–15 分钟轮询所有服务器和频道，将消息缓存到本地 SQLite 数据库（最多保留 72 小时）。查询 `/discord/messages` 时从缓存读取。

### Telegram

Telegram uses the **MTProto** protocol. This project uses [Telethon](https://github.com/LonamiWebs/Telethon) — a pure Python MTProto client. After login, a session file stores the authorization key, so subsequent startups skip authentication entirely. Messages are fetched in real time directly from Telegram servers on each API call; no local storage needed.

Telegram 使用 **MTProto** 协议。本项目通过 [Telethon](https://github.com/LonamiWebs/Telethon) 实现 — 纯 Python 的 MTProto 客户端。登录后 session 文件保存授权密钥，后续启动无需重新登录。每次 API 调用直接从 Telegram 服务器实时拉取消息，无需本地存储。

**API credentials / API 凭证**

This project uses Telegram's own built-in client credentials — no application registration required:

本项目直接使用 Telegram 官方客户端内置凭证，无需自行申请：

```python
API_ID   = 2040
API_HASH = "b18441a1ff607e10a989891a5462e627"
```

If you prefer to use your own credentials, register at [my.telegram.org/apps](https://my.telegram.org/apps).

如需使用自己的凭证，前往 [my.telegram.org/apps](https://my.telegram.org/apps) 申请。

---

## Getting Discord Token / 获取 Discord Token

Discord's user token is required (not a Bot token). It is stored in your browser's local storage after login.

需要 Discord **用户 token**（不是 Bot token），登录后存储在浏览器的 localStorage 中。

**Steps / 步骤：**

1. Open Discord in your browser / 在浏览器中打开 Discord
2. Press `F12` to open DevTools / 按 `F12` 打开开发者工具
3. Go to **Console** tab / 切换到 **Console** 标签
4. Paste and run / 粘贴并执行：
   ```js
   localStorage.token
   ```
5. Copy the value (remove surrounding quotes) / 复制返回值（去掉引号）

> ⚠️ **Warning / 警告**
> Your user token grants full access to your Discord account. Never share it or commit it to version control.
> 用户 token 等同于账号完整权限，切勿分享或提交到版本控制。

---

## Installation / 安装

```bash
git clone https://github.com/ysyms/social-monitor.git
cd social-monitor
pip install -r requirements.txt
```

---

## Usage / 用法

### Interactive setup / 交互式配置

```bash
python cli.py
```

Prompts for Discord token and Telegram phone number + verification code.

交互式输入 Discord token 和 Telegram 手机号 + 验证码。

### Import config file / 导入配置文件

```bash
# Print template / 打印模板
python cli.py --print-template

# Import / 导入
python cli.py --config myconfig.json
```

Config file format / 配置文件格式：

```json
{
  "discord_token": "YOUR_DISCORD_TOKEN",
  "tg_session": "/path/to/tg_session.session"
}
```

### Import existing Telegram session / 导入已有 TG session

```bash
python cli.py --tg-session /path/to/tg.session
```

---

## API Reference / API 文档

All endpoints require header: `x-password: 1314@YSYms`

所有接口需要请求头：`x-password: 1314@YSYms`

### `POST /discord/messages`

```bash
curl -X POST http://localhost:7790/discord/messages \
  -H "x-password: 1314@YSYms" \
  -H "Content-Type: application/json" \
  -d '{"hours": 24}'
```

### `POST /telegram/recent`

```bash
curl -X POST http://localhost:7790/telegram/recent \
  -H "x-password: 1314@YSYms" \
  -H "Content-Type: application/json" \
  -d '{"hours": 24}'
```

### `GET /telegram/dialogs`

```bash
curl http://localhost:7790/telegram/dialogs \
  -H "x-password: 1314@YSYms"
```

### `GET /health`

```bash
curl http://localhost:7790/health
```

```json
{
  "discord": "ok",
  "telegram": "ok"
}
```

---

## Security / 安全

- Credentials are stored locally at `~/.social-monitor/config.json` — never committed to git.
- Session files (`.session`) and databases (`.db`) are in `.gitignore`.
- The API password (`x-password`) should be changed before production deployment.

- 凭证保存在本地 `~/.social-monitor/config.json`，不会提交到 git。
- Session 文件和数据库已加入 `.gitignore`。
- 生产部署前请修改 API 密码（`x-password`）。
