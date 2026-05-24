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
