---
name: windows-ai-tools-lifecycle
description: "Use when installing, uninstalling, reinstalling, or recovering AI coding tools on Windows — codex, claude-code, opencode, hermes — with cc-switch as config hub."
version: 1.0.0
author: agent
metadata:
  hermes:
    tags: [windows, ai-tools, cc-switch, install, uninstall, recovery]
    related_skills: [hermes-agent, claude-code, codex, opencode]
---

# Windows AI Tools Lifecycle

Manage the full lifecycle of AI coding tools on Windows: install, uninstall,
reinstall, and config recovery. Uses cc-switch as the central configuration
hub that persists provider settings across tool reinstalls.

## When to Use

- User asks to reinstall one or more AI coding tools on Windows
- User reports "not configured" errors after a reinstall
- Need to recover API keys or provider configs after accidental deletion
- Setting up a new Windows machine with the standard AI tool suite

## Tools Covered

| Tool | Install Method | Package |
|------|---------------|---------|
| Codex (OpenAI) | `npm install -g @openai/codex` | codex-cli |
| Claude Code | `npm install -g @anthropic-ai/claude-code` | claude-code |
| OpenCode | `npm install -g opencode-ai` | opencode-ai |
| Hermes | `irm install.ps1 \| iex` (PowerShell) | hermes-agent |

## Uninstall Checklist

**Order matters**: uninstall first, then delete files. For npm tools, uninstall
before deleting directories to avoid stale shim references.

```powershell
# 1. npm uninstall (removes binaries + node_modules)
npm uninstall -g @openai/codex @anthropic-ai/claude-code opencode-ai

# 2. Delete config/data directories (see hermes-agent skill
#    references/windows-reinstall-cc-switch-recovery.md for exact paths)
```

### Files to Delete Per Tool

**Codex:**
- `~/.codex/` (config + sessions + skills + sandbox binaries)
- `~/.cache/codex-runtimes/` (runtime cache, can be large)
- `AppData/Roaming/npm/codex*` (shim, if npm uninstall missed it)

**Claude Code:**
- `~/.claude/` (config + sessions + plugins + skills)
- `~/.claude.json` (global config)
- `AppData/Local/AnthropicClaude/` (Electron app data)
- `AppData/Local/claude-cli-nodejs/` (CLI runtime)
- `AppData/Roaming/Claude/` (desktop app data)
- `AppData/Roaming/npm/claude*` (shim)
- `.vscode/extensions/anthropic.claude-code-*` (VSCode extension)
- `AppData/Local/Temp/claude/` (temp files)

**OpenCode:**
- `~/.config/opencode/` (config + node_modules)
- `~/.local/share/opencode/` (database, can be ~200MB)
- `~/.local/state/opencode/` (locks)
- `~/.cache/opencode/` (binary cache + models.json)
- `AppData/Roaming/npm/opencode*` (shim + binary)
- `AppData/Roaming/npm/node_modules/opencode-ai/` (npm package)
- `.vscode/extensions/tanishqkancharla.opencode-vscode-*` (VSCode extension)
- `AppData/Local/Temp/opencode/` (temp files)

**Hermes:**
- `AppData/Local/hermes/` (everything: config, venv, source, data)

**DO NOT delete:**
- `~/.cc-switch/` — cc-switch config hub (preserves provider configs)
- `~/ai-shared/` — shared backups and skills
- Any other unrelated files

## Install Sequence

1. **npm tools first** (codex, claude-code, opencode) — fast, parallel
2. **Hermes last** — uses its own installer, takes longer (Playwright browser download)

```powershell
# From PowerShell
npm install -g @openai/codex
npm install -g @anthropic-ai/claude-code
npm install -g opencode-ai

# Hermes (PowerShell install script)
irm https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.ps1 | iex
```

### From WSL (cross-install to Windows)

```bash
# Use powershell.exe from WSL
/mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe -Command "npm install -g @openai/codex"
# ... etc
```

## Config Recovery from CC-Switch

After reinstall, tools will show "not configured" because their config
directories were deleted. cc-switch preserves the provider configs in its
SQLite database.

### Hermes Recovery

1. Query cc-switch for the provider config:
   ```bash
   sqlite3 ~/.cc-switch/cc-switch.db \
     "SELECT json_extract(settings_config, '$.api_key') FROM providers WHERE app_type='hermes' AND id='<provider_id>';"
   ```

2. Restore `config.yaml` from the install-time backup:
   ```bash
   cp AppData/Local/hermes/config.yaml.bak.<timestamp> AppData/Local/hermes/config.yaml
   ```

3. Merge provider data from cc-switch into the config (replace `model: ''`
   and `providers: {}` with actual values).

4. Write `.env` with the API key.

5. Verify: `hermes config` should show model and provider.

### Codex Recovery (cc-switch proxy pattern)

cc-switch runs a local proxy on `127.0.0.1:15721` that injects real API
keys at request time. The database stores MASKED keys — the proxy handles
real auth transparently.

1. Query cc-switch for the current Codex provider:
   ```bash
   sqlite3 ~/.cc-switch/cc-switch.db \
     "SELECT settings_config FROM providers WHERE app_type='codex' AND is_current=1;"
   ```

2. Extract the config template (adjust `base_url` to proxy):
   ```bash
   sqlite3 ~/.cc-switch/cc-switch.db \
     "SELECT json_extract(settings_config, '$.config') FROM providers WHERE app_type='codex' AND id='<provider_id>';"
   ```

3. Write `~/.codex/config.toml` — **top-level keys, NOT nested under `[model]`**:
   ```toml
   model_provider = "my_codex"
   model = "gpt-5.5"
   model_reasoning_effort = "high"
   disable_response_storage = true
   model_context_window = 1000000
   model_auto_compact_token_limit = 900000

   [model_providers.my_codex]
   name = "my_codex"
   base_url = "http://127.0.0.1:15721/v1"   # cc-switch proxy, NOT original API
   wire_api = "responses"
   requires_openai_auth = true

   [mcp_servers]
   # ... MCP server configs ...
   ```

4. Write `~/.codex/auth.json` with a placeholder (proxy handles real auth):
   ```json
   {"OPENAI_API_KEY": "sk-proxy"}
   ```

5. Verify: `codex exec "say hello"` — should respond via the proxy.

**Pitfall**: `codex doctor` will report "provider base URL route returned 404"
because the proxy doesn't serve `/v1/models`. This is a **false positive** —
actual API calls to `/v1/responses` work fine. Don't chase this error.

**Full details**: See `references/codex-cc-switch-proxy.md`

## Pitfalls

- **WSL `rm -rf` on Windows FS is slow** — use 120s+ timeouts for
  `%LOCALAPPDATA%` directories. The hermes-agent subdir has 5000+ files.
  `.cache/codex-runtimes/` can also hang — delete it separately with 120s timeout.
- **npm uninstall before delete** — deleting directories first can leave
  stale shim binaries that confuse `Get-Command`.
- **Hermes install.ps1 Playwright download** — the browser engine download
  (~300MB) can take several minutes. If the script times out, run it again —
  it detects existing installation and resumes from where it left off.
- **cc-switch config sync** — cc-switch writes configs to tool directories
  on change. If the tool directory doesn't exist yet (post-delete), the
  sync fails silently. Always reinstall tools BEFORE expecting cc-switch
  configs to appear.
- **API key masking in terminal output** — tools may display masked keys
  (`tp-cxm...5w6d`). The actual files contain full keys. Verify with
  `xxd .env` if in doubt.
- **Codex config.toml uses top-level keys, NOT `[model]` section** —
  `model_provider`, `model`, `model_reasoning_effort` etc. must be at the
  top level. Nesting them under `[model]` causes "config could not be loaded".
  See `references/codex-cc-switch-proxy.md` for the correct format.
- **Codex doctor reachability 404 is a false positive** — when using cc-switch
  proxy, `codex doctor` reports "provider base URL route returned 404" because
  the proxy doesn't serve `/v1/models`. Actual API calls (`/v1/responses`) work
  fine. Don't chase this error.
- **cc-switch stores masked API keys in DB** — the `api_key` field in the
  `providers` table contains a display-masked value. The real key is injected
  by the proxy at runtime. To configure a tool to use the proxy, point
  `base_url` at `http://127.0.0.1:15721/v1` and use a dummy auth value.

## Syncing MCP Servers & Skills from WSL to Windows

After reinstall, Windows Hermes will have builtin skills only. If the WSL
Hermes has custom MCP servers and local skills, sync them over:

### MCP Servers

```bash
# Read WSL config for mcp_servers section
grep -A 50 "mcp_servers:" ~/.hermes/config.yaml

# Append to Windows config (adjust paths for Windows)
cat >> /mnt/c/Users/lzy/AppData/Local/hermes/config.yaml << 'EOF'

mcp_servers:
  sequential-thinking:
    enabled: true
    command: npx
    args: [-y, '@modelcontextprotocol/server-sequential-thinking']
  fetch:
    enabled: true
    command: uvx
    args: [mcp-server-fetch]
  context7:
    enabled: true
    command: npx
    args: [-y, '@upstash/context7-mcp']
  holographic:
    enabled: true
    command: node
    args: ['C:\Users\lzy\AppData\Local\hermes\mcp-holographic\index.js']
EOF

# Verify
powershell.exe -Command "hermes mcp list"
```

### Holographic MCP Server

The holographic MCP server needs its own node_modules on Windows:

```bash
# Copy source (exclude node_modules)
rsync -av ~/.hermes/mcp-holographic/ \
  /mnt/c/Users/lzy/AppData/Local/hermes/mcp-holographic/ \
  --exclude="node_modules"

# Install Windows node_modules
powershell.exe -Command "cd 'C:\Users\lzy\AppData\Local\hermes\mcp-holographic'; npm install"
```

### Skills

```bash
# Copy all skills (merge with existing, don't overwrite)
rsync -av --ignore-existing ~/.hermes/skills/ \
  /mnt/c/Users/lzy/AppData/Local/hermes/skills/
```

**Pitfall**: Skills that reference WSL-specific paths (e.g. `~/.hermes/...`)
may need path adjustments for Windows. Check `SKILL.md` files for hardcoded
Linux paths after copying.

### Environment Variables

```bash
# Copy relevant env vars from WSL .env to Windows .env
grep "XIAOMI_BASE_URL" ~/.hermes/.env >> /mnt/c/Users/lzy/AppData/Local/hermes/.env
```

## Verification

After reinstall, verify all 4 tools:

```powershell
codex --version        # e.g. codex-cli 0.140.0
claude --version       # e.g. 2.1.178 (Claude Code)
opencode --version     # e.g. 1.17.7
hermes --version       # e.g. Hermes Agent v0.16.0
hermes config          # Should show model + provider, not "not configured"
hermes mcp list        # Should show all synced MCP servers
```

For Codex, also test actual API connectivity:
```powershell
codex exec "say hello"   # Should respond via cc-switch proxy
codex doctor             # auth ✓, config ✓, reachability ✗ is OK (false positive)
```
