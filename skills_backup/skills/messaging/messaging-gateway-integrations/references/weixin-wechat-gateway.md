---
name: weixin-wechat-gateway
description: "Setup and troubleshoot WeChat (微信/Weixin) integration with Hermes Agent gateway."
version: 1.0.0
tags: [wechat, weixin, gateway, messaging, platform]
metadata:
  hermes:
    tags: [wechat, weixin, gateway, messaging, platform]
---

# WeChat (微信) Gateway Integration

Hermes Agent supports WeChat via the `weixin` platform adapter. This skill covers setup, configuration, troubleshooting, and WSL-specific persistence.

## Quick Setup

```bash
# 1. Run gateway setup wizard, select "Weixin / WeChat"
hermes gateway setup

# 2. Authorize users (add to ~/.hermes/.env)
echo 'GATEWAY_ALLOW_ALL_USERS=true' >> ~/.hermes/.env

# 3. Start gateway (tmux recommended for WSL)
tmux new -s hermes 'hermes gateway run'

# 4. Verify
hermes gateway status
tail -20 ~/.hermes/logs/gateway.log
```

## Configuration Location

WeChat config is stored **separately** from `config.yaml`:

```
~/.hermes/weixin/accounts/<account_id>.json
```

Example account file:
```json
{
  "token": "963e9a...f434",
  "base_url": "https://ilinkai.weixin.qq.com",
  "user_id": "o9cq80-...@im.wechat",
  "saved_at": "2026-05-21T03:46:50Z"
}
```

**Key insight:** `hermes gateway setup` shows WeChat as "configured" based on this directory, NOT based on `config.yaml`. Don't look for `weixin` in config.yaml — it won't be there.

## User Authorization

By default, all unauthorized users are **denied**. Two options:

1. **Allow all users** (simplest):
   ```bash
   echo 'GATEWAY_ALLOW_ALL_USERS=true' >> ~/.hermes/.env
   ```

2. **Specific user allowlist** (more secure):
   ```bash
   # Add to ~/.hermes/.env
   WEIXIN_ALLOWED_USERS=o9cq80-nMdaqz4M3Xe4Ba17i9wX0@im.wechat
   ```

After changing `.env`, restart the gateway for changes to take effect.

## WSL-Specific: Gateway Persistence

WSL2 with systemd enabled works well for gateway persistence. Two options:

### Option A: systemd service (recommended if systemd works)

```bash
# Install the service
sudo hermes gateway restart --system

# Verify
sudo systemctl status hermes-gateway
```

**Pitfall — Proxy for WeChat in WSL2 systemd:** systemd services do NOT inherit your shell's proxy environment variables. If WSL2 cannot reach `ilinkai.weixin.qq.com` directly (common with mirrored networking mode), you must add proxy vars to the service file:

```bash
# Check if you have a local proxy
echo $HTTPS_PROXY  # e.g. http://127.0.0.1:7897

# Add to the systemd service file
sudo systemctl edit hermes-gateway
# Or edit /etc/systemd/system/hermes-gateway.service directly, add:
#   Environment="HTTP_PROXY=http://127.0.0.1:7897"
#   Environment="HTTPS_PROXY=http://127.0.0.1:7897"
#   Environment="NO_PROXY=localhost,127.0.0.1,::1,*.local,10.*,172.16.*,192.168.*"

sudo systemctl daemon-reload
sudo systemctl restart hermes-gateway
```

Symptom of missing proxy: `[Weixin] poll error: Cannot connect to host ilinkai.weixin.qq.com:443 ssl:default [Network is unreachable]`

### Option B: tmux (fallback if systemd is not available)

```bash
tmux new -s hermes 'hermes gateway run'
# Detach: Ctrl+B then D
# Reattach: tmux attach -t hermes
```

**Do NOT use `nohup`** — Hermes detects shell-level background wrappers and rejects them.

## Troubleshooting

### "Unauthorized user" in logs

Symptom: `gateway.log` shows `Unauthorized user: <user_id>`

Fix: Add `GATEWAY_ALLOW_ALL_USERS=true` to `~/.hermes/.env` and restart gateway.

### Gateway not running

```bash
hermes gateway status
# If not running:
tmux new -s hermes 'hermes gateway run'
```

### WeChat not connecting

Check logs:
```bash
# systemd:
sudo journalctl -u hermes-gateway --since "5 min ago" | grep -i weixin
# or tmux:
tail -30 ~/.hermes/logs/gateway.log | grep -i weixin
```

Expected: `[Weixin] Connected account=<id> base=https://ilinkai.weixin.qq.com`

### "Network is unreachable" for ilinkai.weixin.qq.com

WSL2 cannot reach the WeChat API directly. You need a proxy configured in the systemd service. See "WSL-Specific: Gateway Persistence → Proxy for WeChat" section above.

### Messages not received

1. Verify gateway is running: `hermes gateway status`
2. Check user authorization in logs
3. Verify account file exists: `ls ~/.hermes/weixin/accounts/`

## Platform Details

- **Protocol:** WeChat Bot API via `ilinkai.weixin.qq.com`
- **Message types:** Text, images, voice (auto-transcribed)
- **Session routing:** DM-based (each user gets own session)

## Limitations & Alternatives

**WeChat has no official Bot API for personal accounts.** The current integration uses `ilinkai.weixin.qq.com` which has limitations:

- **No multi-bot group chat:** Creating a group with multiple Hermes bots requires multiple WeChat accounts (each needs a phone number)
- **Ban risk:** Third-party integrations may be flagged by WeChat
- **No QQ support:** QQ requires enterprise certification, not viable for personal use
- **MEDIA: syntax does not send files:** Using `MEDIA:/path/to/file` in `send_message` only sends the file path as a text string, NOT the actual file. WeChat does not support file attachments through this integration. To share file content, paste it directly in the message text.

**For multi-agent group chat, use Telegram or Discord instead:**
- Official Bot API, free, no ban risk
- Multiple bots can join one group
- See `agent-group-chat` skill for setup guide

**WeChat ClawBot (Official OpenClaw Integration):**

WeChat has an official **ClawBot** feature that connects **OpenClaw** to WeChat:
- Install: `npx -y @tencent-weixin/openclaw-weixin-cli@latest install`
- Use: Scan QR code in WeChat to enable the plugin
- Limitation: Only receives replies within 24 hours
- **Hermes and OpenClaw share similar architecture** — ClawBot may work with Hermes too (untested)
- User-facing name: "龙虾" (Lobster) — the OpenClaw mobile client

To find this feature in WeChat: search for "Hermes" or look for the ClawBot entry in WeChat's feature list.

**If you must use WeChat for multi-agent:**
- Use a single Hermes instance simulating multiple roles
- Prefix responses with role names (e.g., `[Engineer]`, `[Validator]`)
- Consider WeChat Work (企业微信) which has official API for enterprise use
