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

- **Silent Fallback Degradation**: Model fails → fallback generates garbage → Supervisor treats it as valid
- **Tool-Capability Mismatch**: Worker assigned tasks requiring tools it doesn't have
- **Template-as-Deliverable**: Empty templates presented as completed work
- **Broken Handoff Chain**: Worker dispatched but never reported back
- **Unbatched Dispatch**: All work thrown at one worker instead of planned batches
- **Hallucinated Metadata**: Paper titles, links, venues from memory without verification

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

## Pitfalls

- Don't just check if files exist — read their CONTENT. Empty templates look like deliverables on a directory listing.
- Always check the actual working directory, not just the artifact directory. The real test is whether the user's filesystem was modified.
- Fallback responses often contain the original task text verbatim. This is NOT real work output.
- Handoff summaries that exceed 300 chars are a code-level bug, not just a style issue — check the `compact()` function limits.
