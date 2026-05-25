# Holographic Memory — AGENTS.md Template

Use this template as the content for each tool's instruction file.

## Template

```markdown
# Shared Memory System (Holographic Memory)

You have `holographic` MCP server connected to a shared memory database.
All AI tools (Hermes, Claude Code, Codex, OpenCode) share this database.

## When to use fact_store

1. User says "remember", "note", "save" → `fact_store add`
2. User corrects information → `fact_store update`
3. Learned user preference / environment / project info → `fact_store add`
4. Before answering user questions → `fact_store search` first
5. After using memory → `fact_feedback helpful/unhelpful`

## Common operations

- Search: `fact_store(action="search", query="keyword")`
- Probe: `fact_store(action="probe", entity="name")`
- Add: `fact_store(action="add", content="fact", category="user_pref|project|tool|general", tags="tag1,tag2")`
- Update: `fact_store(action="update", fact_id=123, content="new content")`
- Feedback: `fact_feedback(action="helpful", fact_id=123)`

## Categories

| Category | Use For | Example |
|----------|---------|---------|
| user_pref | User preferences | "User prefers concise answers" |
| project | Project info | "Project uses Kubric physics simulation" |
| tool | Tool config | "Codex uses GPT-5.5" |
| general | Environment | "User runs WSL2 with RTX 4060" |

## Rules

- Search before adding to avoid duplicates
- Keep facts concise
- Don't save passwords/tokens
- Update when info changes
```

## File Locations

| Tool | Path |
|------|------|
| Hermes | `~/.hermes/AGENTS.md` |
| Claude Code | `~/.claude/CLAUDE.md` |
| Codex | `~/.codex/AGENTS.md` |
| OpenCode | `~/.config/opencode/AGENTS.md` |

## Deployment Verification

After deploying, verify all tools can access the shared DB:
```bash
# Check DB has facts
/home/lzy/miniconda3/bin/python3 -c "
import sqlite3
conn = sqlite3.connect('~/.hermes/memory_store.db')
cur = conn.cursor()
cur.execute('SELECT COUNT(*) FROM facts')
print(f'Total facts: {cur.fetchone()[0]}')
conn.close()
"

# Test MCP server starts
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}' | timeout 5 node ~/.hermes/mcp-holographic/index.js
```

## Pitfall: Duplicate memory servers
If a tool has both `memory` (server-memory) and `holographic` MCP servers, remove `memory` — it creates a separate per-tool storage that doesn't share with others. Holographic already provides all memory functionality.
