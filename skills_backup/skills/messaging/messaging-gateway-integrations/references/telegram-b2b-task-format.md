---
name: telegram-b2b-task-format
description: "Telegram AI Team Bot-to-Bot (B2B) task protocol: message framing, role dispatch, response format, and directory structure."
version: 1.0.0
tags: [telegram, b2b, multi-agent, bot-to-bot, ai-team, protocol]
---

# Telegram AI Team — B2B Task Format

When the Telegram AI Team dispatches tasks to worker bots, it uses a structured B2B protocol. This documents the format so Hermes agents can respond correctly.

## Project Location

- Source: `/home/lzy/project/telegrambots/`
- Main entry: `ai_team_b2b_service.py`
- Run script: `run_team.sh`
- Systemd: `telegram-ai-team-bot2bot.service`
- Artifacts: `artifacts/` (role outputs)

## Task Dispatch Format

Tasks arrive as JSON in the user prompt with these fields:

```json
{
  "job_id": "researcher-20260530221824-159b6fad2ee144f0",
  "role": "Researcher",
  "role_description": "调研员。负责事实核查、资料路径、风险和不确定性。",
  "skills": ["web-access", "chinese-platform-research", "literature-survey"],
  "mcp": ["fetch:fetch", "context7:resolve_library_id", ...],
  "hard_rules": ["只处理本条任务，不读取或展开完整群聊历史。", ...],
  "system_prompt": "...",
  "user_prompt": "任务 ID：B2B-xxx\n用户需求：...\n当前短交接摘要：...\nSupervisor 刚发给你的消息：..."
}
```

## Response Format (MUST follow exactly)

The response MUST be framed with these markers. Nothing outside them.

```
<<<B2B_RESPONSE:{job_id}>>>

MESSAGE: 发到 Telegram 群里的正文，必须包含任务 ID，并 @TeamSupervisor_bot

HANDOFF_SUMMARY: 300 字以内给 Supervisor 的交接摘要

<<<B2B_DONE:{job_id}>>>
```

### Rules

1. Start marker: `<<<B2B_RESPONSE:{job_id}>>>` — the job_id from the task JSON
2. End marker: `<<<B2B_DONE:{job_id}>>>` — same job_id
3. NO content after the end marker
4. MESSAGE section: goes to the Telegram group, must include task ID and @TeamSupervisor_bot
5. HANDOFF_SUMMARY: 300 chars max, for Supervisor's internal use
6. If code/config files are produced, use `FILE: relative/path.ext` + code block format
7. All substantive output must be Markdown

## Roles in the Team

| Role | Bot Handle | Responsibility |
|------|-----------|----------------|
| Supervisor | @TeamSupervisor_bot | Dispatch, coordination, final assembly |
| Planner | — | Task decomposition, planning |
| Researcher | @crazysheep_researcher_bot | Fact-check, research, risk analysis |
| Developer | — | Code implementation |
| Tester | — | Testing, validation |

## Hard Rules (from task JSON)

- Only handle the assigned task; do NOT read full group chat history
- Substantive output must be Markdown
- If MCP/tool results were not actually executed, mark as "待执行/待验证"
- Worker bots can only @TeamSupervisor_bot; never @ or direct other workers
- Output must be between the start/end markers

## Directory Exploration Technique

When `search_files` times out on large directories, use browser_navigate to `file://` URLs:

```python
browser_navigate(url="file:///home/lzy/project/")
# Returns an HTML directory listing with clickable links
# Navigate into subdirs to inspect contents
```

This works because WSL mounts the filesystem and the browser can render directory indexes.
