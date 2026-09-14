---
name: agent-memory-patterns
description: When and how to proactively use holographic memory (fact_store) vs session_search vs skill_manage. Use this to avoid the "silent session" anti-pattern where the agent never stores anything.
---

## The Problem

The system prompt says "use fact_store to add facts" but doesn't specify WHEN. This leads to "silent sessions" where the agent never proactively stores anything, even when the user expects it to remember key information.

triggers:
  - 用户问"为啥不用holographic记忆"或类似问题
  - 用户提醒你应该存储信息而你没有主动存储
  - 会话产生了重要发现但你还没有存储到fact_store

`AGENTS.md` is loaded every turn as project context. It already contains comprehensive memory rules (lines 78-107) with 7 trigger categories:
1. 用户明确指示（"记住"、"记一下"）
2. 用户纠正信息
3. 学到用户偏好
4. 学到环境信息
5. 学到项目信息
6. 完成重要配置
7. **会话结束前** — 总结本次会话的重要发现

**DO NOT** reinvent these rules or store them in memory. Just follow AGENTS.md.

## Where NOT To Put Behavioral Instructions

| Place | Purpose | Behavior rules? |
|-------|---------|----------------|
| `AGENTS.md` | Always-loaded project context | ✅ YES — this is where behavioral rules go |
| `CLAUDE.md` | Coding guidelines only | ❌ NO — not for memory/behavior rules |
| Holographic memory (`fact_store`) | Passive facts queried on demand | ❌ NO — you won't proactively read it to remind yourself |
| Skills (`skill_manage`) | Reusable procedures and workflows | ✅ YES — for procedural knowledge |

**Pitfall:** Storing "remember to update memory" as a fact in holographic memory is useless — you won't query memory to remind yourself to update memory. Put it in AGENTS.md or a skill that's loaded every session.

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

**Fix — Concrete Checklist:**
After every substantive session (3+ tool calls), run through AGENTS.md triggers:
1. Did the user correct me? → `fact_store` add (correction)
2. Did the user express a preference? → `fact_store` add (user_pref)
3. Did I learn something about their project? → `fact_store` add (project)
4. Did I discover environment info? → `fact_store` add (general)
5. Did I solve a non-trivial problem? → `fact_store` add (tool) or `skill_manage` add (if reusable)
6. Did I complete a complex task? → Store the outcome, not the process

**If any answer is YES → store it NOW, don't defer.** The user should never have to remind you to update memory.

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
