# Weixin/WeChat Gateway Setup Guide

## Quick Setup

### 1. Configure Weixin Platform
```bash
hermes gateway setup
# Select "Weixin / WeChat" from the platform list
# Follow prompts to enter credentials
```

### 2. Start Gateway with tmux (Recommended for WSL)
```bash
# Stop existing gateway if running
hermes gateway stop

# Start in tmux session (persists after terminal closes)
tmux new-session -d -s hermes 'hermes gateway run'
```

### 3. Verify Connection
```bash
hermes gateway status
tail -f ~/.hermes/logs/gateway.log
```

## Common Issues

### Unauthorized User Error
**Symptom:** `Unauthorized user: <user_id>@im.wechat`

**Fix:** Add to `~/.hermes/.env`:
```bash
GATEWAY_ALLOW_ALL_USERS=true
```
Then restart gateway.

### CLI and Gateway Sessions Are Independent
- **CLI session:** Terminal-based conversation
- **Gateway session:** Platform-based conversation (Weixin, Telegram, etc.)

Messages from Weixin go to the gateway session, not the CLI session.

**View gateway sessions:**
```bash
hermes sessions list
hermes sessions export --session-id <ID> /tmp/session.jsonl
```

### OpenClaw Residue in Weixin
If Weixin shows "OpenClaw" instead of "Hermes":

1. **Check if OpenClaw is installed:**
   ```bash
   ls ~/.openclaw 2>/dev/null || echo "No OpenClaw installation"
   ```

2. **Migrate from OpenClaw (if exists):**
   ```bash
   hermes claw migrate --dry-run  # Preview
   hermes claw migrate --overwrite  # Apply
   ```

3. **Update Weixin app name:**
   - Login to https://ilinkai.weixin.qq.com
   - Change application name to "Hermes Agent" or desired name

## File Locations

| File | Purpose |
|------|---------|
| `~/.hermes/.env` | Weixin credentials (WEIXIN_*) |
| `~/.hermes/weixin/accounts/` | Account configuration |
| `~/.hermes/logs/gateway.log` | Gateway logs |
| `~/.hermes/sessions/` | Session transcripts |

## Environment Variables

```bash
WEIXIN_ACCOUNT_ID=<account>@im.bot
WEIXIN_TOKEN=<token>
WEIXIN_BASE_URL=https://ilinkai.weixin.qq.com
WEIXIN_DM_POLICY=pairing
WEIXIN_ALLOW_ALL_USERS=false  # Set to true for open access
WEIXIN_HOME_CHANNEL=<user_id>@im.wechat
```
