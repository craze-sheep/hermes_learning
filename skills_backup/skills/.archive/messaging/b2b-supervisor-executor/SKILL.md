---
name: b2b-supervisor-executor
description: "Execute B2B Supervisor tasks from tmux job JSON files. Covers reading job files, dispatching to workers, output format with B2B_RESPONSE/B2B_DONE markers, and DONE reporting. Load when receiving a Supervisor-role tmux job."
triggers:
  - "B2B Supervisor task from tmux"
  - "supervisor-*.job.json"
  - "Telegram AI Team Supervisor"
  - "TARGET_ROLE: Planner/Researcher/Developer/Tester/DONE"
  - "B2B_RESPONSE / B2B_DONE markers"
---

# B2B Supervisor Task Executor

When receiving a task as the **Supervisor** role in the Telegram AI Team B2B system, follow these rules. The Supervisor receives user tasks, dispatches work to workers (Planner/Researcher/Developer/Tester), and reports completion.

## Step 0: Understand the Tmux Dispatch Mechanism

**You do NOT need send_message or any messaging tool.** The B2B service captures your tmux pane output and posts it to Telegram. Your output IS the group message.

See `references/tmux-dispatch-mechanism.md` for the full flow diagram and code-level details. Reading the service code (service.py, llm.py) is unnecessary — the reference covers it.

## Step 1: Read the Job JSON + Role Contract

The task arrives as a JSON file at a path like:
```
artifacts/tmux-jobs/supervisor-<timestamp>-<hash>.job.json
```

Read it and extract:
- `job_id` — used for wrapper markers (e.g., `supervisor-20260531174942-563c8565d51b40cc`)
- `system_prompt` — Supervisor behavioral rules
- `user_prompt` — contains the actual task description, task ID, and dispatchable roles
- `hard_rules` — contract constraints

**Also read the role contract file** if present at `artifacts/hermes-role-prompts/supervisor.md`. It defines the exact output format (TARGET_ROLE/MESSAGE/HANDOFF_SUMMARY) and dispatch rules. The user_prompt may reference it as "角色契约文件".

**PITFALL**: The `user_prompt` may reference external files (e.g., "去看 /path/to/prompt.md"). Read those files to understand the ACTUAL task. Do not treat directory paths as tasks.

## Step 2: Read External Task Files

If `user_prompt` says "任务有疑惑时就去看 X" or references a prompt file, READ that file. The real task definition lives there, not in the job JSON itself.

## Step 3: Execute or Dispatch

Based on the task:
- **Simple tasks** (health checks, confirmations): answer directly with DONE
- **Complex tasks**: dispatch to workers via messaging (if Telegram configured) or execute directly (if not)

When executing directly (no Telegram channel available):
- Follow the task requirements from the external prompt file
- Produce all required deliverables
- Write output to the specified working directory

## Output Format (MANDATORY)

Output must follow this EXACT three-part structure. Each part is output as a separate block:

```
<<<B2B_RESPONSE:job_id>>>
```
```
TARGET_ROLE: Planner/Researcher/Developer/Tester/DONE
MESSAGE: [task output here]
HANDOFF_SUMMARY: <=300 Chinese characters summarizing what was done
```
```
<<<B2B_DONE:job_id>>>
```

### Format Rules (CRITICAL — user corrected this 3+ times)
1. **Start marker on its own line.** Nothing else on that line. No content before or after it on the same line.
2. **Response body follows.** TARGET_ROLE / MESSAGE / HANDOFF_SUMMARY go here, separated from markers by blank lines.
3. **End marker on its own line.** Nothing else on that line.
4. **ZERO output after the end marker.** Not a blank line, not a space, not a newline. The DONE marker is the absolute last thing you emit.

### Wrapper Markers
- `<<<B2B_RESPONSE:job_id>>>` — start marker. `job_id` is the FULL `job_id` from the JSON.
- `<<<B2B_DONE:job_id>>>` — end marker. Same `job_id`.

### Anti-pattern: Mixing markers with content
WRONG (puts content on same line as marker):
```
<<<B2B_RESPONSE:xxx>>>
TARGET_ROLE: DONE
MESSAGE: ...
<<<B2B_DONE:xxx>>>
some trailing text
```

RIGHT (markers isolated, nothing after DONE):
```
<<<B2B_RESPONSE:xxx>>>

TARGET_ROLE: DONE
MESSAGE: ...

<<<B2B_DONE:xxx>>
```

### TARGET_ROLE
- `DONE` when the task is complete
- `Planner` / `Researcher` / `Developer` / `Tester` when dispatching to a worker (include `@bot_username` in MESSAGE)

### HANDOFF_SUMMARY
- <=300 Chinese characters
- Enough context for the next role or for task archival
- Mention what was produced and where

## Multi-Phase Tasks

Some tasks have sequential phases defined in different files (e.g., prompt.md for planning, promptv2.md for implementation). When user_prompt says "继续" and references a NEW prompt file, treat it as a new task phase.

For experiment implementation phases (copying base code, modifying per-experiment), see `references/experiment-implementation-pattern.md` for the automation approach.

## Dispatch Rules

### One Worker at a Time
**Only @ one Worker per dispatch.** Wait for their REPORT before dispatching the next. Dispatching multiple workers simultaneously causes duplicated work.

### Don't Rush to DONE (Critical)
When Telegram is configured, the session stays open until you output DONE. Use this to dispatch real work to Workers. Only DONE when the task is **actually complete with verified results** — not when you've just acknowledged it or created infrastructure.

**DONE means "the user's requested outcome is satisfied."** If you only wrote code but never ran it, the task is NOT done. If you only planned but never executed, the task is NOT done.

**Anti-pattern**: Outputting DONE after every dispatch round. This tells Workers the task is over and they stop responding. Use ASSIGN or STATUS instead for in-progress work. Reserve DONE for true completion.

**Verification checklist before DONE**:
- Did the code actually run (not just get written)?
- Are there real metrics/results (not just placeholders)?
- Did a Tester or you verify the results?

### Dispatch via @ in Output
Dispatch by including `@bot_username` in your MESSAGE field within the B2B output markers. No special send_message tool needed — your output IS the group message. Format:
```
[B2B-YYYYMMDD-HHMMSS][Supervisor][ASSIGN] @crazysheep_developer_bot
任务描述...
```

## Pitfalls

### 1. Treating directory paths as tasks
When user_prompt says "项目目录：/path/to/dir", this is CONTEXT, not a task. The actual task is in `user_prompt`'s main text or in a referenced prompt file.

### 2. Telegram message length limit
Worker responses can exceed Telegram's message size limit, causing `BadRequest: Message is too long`. When dispatching to Workers, explicitly instruct them to keep responses concise (e.g., "请精简输出，500 字以内"). If a Worker's previous response was rejected for length, re-dispatch with explicit length constraints.

**File-based requirements pattern**: When dispatch requirements are long (multi-step commands, detailed checklists), write the full requirements to a file in the working directory and reference it in the @ message. This avoids Telegram truncation and gives Workers a persistent reference:
```
[B2B-...][Supervisor][ASSIGN] @crazysheep_developer_bot
详细要求已写入 experiments/smoke_test_requirements.md。请读取并执行。
```
The file should be self-contained with exact commands, expected outputs, and success criteria.

### 3. Outputting anything after <<<B2B_DONE:...>>>
The tmux dispatcher reads everything between the markers. Content after DONE may be interpreted as a new response or cause parsing errors. **Zero content after DONE.**

### 4. Confusing job_id with task_id
- `job_id` (from JSON): `supervisor-20260531174942-563c8565d51b40cc` — used in wrapper markers
- `task_id` (from user_prompt): `B2B-20260531-174940` — used in message headers and task directories
- Do NOT mix them up.

### 4. Re-executing completed tasks or task transitions
When user says "继续" (continue), check if the previous task is already complete (look for existing deliverables). If complete, report DONE with a summary rather than redoing work.
**BUT**: "继续" may also mean "proceed to the NEXT task file" (e.g., prompt.md → promptv2.md). Always re-read user_prompt carefully — if it references a DIFFERENT prompt file, that's a NEW task, not a continuation of the old one.

### 5. Missing external file reads
If user_prompt references a file path for task details, you MUST read it. Guessing the task from the user_prompt alone is insufficient — the referenced file contains the full specification.

### 6. Automation script patch_file silent failures
When using `str.replace()` in Python automation scripts (e.g., create_experiments.py), string matching can silently fail if whitespace, indentation, or line endings differ from expectations. The replacement simply doesn't apply, leaving the original code unchanged.
**Mitigation**: After running any automation script that patches files, verify the patches actually applied by searching for the expected new code (e.g., `grep "EXP003" encoder.py`). Fix any misses with the `patch` tool.

### 7. Confusing infrastructure with actual results
Creating experiment code directories is NOT the same as running experiments and getting results. When the user asks "did the optimization actually work?", the answer is NO if you only wrote code without training.

**Pattern**: User asks "真的优化了吗" after code creation phase. The honest answer is: "We created the experiment infrastructure but haven't run any training." Don't claim DONE for code-only work when the task requires actual optimization results.

**Remedy**: After creating experiment code, explicitly state what's missing (baseline training, experiment execution, metric comparison) and ask if the user wants to proceed with actual execution.

For the full execution workflow (baseline → experiments → comparison), see `references/ml-experiment-execution-workflow.md`.

For iterative experiment dispatching (smoke test → full training), see `references/iterative-experiment-dispatch.md`.

### 8. B2B dispatch works through tmux pane capture, NOT send_message

When you receive a B2B supervisor task (job JSON in `artifacts/tmux-jobs/`), dispatch works through **tmux pane capture** — the B2B service captures your output and posts to Telegram. You do NOT need `send_message()`.

**Key insight:** `send_message(action='list')` showing no Telegram target does NOT mean you can't dispatch. The tmux capture mechanism bypasses Hermes messaging channels entirely.

**The real check:** Did the task arrive via a `supervisor-*.job.json` file? If yes → you're in B2B mode → output B2B response format directly. The service handles routing.

**When B2B dispatch works (job JSON present):**
- Output B2B response markers + TARGET_ROLE + MESSAGE directly in your text
- Don't call `send_message()` — it's irrelevant for B2B routing
- Workers see @mentions because the service posts your output to the Telegram group

**When B2B dispatch doesn't work (no job JSON, plain CLI):**
- Execute the work directly using available tools
- Load worker-relevant skills to do the work yourself

**Anti-pattern:** Calling `send_message(action='list')`, seeing no Telegram, concluding you can't dispatch, then wasting turns redoing everything yourself. If a job JSON was provided, dispatch works.

### 9. Confusing dispatch acknowledgment with task completion (CRITICAL — most common mistake)

The B2B output format has TWO different "done" concepts:
- `<<<B2B_DONE:job_id>>>` — end marker for YOUR response (always output this)
- `TARGET_ROLE: DONE` — signals task completion to the team (only when truly done)

**RULE: If you are dispatching a Worker, TARGET_ROLE must be ASSIGN — never DONE.**

When you have more work to do (waiting for Worker reports, dispatching next steps), use:
- `TARGET_ROLE: ASSIGN` — dispatching to a Worker
- `TARGET_ROLE: STATUS` — reporting progress without dispatching

Do NOT put `TARGET_ROLE: DONE` when there are pending Worker assignments or unverified results.

**Why this matters**: Outputting DONE in the Telegram group tells ALL Workers the task is over. They stop responding. You then wait forever for a report that will never come. This happened 4+ times in a single session.

**Correct pattern for dispatch**:
```
TARGET_ROLE: Planner   ← or Researcher/Developer/Tester
MESSAGE: [B2B-...][Supervisor][ASSIGN] @bot_username 任务描述...
HANDOFF_SUMMARY: ...
```

**Correct pattern for completion**:
```
TARGET_ROLE: DONE
MESSAGE: [B2B-...][Supervisor][DONE] 任务完成，结果...
HANDOFF_SUMMARY: ...
```

**Test**: If your MESSAGE contains "[ASSIGN]" or "@bot_username", your TARGET_ROLE must NOT be DONE.

### 10. FP16 overflow in masked_fill
When using AMP (mixed precision), `masked_fill` with -1e9 can overflow FP16 range. Use -1e4 instead. This commonly occurs in interaction.py's attention masking. The symptom is NaN/Inf loss during training. Fix: change `-1e9` to `-1e4` in the copied code before running training.

### 11. Worker not responding / re-dispatching
If a Worker doesn't respond after a reasonable wait (training takes a few minutes, but 10+ minutes with no report is a problem), check:
1. Did the Worker's response get rejected for message length? (Check for `BadRequest: Message is too long` in logs)
2. Did the task get auto-completed by the system before the Worker responded?
3. Is the Worker still running (check for metrics files in the working directory)?

Re-dispatch with a shorter message if length was the issue. Use the file-based requirements pattern (pitfall #2).

### 12. Check existing deliverables before re-dispatching
When user says "继续" or "怎么没有反应了", check if deliverables already exist:
- Look for metrics files (`*metrics*`, `*smoke*`, `comparison*`)
- Look for Developer/Tester reports in `artifacts/tasks/<task_id>/`
- Check if the task directory has a `supervisor/*-done.md`

If results exist, summarize and proceed to the next step rather than re-dispatching the same work.

### 13. Premature DONE due to context loss (most insidious bug)

The Supervisor LLM outputs `TARGET_ROLE: DONE` after the first Worker report because it lacks progress context. The `manager_decide()` prompt only shows the latest `state.summary` (which gets overwritten each turn) and the current `incoming` message. It does NOT show:
- How many subtasks/phases are complete vs remaining
- Previous handoff summaries (they're overwritten)
- Whether the user's original request has multi-phase structure

**Symptom:** Task marked `completed: true` after 1 turn. User messages after that are silently ignored (`if state.completed: return`). User complains "你都设置done了但是任务还没完成啊".

**Diagnosis:** Check `artifacts/tasks/<task_id>/state.json` — if `turns: 1` and `completed: true` but the user request clearly needs multiple rounds, this bug hit.

**See:** `references/supervisor-context-loss-diagnosis.md` for full code-level analysis and fix options.

### 14. Doing work yourself instead of dispatching
User feedback: "要学会把大任务分配下去，你有一个团队" (Learn to delegate big tasks, you have a team).

When Telegram is configured and Workers are available, DISPATCH work instead of doing it yourself. The Supervisor's job is to:
1. Decompose the task
2. Dispatch to the right Worker
3. Wait for reports
4. Make decisions on next steps

The Supervisor should NOT:
- Run training scripts directly
- Write experiment code directly
- Execute shell commands directly

Exception: When Telegram is NOT configured (no messaging channel available), the Supervisor must execute directly. But when Workers can be reached, always dispatch.

**Pattern for long tasks**: Write requirements to a file → dispatch Worker with short @ message referencing the file → wait for report → decide next step.

## Relationship to b2b-team-worker

This skill covers the **Supervisor** side. The `b2b-team-worker` skill covers the **Worker** side. Key differences:

| Aspect | Supervisor | Worker |
|--------|-----------|--------|
| Header | `TARGET_ROLE: DONE/role` | `[task][Role][REPORT]` |
| Dispatch | Can assign workers | Cannot assign workers |
| Output | Wraps with B2B_RESPONSE/DONE | Wraps with B2B_RESPONSE/DONE |
| @ mentions | Can @ any worker | Can only @ Supervisor |
