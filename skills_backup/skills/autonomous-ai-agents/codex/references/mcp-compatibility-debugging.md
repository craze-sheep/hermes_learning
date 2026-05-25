## sql.js FTS5 Incompatibility (discovered 2026-05-25)

**Problem:** holographic MCP server uses `sql.js` (WASM SQLite), which does NOT support FTS5. If the database was created or modified by system SQLite (which supports FTS5), it may contain FTS5 tables (`facts_fts`, `facts_fts_data`, etc.). When sql.js tries to load this database, it fails with `no such module: fts5`.

**Symptoms:**
- `danger-full-access` mode: `fact_store` returns `"Error: no such module: fts5"`
- `workspace-write` mode: shows "user cancelled MCP tool call" (hides the real error)

**Detection:**
```bash
sqlite3 ~/.hermes/memory_store.db "SELECT name FROM sqlite_master WHERE sql LIKE '%fts5%';"
```

**Fix:** Remove FTS5 tables:
```bash
sqlite3 ~/.hermes/memory_store.db "
DROP TABLE IF EXISTS facts_fts;
DROP TABLE IF EXISTS facts_fts_data;
DROP TABLE IF EXISTS facts_fts_idx;
DROP TABLE IF EXISTS facts_fts_docsize;
DROP TABLE IF EXISTS facts_fts_config;
"
```

**Root cause:** Hermes's built-in holographic provider (plugin mode) uses Python's sqlite3 module which supports FTS5. But the MCP server for external tools uses sql.js (WASM) which doesn't. If Hermes ever creates FTS5 tables via the plugin, the MCP server breaks.

**Prevention:** The MCP server's `initDb()` only creates regular tables (no FTS5). FTS5 tables are leftovers from the plugin provider. After removing them, both plugin and MCP access work.

## Codex Sandbox vs MCP Tool Behavior

| Sandbox Mode | MCP read-only tool | MCP destructive tool |
|---|---|---|
| `workspace-write` + hooks OK | ✅ works | ✅ works (with PermissionRequest) |
| `workspace-write` + hooks broken | ❌ "user cancelled" | ❌ "user cancelled" |
| `danger-full-access` | ✅ works | ✅ works (no approval needed) |
| `approval: never` + any sandbox | ✅ if readOnlyHint | ❌ silently cancelled |

**Key insight:** `workspace-write` sandbox + broken hooks shows "user cancelled" for ALL MCP tools. `danger-full-access` bypasses this and shows the REAL error. Use `danger-full-access` for debugging MCP issues.

## Hook Hash Verification

Codex tracks hook script hashes in `~/.codex/config.toml` under `[hooks.state]`. When you modify a hook script:

1. Compute new hash: `sha256sum ~/.codex/approve-hook.sh`
2. Update config.toml: `trusted_hash = "sha256:<hash>"`
3. The key format is: `[hooks.state."<hooks.json-path>:<event-name>:<index>:<index>"]`

If hash doesn't match, Codex may silently skip the hook.

## Debugging Workflow

When Codex MCP tools fail:
1. Check `approval: never` mode → if yes, use `danger-full-access` to see real error
2. Check hooks.json → not empty, PermissionRequest exists
3. Check hook hash → matches config.toml
4. Check hook output format → `{"hookSpecificOutput":{"hookEventName":"PermissionRequest","decision":{"behavior":"allow"}}}`
5. Check MCP server annotations → `readOnlyHint: true` for read-only tools
6. Check database compatibility → no FTS5 tables if using sql.js
