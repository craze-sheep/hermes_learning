---
name: b2b-task-audit
description: Audit B2B (bot-to-bot) multi-agent task artifacts for systemic failures — silent fallbacks, tool-capability mismatches, unbatched dispatches, template-as-deliverable confusion, and broken handoff chains. Use when reviewing artifacts/tasks/ directories, diagnosing stalled tasks, or improving the B2B orchestration system.
triggers:
  - user asks to review/audit/check B2B task artifacts
  - user asks why a B2B task failed or stalled
  - user asks to improve B2B task quality
  - artifacts/tasks/ directory is mentioned
---

# B2B Task Audit Skill

## When to Use

When the user asks you to review, audit, diagnose, or improve the output of the B2B bot-to-bot team system (Supervisor / Planner / Researcher / Developer / Tester). This covers:

- Post-mortem of completed or stalled tasks
- Quality review of task artifacts
- Identifying systemic patterns across multiple tasks
- Recommending fixes to the B2B codebase or prompts

## Audit Methodology

### Phase 1: Artifact Structure Scan

Read files in this order to reconstruct the execution timeline:

1. `README.md` — task definition, user text, topology
2. `supervisor/*.md` — dispatch decisions (ASSIGN, DONE, ERROR, STATUS)
3. Worker directories (`planner/`, `researcher/`, `developer/`, `testerier/`) — worker reports
4. `files/` — code files, configs, deliverables written during task
5. Actual working directory (from README user_text) — verify real-world side effects

### Phase 2: Execution Chain Verification

For each worker dispatch, verify:

- **Was a report filed?** Missing worker/ directory = broken chain
- **Was it a real response or a fallback?** Check for "本地 fallback" / "模型不可用" / "RuntimeError" in reports
- **Did the report contain actual work?** Or just echoed the input back?
- **Was the handoff summary actionable?** Or was it too vague/long for the next worker?

### Phase 3: Content Quality Review

- **Templates vs deliverables**: Are files in `files/` actual content or just empty templates?
- **Working directory state**: Does the actual filesystem reflect the claimed work?
- **Data accuracy**: Are paper names, links, dates, venues verified or hallucinated?
- **Completeness**: Does the output match what the user originally requested?

### Phase 4: Root Cause Analysis

Trace failures back through the chain. Common root cause patterns:

1. Worker lacked required tools (e.g., no web access for research tasks)
2. Model call failed → silent fallback degraded to garbage
3. Supervisor didn't validate worker output quality before continuing
4. Task wasn't batched — single dispatch overwhelmed the worker
5. Plan was created but not followed during execution

## Common Failure Modes

Load `references/failure-modes.md` for the full taxonomy. Key categories:

- **Premature DONE**: Supervisor marks task complete after partial worker report, R2+ never dispatched (#10 in taxonomy)
- Load `references/batch-experiment-creation.md` for the pattern of automating multi-directory experiment creation with per-directory code modifications.
- **Silent Fallback Degradation**: Model fails → fallback generates garbage → Supervisor treats it as valid
- **Tool-Capability Mismatch**: Worker assigned tasks requiring tools it doesn't have
- **Template-as-Deliverable**: Empty templates presented as completed work
- **Broken Handoff Chain**: Worker dispatched but never reported back
- **Unbatched Dispatch**: All work thrown at one worker instead of planned batches
- **Hallucinated Metadata**: Paper titles, links, venues from memory without verification

## Live System Diagnosis (not just artifact review)

When the user asks "why did the bot stop" or "is my task stuck" during a live B2B session, follow this diagnostic chain:

1. **Check bot2bot process**: `ps aux | grep bot2bot` — is the main service alive?
2. **Check tmux sessions**: `tmux capture-pane -t telegrambots-<role> -p -S -50` — what's each agent doing?
3. **Check Telegram pending updates**: Use each bot's token to call `get_updates(timeout=0, limit=10)` — are messages piling up?
4. **Check task state**: Read `artifacts/tasks/<task_id>/state.json` — is `completed` true? What are `turns` and `contacted_roles`?
5. **Check tmux-jobs**: `ls -lt artifacts/tmux-jobs/` — when was the last job dispatched to each role?
6. **Cross-reference**: If supervisor shows dispatch in tmux but no researcher job file exists → message never reached researcher bot

### Deep Diagnosis: Tracing `manager_decide()` Flow

When the task state shows `completed: true` but the user says work isn't done:

1. **Read `state.json`** — check `completed`, `turns`, `contacted_roles`, `status`
2. **Read the last supervisor tmux output** — look for `TARGET_ROLE: DONE` vs `TARGET_ROLE: Researcher`
3. **Check if worker jobs exist after the DONE**: `ls -lt artifacts/tmux-jobs/<role>-*` — if no new jobs after the DONE, the dispatch was never executed
4. **Root cause**: Supervisor LLM output `TARGET_ROLE: DONE` → `manager_decide()` sets `state.completed = True` → `send_manager_decision()` sends DONE to Telegram → subsequent `manager_receive_report()` hits `if state.completed: return` → all future dispatches blocked

### Supervisor Context-Thin Prompt Problem

The `manager_decide()` prompt gives the Supervisor LLM:
- `用户需求：{state.user_text}` — full original text
- `当前短摘要：{state.summary}` — **only the LAST handoff summary** (overwritten each turn)
- `已联系过的角色：{contacted_roles}` — role names only, no progress detail
- `新收到的信息：{incoming}` — current worker report

**Missing**: subtask progress, completion percentage, remaining work items. The LLM sees "R1 completed" but doesn't see "15/20 papers done, 5 remaining" as structured data. This causes premature DONE.

**Fix approaches**:
- Code: Add `subtasks` field to `TaskState`, inject progress into prompt, block DONE when incomplete
- Prompt: Add rule "只有当所有子任务完成时才能 DONE" to Supervisor role prompt
- Hybrid: `/goal` command sets structured milestones, code enforces completion check

## Output Format

Structure audit reports as:

```
## Task [ID] Audit Report

### Critical Issues (task-breaking)
### Architecture/Design Flaws (systemic)
### Content Quality Problems (per-task)
### Root Cause Chain (diagram)
### Recommended Fixes (prioritized)
```

## Supervisor Operational Rules (learned from live sessions)

When acting as Supervisor in a B2B Telegram team, follow these dispatch protocol rules:

### Output Mechanism
- **The output IS the Telegram message**. Between B2B_RESPONSE and B2B_DONE markers, the text is sent to the Telegram group. No separate send_message needed.
- This means message length limits apply — keep dispatch messages under ~3000 chars.
- For long requirements, write to file and reference the path.

### DONE Marker Semantics
- **DONE = task complete**. Outputting `[Supervisor][DONE]` tells ALL workers the task is finished. They will stop responding.
- **Never output DONE when bugs/issues are reported**. If a worker reports problems, dispatch a fix — don't mark DONE.
- **Use STATUS for in-progress updates**: `[Supervisor][STATUS]` for progress reports that don't require worker action.
- **Use ASSIGN for dispatching**: `[Supervisor][ASSIGN] @worker_bot` with task instructions.
- Only DONE when ALL deliverables are verified complete.
- **B2B_DONE marker** (outside B2B_RESPONSE) is for the task system to know the supervisor's turn is complete — NOT to signal task completion to workers. The `[Supervisor][DONE]` inside the response is what workers see.

### Dispatch Rules
- **One worker at a time**. Never @ multiple workers in one message — their work will duplicate.
- **Wait for report before next dispatch**. Don't fire-and-forget.
- **The output IS the Telegram message**. Between B2B_RESPONSE and B2B_DONE markers, the text is sent to the group. No separate send_message needed.
- **Fix before DONE**. When a worker reports bugs: dispatch Developer to fix → wait for fix report → dispatch Tester to verify → then DONE.

### File-Based Communication (avoid Telegram message limits)
- Telegram has a ~4000 char message limit. Long @ messages get rejected with "BadRequest: Message is too long".
- **Solution**: Write detailed requirements to a file (e.g., `experiments/smoke_test_requirements.md`), then @ with a short message referencing the file path.
- Pattern: `@worker_bot 读取 <path> 并执行。简述：<one-line summary>`
- This also applies to Planner reports — if the analysis is long, write to file and reference.

### Iterative Development Strategy
When users want to evaluate many experiment variants without training each one:
1. **Smoke test phase**: Run each experiment with `--mode smoke` (3 steps) to verify no errors + loss trend
2. **Filter**: Select top 3-5 candidates based on smoke results (loss decreasing, lowest val_loss)
3. **Full training phase**: Only train candidates with `--mode small --epochs N --max-steps M`
4. **Compare**: Generate comparison_report.md with baseline vs each experiment
5. **Select best**: Pick the winner for production training

### Honest Status Reporting
- Never claim "optimization complete" when only code/plans were created
- Distinguish between: planning done, code prepared, smoke tested, fully trained, verified
- When user asks "did it really improve?", be honest: "No, we only created the experiment infrastructure. No actual training was run."

### Workflow Pattern
```
1. Receive task → read task file (system_prompt + user_prompt)
2. If simple/feedback → DONE directly
3. If concrete work → ASSIGN to appropriate worker
4. Wait for worker REPORT
5. If issues found → ASSIGN Developer to fix → goto 4
6. If all clear → ASSIGN Tester to verify → then DONE
7. If message too long → write requirements to file, reference in short @
```

## Pitfalls

- Don't just check if files exist — read their CONTENT. Empty templates look like deliverables on a directory listing.
- Always check the actual working directory, not just the artifact directory. The real test is whether the user's filesystem was modified.
- Fallback responses often contain the original task text verbatim. This is NOT real work output.
- Handoff summaries that exceed 300 chars are a code-level bug, not just a style issue — check the `compact()` function limits.
- **Premature DONE is the #1 Supervisor failure mode**. When in doubt, dispatch next worker instead of marking DONE.
- **Don't do worker's job yourself**. If you're Supervisor, dispatch — don't write code/fix bugs directly (unless no workers are available).
