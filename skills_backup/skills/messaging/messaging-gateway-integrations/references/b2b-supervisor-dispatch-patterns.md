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

## Role Contract File

The Supervisor should read the role contract file (e.g., `artifacts/hermes-role-prompts/supervisor.md`) at the start of each dispatch. This file defines:
- Available workers and their real bot usernames
- Worker capabilities (skills, MCP tools, hermes toolsets)
- Team topology rules (who can talk to whom)
- Artifact rules (file paths, naming conventions)

The role contract is **static** — it doesn't change between dispatches. But reading it ensures you have the correct bot usernames and capability information.

## Common Pitfalls

### 1. Dispatching Without Verifying State
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

### 5. Not Using Real Bot Username
❌ @Planner, @Researcher, @Developer
✅ @crazysheep_decomposer_bot, @crazysheep_researcher_bot, @crazysheep_developer_bot

### 6. Forgetting to Include Task ID
The MESSAGE must include the original task ID (e.g., B2B-20260531-022711), not the supervisor's job ID.

## When to DONE

Finish with DONE only when:
- All requested deliverables are complete
- Or a clear limitation has been explained and accepted

Do NOT DONE when:
- Only some items have been analyzed
- The comparison table hasn't been created
- Resources are incomplete and could be retried

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
