# Windows Reinstall & CC-Switch Config Recovery

When reinstalling AI coding tools on Windows, the Hermes config directory
(`%LOCALAPPDATA%\hermes\`) contains `config.yaml` and `.env` which hold
provider settings and API keys. If this directory is deleted, the config
is lost — but cc-switch preserves it.

## CC-Switch as Config Source of Truth

cc-switch stores all provider configs in its SQLite database:

```
~/.cc-switch/cc-switch.db
```

Key table: `providers` — each row has `(id, app_type, settings_config)`.

### Extracting a Hermes Provider Config

```sql
-- List all hermes providers
SELECT id, name, settings_config FROM providers WHERE app_type='hermes';

-- Get API key for a specific provider
SELECT json_extract(settings_config, '$.api_key')
FROM providers WHERE app_type='hermes' AND id='<provider_id>';

-- Get base_url
SELECT json_extract(settings_config, '$.base_url')
FROM providers WHERE app_type='hermes' AND id='<provider_id>';

-- Get default model
SELECT json_extract(settings_config, '$.model')
FROM providers WHERE app_type='hermes' AND id='<provider_id>';
```

### settings_config JSON Shape

```json
{
  "name": "",
  "base_url": "https://...",
  "api_key": "tp-cxm...",
  "models": [{"id": "mimo-v2.5-pro", "name": "mimo-v2.5-pro"}],
  "api_mode": "chat_completions",
  "model": "mimo-v2.5-pro"
}
```

## Reinstall Workflow

1. Delete old tool files (see main skill for exact paths)
2. Reinstall tools (npm for codex/claude/opencode, install.ps1 for hermes)
3. **Before first run**: restore config from cc-switch:
   ```bash
   # Query cc-switch DB for provider config
   sqlite3 ~/.cc-switch/cc-switch.db \
     "SELECT settings_config FROM providers WHERE app_type='hermes' AND id='<provider_id>';"
   
   # Write config.yaml with model + providers sections
   # Write .env with API key
   ```
4. Verify: `hermes config` should show the model and provider

## Pitfalls

- **Don't delete `~/.cc-switch/`** — it's the config backup. Only delete
  tool-specific directories.
- **WSL `rm -rf` on Windows filesystems is slow** — use longer timeouts
  (120s+) for `%LOCALAPPDATA%` directories. The `hermes-agent/` subdir
  alone has 5000+ files.
- **Hermes install.ps1 creates a backup config** at
  `config.yaml.bak.<timestamp>` — if the config was empty at install time,
  the backup will have `model: ''` and `providers: {}`. Use it as a
  template and merge in the cc-switch provider data.
- **API key masking**: terminal output may show `tp-cxm...5w6d` but the
  actual file contains the full key. Verify with `xxd .env` if unsure.

## Windows AI Tool File Locations (Quick Reference)

| Tool | Config Dir | Data/State | npm Binary |
|------|-----------|------------|------------|
| Codex | `~/.codex/` | `~/.cache/codex-runtimes/` | `npm/codex*` |
| Claude Code | `~/.claude/` + `~/.claude.json` | `AppData/Local/AnthropicClaude/` | `npm/claude*` |
| OpenCode | `~/.config/opencode/` | `~/.local/share/opencode/` | `npm/opencode*` |
| Hermes | `%LOCALAPPDATA%\hermes\` | same dir | `venv/Scripts/hermes.exe` |
| cc-switch | `~/.cc-switch/` | same dir (SQLite) | N/A (Electron app) |
