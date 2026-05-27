# CodeGraph MCP Server — Usage Guide

CodeGraph is a code intelligence MCP server that indexes a project and provides static analysis tools (call graphs, impact analysis, symbol search). It connects to Hermes via the `codegraph` MCP server config.

## Setup

```bash
# Install (if not already)
npm install -g codegraph   # or pip install codegraph

# Verify
which codegraph
hermes mcp list | grep codegraph
```

Config in `~/.hermes/config.yaml`:
```yaml
mcp_servers:
  codegraph:
    command: codegraph
    args:
      - serve
      - --mcp
    timeout: 120
    connect_timeout: 60
```

## Per-Project Workflow

Must be run in the project root. Creates `.codegraph/` directory.

```bash
cd /path/to/project
codegraph init          # Initialize .codegraph/ directory
codegraph index         # Scan files, build index (nodes + edges)
codegraph sync          # Incremental update (only changed files)
codegraph status        # Show index stats
codegraph uninit        # Remove .codegraph/ entirely
```

## CLI Commands (standalone, no MCP needed)

```bash
codegraph files                          # Show project file structure
codegraph query "symbol_name"            # Search for symbols
codegraph callers <symbol>               # Who calls this function
codegraph callees <symbol>               # What does this function call
codegraph impact <symbol>                # What code is affected by changing this
codegraph context "task description"     # Build context markdown for a task
codegraph affected [files...]            # Find tests affected by changed files
codegraph trace --from A --to B          # Trace call path between two symbols
```

## MCP Tools (available inside Hermes sessions)

After `codegraph init && codegraph index`, these tools are available:

| Tool | Purpose | When to use |
|------|---------|-------------|
| `codegraph_files` | Project file tree with metadata | First step when exploring a new project |
| `codegraph_search` | Find symbols by name (returns locations only) | Quick lookup before diving deeper |
| `codegraph_node` | One symbol's details + callers/callees trail | Walk the call graph hop-by-hop |
| `codegraph_context` | Auto-compose search + node + callers + callees | Best first tool for "how does X work" questions |
| `codegraph_explore` | Multiple related symbols grouped by file | Inspect many symbols at once (prefer over multiple node calls) |
| `codegraph_callers` | All functions that call a symbol | Understanding usage and impact |
| `codegraph_callees` | All functions a symbol calls | Understanding dependencies |
| `codegraph_impact` | Impact radius of changing a symbol | Before modifying code, assess blast radius |
| `codegraph_trace` | Call path from A to B | "How does X reach Y?" flow questions |

## Interpreting Status Output

```
Files: 24          # Source files indexed
Nodes: 382         # Symbols found (functions, classes, variables, imports, etc.)
Edges: 866         # Relationships (calls, references, imports)
DB Size: 0.91 MB   # SQLite database size
Backend: node:sqlite — built-in (full WAL)

Nodes by Kind:
  function   158    # Standalone functions
  method      37    # Class methods
  class       10    # Classes/structs
  import      98    # Import statements
  variable    40    # Global/static variables

Files by Language:
  c           21    # Language distribution
  python       3
```

## Pitfalls

1. **Must init + index first** — MCP tools fail with "No CodeGraph project is loaded" if `.codegraph/` doesn't exist
2. **`codegraph sync` not `codegraph index`** for updates — sync is incremental, index rebuilds from scratch
3. **`codegraph_context` > chaining search+node** — context composes them in one call, cheaper and faster
4. **`codegraph_explore` > multiple node calls** — explore fetches many symbols in one capped call; 8 separate node calls cost far more
5. **Use `codegraph_search` first** — find exact symbol names before using node/explore/trace (they need exact names, not natural language)
6. **projectPath parameter** — if Hermes launched MCP outside the project dir, pass `projectPath="/absolute/path"` to every tool call

## Multi-Tool Code Index Reality

Each AI tool maintains its own code index:
- Hermes: `.codegraph/`
- Claude Code: `.claude/`
- Codex: `~/.codex/`
- OpenCode: `.opencode/`

They cannot share indexes (different formats). The source code is one copy; indexes are caches. Don't try to unify them — use each tool's native index.
