# WeChat Multi-Agent Project Template

Complete project structure for setting up 4 AI agents (Hermes + Claude Code + Codex + OpenCode) in a WeChat group chat via cc-connect.

## Directory Structure

```
WeChat_ai/
├── config.toml              # cc-connect main config (4 agents)
├── README.md                # Detailed usage documentation
├── .env.template            # API key template
├── scripts/
│   ├── setup.sh             # One-click install (node, cc-connect, agents)
│   ├── start.sh             # Start cc-connect service
│   ├── test.sh              # Test all agent connections
│   ├── bind-agents.sh       # Print /bind commands for user
│   └── cc-connect.service   # systemd service unit
└── agents/
    ├── hermes/README.md     # Hermes ACP config guide
    ├── claude/README.md     # Claude Code setup guide
    ├── codex/README.md      # Codex CLI setup guide
    └── opencode/README.md   # OpenCode setup guide
```

## Quick Start

```bash
# 1. Create project
mkdir -p /path/to/WeChat_ai/{agents/{hermes,claude,codex,opencode},scripts,logs,data}

# 2. Copy config.toml from cc-connect-integration.md reference

# 3. Create .env.template
cat > .env.template << 'EOF'
ANTHROPIC_API_KEY=sk-ant-xxx
OPENAI_API_KEY=sk-xxx
EOF

# 4. Run setup
bash scripts/setup.sh

# 5. Edit .env with real API keys
vim ~/.hermes/.env

# 6. Start service
bash scripts/start.sh

# 7. In WeChat group, bind agents
/bind hermes
/bind claude
/bind codex
/bind opencode
```

## Agent Specializations

| Agent | Best For | Model |
|-------|----------|-------|
| Hermes | Search, research, MCP tools, memory | Configurable |
| Claude Code | Code understanding, architecture, reasoning | Claude Sonnet/Opus |
| Codex | Code generation, testing, optimization | GPT-5.x |
| OpenCode | Code review, style, best practices | Claude/GPT |

## Usage Patterns

### Directed Work
```
@hermes search for Redis cluster best practices
@codex write a connection pool implementation
@claude review this architecture proposal
@opencode optimize this code
```

### Collaborative Review
```
You: Review this PR
@claude: Code structure and design...
@codex: Performance and security...
@hermes: Test coverage...
@opencode: Style and best practices...
```

### Architecture Discussion
```
You: How should we split this microservice?
@claude: DDD perspective...
@codex: Performance considerations...
@hermes: Similar open-source projects...
@opencode: Container deployment...
```
