# Exposing Local Hermes Gateway to Mobile Clients

When running Hermes on WSL/local machine and connecting mobile apps (OpenClaw/龙虾, etc.), you need:

## Architecture
```
Mobile App → cpolar/ngrok (公网) → WSL Local → Hermes Gateway
```

## Step 1: Find Gateway Tokens

Tokens are in `~/.hermes/.env`, NOT `config.yaml`:

```bash
# WeChat/Weixin
cat ~/.hermes/.env | grep WEIXIN_TOKEN
# → WEIXIN_TOKEN=963e9a...f434

# Telegram
cat ~/.hermes/.env | grep TELEGRAM_BOT_TOKEN

# General gateway auth
cat ~/.hermes/.env | grep -i "gateway\|token\|auth"
```

## Step 2: Install cpolar (内网穿透)

```bash
# Install
curl -L https://www.cpolar.com/static/downloads/install-release-cpolar.sh | bash

# Login (register at https://www.cpolar.com first)
cpolar authtoken <your-cpolar-token>

# Expose gateway port (check actual port with: hermes gateway status)
cpolar http 8080
```

cpolar will give you a public URL like: `https://xxxxx.cpolar.top`

## Step 3: Configure Mobile Client

For OpenClaw/龙虾 App:

| Field | Value |
|-------|-------|
| 部署方式 | 本地电脑 (Local) |
| WebSocket地址 | `wss://xxxxx.cpolar.top` |
| 网关令牌 | Token from .env |
| 名称 | Custom name |

## Important Notes

- **WSL must stay running** - use tmux or PowerShell (not VSCode SSH)
- **cpolar free tier** - URL changes on restart, upgrade for fixed domain
- **Gateway must be running** first: `hermes gateway status`
- **Restart gateway** after config changes: `hermes gateway restart`

## Troubleshooting

1. **Connection refused**: Check gateway is running, check port number
2. **Token invalid**: Verify token in .env matches what you entered
3. **URL changes**: cpolar free tier assigns new URL on restart
