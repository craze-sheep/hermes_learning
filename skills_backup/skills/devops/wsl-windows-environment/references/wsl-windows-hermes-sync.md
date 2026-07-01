# WSL-to-Windows Hermes Sync: MCP Servers & Skills

When WSL Hermes has custom MCP servers and local skills that Windows Hermes lacks,
sync them over. This is typically needed after a clean Windows Hermes install.

## Config Recovery from cc-switch

After a clean Hermes install, restore provider configs from cc-switch's SQLite database:

```bash
DB=/mnt/c/Users/lzy/.cc-switch/cc-switch.db

# List all Hermes providers
sqlite3 "$DB" "SELECT id, name FROM providers WHERE app_type='hermes';"

# Get full config for a provider
sqlite3 "$DB" "SELECT settings_config FROM providers WHERE app_type='hermes' AND id='xiaomi';"

# Get API key (note: appears masked in sqlite3 output but is stored full)
sqlite3 "$DB" "SELECT json_extract(settings_config, '$.api_key') FROM providers WHERE app_type='hermes' AND id='xiaomi';"

# The first-run creates config.yaml.bak.* — use it as base, merge cc-switch values
```

## MCP Servers

Append the `mcp_servers` section from WSL config to Windows config.yaml.
Key servers to sync:

| Server | Command | Notes |
|--------|---------|-------|
| sequential-thinking | `npx -y @modelcontextprotocol/server-sequential-thinking` | npm package |
| fetch | `uvx mcp-server-fetch` | Python package |
| context7 | `npx -y @upstash/context7-mcp` | npm package |
| holographic | `node C:\Users\lzy\AppData\Local\hermes\mcp-holographic\index.js` | Needs local install |

## Holographic MCP Server Setup

```bash
# 1. Copy source from WSL (exclude node_modules)
rsync -av ~/.hermes/mcp-holographic/ \
  /mnt/c/Users/lzy/AppData/Local/hermes/mcp-holographic/ \
  --exclude="node_modules"

# 2. Install Windows node_modules
powershell.exe -Command \
  "cd 'C:\Users\lzy\AppData\Local\hermes\mcp-holographic'; npm install"
```

## Skills Sync

```bash
# Merge all WSL skills into Windows (don't overwrite existing)
rsync -av --ignore-existing ~/.hermes/skills/ \
  /mnt/c/Users/lzy/AppData/Local/hermes/skills/
```

## Environment Variables

```bash
# Copy relevant env vars from WSL .env to Windows .env
grep "XIAOMI_BASE_URL" ~/.hermes/.env >> /mnt/c/Users/lzy/AppData/Local/hermes/.env
```

## Additional CLI Tools

### codegraph

```bash
# Install via Windows pip (usually Anaconda)
powershell.exe -Command "pip install codegraph"

# Verify
powershell.exe -Command "codegraph --version"
```

### docling (PDF/DOCX to structured data)

```bash
# Install via Windows pip (Anaconda)
powershell.exe -Command "pip install docling"
```

**Known issue:** Docling depends on PyTorch, and Windows Anaconda PyTorch may have broken C extensions (`Failed to load PyTorch C extensions`). If this happens, docling CLI won't work directly on Windows. Workaround: use WSL docling via `wsl docling ...` or fix PyTorch with `pip install --force-reinstall torch`.

The skill is still available for Hermes agent to use — it can invoke docling through WSL.

## Hermes Environment Variables

Check WSL `.env` for API keys to sync:

```bash
# List key names (not values)
cat ~/.hermes/.env | grep -v "^#" | grep -v "^$" | sed 's/=.*//' | sort

# Sync specific keys
grep "XIAOMI_BASE_URL" ~/.hermes/.env >> /mnt/c/Users/lzy/AppData/Local/hermes/.env
```

## cc-switch Proxy Architecture

cc-switch runs a local HTTP proxy on `127.0.0.1:15721` that handles authentication for all tools. The proxy:
- Accepts requests on standard OpenAI-compatible endpoints
- Injects real API keys before forwarding to upstream APIs
- Supports codex, claude, gemini tool types

Check if proxy is running:
```bash
powershell.exe -Command "Get-NetTCPConnection -LocalPort 15721 -ErrorAction SilentlyContinue"
```

Tools configured to use the proxy don't need real API keys — a placeholder suffices.

## Verification

```bash
powershell.exe -Command "hermes mcp list"
powershell.exe -Command "hermes skills list"
```
