# MCP Memory vs Hermes Memory — Critical Distinction

## The Confusion

Users often assume that configuring the MCP `memory` server gives Claude Code/Codex/OpenCode access to Hermes's persistent memory (`~/.hermes/memories/`). **This is FALSE.**

## Two Separate Systems

| System | Storage Location | Used By |
|--------|------------------|---------|
| **Hermes Memory** | `~/.hermes/memories/MEMORY.md` + `USER.md` | Hermes Agent only |
| **MCP Memory Server** | `@modelcontextprotocol/server-memory` internal storage | Claude Code, Codex, OpenCode |

They are **completely independent** — no shared data, no sync, no bridge.

## Why This Matters

When you configure:
```yaml
mcp_servers:
  memory:
    command: "npx"
    args: ["-y", "@modelcontextprotocol/server-memory"]
```

This gives Claude Code a **separate** knowledge graph memory, NOT access to Hermes's memory.

## Solutions for Shared Memory

### Option 1: Use Hermes as MCP Server (Recommended)

Configure Claude Code/Codex/OpenCode to connect TO Hermes as an MCP server:

```json
// ~/.claude.json (global config)
{
  "mcpServers": {
    "hermes": {
      "command": "hermes",
      "args": ["mcp", "serve"]
    }
  }
}
```

This lets external tools access Hermes's memory, sessions, and tools via MCP.

### Option 2: Manual Sync

Periodically copy Hermes memory to MCP memory location (not recommended — fragile).

### Option 3: Accept Separation

Keep both systems independent. Use Hermes memory for Hermes conversations, MCP memory for Claude Code conversations.

## Configuration Commands

```bash
# Increase Hermes memory limits
hermes config set memory.memory_char_limit 10000
hermes config set memory.user_char_limit 5000

# Check current limits
cat ~/.hermes/config.yaml | grep -A 10 "memory:"
```

## Key Takeaway

**MCP memory server ≠ Hermes memory.** They are separate systems. To share Hermes memory with external tools, configure Hermes as an MCP server (Option 1).
