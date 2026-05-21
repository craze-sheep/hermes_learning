---
name: qqbot-setup
description: "Configure QQ Bot for Hermes Agent gateway — registration, credentials, group chat, troubleshooting."
version: 1.0.0
author: hermes
tags: [qq, qqbot, messaging, gateway, setup, platform]
metadata:
  hermes:
    triggers:
      - "configure QQ bot"
      - "set up QQ"
      - "QQ not replying"
      - "QQ group chat"
      - "qqbot setup"
---

# QQ Bot Setup for Hermes Agent

QQ Bot is a **supported** Hermes gateway platform (adapter: `gateway/platforms/qqbot/`). It uses the Official QQ Bot API v2 with WebSocket gateway for inbound events and REST API for outbound messages.

> The hermes-agent bundled skill's platform list may not mention QQ — but it IS supported and ships with a full adapter.

## Prerequisites

1. Register at [q.qq.com](https://q.qq.com)
2. Create a new application → get **App ID** and **App Secret**
3. Enable intents: **C2C messages**, **Group @-messages**, **Guild messages**
4. Publish the app (sandbox mode limits to test channels only)

## Configuration

### Add credentials to ~/.hermes/.env

```bash
QQ_APP_ID=<your-app-id>
QQ_CLIENT_SECRET=<your-app-secret>
QQ_ALLOW_ALL_USERS=true          # open access (default is false = restricted)
QQ_GROUP_POLICY=open             # allow all groups
```

### Restart gateway

```bash
sudo systemctl restart hermes-gateway
```

### Verify connection

```bash
grep -i "qqbot" ~/.hermes/logs/gateway.log | tail -10
# Should show: [QQBot:<appid>] Connected, Ready
```

## Group Chat Setup

1. In q.qq.com, enable **Group @-messages** intent
2. Set `QQ_GROUP_POLICY=open` in `.env`
3. In QQ app: open group → group settings → group robots → search and add your bot
4. In group chat: **@bot-name message** to trigger a reply

Bot can only reply to @-mentioned messages in groups (cannot proactively post).

## Pitfalls

### Duplicate .env entries cause silent failures

**Problem**: Using `echo >> ~/.hermes/.env` multiple times creates duplicate keys. The system may use the wrong (old) entry.

**Fix**: Before adding QQ config, remove ALL existing QQ lines first:
```bash
grep -v "^QQ_" ~/.hermes/.env > /tmp/env_clean && cp /tmp/env_clean ~/.hermes/.env
# Then add fresh entries
```

### QQ_ALLOW_ALL_USERS defaults to false

Without setting this to `true`, only users listed in `QQ_ALLOWED_USERS` can interact. This is the #1 cause of "bot doesn't reply" — the bot IS connected and receiving messages, but silently drops them due to allowlist.

### Sandbox mode

Sandbox bots only receive messages from QQ's sandbox test channel. Must publish the app on q.qq.com for production use.

### Multiple QQ App IDs

Only the LAST `QQ_APP_ID` in `.env` takes effect if there are duplicates. Clean up old entries before adding new ones.

## Environment Variables Reference

| Variable | Description | Default |
|---|---|---|
| `QQ_APP_ID` | QQ Bot App ID (required) | — |
| `QQ_CLIENT_SECRET` | QQ Bot App Secret (required) | — |
| `QQ_ALLOW_ALL_USERS` | Allow all DMs | `false` |
| `QQ_ALLOWED_USERS` | Comma-separated user OpenIDs | — |
| `QQ_GROUP_POLICY` | `open`, `allowlist`, or `disabled` | — |
| `QQ_GROUP_ALLOWED_USERS` | Comma-separated group OpenIDs | — |
| `QQBOT_HOME_CHANNEL` | OpenID for cron/notification delivery | — |

## Advanced: config.yaml override

```yaml
platforms:
  qqbot:
    extra:
      app_id: "your-app-id"
      client_secret: "your-secret"
      markdown_support: true
      dm_policy: "open"
      group_policy: "open"
```
