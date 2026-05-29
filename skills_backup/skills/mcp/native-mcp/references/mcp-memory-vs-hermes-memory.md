# MCP Memory vs Hermes Memory — Three Systems, Not Two

## The Architecture

There are actually THREE memory systems, not two:

| System | Storage | Tool | Who Can Read |
|--------|---------|------|--------------|
| **Hermes Built-in** | `~/.hermes/memories/MEMORY.md` + `USER.md` | `memory` | Hermes only |
| **MCP Memory Server** | `@modelcontextprotocol/server-memory` internal | `mcp_memory_*` | Per-tool (each has own storage) |
| **Holographic Memory** | `~/.hermes/memory_store.db` (SQLite) | `fact_store` / `fact_feedback` | All tools sharing the MCP server |

**The Holographic Memory system is the recommended solution for cross-tool shared memory.**

## Recommended Setup: Holographic Memory

### 1. MCP Server (already built)

Location: `~/.hermes/mcp-holographic/index.js`
Database: `~/.hermes/memory_store.db`

### 2. Configure ALL tools to use the same holographic MCP server

**Hermes** (`~/.hermes/config.yaml`):
```yaml
memory:
  provider: holographic
mcp_servers:
  # ... other servers ...
```

**Claude Code** (`~/.claude.json`):
```json
{
  "mcpServers": {
    "holographic": {
      "type": "stdio",
      "command": "node",
      "args": ["/home/user/.hermes/mcp-holographic/index.js"]
    }
  }
}
```

**Codex** (`~/.codex/config.toml`):
```toml
[mcp_servers.holographic]
type = "stdio"
command = "node"
args = ["/home/user/.hermes/mcp-holographic/index.js"]
```

**OpenCode** (`~/.config/opencode/opencode.json`):
```json
{
  "mcp": {
    "holographic": {
      "command": ["node", "/home/user/.hermes/mcp-holographic/index.js"],
      "enabled": true,
      "type": "local"
    }
  }
}
```

### 3. Add instruction files so tools know WHEN to use fact_store

Each tool needs an instruction file telling it when to use `fact_store`:

| Tool | Instruction File | Format |
|------|-----------------|--------|
| Hermes | `~/.hermes/AGENTS.md` | Markdown (auto-loaded) |
| Claude Code | `~/.claude/CLAUDE.md` | Markdown (auto-loaded) |
| Codex | `~/.codex/AGENTS.md` | Markdown (auto-loaded) |
| OpenCode | `~/.config/opencode/AGENTS.md` | Markdown (auto-loaded) |

Content for each: see `references/holographic-memory-agents-template.md`.

### 4. Hermes has TWO memory tools — know the difference

| Tool | Writes To | Shared? | Use For |
|------|-----------|---------|---------|
| `memory` | MEMORY.md/USER.md | ❌ Hermes only | Hermes-private context, session state |
| `fact_store` | memory_store.db | ✅ All tools | User prefs, project info, env facts |

## Migration Approach (MEMORY.md → fact_store)

When consolidating two memory systems:

1. **Audit existing MEMORY.md** — identify distinct facts, categorize (user_pref/project/tool/general)
2. **Check fact_store for duplicates** — query existing facts before adding
3. **Add missing facts** with proper categories and tags
4. **Remove test/dummy data** from fact_store
5. **Keep MEMORY.md for Hermes-private context only** — session state, internal prompts

**What to store in fact_store vs MEMORY.md:**

| fact_store (shared) | MEMORY.md (Hermes only) |
|---------------------|------------------------|
| User preferences | Current task state |
| Project config | Internal prompts |
| Environment info | Temporary notes |
| Tool quirks/lessons | Session-specific context |
| Known bugs/workarounds | |

## Disabling memory entirely (recommended long-term)

**As of May 2026, `memory.provider: holographic` in config.yaml does NOT actually work** — the memory system still writes to `~/.hermes/memories/MEMORY.md` and `USER.md` files. The `memory_banks` table in the SQLite DB stays empty. The provider config key exists but the holographic backend is not implemented.

**To fully switch to fact_store only:**

```bash
hermes config set memory.memory_enabled false
hermes config set memory.user_profile_enabled false
hermes config set agent.disabled_toolsets '["memory"]'
```

**Trade-off:** Hermes won't auto-inject memory into the system prompt. The agent must explicitly call `fact_store search` to retrieve memories. This adds one tool call per turn but eliminates the dual-system problem.

**Codex's recommended long-term approach:** Implement a retrieval-based injection layer in Hermes that auto-queries relevant high-trust facts per turn (max 8, min_trust 0.6), then disable MEMORY.md auto-injection entirely. This preserves the "auto-injection" benefit of memory while using holographic DB as the single source.

**Hermes memory file location:** `~/.hermes/memories/MEMORY.md` (note the `memories/` subdirectory, NOT `~/.hermes/MEMORY.md`)

## Pitfalls

### Pitfall: `memory.provider: holographic` is a no-op
Configuring `memory.provider: holographic` in config.yaml does NOT make the memory tool write to the holographic DB. The memory system ignores this setting and continues writing to files. Don't rely on it — disable memory and use fact_store directly instead.

### Pitfall: Codex hooks hang when Clawd is not running
Codex's `hooks.json` calls Clawd on `localhost:23333`. If Clawd is not running, `PermissionRequest` hooks hang for 600s timeout. **Fix:** Temporarily rename `~/.codex/hooks.json` to `hooks.json.bak`, run Codex, then restore.

### Pitfall: `hermes mcp serve` is stdio, NOT HTTP
When configuring Claude Code/Codex/OpenCode to connect TO Hermes, use `hermes mcp serve` (stdio). Do NOT use `mcp-remote http://localhost:3000` — Hermes gateway does not listen on a port by default.

```json
// ✅ Correct
{"command": "hermes", "args": ["mcp", "serve"]}

// ❌ Wrong — port 3000 likely not listening
{"command": "npx", "args": ["-y", "@anthropic-ai/mcp-remote", "http://localhost:3000"]}
```

### Pitfall: fact_store AGENTS.md not auto-shared
The `~/.hermes/AGENTS.md` file is only read by Hermes. Each tool needs its own copy at its expected location. Copy the template to all four locations.

### Pitfall: Hermes uses `memory` by default, not `fact_store`
Even with holographic provider configured, Hermes's system prompt prominently shows the `memory` tool. The agent tends to use `memory` instead of `fact_store`. Make the AGENTS.md instructions prominent and specific about when to use `fact_store`.

### Pitfall: WSL2 `ss -tlnp` doesn't show Windows ports
Even with WSL2 `networkingMode=mirrored`, `ss -tlnp` does NOT show Windows host ports. Use `curl -s --connect-timeout 3 http://localhost:PORT/` or `powershell.exe -Command "Get-NetTCPConnection -LocalPort PORT"` to verify Windows services are listening.

### Pitfall: Hermes fact_store wrapper doesn't expose all MCP server actions
The holographic MCP server (`~/.hermes/mcp-holographic/index.js`) supports `dedup` and `merge` actions in its Zod schema, but Hermes's built-in `fact_store` tool wrapper (`plugins/memory/holographic/__init__.py`) only handles: add, search, probe, related, reason, contradict, update, remove, list. Calling `dedup` or `merge` through Hermes returns "Unknown action".

**Impact:** Claude Code, Codex, and OpenCode (direct MCP clients) CAN use dedup/merge. Hermes CANNOT — it goes through the Python wrapper which filters actions.

**Workaround:** Use `delegate_task` to have Claude Code run dedup, or call the MCP server directly via terminal.

## Verification

```bash
# Check holographic DB has data
/home/lzy/miniconda3/bin/python3 -c "
import sqlite3
conn = sqlite3.connect('/home/user/.hermes/memory_store.db')
cur = conn.cursor()
cur.execute('SELECT COUNT(*) FROM facts')
print(f'Total facts: {cur.fetchone()[0]}')
cur.execute('SELECT category, COUNT(*) FROM facts GROUP BY category')
for cat, cnt in cur.fetchall():
    print(f'  {cat}: {cnt}')
conn.close()
"

# Test MCP server starts
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}' | timeout 5 node ~/.hermes/mcp-holographic/index.js
```
