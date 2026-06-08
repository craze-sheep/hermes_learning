---
name: messaging-gateway-integrations
description: Use when setting up, troubleshooting, or designing messaging/chat integrations for Hermes or agent workflows, including Telegram/Discord/WeChat/QQ bots, gateway credentials, group chat routing, and multi-agent chat architectures.
tags: [messaging, gateway, bots, telegram, discord, wechat, weixin, qq, group-chat, multi-agent]
---

# Messaging Gateway Integrations

Umbrella skill for chat platform integration and bot-mediated agent workflows: Hermes gateway setup, platform credentials, user/group authorization, Telegram/Discord/WeChat/QQ tradeoffs, and multi-agent group chat architecture.

## When to Use

- User wants Hermes or agents reachable through chat apps.
- Setting up or troubleshooting WeChat/Weixin, QQ Bot, Telegram, Discord, Slack, or similar gateway platforms.
- Designing multi-agent group chat, bot tokens, group routing, or executor-vs-agent coordination.
- Diagnosing unauthorized users, group @-mention behavior, gateway logs, missing replies, or platform limitations.

## Platform Selection

- **Telegram/Discord** — best default for group bot workflows: official APIs, low ban risk, multiple bots can share a group.
- **WeChat/Weixin** — useful if the user is already there, but personal-account bot support is limited; expect authorization, proxy, and attachment limitations.
- **QQ Bot** — official API exists but requires QQ developer setup, intents, app publication, and group robot permissions.
- **Slack/enterprise chat** — use when already provisioned by the workspace.

## Gateway Setup Checklist

1. Identify platform and whether the task is DM, group chat, cron delivery, or multi-agent coordination.
2. Create/register bot or gateway account and collect required credentials.
3. Add credentials to the correct Hermes location (`~/.hermes/.env`, platform account directory, or config as platform requires).
4. Configure authorization deliberately: allow-all for simple private deployments, allowlists for shared environments.
5. Restart gateway or service and inspect logs.
6. Test inbound and outbound messages from the intended chat/group/topic.
7. Document limitations (group @ requirements, attachment support, sandbox/publish status, ban risk).

## Multi-Agent Chat Pattern

Keep the distinction clear:

- **Agent**: can reason, decide, execute, and remember (Hermes profiles/subagents).
- **Executor**: coding or command tool that follows instructions (Claude Code, Codex, OpenCode).

Recommended architecture: one Hermes coordinator in the chat, with subprocess/subagent/executor workers behind it. Multiple visible bot personas are useful only when the platform supports them safely and the coordination cost is justified.

### Alternative: cc-connect Multi-Bot Relay

For multi-agent group chat where each agent is a visible participant, **cc-connect** (GitHub: chenhg5/cc-connect, ⭐11.2k) is a Go-based bridge supporting 12 platforms. Hermes integrates via ACP (`type = "acp"`, `command = "hermes-acp"`). See `references/cc-connect-integration.md` for full config examples and setup. See `references/wechat-multi-agent-template.md` for a complete project template with 4 agents.

## User Workflow Preferences

- **Check before installing**: When exploring a new tool/integration, verify the repository and documentation first before attempting installation. Read README, check config examples, and understand the architecture before running install commands.
- **Plan before executing**: For multi-step setups, create a plan with all steps, then execute. Don't start installing/configuring without a clear picture of what's needed.
- **Skip user-dependent steps**: When a step requires user input (API keys, auth tokens, manual verification), mark it clearly and skip it. Focus on what can be automated.

## Common Pitfalls

- WeChat file sending works via two methods (verified 2026-06): (1) include `MEDIA:/absolute/path` in your regular response text — the system delivers it natively as an image/file; (2) call `send_message(action='send', target='weixin', message='MEDIA:/path')` explicitly. Both return success. For images, prefer method (1) for simplicity. For sending multiple files or explicit delivery, use method (2). The old limitation ("MEDIA: only sends text path") may have been resolved by platform updates.
- WeChat systemd gateway services do not inherit shell proxy variables; add proxy env to the service when `ilinkai.weixin.qq.com` is unreachable.
- QQ bots require correct intents and production publication; sandbox mode only reaches test channels.
- Duplicate `.env` keys cause silent confusion; clean existing platform keys before adding new ones.
- Group bots often require explicit @-mentions and admin/robot permissions.
- **For multi-agent coding, chat is coordination; actual work should still happen through Hermes tools, subagents, or executor CLIs.**
- **B2B Supervisor dispatch uses tmux pane capture, not send_message.** When acting as Supervisor in a Telegram AI Team B2B task (dispatched via job JSON to a tmux session), output the B2B response format directly — the service captures the pane and posts to Telegram. Do NOT call `send_message()` — Telegram is typically not configured in the CLI agent's Hermes instance. See `references/b2b-supervisor-dispatch-patterns.md` for the full CLI/tmux dispatch pattern.
- **cc-connect absolute paths in WSL/miniconda**
- **npm global install into miniconda**: When system npm is missing, use miniconda's npm with explicit prefix: `~/miniconda3/bin/npm config set prefix ~/miniconda3 && ~/miniconda3/bin/npm install -g cc-connect`. Binary lands in `~/miniconda3/bin/cc-connect`.

## Support Files

Absorbed platform-specific skills are preserved under `references/` with their original names.

### Telegram B2B Task Protocol
- `references/telegram-b2b-task-format.md` — The Telegram AI Team Bot-to-Bot protocol: task dispatch JSON format, required response framing (`<<<B2B_RESPONSE:job_id>>>` / `<<<B2B_DONE:job_id>>>` markers), MESSAGE + HANDOFF_SUMMARY structure, role assignments, hard rules, and directory exploration fallback technique.
- `references/b2b-supervisor-dispatch-patterns.md` — Supervisor role decision framework: worker capability matching (Planner/Developer/Researcher/Tester), DONE semantics (task complete, not turn complete), single-worker dispatch rule, don't-modify-source rule, virtual environment requirement, phased execution patterns for research tasks, batch sizing, re-dispatch state verification, file numbering mismatch pitfall, and handoff summary best practices.
- `references/experiment-execution-workflow.md` — ML/AI experiment execution workflow: baseline training, experiment comparison, metrics collection, execution order (low-risk first), common pitfalls (parameter mismatch, dependency failures, patch application).

### cc-connect Multi-Agent Setup
- `references/cc-connect-integration.md` — Full cc-connect setup: ACP config, 4-agent example (Hermes + Claude Code + Codex + OpenCode), verification steps, setup scripts pattern, and non-ACP agent patterns (ReasonX).
- `references/wechat-multi-agent-template.md` — Complete project template for WeChat multi-agent group chat: directory structure, quick start, agent specializations, and usage patterns.

## Related Skills

- `b2b-task-audit` (devops) — For reviewing completed B2B task artifacts: post-mortems, failure mode analysis, execution chain verification, and quality audits of artifacts/tasks/ directories.
