---
name: agent-memory-patterns
description: When and how to proactively use holographic memory (fact_store) vs session_search vs skill_manage. Use this to avoid the "silent session" anti-pattern where the agent never stores anything.
---

## The Problem

The system prompt says "use fact_store to add facts" but doesn't specify WHEN. This leads to "silent sessions" where the agent never proactively stores anything, even when the user expects it to remember key information.

## Memory Tool Triage

| Tool | Purpose | When to Use |
|------|---------|-------------|
| `fact_store` | Store structured facts with entities/tags/trust | User preferences, project decisions, key learnings, corrections |
| `session_search` | Recall past conversations | When user references something from a prior session |
| `skill_manage` | Store reusable workflows/procedures | After complex tasks (5+ calls) that produce a repeatable pattern |

## Proactive Storage Triggers

**ALWAYS store when:**
1. User corrects your approach, style, or workflow ("don't do X", "remember this", "stop formatting like Y")
2. User expresses a preference (language, tone, tools, frameworks)
3. A non-trivial decision is made about a project
4. A debugging session reveals a root cause or workaround
5. You complete a complex task (5+ tool calls) — store the outcome, not the process

**CONSIDER storing when:**
1. User shares information about their setup, environment, or constraints
2. You discover something surprising about the codebase or system
3. A task fails in a way that's worth remembering (but NOT transient errors)

**DO NOT store:**
1. One-off task details that won't recur
2. Transient errors that resolved (store the fix pattern, not the error)
3. Environment-specific issues (install commands, path mismatches)

## Anti-Pattern: The Silent Session

**Symptom:** Session runs fine, user gets answer, but nothing is stored. Next session starts from scratch.

**Cause:** Agent treats holographic memory as optional, not as a core responsibility.

**Fix:** After every substantive session, ask: "Is there anything here that would help a future session?" If yes, store it.

## Entity Tagging Best Practices

- Always include relevant entities (project names, tools, people)
- Use comma-separated tags for searchability
- Set category: `user_pref`, `project`, `tool`, or `general`
- Start with trust 0.5; it increases as facts are used and rated helpful

## Example Storage Patterns

**User preference:**
```
action: add
content: "用户偏好中文回复，使用简洁风格，不要过度解释"
category: user_pref
tags: 语言,风格,偏好
```

**Project decision:**
```
action: add
content: "项目 X 使用 React + TypeScript，状态管理用 Zustand，不用 Redux"
category: project
tags: 技术栈,项目X,前端
```

**Debugging insight:**
```
action: add
content: "项目 Y 的 build 失败是因为 Node 18 的 OpenSSL 变更，解决方案是设置 NODE_OPTIONS=--openssl-legacy-provider"
category: tool
tags: 构建,Node.js,错误修复,项目Y
```
