---
name: native-mcp
description: "MCP client: connect servers, register tools (stdio/HTTP)."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [MCP, Tools, Integrations]
    related_skills: [mcporter]
---

# Native MCP Client

Hermes Agent has a built-in MCP client that connects to MCP servers at startup, discovers their tools, and makes them available as first-class tools the agent can call directly. No bridge CLI needed -- tools from MCP servers appear alongside built-in tools like `terminal`, `read_file`, etc.

## When to Use

Use this whenever you want to:
- Connect to MCP servers and use their tools from within Hermes Agent
- Add external capabilities (filesystem access, GitHub, databases, APIs) via MCP
- Run local stdio-based MCP servers (npx, uvx, or any command)
- Connect to remote HTTP/StreamableHTTP MCP servers
- Have MCP tools auto-discovered and available in every conversation

For ad-hoc, one-off MCP tool calls from the terminal without configuring anything, see the `mcporter` skill instead.

## Prerequisites

- **mcp Python package** -- optional dependency; install with `pip install mcp`. If not installed, MCP support is silently disabled.
- **Node.js** -- required for Node-based MCP servers (most community servers)
- **npm** -- for `npm install -g` to pre-install packages (recommended over `npx -y` for 20-36x faster startup)
- **uv** -- optional, for `uvx`-based MCP servers (Python-based servers)

Install the MCP SDK:

```bash
pip install mcp
# or, if using uv:
uv pip install mcp
```

## Quick Start

Add MCP servers to `~/.hermes/config.yaml` under the `mcp_servers` key:

```bash
# Install globally for fast startup
npm install -g @modelcontextprotocol/server-memory
npm_root=$(npm root -g)
```

```yaml
mcp_servers:
  memory:
    command: "node"
    args: ["<npm_root>/@modelcontextprotocol/server-memory/dist/index.js"]
```

Restart Hermes Agent. On startup it will:
1. Connect to the server
2. Discover available tools
3. Register them with the prefix `mcp_memory_*`
4. Inject them into all platform toolsets

You can then use the tools naturally -- just ask the agent to create or search entities.

## Configuration Reference

Each entry under `mcp_servers` is a server name mapped to its config. There are two transport types: **stdio** (command-based) and **HTTP** (url-based).

### Stdio Transport (command + args)

```yaml
mcp_servers:
  server_name:
    command: "node"            # (required) executable to run
    args: ["/path/to/server/dist/index.js"]  # (optional) command arguments, default: []
    env:                       # (optional) environment variables for the subprocess
      SOME_API_KEY: "value"
    timeout: 120               # (optional) per-tool-call timeout in seconds, default: 120
    connect_timeout: 60        # (optional) initial connection timeout in seconds, default: 60
```

### HTTP Transport (url)

```yaml
mcp_servers:
  server_name:
    url: "https://my-server.example.com/mcp"   # (required) server URL
    headers:                                     # (optional) HTTP headers
      Authorization: "Bearer sk-..."
    timeout: 180               # (optional) per-tool-call timeout in seconds, default: 120
    connect_timeout: 60        # (optional) initial connection timeout in seconds, default: 60
```

### All Config Options

| Option            | Type   | Default | Description                                       |
|-------------------|--------|---------|---------------------------------------------------|
| `command`         | string | --      | Executable to run (stdio transport, required)     |
| `args`            | list   | `[]`    | Arguments passed to the command                   |
| `env`             | dict   | `{}`    | Extra environment variables for the subprocess    |
| `url`             | string | --      | Server URL (HTTP transport, required)             |
| `headers`         | dict   | `{}`    | HTTP headers sent with every request              |
| `timeout`         | int    | `120`   | Per-tool-call timeout in seconds                  |
| `connect_timeout` | int    | `60`    | Timeout for initial connection and discovery      |

Note: A server config must have either `command` (stdio) or `url` (HTTP), not both.

## How It Works

### Startup Discovery

When Hermes Agent starts, `discover_mcp_tools()` is called during tool initialization:

1. Reads `mcp_servers` from `~/.hermes/config.yaml`
2. For each server, spawns a connection in a dedicated background event loop
3. Initializes the MCP session and calls `list_tools()` to discover available tools
4. Registers each tool in the Hermes tool registry

### Tool Naming Convention

MCP tools are registered with the naming pattern:

```
mcp_{server_name}_{tool_name}
```

Hyphens and dots in names are replaced with underscores for LLM API compatibility.

Examples:
- Server `filesystem`, tool `read_file` → `mcp_filesystem_read_file`
- Server `github`, tool `list-issues` → `mcp_github_list_issues`
- Server `my-api`, tool `fetch.data` → `mcp_my_api_fetch_data`

### Auto-Injection

After discovery, MCP tools are automatically injected into all `hermes-*` platform toolsets (CLI, Discord, Telegram, etc.). This means MCP tools are available in every conversation without any additional configuration.

### Connection Lifecycle

- Each server runs as a long-lived asyncio Task in a background daemon thread
- Connections persist for the lifetime of the agent process
- If a connection drops, automatic reconnection with exponential backoff kicks in (up to 5 retries, max 60s backoff)
- On agent shutdown, all connections are gracefully closed

### Idempotency

`discover_mcp_tools()` is idempotent -- calling it multiple times only connects to servers that aren't already connected. Failed servers are retried on subsequent calls.

## Transport Types

### Stdio Transport

The most common transport. Hermes launches the MCP server as a subprocess and communicates over stdin/stdout.

```yaml
mcp_servers:
  filesystem:
    command: node
    args: ["/home/user/miniconda3/lib/node_modules/@modelcontextprotocol/server-filesystem/dist/index.js", "/home/user/projects"]
```

The subprocess inherits a **filtered** environment (see Security section below) plus any variables you specify in `env`.

### HTTP / StreamableHTTP Transport

For remote or shared MCP servers. Requires the `mcp` package to include HTTP client support (`mcp.client.streamable_http`).

```yaml
mcp_servers:
  remote_api:
    url: "https://mcp.example.com/mcp"
    headers:
      Authorization: "Bearer sk-..."
```

If HTTP support is not available in your installed `mcp` version, the server will fail with an ImportError and other servers will continue normally.

## Security

### Environment Variable Filtering

For stdio servers, Hermes does NOT pass your full shell environment to MCP subprocesses. Only safe baseline variables are inherited:

- `PATH`, `HOME`, `USER`, `LANG`, `LC_ALL`, `TERM`, `SHELL`, `TMPDIR`
- Any `XDG_*` variables

All other environment variables (API keys, tokens, secrets) are excluded unless you explicitly add them via the `env` config key. This prevents accidental credential leakage to untrusted MCP servers.

```yaml
mcp_servers:
  github:
    command: node
    args: ["/home/user/miniconda3/lib/node_modules/@modelcontextprotocol/server-github/dist/index.js"]
    env:
      # Only this token is passed to the subprocess
      GITHUB_PERSONAL_ACCESS_TOKEN: "ghp_..."
```

### Credential Stripping in Error Messages

If an MCP tool call fails, any credential-like patterns in the error message are automatically redacted before being shown to the LLM. This covers:

- GitHub PATs (`ghp_...`)
- OpenAI-style keys (`sk-...`)
- Bearer tokens
- Generic `token=`, `key=`, `API_KEY=`, `password=`, `secret=` patterns

## Troubleshooting

### "MCP SDK not available -- skipping MCP tool discovery"

The `mcp` Python package is not installed. Install it:

```bash
pip install mcp
```

### "No MCP servers configured"

No `mcp_servers` key in `~/.hermes/config.yaml`, or it's empty. Add at least one server.

### "Failed to connect to MCP server 'X'"

Common causes:
- **Command not found**: The `command` binary isn't on PATH. Ensure `node`, `python`, `npx`, `uvx`, or the relevant command is installed.
- **Package not found**: The npm package may not exist (some official MCP packages have been removed). Verify with `npm view <package>` before configuring.
- **Slow startup**: Using `npx -y` causes ~12s delay per server. Install globally and use `node` directly (see Performance section above).
- **Timeout**: The server took too long to start. Increase `connect_timeout`.
- **Port conflict**: For HTTP servers, the URL may be unreachable.

### "MCP server 'X' requires HTTP transport but mcp.client.streamable_http is not available"

Your `mcp` package version doesn't include HTTP client support. Upgrade:

```bash
pip install --upgrade mcp
```

### Tools not appearing

- Check that the server is listed under `mcp_servers` (not `mcp` or `servers`)
- Ensure the YAML indentation is correct
- Look at Hermes Agent startup logs for connection messages
- Tool names are prefixed with `mcp_{server}_{tool}` -- look for that pattern

### Connection keeps dropping

The client retries up to 5 times with exponential backoff (1s, 2s, 4s, 8s, 16s, capped at 60s). If the server is fundamentally unreachable, it gives up after 5 attempts. Check the server process and network connectivity.

### "I updated ~/.claude.json but hermes mcp list shows old config"

Hermes reads from `~/.hermes/config.yaml`, NOT `~/.claude.json`. These are separate config files. Update both when changing MCP servers. See "Dual Config Files" section above.

## Examples

### Memory Server (global node)

```bash
npm install -g @modelcontextprotocol/server-memory
```

```yaml
mcp_servers:
  memory:
    command: node
    args:
    - /home/user/miniconda3/lib/node_modules/@modelcontextprotocol/server-memory/dist/index.js
```

Registers tools like `mcp_memory_create_entities`, `mcp_memory_search_nodes`, etc.

### Filesystem Server (global node)

```yaml
mcp_servers:
  filesystem:
    command: node
    args: ["/home/user/miniconda3/lib/node_modules/@modelcontextprotocol/server-filesystem/dist/index.js", "/home/user/documents"]
    timeout: 30
```

Registers tools like `mcp_filesystem_read_file`, `mcp_filesystem_write_file`, `mcp_filesystem_list_directory`.

### GitHub Server with Authentication

```yaml
mcp_servers:
  github:
    command: node
    args: ["/home/user/miniconda3/lib/node_modules/@modelcontextprotocol/server-github/dist/index.js"]
    env:
      GITHUB_PERSONAL_ACCESS_TOKEN: "ghp_xxxxxxxxxxxxxxxxxxxx"
    timeout: 60
```

Registers tools like `mcp_github_list_issues`, `mcp_github_create_pull_request`, etc.

### Remote HTTP Server

```yaml
mcp_servers:
  company_api:
    url: "https://mcp.mycompany.com/v1/mcp"
    headers:
      Authorization: "Bearer sk-xxxxxxxxxxxxxxxxxxxx"
      X-Team-Id: "engineering"
    timeout: 180
    connect_timeout: 30
```

### Multiple Servers

```yaml
mcp_servers:
  memory:
    command: node
    args: ["/home/user/miniconda3/lib/node_modules/@modelcontextprotocol/server-memory/dist/index.js"]

  filesystem:
    command: node
    args: ["/home/user/miniconda3/lib/node_modules/@modelcontextprotocol/server-filesystem/dist/index.js", "/tmp"]

  github:
    command: node
    args: ["/home/user/miniconda3/lib/node_modules/@modelcontextprotocol/server-github/dist/index.js"]
    env:
      GITHUB_PERSONAL_ACCESS_TOKEN: "ghp_xxxxxxxxxxxxxxxxxxxx"

  company_api:
    url: "https://mcp.internal.company.com/mcp"
    headers:
      Authorization: "Bearer sk-xxxxxxxxxxxxxxxxxxxx"
    timeout: 300
```

All tools from all servers are registered and available simultaneously. Each server's tools are prefixed with its name to avoid collisions.

## Sampling (Server-Initiated LLM Requests)

Hermes supports MCP's `sampling/createMessage` capability — MCP servers can request LLM completions through the agent during tool execution. This enables agent-in-the-loop workflows (data analysis, content generation, decision-making).

Sampling is **enabled by default**. Configure per server:

```yaml
mcp_servers:
  my_server:
    command: node
    args: ["/path/to/my-mcp-server/dist/index.js"]
    sampling:
      enabled: true           # default: true
      model: "gemini-3-flash" # model override (optional)
      max_tokens_cap: 4096    # max tokens per request
      timeout: 30             # LLM call timeout (seconds)
      max_rpm: 10             # max requests per minute
      allowed_models: []      # model whitelist (empty = all)
      max_tool_rounds: 5      # tool loop limit (0 = disable)
      log_level: "info"       # audit verbosity
```

Servers can also include `tools` in sampling requests for multi-turn tool-augmented workflows. The `max_tool_rounds` config prevents infinite tool loops. Per-server audit metrics (requests, errors, tokens, tool use count) are tracked via `get_mcp_status()`.

Disable sampling for untrusted servers with `sampling: { enabled: false }`.

## Performance: Global Install vs npx -y

**`npx -y` is slow (~12s per server).** Each call checks/downloads the package. With 4+ servers, startup takes 40-60 seconds.

**Fix: globally install and use `node` directly (0.3-0.9s per server, 20-36x faster):**

```bash
# 1. Install globally
npm install -g @modelcontextprotocol/server-memory \
               @modelcontextprotocol/server-sequential-thinking \
               @upstash/context7-mcp

# 2. Find the global root
npm root -g
# e.g. /home/user/miniconda3/lib/node_modules

# 3. Update config to use node directly
mcp_servers:
  memory:
    command: node
    args:
    - /home/user/miniconda3/lib/node_modules/@modelcontextprotocol/server-memory/dist/index.js
```

For Python-based servers, prefer `python -m mcp_server_fetch` over `uvx mcp-server-fetch`.

**Verification:** `hermes mcp test <name>` — check the "Connected" time. Anything over 2s means npx/uvx overhead.

## Dual Config Files (Hermes vs Claude Code)

**Hermes reads MCP config from `~/.hermes/config.yaml` under `mcp_servers`.**
**Claude Code / OpenCode / Codex read from `~/.claude.json` under `mcpServers`.**

These are SEPARATE configs. When adding/removing/updating MCP servers, update BOTH:

| Tool | Config File | Key |
|------|-------------|-----|
| Hermes Agent | `~/.hermes/config.yaml` | `mcp_servers` |
| Claude Code | `~/.claude.json` | `mcpServers` |
| Codex | `~/.codex/config.toml` | `[mcp_servers]` |
| OpenCode | `~/.config/opencode/opencode.json` | `mcp` |

Use `hermes mcp list` to verify Hermes config, and `cat ~/.claude.json | jq .mcpServers` for Claude Code config.

**Pitfall:** `hermes mcp test` reads from `~/.hermes/config.yaml`, NOT `~/.claude.json`. If you only update one file, the tools will show different server lists.

## Troubleshooting

### Package not found (404)

Some official MCP packages have been removed from npm (e.g. `@modelcontextprotocol/server-time` was deleted). Always verify a package exists before configuring:

```bash
npm view @modelcontextprotocol/server-time 2>&1 | head -3
# If 404, the package is gone. Search for alternatives:
npm search mcp server time
```

### Dependency conflicts with mcp-server-fetch (Python)

**Do NOT use the Python `mcp-server-fetch` package with Hermes.** It requires `httpx<0.28` but `hermes-agent` pins `httpx[socks]==0.28.1`. This is NOT just a pip warning — the server will crash at runtime with `AsyncClient.__init__() got an unexpected keyword argument 'proxies'` because httpx 0.28 removed the `proxies` kwarg.

**Fix: replace with the Node-based `mcp-fetch-server`:**

```bash
npm install -g mcp-fetch-server
pip uninstall mcp-server-fetch  # remove conflicting Python package
```

Update `~/.hermes/config.yaml`:
```yaml
mcp_servers:
  fetch:
    enabled: true
    command: npx
    args:
      - mcp-fetch-server
```

**Pitfall:** `hermes config set mcp_servers.fetch.args '["mcp-fetch-server"]'` saves args as a YAML string, not a list. Edit `config.yaml` directly for list values.

Restart the gateway after changes: `sudo systemctl restart hermes-gateway`

## Notes

- MCP tools are called synchronously from the agent's perspective but run asynchronously on a dedicated background event loop
- Tool results are returned as JSON with either `{"result": "..."}` or `{"error": "..."}`
- The native MCP client is independent of `mcporter` -- you can use both simultaneously
- Server connections are persistent and shared across all conversations in the same agent process
- Adding or removing servers requires restarting the agent (no hot-reload currently)
- **Reverse direction:** To let Claude Code/Codex/OpenCode connect TO Hermes as an MCP server, see `hermes-agent` skill → `references/mcp-external-tool-integration.md`. Key: `hermes mcp serve` is stdio, NOT HTTP.
- **Memory server ≠ Hermes memory:** There are THREE memory systems: Hermes built-in (MEMORY.md), MCP memory server (per-tool), and Holographic memory (shared SQLite DB). For cross-tool shared memory, use the Holographic system. See `references/mcp-memory-vs-hermes-memory.md` for the full architecture and `references/holographic-memory-agents-template.md` for the AGENTS.md template to deploy across tools.
- **Building custom MCP servers:** See `references/mcp-server-development-pitfalls.md` for sql.js limitations, atomic write patterns, entity extraction anti-patterns, and cascade deletion pitfalls.
- **Codex hooks/Clawd dependency:** See `references/codex-hooks-clawd-dependency.md` — Codex hooks hang 600s when Clawd is not running on localhost:23333.
