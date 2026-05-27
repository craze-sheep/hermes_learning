# Connecting Claude Code, Codex, and OpenCode to Hermes MCP

Hermes can act as an MCP server, letting other coding agents (Claude Code, Codex, OpenCode) share Hermes's memory, context, and tools.

## Critical: `hermes mcp serve` is stdio, NOT HTTP

```
hermes mcp serve          # ← stdio mode (correct for tool integration)
hermes mcp serve --http   # ← does NOT exist
http://localhost:3000     # ← WRONG — this is not how it works
```

When adding Hermes as an MCP server to other tools, the command is:
```
hermes mcp serve
```
NOT a URL. The tool launches `hermes mcp serve` as a subprocess and communicates over stdin/stdout.

## Claude Code

### Global scope (all projects)
```bash
claude mcp add -s user hermes -- hermes mcp serve
```
Config stored in `~/.claude.json` under top-level `mcpServers`.

### Project scope (single project)
```bash
claude mcp add hermes -- hermes mcp serve
```
Config stored in `~/.claude.json` under `projects.<path>.mcpServers`.

### Verify
```bash
claude mcp list
```
Look for `hermes: hermes mcp serve - ✓ Connected`.

### Pitfall: scope flag
- `-s user` = global (recommended for Hermes)
- No flag = project-level only (works but limited)

## Codex

Config file: `~/.codex/config.toml`

Add to the `[mcp_servers]` section:
```toml
[mcp_servers.hermes]
type = "stdio"
command = "hermes"
args = ["mcp", "serve"]
```

### Verify
```bash
codex exec "list your mcp tools"
```

## OpenCode

Config file: `~/.config/opencode/opencode.json` (or `opencode.jsonc`)

**Pitfall: OpenCode may use `.jsonc` instead of `.json`.** When auditing or adding MCP servers, check BOTH files:
```bash
ls ~/.config/opencode/opencode.json ~/.config/opencode/opencode.jsonc 2>/dev/null
```
If both exist, OpenCode merges them (jsonc may take precedence). When in doubt, grep to find where a specific server is configured:
```bash
grep -l "codegraph" ~/.config/opencode/opencode.json* 2>/dev/null
```

Add to the `mcp` object:
```json
{
  "mcp": {
    "hermes": {
      "command": ["hermes", "mcp", "serve"],
      "enabled": true,
      "type": "local"
    }
  }
}
```

### Verify
```bash
opencode  # check startup for MCP connection messages
```

## Common Pitfalls

1. **Using `http://localhost:3000`** — This is WRONG. `hermes mcp serve` is stdio, not HTTP. There is no HTTP endpoint.

2. **Using `npx -y @anthropic-ai/mcp-remote http://localhost:3000`** — This is for connecting to remote MCP servers over HTTP. Hermes serves locally via stdio.

3. **MCP server not running** — Each tool launches `hermes mcp serve` as a subprocess when needed. No separate server process needs to be running.

4. **Config file location** — Each tool has its own config file. Editing the wrong one has no effect.

5. **Scope confusion (Claude Code)** — Without `-s user`, the MCP server is only available in the current project directory.

## Config File Locations Summary

| Tool | Config File | Scope Flag |
|------|------------|------------|
| Claude Code | `~/.claude.json` | `-s user` for global |
| Codex | `~/.codex/config.toml` | N/A (always global) |
| OpenCode | `~/.config/opencode/opencode.json` (or `.jsonc`) | N/A (always global) |

## Verifying MCP Servers Across All Tools

When auditing whether a specific MCP server (e.g. codegraph, holographic) is configured everywhere:

```bash
# Claude Code — use `claude mcp list` as authoritative source
claude mcp list

# Codex — grep config.toml
grep '\[mcp_servers\.' ~/.codex/config.toml

# OpenCode — check BOTH json and jsonc
grep -h "server_name" ~/.config/opencode/opencode.json ~/.config/opencode/opencode.jsonc 2>/dev/null
```

**Pitfall: `claude mcp list` is the source of truth for Claude Code.** The `~/.claude.json` file has `mcpServers` at the top level (user scope) AND under `projects.<path>.mcpServers` (project scope). `claude mcp list` merges both and shows connection status. Don't just grep the JSON file — you may miss project-scoped servers or see stale entries.

## What Hermes MCP Exposes

When connected, other tools can access:
- Hermes memory (cross-session context)
- Session search (past conversations)
- Skills library
- Tool execution (terminal, file ops, etc.)

This means Claude Code can query Hermes's memory for project context without you having to paste it in.
