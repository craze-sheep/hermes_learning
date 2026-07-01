# AI Coding Tools: Cleanup & Reinstall on Windows from WSL

Workflow for fully removing and reinstalling codex, claude-code, opencode, and hermes on the Windows host, executed from WSL.

## Why From WSL

All four tools store config/data on the Windows filesystem. WSL has direct access via `/mnt/c/`. PowerShell commands can be invoked via `/mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe -Command "..."`.

## File Locations per Tool

### Codex (OpenAI)
| Type | Path |
|------|------|
| Config + data | `~/.codex/` |
| Runtime cache | `~/.cache/codex-runtimes/` |
| npm binaries | `AppData/Roaming/npm/codex`, `codex.cmd`, `codex.ps1` |

### Claude Code (Anthropic)
| Type | Path |
|------|------|
| Config + data | `~/.claude/` |
| Config file | `~/.claude.json` |
| App data | `AppData/Local/AnthropicClaude/` |
| CLI runtime | `AppData/Local/claude-cli-nodejs/` |
| App data | `AppData/Roaming/Claude/` |
| npm binaries | `AppData/Roaming/npm/claude`, `claude.cmd`, `claude.ps1` |
| VSCode ext | `.vscode/extensions/anthropic.claude-code-*` |
| Temp | `AppData/Local/Temp/claude/` |

### OpenCode
| Type | Path |
|------|------|
| Config | `~/.config/opencode/` |
| Data (DB) | `~/.local/share/opencode/` |
| State | `~/.local/state/opencode/` |
| Cache | `~/.cache/opencode/` |
| npm binaries | `AppData/Roaming/npm/opencode`, `opencode.cmd`, `opencode.exe`, `opencode.ps1` |
| npm package | `AppData/Roaming/npm/node_modules/opencode-ai/` |
| VSCode ext | `.vscode/extensions/tanishqkancharla.opencode-vscode-*` |
| Temp | `AppData/Local/Temp/opencode/` |

### Hermes (Windows-native)
| Type | Path |
|------|------|
| Everything | `AppData/Local/hermes/` (bin, hermes-agent repo, venv, config, data) |
| Binary | `AppData/Local/hermes/hermes-agent/venv/Scripts/hermes.exe` |

## Important: DO NOT Delete

- `~/.cc-switch/` — separate claude-code profile switcher tool
- `~/ai-shared/` — shared backups, skills, configs
- Any VSCode extensions unrelated to these tools
- Other npm global packages

## Cleanup Commands (WSL)

All paths are under `/mnt/c/Users/<USERNAME>/`. Set `WINHOME=/mnt/c/Users/lzy` first.

```bash
WINHOME=/mnt/c/Users/lzy

# Codex
rm -rf $WINHOME/.codex $WINHOME/.cache/codex-runtimes
rm -f $WINHOME/AppData/Roaming/npm/codex*

# Claude Code
rm -rf $WINHOME/.claude $WINHOME/.claude.json
rm -rf $WINHOME/AppData/Local/AnthropicClaude $WINHOME/AppData/Local/claude-cli-nodejs
rm -rf "$WINHOME/AppData/Roaming/Claude"
rm -f $WINHOME/AppData/Roaming/npm/claude*
rm -rf $WINHOME/.vscode/extensions/anthropic.claude-code-*
rm -rf $WINHOME/AppData/Local/Temp/claude

# OpenCode
rm -rf $WINHOME/.config/opencode $WINHOME/.local/share/opencode
rm -rf $WINHOME/.local/state/opencode $WINHOME/.cache/opencode
rm -f $WINHOME/AppData/Roaming/npm/opencode*
rm -rf $WINHOME/AppData/Roaming/npm/node_modules/opencode-ai
rm -rf $WINHOME/.vscode/extensions/tanishqkancharla.opencode-vscode-*
rm -rf $WINHOME/AppData/Local/Temp/opencode

# Hermes
rm -rf $WINHOME/AppData/Local/hermes
```

### Timeout Pitfall

WSL `rm -rf` on `/mnt/c/` is VERY slow (NTFS cross-filesystem). Use timeout=120s+ per operation. If a single `rm -rf` times out, break it into smaller pieces (delete subdirs first, then parent).

## Reinstall Commands

### npm tools (codex, claude-code, opencode)

Access Windows npm via PowerShell:

```bash
PS="powershell.exe -Command"  # alias shorthand, use full path in practice

# Install all three in parallel
powershell.exe -Command "npm install -g @openai/codex"
powershell.exe -Command "npm install -g @anthropic-ai/claude-code"
powershell.exe -Command "npm install -g opencode-ai"

# Verify
powershell.exe -Command "codex --version; claude --version; opencode --version"
```

### Hermes (Windows-native)

```bash
powershell.exe -Command "irm https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.ps1 | iex"
```

**Pitfalls:**
- The install script clones the repo (~5000 files) and creates a venv — can take 3-5 minutes.
- Playwright browser download (Chromium ~184MB) happens at the end and may timeout.
- If interrupted, re-run the script — it detects existing installation and resumes.
- If git fetch fails (connection reset), the repo may already be cloned. Check `$WINHOME/AppData/Local/hermes/hermes-agent/venv/Scripts/hermes.exe` — if it exists, the install is functionally complete.
- The binary ends up in `venv/Scripts/hermes.exe` and gets added to User PATH automatically.

## Verification Checklist

After reinstall, verify from WSL:

```bash
powershell.exe -Command "codex --version"        # expect: codex-cli X.Y.Z
powershell.exe -Command "claude --version"       # expect: X.Y.Z (Claude Code)
powershell.exe -Command "opencode --version"     # expect: X.Y.Z
powershell.exe -Command "hermes --version"       # expect: Hermes Agent vX.Y.Z
```

All four should return version numbers without errors. Config/API keys will need to be re-configured after cleanup.

## Config Recovery from cc-switch

cc-switch stores all provider configurations in its SQLite database. After a clean reinstall, configs can be recovered without manual re-entry.

### Hermes Config Recovery

```bash
DB=/mnt/c/Users/lzy/.cc-switch/cc-switch.db

# Get Hermes provider config
sqlite3 "$DB" "SELECT settings_config FROM providers WHERE app_type='hermes';"

# Extract API key (full key, not masked)
sqlite3 "$DB" "SELECT json_extract(settings_config, '$.api_key') FROM providers WHERE app_type='hermes' AND id='xiaomi';"

# Restore config.yaml: start from the backup created by hermes first-run,
# then merge in model/provider settings from cc-switch
cp $WINHOME/AppData/Local/hermes/config.yaml.bak.* $WINHOME/AppData/Local/hermes/config.yaml
# Edit model and providers sections to match cc-switch values
```

### Codex Config Recovery (cc-switch Proxy)

cc-switch runs a **local proxy** on `127.0.0.1:15721` that injects real API keys. The proxy is transparent — tools connect to it as if it were the real API.

```bash
# 1. Get provider config from cc-switch
sqlite3 "$DB" "SELECT json_extract(settings_config, '$.config') FROM providers WHERE app_type='codex' AND id='mycodex-1779092949064';"

# 2. Create config.toml with proxy base_url (NOT the real API URL)
cat > $WINHOME/.codex/config.toml << 'TOML'
model_provider = "my_codex"
model = "gpt-5.5"
model_reasoning_effort = "high"
disable_response_storage = true

model_context_window = 1000000
model_auto_compact_token_limit = 900000
[model_providers.my_codex]
name = "my_codex"
base_url = "http://127.0.0.1:15721/v1"
wire_api = "responses"
requires_openai_auth = true
TOML

# 3. Create auth.json with placeholder (proxy handles real auth)
echo '{"OPENAI_API_KEY": "sk-proxy"}' > $WINHOME/.codex/auth.json
```

**Key insight:** The API keys in cc-switch DB appear masked (`sk-OaC...Oecs`) but this is intentional — the proxy injects the real key. Don't try to extract the real key; configure tools to use the proxy instead.

**Pitfall:** `codex doctor` will report `✗ reachability provider base URL route returned 404` because the proxy doesn't serve `/v1/models`. This is a false positive — actual `/v1/responses` calls work fine.
