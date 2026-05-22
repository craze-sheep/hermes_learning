# AI Tools Architecture — Hermes + Coding Agents

## Current Setup

```
┌─────────────────────────────────────────────────────────────┐
│                     👤 用户 (微信/QQ)                        │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              💬 消息网关 (WeChat/QQ Gateway)                  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              🤖 Hermes Agent (智能中枢)                       │
│         任务编排 · 上下文管理 · MCP集成 · Cron                 │
└─────────────────────────────────────────────────────────────┘
                    │           │           │
        ┌───────────┼───────────┼───────────┤
        ▼           ▼           ▼           ▼
   ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐
   │ Claude  │ │  Codex  │ │OpenCode │ │  MCP    │
   │  Code   │ │ (OpenAI)│ │         │ │ Server  │
   └─────────┘ └─────────┘ └─────────┘ └─────────┘
```

## Tool Roles

| Tool | Model | Primary Use |
|------|-------|-------------|
| Hermes Agent | mimo-v2.5-pro | 任务编排、监控、审查 |
| Claude Code | Claude Sonnet | 代码生成、PR审查 |
| Codex | GPT-5.5 | 批量修复、独立评审 |
| OpenCode | mimo-v2.5-pro | 辅助开发 |

## Multi-Agent Validation Pattern

User prefers **三方独立检验** (3-agent independent validation):
1. Hermes checks high-level structure
2. Claude Code checks implementation details
3. Codex checks independently

Workflow: Hermes identifies → Codex/Claude Code fix → All verify

## Delegation Rules

- **"让codex修复"** → Delegate to Codex, don't fix directly
- **"你们三个都要检验"** → All 3 agents must independently verify
- **"不用给我看"** → Complete autonomously, report results
- **"你不要动我的参数"** → Never modify parameters without explicit confirmation

## Session Template for Code Review

```bash
# Claude Code review
claude -p "审查代码..." --allowedTools "Read,Bash" --max-turns 15

# Codex review  
codex exec "审查代码..." --full-auto
```
