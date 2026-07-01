# Shared AI Rules

This machine uses one shared AI memory and tool layer for Codex, Claude Code,
OpenCode, Hermes, and Reasonix across WSL and Windows.

## Holographic Memory

All agents share the same Holographic Memory database:

```text
/home/lzy/.hermes/memory_store.db
```

Windows agents must access it through the WSL MCP server, not through a local
Windows copy:

```text
wsl.exe -d Ubuntu-24.04 --exec /home/lzy/miniconda3/bin/node /home/lzy/.hermes/mcp-holographic/index.js
```

Use these MCP tools when available:

| Tool | Purpose | Allowed operations |
| --- | --- | --- |
| `fact_query` | read memory | `search`, `probe`, `related`, `reason`, `contradict`, `list` |
| `fact_store` | write memory | `add`, `update`, `remove` |
| `fact_feedback` | rate memory quality | `helpful`, `unhelpful` |

### Required proactive use

- Before answering questions about the user, preferences, environment, tools,
  project state, configuration, or previous work, call `fact_query search`.
- Before changing AI/tool configuration, call `fact_query search` for relevant
  setup history.
- When the user says "remember", "记住", "记一下", "保存", or similar, use
  `fact_store add`.
- When the user corrects a fact, search for the existing fact first, then use
  `fact_store update` instead of adding a duplicate.
- When important non-sensitive environment, project, or tool configuration is
  learned or completed, save a concise fact with `fact_store add`.
- After using a remembered fact in an answer, call `fact_feedback helpful` if
  the fact was accurate, or `fact_feedback unhelpful` if it was stale/wrong.

### Memory hygiene

- Search before adding so duplicates are avoided.
- Keep facts short, concrete, and useful.
- Never store passwords, API keys, tokens, cookies, private credentials, or
  other secrets.
- Claude Code must not use its file-based long-term memory under
  `~/.claude/projects/*/memory/` for user/project/tool facts. Use Holographic
  Memory instead.
- Prefer categories: `user_pref`, `project`, `tool`, `general`.
- Use lowercase English tags separated by commas, for example
  `windows,wsl,mcp`.
- If Holographic tools are unavailable in a client, say that memory tools are
  unavailable in that session and continue with local context.

### Examples

```json
{"action":"search","query":"Windows WSL holographic MCP"}
```

```json
{"action":"add","content":"Windows and WSL AI tools use WSL Holographic Memory through the holographic MCP server.","category":"tool","tags":"windows,wsl,mcp,memory"}
```

```json
{"action":"update","fact_id":123,"content":"Updated concise fact"}
```

## CodeGraph

When `codegraph_*` tools are available, use them proactively for codebase
structure instead of rebuilding the same picture with text search.

- For "how does this work", architecture, feature, or bug-context questions,
  call `codegraph_context` first.
- For "where is X defined", use `codegraph_search`.
- For "what calls X", use `codegraph_callers`.
- For "what does X call", use `codegraph_callees`.
- For "how does X reach Y", use `codegraph_trace`.
- For "what would break if I changed X", use `codegraph_impact`.
- For source of one symbol, use `codegraph_node`.
- For source of several related symbols, use one `codegraph_explore` call.
- For file structure, use `codegraph_files`.
- Use `rg` or file reads only for literal text queries or after a specific file
  is already known.

If CodeGraph reports that the project is not initialized, ask whether to run
`codegraph init -i`.

## PDF and Docling

When handling PDFs, especially scanned PDFs or image-based PDFs, prefer the
`docling-pdf` or `pdf` skill if available. Windows agents should call the WSL
docling environment/tooling instead of installing a separate Windows PyTorch
stack unless the user explicitly asks for a native Windows install.

## Shared Skills and Tools

- Treat WSL as the source of truth for shared skills and MCP servers.
- Do not create a second Windows memory database.
- Do not fork shared skills unless the user explicitly asks.
- Preserve existing unrelated configuration and secrets.
