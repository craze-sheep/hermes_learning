# Holographic Memory MCP Bridge (Current Implementation)

Reference: `~/.hermes/mcp-holographic/index.js`

## Architecture

Bridges Hermes Holographic memory (SQLite knowledge graph) to Claude Code, OpenCode, Codex, Hermes via MCP. All tools share one database (`~/.hermes/memory_store.db`).

## Stack

- **Database**: better-sqlite3 (migrated from sql.js for FTS5 support)
- **Runtime**: Node.js ES modules
- **Protocol**: MCP stdio transport

## Tools (Read-Write Separated)

| Tool | Purpose | Annotations | Actions |
|------|---------|-------------|---------|
| `fact_query` | Read-only queries | `readOnlyHint: true, destructiveHint: false` | search, probe, related, reason, contradict, list |
| `fact_store` | Write operations | `readOnlyHint: false, destructiveHint: true` | add, update, remove |
| `fact_feedback` | Rate facts | `readOnlyHint: false, destructiveHint: true` | helpful, unhelpful |

**Why split read/write:** Codex in workspace-write sandbox can call `fact_query` without PermissionRequest hooks (readOnlyHint bypasses approval). Claude Code also respects annotations for auto-approve decisions.

## Database Schema

```sql
CREATE TABLE facts (
  fact_id INTEGER PRIMARY KEY AUTOINCREMENT,
  content TEXT NOT NULL UNIQUE,
  category TEXT DEFAULT 'general',
  tags TEXT DEFAULT '',
  trust_score REAL DEFAULT 0.5,
  retrieval_count INTEGER DEFAULT 0,
  helpful_count INTEGER DEFAULT 0,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE entities (
  entity_id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL UNIQUE,
  entity_type TEXT DEFAULT 'unknown',
  aliases TEXT DEFAULT '',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE fact_entities (
  fact_id INTEGER REFERENCES facts(fact_id),
  entity_id INTEGER REFERENCES entities(entity_id),
  PRIMARY KEY (fact_id, entity_id)
);
```

## Migration: sql.js → better-sqlite3

1. Export data from sql.js DB: `const data = db.export(); writeFileSync('backup.db', Buffer.from(data));`
2. Remove FTS5 tables if present: `DROP TABLE IF EXISTS facts_fts*`
3. Open with better-sqlite3: `const db = new Database('memory_store.db')`
4. Verify: `integrity_check`, count rows, test write+read

**Key difference:** better-sqlite3 is synchronous (no saveDb() needed), sql.js requires manual export after writes.

## AGENTS.md Template

See `references/multi-tool-agents-template.md` for the standardized instruction file content placed in each tool's config directory (`~/.hermes/AGENTS.md`, `~/.claude/CLAUDE.md`, `~/.codex/AGENTS.md`, `~/.config/opencode/AGENTS.md`).

## Config Locations

| Tool | Config Path | Instruction File |
|------|-------------|------------------|
| Hermes | `~/.hermes/config.yaml` (mcp_servers) | `~/.hermes/AGENTS.md` |
| Claude Code | `~/.claude.json` (mcpServers) | `~/.claude/CLAUDE.md` |
| OpenCode | `~/.config/opencode/opencode.json` (mcp) | `~/.config/opencode/AGENTS.md` |
| Codex | `~/.codex/config.toml` (mcp_servers) | `~/.codex/AGENTS.md` |

## Common Pitfalls

1. **Claude Code memory MCP residual** — `~/.claude.json` may still have old `memory` MCP from `@modelcontextprotocol/server-memory`. Remove it to avoid confusion.
2. **Codex memory MCP residual** — `~/.codex/config.toml` may still have `[mcp_servers.memory]` section. Remove it.
3. **Old MEMORY.md/USER.md injection** — Even with `memory_enabled: false` and `disabled_toolsets: ["memory"]`, the files in `~/.hermes/memories/` still get injected into Hermes system prompt. Must delete the files to stop injection.
4. **npx vs pre-installed node** — Use pre-installed node paths for context7 and sequential-thinking to avoid npx download delays.
