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

## Common Pitfalls

- WeChat `MEDIA:/path` may send only a text path, not an attachment; paste content or use another platform for files.
- WeChat systemd gateway services do not inherit shell proxy variables; add proxy env to the service when `ilinkai.weixin.qq.com` is unreachable.
- QQ bots require correct intents and production publication; sandbox mode only reaches test channels.
- Duplicate `.env` keys cause silent confusion; clean existing platform keys before adding new ones.
- Group bots often require explicit @-mentions and admin/robot permissions.
- For multi-agent coding, chat is coordination; actual work should still happen through Hermes tools, subagents, or executor CLIs.

## Support Files

Absorbed platform-specific skills are preserved under `references/` with their original names.

### Telegram B2B Task Protocol
- `references/telegram-b2b-task-format.md` — The Telegram AI Team Bot-to-Bot protocol: task dispatch JSON format, required response framing (`<<<B2B_RESPONSE:job_id>>>` / `<<<B2B_DONE:job_id>>>` markers), MESSAGE + HANDOFF_SUMMARY structure, role assignments, hard rules, and directory exploration fallback technique.
- `references/b2b-supervisor-dispatch-patterns.md` — Supervisor role decision framework: worker capability matching (Planner/Developer/Researcher/Tester), phased execution patterns for research tasks, batch sizing, handoff summary best practices, and common pitfalls.

## Related Skills

- `b2b-task-audit` (devops) — For reviewing completed B2B task artifacts: post-mortems, failure mode analysis, execution chain verification, and quality audits of artifacts/tasks/ directories.
