---
name: codegraph-setup
description: Initialize and use CodeGraph for code analysis — symbol search, call graph tracing, impact analysis.
tags: [codegraph, code-analysis, mcp, indexing]
triggers:
  - "codegraph"
  - "代码分析"
  - "调用链"
  - "谁调用了"
  - "影响范围"
---

# CodeGraph Setup & Usage

CodeGraph indexes a project's code structure and provides MCP tools for querying symbols, callers, callees, and impact analysis.

## Initialize a project

```bash
cd /path/to/project
codegraph init
codegraph index
```

The `index` command scans all source files and builds a SQLite database in `.codegraph/`.

## MCP Tools (available via Hermes)

| Tool | Purpose |
|------|---------|
| `codegraph_status` | Index stats (files, nodes, edges) |
| `codegraph_files` | Project file tree |
| `codegraph_search` | Find symbols by name |
| `codegraph_node` | Symbol details + callers/callees |
| `codegraph_context` | Full task context (best for first query) |
| `codegraph_explore` | Multi-symbol source in one call |
| `codegraph_trace` | Call path from A to B |
| `codegraph_impact` | Impact radius of changing a symbol |

## Recommended query order

1. `codegraph_context` — usually enough for a first answer
2. `codegraph_explore` — when you need to see source of several related symbols
3. `codegraph_trace` — when following a specific call chain
4. `codegraph_impact` — when assessing change risk

## Pitfalls

- Must call `codegraph init` + `codegraph index` before any query
- Index is project-scoped — pass `projectPath` if not in the default project
- `codegraph_explore` budget is capped — don't call repeatedly; use `codegraph_node` to drill deeper
- Dynamic dispatch (callbacks, descriptors) breaks static call tracing — `codegraph_trace` will say where it breaks
