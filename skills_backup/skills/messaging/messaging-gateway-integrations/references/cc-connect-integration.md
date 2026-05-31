# cc-connect Integration with Hermes

**cc-connect** (GitHub: chenhg5/cc-connect, ⭐11.2k) bridges local AI agents to 12+ messaging platforms. Written in Go.

## Why Use cc-connect

- **Multi-Bot Relay**: bind multiple agents to one group chat, they see each other's messages and can collaborate
- **12 platforms**: Feishu, DingTalk, Telegram, Slack, Discord, WeChat Work, Weixin (personal), QQ, LINE, Weibo, WPS Xiezuo, QQ Bot
- **Most platforms need no public IP** (WebSocket/long-polling)
- **Hermes is NOT built-in**, but works via ACP protocol

## Hermes ACP Integration

Hermes has a full `acp_adapter/` (stdio JSON-RPC 2.0). cc-connect supports `type = "acp"` for any ACP-speaking binary.

### Config (config.toml)

```toml
[[projects]]
name = "hermes"

[projects.agent]
type = "acp"

[projects.agent.options]
work_dir = "/path/to/project"
command = "hermes-acp"       # or: python3 -m acp_adapter.entry
display_name = "Hermes"
command = "/home/user/miniconda3/bin/claude"  # absolute path required in WSL/miniconda
```

### Multi-Agent Group Chat Config

```toml
# Hermes
[[projects]]
name = "hermes"
[projects.agent]
type = "acp"
[projects.agent.options]
work_dir = "/home/user/project"
command = "hermes-acp"
display_name = "Hermes"

# Claude Code
[[projects]]
name = "claude"
[projects.agent]
type = "claudecode"
[projects.agent.options]
work_dir = "/home/user/project"

# Gemini CLI
[[projects]]
name = "gemini"
[projects.agent]
type = "gemini"
[projects.agent.options]
work_dir = "/home/user/project"
```

Then in group chat:
```
/bind hermes
/bind claude
/bind gemini
```

### Group Chat Interaction

- User messages visible to all bound agents
- `@bot_name` targets specific agent
- Agents can cross-communicate via `cc-connect relay send --to <name> "message"`

## Supported Agent Types in cc-connect

| Agent | type | Notes |
|-------|------|-------|
| Claude Code | `claudecode` | Built-in, full support |
| Codex | `codex` | Built-in |
| Cursor Agent | `cursor` | Built-in |
| Gemini CLI | `gemini` | Built-in |
| OpenCode | `opencode` | Built-in |
| Devin | `devin` | Built-in, uses `devin acp` |
| Hermes | `acp` | Via ACP protocol |
| Any ACP agent | `acp` | Generic, set command+args |

## Install

```bash
npm install -g cc-connect
# or
brew install cc-connect
# or download binary from GitHub Releases
```

## Key Commands

```bash
cc-connect web              # Web admin dashboard
cc-connect feishu setup     # Platform setup CLIs
cc-connect weixin setup     # WeChat personal setup
cc-connect daemon install   # Background service
```

## Pitfalls

- `hermes-acp` needs `~/.hermes/.env` with API keys — ACP adapter loads it automatically
- `work_dir` must point to project root
- WeChat personal uses ilink long-polling, no public IP needed
- Multi-Bot Relay `/bind` syntax: `/bind <project-name>` (matches `[[projects]] name`)
- cc-connect is Go binary, no Python/Node runtime needed for the bridge itself
- npm install may timeout in WSL; use `curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash -` then `sudo apt-get install -y nodejs` if needed

## ACP Verification

Before configuring an agent for cc-connect, verify ACP support:

```bash
# Check if agent has ACP adapter
which hermes-acp && hermes acp --check

# Look for ACP adapter in source
ls -la /path/to/agent/acp_adapter/

# Test ACP stdio
echo '{"jsonrpc":"2.0","method":"initialize","id":1}' | hermes-acp
```

## Full 4-Agent Config Example (Hermes + Claude Code + Codex + OpenCode)

```toml
# ~/.cc-connect/config.toml
language = "zh"
data_dir = "/home/user/project/WeChat_ai/data"

[log]
level = "info"

[[providers]]
name = "anthropic"
api_key = "${ANTHROPIC_API_KEY}"

[[providers]]
name = "openai"
api_key = "${OPENAI_API_KEY}"

[display]
mode = "compact"
thinking_messages = true
thinking_max_len = 200
tool_max_len = 300

# Hermes (ACP)
[[projects]]
name = "hermes"
[projects.agent]
type = "acp"
[projects.agent.options]
work_dir = "/home/user/project"
command = "hermes-acp"
display_name = "Hermes"
mode = "yolo"
[projects.agent.options.env]
HERMES_HOME = "/home/user/.hermes"
[[projects.platforms]]
type = "weixin"

# Claude Code
[[projects]]
name = "claude"
[projects.agent]
type = "claudecode"
[projects.agent.options]
work_dir = "/home/user/project"
mode = "yolo"
model = "sonnet"
[[projects.platforms]]
type = "weixin"

# Codex
[[projects]]
name = "codex"
[projects.agent]
type = "codex"
[projects.agent.options]
work_dir = "/home/user/project"
mode = "full-auto"
[[projects.platforms]]
type = "weixin"

# OpenCode
[[projects]]
name = "opencode"
[projects.agent]
type = "opencode"
[projects.agent.options]
work_dir = "/home/user/project"
mode = "yolo"
[[projects.platforms]]
type = "weixin"
```

## Setup Scripts Pattern

Create a project directory with these scripts:

```
WeChat_ai/
├── config.toml              # cc-connect config
├── README.md                # Usage docs
├── .env.template            # API key template
├── scripts/
│   ├── setup.sh             # Install deps (node, cc-connect, agents)
│   ├── start.sh             # Start cc-connect service
│   ├── test.sh              # Test all agent connections
│   ├── bind-agents.sh       # Print /bind commands for user
│   └── cc-connect.service   # systemd unit (optional)
└── agents/
    ├── hermes/README.md
    ├── claude/README.md
    ├── codex/README.md
    └── opencode/README.md
```

The `setup.sh` should:
1. Check/install Node.js (cc-connect npm dependency)
2. Install cc-connect via npm
3. Check each agent CLI (claude, codex, opencode, hermes-acp)
4. Create `.env` template with API key placeholders
5. Copy config to `~/.cc-connect/config.toml`

The `test.sh` should:
1. Check each agent CLI is installed
2. Run `hermes acp --check` for Hermes
3. Verify API keys are set (not placeholder values)
4. Report status with ✓/✗ indicators

## Non-ACP Agents (Workflow Patterns)

Some "agents" are actually workflow patterns that run on top of existing ACP-compatible agents:

- **ReasonX** (funct1ons/reasonx-codex-workflow) — Structured collaboration workflow with DeepSeek V4 Pro as main executor and GLM 5.1/GPT-5.5 as advisors. NOT an ACP agent itself, but uses Codex/OpenCode as underlying agents. To use in cc-connect: bind the underlying agent (Codex/OpenCode) and place `.reasonix/skills/` in the project.
