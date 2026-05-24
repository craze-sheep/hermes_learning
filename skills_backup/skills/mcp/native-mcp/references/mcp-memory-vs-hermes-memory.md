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

**Migration pattern:** When setting up, migrate key facts from MEMORY.md to fact_store. Then:
- **fact_store**: shared facts (user prefs, project config, environment, tool quirks)
- **memory**: Hermes-private context (session state, internal prompts, temporary notes)

## Pitfalls

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
