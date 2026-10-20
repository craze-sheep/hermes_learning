# Codex + cc-switch Proxy Configuration

## How cc-switch Proxy Works

cc-switch runs a local HTTP proxy on `127.0.0.1:15721` that intercepts API
requests and injects real authentication headers. The database stores
**masked** API keys (e.g. `sk-OaC...Oecs`) — the full key is only held in
the proxy's memory at runtime.

```
Codex CLI  →  127.0.0.1:15721 (cc-switch proxy)  →  api.9e.lv/v1 (actual API)
                 ↑ injects real API key
```

This means:
- `~/.codex/auth.json` only needs a **dummy** key (`"sk-proxy"`)
- `config.toml` must point `base_url` to the proxy, NOT the original API
- The proxy must be running (check with `Get-NetTCPConnection -LocalPort 15721`)

## config.toml Format (Critical)

Codex uses **top-level keys** for model config, NOT nested TOML sections:

```toml
# ✗ WRONG — nested [model] section
[model]
provider = "my_codex"
model = "gpt-5.5"

# ✓ CORRECT — top-level keys
model_provider = "my_codex"
model = "gpt-5.5"
model_reasoning_effort = "high"
model_context_window = 1000000
model_auto_compact_token_limit = 900000
disable_response_storage = true
```

The `[model_providers.<name>]` section IS a TOML section (correct).

## Querying cc-switch Database

```bash
# List all Codex providers
sqlite3 ~/.cc-switch/cc-switch.db \
  "SELECT id, name FROM providers WHERE app_type='codex';"

# Get current provider
sqlite3 ~/.cc-switch/cc-switch.db \
  "SELECT id FROM providers WHERE app_type='codex' AND is_current=1;"

# Get config template (contains base_url, model, wire_api)
sqlite3 ~/.cc-switch/cc-switch.db \
  "SELECT json_extract(settings_config, '$.config') FROM providers WHERE id='<id>' AND app_type='codex';"

# Get masked API key (for reference, not usable directly)
sqlite3 ~/.cc-switch/cc-switch.db \
  "SELECT json_extract(settings_config, '$.auth.OPENAI_API_KEY') FROM providers WHERE id='<id>' AND app_type='codex';"
```

## Proxy Verification

```powershell
# Check proxy is listening
Get-NetTCPConnection -LocalPort 15721 -ErrorAction SilentlyContinue

# Test responses endpoint (should return 200 with JSON)
curl -X POST http://127.0.0.1:15721/v1/responses `
  -H "Content-Type: application/json" `
  -H "Authorization: Bearer sk-proxy" `
  -d '{"model":"gpt-5.5","input":"test"}'

# Test models endpoint (returns 404 — this is expected)
curl http://127.0.0.1:15721/v1/models
```

## codex doctor False Positives

| Check | Status | Notes |
|-------|--------|-------|
| auth | ✓ | Dummy key in auth.json is accepted |
| config | ✓ | Top-level keys parsed correctly |
| reachability | ✗ 404 | Proxy doesn't serve `/v1/models` — IGNORE |
| websocket | ⚠ timeout | Proxy doesn't support WS upgrade — uses HTTPS fallback |
| actual API calls | ✓ | `/v1/responses` works through proxy |

## Full Recovery Script (WSL → Windows)

```bash
# 1. Query cc-switch for config
CONFIG=$(sqlite3 ~/.cc-switch/cc-switch.db \
  "SELECT json_extract(settings_config, '$.config') FROM providers WHERE app_type='codex' AND is_current=1;")

# 2. Write config.toml with proxy base_url
cat > /mnt/c/Users/lzy/.codex/config.toml << EOF
$CONFIG
[mcp_servers]
# add MCP servers here...
EOF

# Fix base_url to point to proxy
sed -i 's|base_url = "https://[^"]*"|base_url = "http://127.0.0.1:15721/v1"|' \
  /mnt/c/Users/lzy/.codex/config.toml

# 3. Write auth placeholder
echo '{"OPENAI_API_KEY": "sk-proxy"}' > /mnt/c/Users/lzy/.codex/auth.json

# 4. Verify
/mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe -Command "codex exec 'say hello'"
```
