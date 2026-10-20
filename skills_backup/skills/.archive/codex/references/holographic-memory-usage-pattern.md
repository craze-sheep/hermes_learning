# Holographic Memory Usage Pattern (from Codex AGENTS.md)

Codex actively uses holographic memory because its `~/.codex/AGENTS.md` contains **explicit, actionable usage instructions**. Hermes and other agents with only vague instructions ("use fact_store to add facts") do NOT proactively use memory. The difference is entirely in the prompt-level guidance.

## The AGENTS.md Pattern

Location: `~/.codex/AGENTS.md` (TOML-configured per tool, see `mcp-memory-unification.md` for config paths).

### Auto-Write Triggers (the key missing piece)

| Trigger | Tool | Action |
|---------|------|--------|
| User says "记住", "记一下", "保存" | `fact_store` | add |
| User corrects wrong info ("不对，应该是...") | `fact_store` | update |
| Learns user preference / environment / project info | `fact_store` | add |
| Before answering user's question | `fact_query` | search first |
| After using memory to answer | `fact_feedback` | helpful/unhelpful |

### Query Rules

Before answering questions about these topics, always `fact_query` search first:
- User info (name, preferences, habits)
- Project info (config, progress, issues)
- Environment info (tools, config, constraints)
- Historical info (what was done before, what was learned)

### Usage Scenario Matrix

| User asks | Tool | Action |
|-----------|------|--------|
| "我的项目是什么？" | fact_query | search |
| "关于我的所有信息" | fact_query | probe |
| "X 和 Y 有什么关系？" | fact_query | reason |
| "检查记忆有没有矛盾" | fact_query | contradict |
| "列出所有记忆" | fact_query | list |
| "记住这个" | fact_store | add |
| "更新这条信息" | fact_store | update |
| "删掉这条" | fact_store | remove |
| "这个信息有用" | fact_feedback | helpful |
| "这个信息过时了" | fact_feedback | unhelpful |

### Categories

| Category | Description | Example |
|----------|-------------|---------|
| user_pref | User preferences | "用户喜欢简洁回答" |
| project | Project info | "项目使用 Kubric 物理仿真" |
| tool | Tool config | "Codex 使用 GPT-5.5" |
| general | General info | "用户使用 WSL 环境" |

### Rules

1. Don't duplicate — `fact_query` search before adding
2. Keep descriptions concise
3. Update promptly when info changes
4. Always feedback after using memory
5. Don't store sensitive info (passwords, tokens)
6. Periodically check for contradictions via `fact_query` contradict

## Why This Works

The AGENTS.md pattern succeeds because it:
1. **Lists explicit triggers** — not "use it when appropriate" but "when X happens, do Y"
2. **Provides a scenario matrix** — maps user intents to specific tool calls
3. **Establishes query-before-answer rules** — forces memory lookup as a precondition
4. **Separates read/write concerns** — fact_query (read) vs fact_store (write) vs fact_feedback (quality)

## Applying to Other Agents

To make any agent (Hermes, Claude Code, OpenCode) use holographic memory proactively:

1. Add the trigger table to the agent's persona/system prompt or AGENTS.md
2. Add the query rules as a pre-answer checklist
3. Add the feedback rules as a post-answer step
4. Keep the scenario matrix visible so the agent can map user intents

For Hermes specifically: the persona.md (`~/.hermes/agent/persona.md`) should include these triggers. Currently it only says "Use fact_store to search, probe entities, reason across entities, or add facts" — which is too vague to drive proactive behavior.

## Related

- `mcp-memory-unification.md` — how to configure MCP servers across all 4 tools
- `mcp-compatibility-debugging.md` — Codex + MCP compatibility issues
- Hermes persona: `~/.hermes/agent/persona.md` (needs these triggers added)
- Codex AGENTS.md: `~/.codex/AGENTS.md` (the reference implementation)
