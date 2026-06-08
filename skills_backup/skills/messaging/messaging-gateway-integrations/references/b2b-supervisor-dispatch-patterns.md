---
name: b2b-supervisor-dispatch-patterns
description: "Decision framework and dispatch patterns for the Supervisor role in Telegram AI Team B2B tasks. Covers worker capability matching, phased execution, and handoff structure."
version: 1.0.0
tags: [telegram, b2b, supervisor, orchestration, multi-agent]
---

# B2B Supervisor Dispatch Patterns

When acting as **Supervisor** in a Telegram AI Team B2B task, follow this decision framework to dispatch work to the right worker at the right time.

## Output Format (MANDATORY)

Every Supervisor dispatch must use this exact structure:

```
<<<B2B_RESPONSE:{job_id}>>>

TARGET_ROLE: Planner/Researcher/Developer/Tester/DONE
MESSAGE: [B2B-YYYYMMDD-HHMMSS][Supervisor][ASSIGN] @real_bot_username task description
HANDOFF_SUMMARY: <=300 Chinese characters for next worker

<<<B2B_DONE:{job_id}>>>
```

- Use the **real bot username** (e.g., `@crazysheep_decomposer_bot`), never role names like `@Planner`
- MESSAGE goes to Telegram group — must include task ID and target worker username
- HANDOFF_SUMMARY is internal context for the next worker

## Decision Framework

### Step 1: Read Task State

**Always read the actual job JSON file first** — do not rely on conversation context or injected metadata prompts. The job file path is provided in the user message (e.g., `任务文件(JSON)：/path/to/job.json`).

Read the task JSON `user_prompt` to extract:
- Current short summary (当前短摘要) — what's been done
- Already contacted roles (已联系过的角色)
- Working directory (真实工作目录)

### Step 2: Identify Current Phase

Map the task state to a phase:

| Phase | Description | Signs |
|-------|-------------|-------|
| Planning | Task decomposition, plan creation | No plan exists, ambiguous requirements |
| Resource Collection | Downloads, clones, file setup | Plan exists but resources incomplete |
| Analysis | Deep reading, per-item analysis | Resources ready, analysis not started |
| Synthesis | Summary tables, final reports | Analysis complete or partially complete |

### Step 3: Match Worker to Phase

| Phase | Best Worker | Capability Match |
|-------|-------------|------------------|
| Planning | Planner (`@crazysheep_decomposer_bot`) | brainstorming, plan, writing-plans, literature-survey |
| Resource Collection | Developer (`@crazysheep_developer_bot`) | terminal, file, code_execution |
| Analysis | Researcher (`@crazysheep_researcher_bot`) | literature-survey, web-access, context7 |
| Synthesis | Researcher or Planner | Depends on whether it's data synthesis or plan refinement |
| Validation | Tester (`@crazysheep_tester_bot`) | test-driven-development, verification |

### Step 4: Verify State Before Dispatching

Before dispatching, verify the actual state matches expectations:
- Check if files/directories exist in the working directory
- Read execution plans to understand what's been completed
- Don't trust the summary blindly — verify key claims

### Step 5: Compose Dispatch

Include in the MESSAGE:
1. Task ID from the original assignment
2. Clear description of what to do
3. Specific file paths, paper numbers, or deliverable names
4. Verification criteria (how to know when done)

Include in HANDOFF_SUMMARY:
- Current phase and what was completed
- Specific next steps
- Key constraints or context (e.g., "papers #1-#5 are the foundation, do these first")

## Research Task Orchestration Pattern

For large research/analysis tasks (e.g., analyzing 20 papers), use this phased approach:

```
Phase 1: Planner → Create execution plan, define templates, identify resources
Phase 2: Developer → Download resources (PDFs, code repos), verify completeness
Phase 3: Researcher → Analyze in batches (start with foundation batch)
Phase 4: Researcher → Synthesize comparison tables, write final report
```

### Batching Strategy

When the analysis workload is large (10+ items):
1. **Foundation batch first** — items that establish core concepts (e.g., Dreamer series #1-#5)
2. **Parallel batches after** — remaining items can be analyzed independently
3. **Each batch is one dispatch** — don't try to fit all items in one worker call

### Batch Sizing

- 5 papers per batch is a good default for deep analysis
- Smaller batches (2-3) for very long/complex papers
- Larger batches (8-10) for shallow analysis or simple items

### Multi-Worker Parallel Dispatch (DAG Pattern)

When multiple independent batches exist AND a synthesis step depends on them, dispatch all independent tasks in one Supervisor response with explicit dependency arrows:

```
R1 (Researcher, batch A) ──┐
                            ├──→ P1 (Planner, synthesis)
R2 (Researcher, batch B) ──┘
```

**Format for multi-worker dispatch in one response:**

```
<<<B2B_RESPONSE:{job_id}>>>

## Supervisor 调度

### 执行顺序
R1 + R2 并行 → P1 依赖 R1+R2 完成

### @crazysheep_researcher_bot — R1：[batch A description]
- 任务 ID, 交付物, 具体输入列表, 输出路径
- dependencies: 无

### @crazysheep_researcher_bot — R2：[batch B description]
- 任务 ID, 交付物, 具体输入列表, 输出路径
- dependencies: 无

### @crazysheep_decomposer_bot — P1：[synthesis description]
- 任务 ID, 交付物, 输出路径
- dependencies: R1 + R2 完成后执行

<<<B2B_DONE:{job_id}>>>
```

**Key rules:**
- Each sub-task gets its own task ID suffix (e.g., `-R1`, `-R2`, `-P1`)
- Dependencies are stated explicitly in plain text
- The synthesis task says "等待 R1 和 R2 完成后执行"
- All tasks go in one Supervisor response — don't split into multiple responses

### Re-dispatch Handling

When the same underlying task is re-dispatched (new job ID, same user task):
1. **Verify filesystem state** — check if workers from the previous dispatch actually produced output
2. **If no progress** — re-dispatch with the same plan (workers may not have run)
3. **If partial progress** — adjust the plan to cover only remaining work
4. **If complete** — skip to synthesis or DONE

The short summary (当前短摘要) is the primary source of truth, but **always verify against the filesystem**. Workers may have completed work the summary doesn't mention, or the summary may claim completion that doesn't exist on disk.

### File Numbering Mismatch Pitfall

When analysis files are numbered sequentially (01, 02, ...) but the source items have non-sequential IDs (paper #1-#7, #11-#13), the numbering won't match. This creates confusion about which items are analyzed.

**Prevention:** When dispatching analysis tasks, instruct workers to use the **source ID** in the filename (e.g., `08-TransDreamer.md` for paper #8, not `11-TransDreamer.md`).

**Detection:** When verifying state, don't just count files — read the first line of each analysis file to confirm which paper it covers. Example:
```
analysis/08-Genie.md → header says "Genie" → this is paper #11 in the plan
```

This mismatch means "10 files in analysis/" does NOT necessarily mean "papers #1-#10 are done".

## Role Contract File

The Supervisor should read the role contract file (e.g., `artifacts/hermes-role-prompts/supervisor.md`) at the start of each dispatch. This file defines:
- Available workers and their real bot usernames
- Worker capabilities (skills, MCP tools, hermes toolsets)
- Team topology rules (who can talk to whom)
- Artifact rules (file paths, naming conventions)

The role contract is **static** — it doesn't change between dispatches. But reading it ensures you have the correct bot usernames and capability information.

## Common Pitfalls

### 0. Treating Injected Metadata as User Tasks (CRITICAL)
The job file's `user_prompt` contains injected metadata that are NOT user tasks:
- "项目目录：/path" — just context about the project location
- "角色契约文件(已在会话启动时注入，仅作参考)" — reference file path
- "真实工作目录：未指定" — working directory hint

These are **system-injected context**, not actionable instructions. The Supervisor must:
1. Read the actual `user_prompt` from the job JSON to find the real user task
2. Ignore metadata lines that describe the environment, paths, or configuration
3. Only act on the "用户需求" (user need) field

**Anti-pattern:** Treating "项目目录：/home/lzy/project/telegrambots" as a task to read that directory. It's just telling you where the project lives.

### 1. Output Format Violations (CRITICAL)
The B2B markers are **strict framing** — the entire response must be between start and end markers:
```
<<<B2B_RESPONSE:{job_id}>>>
[all content here]
<<<B2B_DONE:{job_id}>>>
```

**Rules:**
- Start marker: `<<<B2B_RESPONSE:{job_id}>>>` — on its own line, nothing before it
- End marker: `<<<B2B_DONE:{job_id}>>>` — on its own line, nothing after it
- NO content after the end marker — not even a closing remark or sign-off
- The markers use the **Supervisor's job_id** from the task JSON (e.g., `supervisor-20260531131143-2ddf7983f59047e7`)
- Worker dispatches use the **user's task ID** in the MESSAGE (e.g., `B2B-20260531-131141`)

**Anti-pattern:** Adding "以上是我的调度决策" or any trailing text after `<<<B2B_DONE:...>>>`. The parsing system stops at the end marker.

### 2. Dispatching Without Verifying State
The short summary may claim "Phase 1 complete" but files might be missing. Always verify:
```bash
# Check PDF count
ls papers/*.pdf | wc -l
# Check code repos
ls -d code/*/ | wc -l
```

### 2. Skipping the Foundation Batch
For research tasks, the foundation batch (earliest/most cited papers) must be analyzed first. Subsequent papers reference these concepts. Don't jump to "interesting" papers first.

### 3. Vague Handoff Summaries
❌ "请分析论文"
✅ "精读#1-#5（World Models+Dreamer系列），按analysis_template.md填写7问分析，输出到analysis/目录。Q4要有具体数值，Q7要有可操作实验方案。"

### 4. Wrong Worker for the Phase
❌ Dispatching Planner for file downloads (no terminal access)
❌ Dispatching Developer for literature analysis (not their specialty)
✅ Match capabilities to phase requirements

### Referencing Previous Task Outputs

When dispatching a task that's similar to a previously completed task (e.g., same analysis request with a new task ID), include the previous report path in the dispatch message so the worker can build on it:

```
参考：此前已有一次类似分析（task B2B-20260531-131141），其报告在
artifacts/tasks/B2B-20260531-131141/files/project-analysis-report.md。
如果内容仍然适用，可引用并补充更新；如有新发现，请独立产出完整报告。
```

This avoids redundant work and lets the worker focus on new findings or updates.

### 5. Not Using Real Bot Username
❌ @Planner, @Researcher, @Developer
✅ @crazysheep_decomposer_bot, @crazysheep_researcher_bot, @crazysheep_developer_bot

### 6. Forgetting to Include Task ID
The MESSAGE must include the original task ID (e.g., B2B-20260531-022711), not the supervisor's job ID.

### 7. DONE Semantics: Task Complete, Not Turn Complete (CRITICAL)
The DONE marker in the Telegram group means **the entire task is finished** — not "my dispatch turn is done." Workers interpret DONE as "stop working, the task is complete."

**Wrong understanding:** DONE = "I've finished my Supervisor turn, waiting for worker response"
**Correct understanding:** DONE = "The task is fully complete, no more work needed"

**Consequences of premature DONE:**
- Workers stop responding (they think the task ended)
- User has to re-open the task manually
- The B2B session closes

**When to use each marker:**
| Situation | Output |
|-----------|--------|
| Dispatching a worker | ASSIGN (no DONE) |
| Waiting for worker response | STATUS (no DONE) |
| Task truly complete | DONE |

**Anti-pattern:** Outputting DONE after every dispatch round. Only DONE when ALL deliverables are verified on disk.

### 8. Single Worker Dispatch (One at a Time)
Dispatch to **one Worker at a time**. Multiple Workers dispatched simultaneously may duplicate work.

**Wrong:** @Developer do X, @Tester do Y (in same response)
**Right:** @Developer do X → wait for report → @Tester verify X

Exception: The DAG pattern describes parallel dispatch, but the user explicitly corrected this — one at a time avoids duplicated work. Only use parallel dispatch when tasks are truly independent and the user approves.

### 9. Don't Modify Source Code — Work in Copies
When the user has a source directory (e.g., `ai_model/`), NEVER modify it directly. Always copy to the working directory first.

**Pattern:**
```bash
cp -r /path/to/source /path/to/working/copy
# Then modify the copy
```

**Verification:** After copying, `diff` source vs copy to confirm only intended changes differ.

### 10. Use Virtual Environment for All Execution
When the user specifies a conda/venv environment, ALL Python execution commands must use it.

**Wrong:** `python train.py`
**Right:** `conda run -n model python train.py`

Include the env activation in every dispatch message to Workers.

### 11. Premature DONE on User Complaints
Setting DONE when the task is incomplete — even for "health check" messages. If deliverables are missing on disk, any user message about it is a complaint, not a status inquiry. Respond with status + action (re-dispatch or pivot), NOT DONE.
- **Trigger:** User says "咋没反应了", "你都设置done了但是任务还没完成啊", "咋回事啊"
- **Wrong:** DONE + "在的！当前进展..." (treating it as a health check)
- **Right:** Status report + re-dispatch to stuck worker, or pivot to direct execution
- **Verification:** Before any DONE, check: are ALL deliverables present on disk? If not, don't DONE.

### 12. Telegram Message Too Long (BadRequest)
Telegram has a ~4096 character limit for bot messages. Long dispatch messages with inline code blocks, detailed requirements, and multiple steps will be rejected with `BadRequest: Message is too long`.

**Solution:** Write detailed requirements to a file in the working directory, then reference it in the @ message:
```
详细要求：读取 /path/to/requirements.md 并执行。
简述：[one-line summary]
```

**Anti-pattern:** Putting full training commands, config details, and step-by-step instructions all in the @ message.
**Correct pattern:** Write `requirements.md` → short @ message referencing the file.

### 13. Infinite Re-dispatch Loop
Re-dispatching the same worker 5+ times without ever pivoting. After 3 failed dispatches with zero output on disk, pivot to doing the work directly. See "Pivot to Direct Execution" section above.

### 14. Using send_message for B2B Dispatch (CRITICAL)
The B2B Supervisor dispatch goes through the **tmux pane**, not through `send_message()`. The B2B service captures tmux output and posts to Telegram.

**Wrong:** Calling `send_message(action='list')` → finding no Telegram target → trying `send_message(target='telegram')` → "Platform 'telegram' is not configured" → wasting rounds diagnosing.

**Right:** Just output the B2B response format directly in your text response. The service handles routing.

**Trigger:** Any time you're acting as Supervisor in a B2B task dispatched via job JSON. The job JSON path (`artifacts/tmux-jobs/*.job.json`) is the signal that you're in tmux-capture mode.

### 15. Pretending to Dispatch When Workers Can't Respond
In CLI/tmux mode, if the B2B service isn't running or workers aren't online, dispatches go into the void. After 1-2 failed attempts, pivot to direct execution. Don't keep outputting ASSIGN messages that nobody will pick up — the user sees empty @mentions and gets frustrated.

**Detection:** If your previous dispatch produced no worker report in the conversation, the worker likely didn't receive it.

**Response:** Load the relevant skill yourself and execute the work directly. Announce the pivot: "Worker 未响应，Supervisor 直接执行。"

**Nuance — Workers may respond across invocations:** In tmux-capture mode, workers don't respond within the same Supervisor invocation. The B2B service captures your output, posts to Telegram, workers process, and then creates a NEW Supervisor job. So "no response" means "no response by the next invocation", not "no response within this turn." Check the filesystem for new worker reports at the start of each invocation before deciding to re-dispatch or pivot. A worker that didn't respond in invocation N may have produced output by invocation N+1.

### 16. Trailing Content After End Marker (CRITICAL)
The end marker `<<<B2B_DONE:{job_id}>>>` must be the **absolute last line** of the response. Nothing after it — no closing remarks, no sign-offs, no explanations, no blank lines with text.

**Wrong:**
```
<<<B2B_DONE:supervisor-xxx>>>
以上是本轮调度。
```
**Right:**
```
<<<B2B_DONE:supervisor-xxx>>>
```

The B2B parser stops at the end marker. Anything after it is invisible to the service but confusing to the user who sees raw terminal output.

## When to DONE

Finish with DONE only when:
- All requested deliverables are **verified on disk** (not just claimed in summaries)
- Or a clear limitation has been explained and accepted

### DONE Response Content Structure

When outputting DONE, the MESSAGE should be **concise and actionable**:

```
[B2B-task-id][Supervisor][DONE] 任务完成。

**已完成的交付物：**
- `path/to/file1.md` — 说明
- `path/to/file2.md` — 说明

**核心结论：**
[1-3 sentences with the key finding]

**建议下一步：**
[Optional: recommended follow-up action]
```

**Rules:**
- List deliverables with verified file paths
- State the core conclusion in plain language (not a wall of text)
- Keep HANDOFF_SUMMARY under 300 chars for the next invocation's context
- Do NOT repeat the entire report content — the user can read the files

Do NOT DONE when:
- Only some items have been analyzed
- The comparison table hasn't been created
- Resources are incomplete and could be retried
- A worker was dispatched but hasn't produced output yet (re-dispatch or pivot instead)
- The user is asking about an incomplete task (even if phrased as a question)

**Anti-pattern (learned the hard way):** Setting DONE for a "health check" when the underlying task is genuinely incomplete. The user said "你都设置done了但是任务还没完成啊" — the Supervisor had treated "咋没反应了" as a pure status inquiry and set DONE, but the task had 5/20 papers unfinished. The rule: **if the task is incomplete, a user message about it is NOT a health check — it's a complaint about stalled progress. Respond with status + re-dispatch or pivot, NOT DONE.**

### Simple Informational Queries → DONE (No Dispatch)

Questions like "who are you", "introduce the team", "what can you do" are NOT tasks requiring worker dispatch. Answer directly with DONE and the information requested. Do NOT dispatch to Planner/Researcher/Developer/Tester for pure introductions or capability inquiries.

**Pattern:**
```
<<<B2B_RESPONSE:{job_id}>>>

TARGET_ROLE: DONE

MESSAGE: @user Here's the team introduction...
[content answering the question]

HANDOFF_SUMMARY: 用户询问团队介绍，属简单信息查询，直接 DONE 回复。

<<<B2B_DONE:{job_id}>>>
```

### Health Check vs. Complaint Distinction

| User Message | Is it a Health Check? | Correct Response |
|---|---|---|
| "还在吗" / "are you there" (task complete) | ✅ Yes | DONE + status |
| "进度怎么样" (task in progress, workers active) | ✅ Yes | DONE + progress report + nudge if needed |
| "你们是谁" / "介绍团队" | ✅ Yes — informational | DONE + direct answer |
| "咋没反应了" (task incomplete, worker stuck) | ❌ No — it's a complaint | Status + re-dispatch or pivot, NOT DONE |
| "你都设置done了但是任务还没完成啊" | ❌ No — it's a correction | Apologize, re-dispatch or pivot, NOT DONE |
| "咋回事啊，不安排继续了" (task incomplete) | ❌ No — it's a complaint | Status + re-dispatch or pivot, NOT DONE |

**Rule of thumb:** If the task has unfinished deliverables, ANY user message about it — even phrased as a question — is a complaint about stalled progress, not a health check. Re-dispatch or pivot. Only DONE when deliverables are verified complete on disk.

### Health Check / Status Inquiry Handling

When the user message is a **genuine** status check (task is complete or workers are actively producing output), respond with DONE and a status report. Do NOT dispatch to workers — this is not a new task.

**Pattern:**
```
<<<B2B_RESPONSE:{job_id}>>>

在的！当前进展：

✅ **已完成 X/N：**
- [list completed items]

❌ **待完成：**
- [list pending items]

@target_bot — [brief nudge if a worker is stuck]

<<<B2B_DONE:{job_id}>>>
```

Key rules:
- Use DONE, not a worker dispatch — health checks are not actionable work items
- Give a clear progress summary with ✅/❌ markers
- If a worker is stuck, include a brief nudge in the MESSAGE (this is visible to the user and the worker)
- Don't over-explain or apologize — just report state and any pending actions

### Worker "Stuck" Re-dispatch

When a worker has been dispatched but hasn't produced output (no files on disk), the Supervisor should:
1. Verify filesystem state — confirm the worker's expected output is truly missing
2. Re-dispatch with the same task — workers may not have run due to timing, queue issues, or message delivery failures
3. Label as "催促" (nudge) in the dispatch — makes it clear this is a retry, not a new task
4. Include the original task ID suffix (e.g., `-R2`) for traceability

Do NOT:
- Assume the worker failed — they may simply not have been invoked yet
- Change the task scope — keep the same deliverables and format requirements
- Escalate to a different worker — the original worker's capabilities are still the right match

### Pivot to Direct Execution (CRITICAL)

When a worker has been dispatched **3+ times** without producing any output on disk, the Supervisor must **pivot to doing the work directly** instead of continuing to re-dispatch. Repeated dispatches that never get picked up are a strong signal that the worker invocation mechanism is broken (e.g., CLI context where @mentions don't trigger real processes, worker queue backlog, or bot offline).

**Pivot trigger:** 3 dispatches to the same worker for the same sub-task, zero files produced on disk.

**Pivot pattern:**
1. Verify one final time that the expected output is truly missing
2. Announce the pivot: "Researcher 调度未被拾起，现亲自完成剩余工作"
3. Execute the work directly using available tools (web search, file write, code repos)
4. Update the comparison table / deliverables with the new results
5. DONE — don't re-dispatch to the worker after completing the work yourself

**Why this matters:** The Supervisor has access to the same tools (web, file, browser) that workers use. The B2B protocol is a coordination mechanism, not a capability constraint. If coordination fails, the Supervisor should still deliver.

**Anti-pattern (learned the hard way):**
```
Round 1: @Researcher please do R2 → no pickup
Round 2: @Researcher 催促 R2 → no pickup
Round 3: @Researcher 再次催促 R2 → no pickup
Round 4: @Researcher 请立即执行 R2 → no pickup
Round 5: @Researcher ... → STILL no pickup, user frustrated
```
**Correct pattern:**
```
Round 1: @Researcher please do R2 → no pickup
Round 2: @Researcher 催促 R2 → no pickup
Round 3: @Researcher 最后催促 R2 → no pickup
Round 4: Supervisor pivots, does R2 directly, DONE
```

## CLI/Tmux Mode Dispatch (CRITICAL)

When the Supervisor runs as a Hermes agent in a **tmux session** (the standard B2B deployment), the dispatch mechanism works through **tmux pane capture**, not through `send_message()`.

**The tmux pane output IS the dispatch channel.** The B2B service (`llm.py` → `TmuxHermesClient`) captures the tmux pane content via `tmux capture-pane` and posts it to the Telegram group. You do NOT need `send_message()` or any messaging tool.

**Do NOT:**
- Call `send_message(action='list')` to find Telegram targets
- Call `send_message(target='telegram', message=...)` — Telegram is likely not configured in the CLI agent's Hermes instance
- Spend multiple rounds diagnosing "Telegram not configured" errors
- Treat "Platform 'telegram' is not configured" as a blocker

**Do:**
- Simply output the B2B response format (markers + TARGET_ROLE + MESSAGE + HANDOFF_SUMMARY) directly in your response text
- The B2B service captures your output and routes it to the Telegram group
- Workers see the @mention and respond in the group

**Flow:**
```
B2B Service → creates job JSON → pastes prompt into tmux session
                                    ↓
Supervisor agent reads job, outputs B2B response in tmux pane
                                    ↓
B2B Service → captures pane → posts MESSAGE to Telegram group
                                    ↓
Worker bot sees @mention → processes task → reports back
                                    ↓
B2B Service → new job JSON for Supervisor → cycle continues
```

**Why send_message fails:** The CLI agent's Hermes instance typically only has Weixin/other platforms configured, not Telegram. The Telegram bots are separate processes managed by the B2B service. The agent's role is to produce the right output format — routing is the service's job.

## Pivot to Direct Execution (CLI Mode)

In CLI/tmux mode, if a worker doesn't pick up the dispatched task after 1-2 attempts (worker tmux session not running, B2B service not routing, etc.), the Supervisor should **pivot to doing the work directly** instead of endlessly re-dispatching.

The Supervisor can load worker-relevant skills (e.g., `literature-survey`) and execute the work itself. Use the skill's fallback strategies (e.g., Tier 3 knowledge-only mode for research without web tools). This is preferable to the user seeing repeated unanswered @mentions.

## Architectural Insight: Stateless Supervisor with Stateful Summary

Each Supervisor invocation is a **separate job** — it does not retain memory from previous dispatches. The only state that carries forward is the "当前短摘要" (current short summary) field in the task JSON.

Implications:
- **Always read the short summary first** — it's your only source of truth about what happened
- **Verify claims in the summary** — check if files actually exist before dispatching the next phase
- **Write good summaries as a worker** — the next Supervisor invocation depends on your summary being accurate and complete
- **Don't assume continuity** — each Supervisor invocation must re-read the task JSON, execution plan, and working directory to understand the current state

## Capability Gap Handling

If a task requires capabilities no worker has:
1. Mark as "待执行/待验证" (pending execution/verification)
2. Explain what's missing in the HANDOFF_SUMMARY
3. Suggest what the user needs to provide or configure

## Related Skills

- `b2b-team-worker` — Worker contract rules (REPORT format, forbidden patterns)
- `telegram-b2b-task-format` (reference) — Protocol format details
- `kanban-orchestrator` — Kanban-based orchestration (different system)
