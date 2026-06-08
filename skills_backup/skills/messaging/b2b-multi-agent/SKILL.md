---
name: b2b-multi-agent
description: "B2B (bot-to-bot) multi-agent Telegram team system: Supervisor dispatch, Worker contracts, Task auditing, and Tmux-based output protocol. Load when receiving B2B tasks, dispatching workers, auditing artifacts, or diagnosing stalled multi-agent tasks."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [b2b, multi-agent, telegram, supervisor, worker, audit, tmux, dispatch]
    related_skills: [literature-survey, plan, writing-plans, brainstorming]
---

# B2B Multi-Agent System

Complete reference for the Telegram AI Team B2B (bot-to-bot) system — a multi-agent architecture where a Supervisor dispatches tasks to specialized Workers (Planner/Researcher/Developer/Tester) via Telegram group chat, using tmux pane capture for message routing.

## When to Use

- Receiving a B2B Supervisor task (job JSON at `artifacts/tmux-jobs/supervisor-*.job.json`)
- Receiving a B2B Worker task from Supervisor
- Auditing/reviewing B2B task artifacts in `artifacts/tasks/`
- Diagnosing stalled or failed B2B tasks
- Understanding the B2B dispatch mechanism

## Architecture Overview

```
User → Telegram Group → B2B Service (bot2bot)
                          ├── Supervisor (this agent, tmux pane)
                          │   ├── dispatches → Planner bot
                          │   ├── dispatches → Researcher bot
                          │   ├── dispatches → Developer bot
                          │   └── dispatches → Tester bot
                          └── Workers (other tmux panes)
                              └── report back to Supervisor
```

**Key insight:** You do NOT need `send_message`. The B2B service captures your tmux pane output and posts it to Telegram. Your output IS the group message.

## Output Protocol (ALL roles)

Every B2B response uses wrapper markers:

```
<<<B2B_RESPONSE:job_id>>>

[role-specific content here]

<<<B2B_DONE:job_id>>>
```

### Marker Rules (CRITICAL)
1. Start marker on its own line — nothing else on that line
2. Response body follows, separated by blank lines
3. End marker on its own line — nothing else on that line
4. **ZERO output after the end marker** — not a blank line, not a space

### job_id vs task_id
- `job_id` (from JSON): `supervisor-20260531174942-563c8565d51b40cc` — used in wrapper markers
- `task_id` (from user_prompt): `B2B-20260531-174940` — used in message headers

---

## Supervisor Role

When receiving a task as the **Supervisor** role:

### Step 1: Read Job JSON + External Files

Read the job JSON and extract `job_id`, `system_prompt`, `user_prompt`, `hard_rules`. If `user_prompt` references external files (e.g., "去看 /path/to/prompt.md"), READ those files — the real task lives there.

### Step 2: Execute or Dispatch

- **Simple tasks**: answer directly with DONE
- **Complex tasks**: dispatch to workers via @ mentions in output

### Supervisor Output Format

```
<<<B2B_RESPONSE:job_id>>>

TARGET_ROLE: Planner/Researcher/Developer/Tester/DONE
MESSAGE: [task output here]
HANDOFF_SUMMARY: <=300 Chinese characters

<<<B2B_DONE:job_id>>>
```

### Dispatch Rules

- **One worker at a time** — only @ one Worker per dispatch
- **Wait for report** before dispatching next
- **Don't rush to DONE** — only when task is actually complete with verified results
- **Use ASSIGN for dispatching**, STATUS for progress, DONE only for completion

### Supervisor Pitfalls

1. **Premature DONE** (#1 failure mode) — outputting DONE after first worker report. If MESSAGE contains "[ASSIGN]" or "@bot_username", TARGET_ROLE must NOT be DONE
2. **Doing work yourself** — dispatch to Workers instead of executing directly
3. **Telegram message length** — keep dispatch messages under ~3000 chars; write long requirements to file and reference the path
4. **Confusing job_id with task_id** — wrapper markers use job_id, message headers use task_id
5. **Output after DONE marker** — zero content after `<<<B2B_DONE:...>>>`
6. **FP16 overflow** — use `-1e4` not `-1e9` in masked_fill with AMP
7. **Missing external file reads** — if user_prompt references a file, you MUST read it

---

## Worker Role

When receiving a task as a **Worker** (Planner/Researcher/Developer/Tester):

### Worker Output Format

```
<<<B2B_RESPONSE:job_id>>>

MESSAGE:
[B2B-YYYYMMDD-HHMMSS][YourRole][REPORT]
@TeamSupervisor_bot
your report body here

HANDOFF_SUMMARY: <=300 Chinese characters

<<<B2B_DONE:job_id>>>
```

### Forbidden Patterns (INSTANT REJECTION)

| Pattern | Why blocked |
|---------|-------------|
| `[task][Planner][DONE]` | Only REPORT allowed for workers |
| `下一步由 Researcher 执行` | Workers cannot assign other workers |
| `@other_bot please continue` | Can only @TeamSupervisor_bot |
| `建议按批次调度Researcher` | Managerial tone forbidden |

### Worker Pitfalls

1. **Missing wrapper markers** — causes immediate rework
2. **"描述能力需求" vs "安排工作"** — describe capabilities, don't assign roles
3. **Telegram length limit** — keep MESSAGE under 3000 chars; write details to file
4. **Header kind must be `[REPORT]`** — never `[DONE]`, `[STATUS]`, etc.
5. **Re-output after rejection** — fix ONLY the violation, keep substantive content

### Role-Specific Guidance

**Planner:** Write full plan to file, keep MESSAGE short (~300-500 chars). Use "供 Supervisor 决策参考" for recommendations.

**Researcher:** Verify critical papers via arXiv title search. Mark verified vs unverified citations. Expect 20-30% failure rate on academic repo clones.

**Developer:** Never modify source code directly — copy to working directory first. Run smoke test before full training. Record metrics to JSON.

**Tester:** Run structural checks first, then content/semantic, then syntax/lint. Produce table-format report. Write acceptance report to working directory.

---

## Task Audit

When reviewing B2B task artifacts:

### Audit Methodology

1. **Artifact Structure Scan**: Read README.md → supervisor/*.md → worker dirs → files/ → actual working directory
2. **Execution Chain Verification**: Check each worker dispatch for: was report filed? Real response or fallback? Actual work content?
3. **Content Quality Review**: Templates vs deliverables, working directory state, data accuracy, completeness
4. **Root Cause Analysis**: Trace failures through the chain

### Common Failure Modes

- **Premature DONE**: Supervisor marks complete after partial report
- **Silent Fallback Degradation**: Model fail → fallback garbage → treated as valid
- **Tool-Capability Mismatch**: Worker assigned tasks requiring tools it doesn't have
- **Template-as-Deliverable**: Empty templates presented as completed work
- **Broken Handoff Chain**: Worker dispatched but never reported
- **Hallucinated Metadata**: Paper titles, links from memory without verification

### Live System Diagnosis

When diagnosing stuck tasks:
1. Check bot2bot process: `ps aux | grep bot2bot`
2. Check tmux sessions: `tmux capture-pane -t telegrambots-<role> -p -S -50`
3. Check task state: Read `artifacts/tasks/<task_id>/state.json`
4. Check tmux-jobs: `ls -lt artifacts/tmux-jobs/`

---

## Skills That Complement This

- `literature-survey` — for paper research tasks
- `writing-plans` / `plan` — for structuring implementation plans
- `brainstorming` — for ideation phases
