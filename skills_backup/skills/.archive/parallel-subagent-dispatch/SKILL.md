---
name: parallel-subagent-dispatch
description: "Dispatch multiple independent tasks to subagents in parallel, with mandatory post-verification for import consistency."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [delegation, parallel, subagent, verification, refactoring]
    related_skills: [subagent-driven-development, writing-plans, test-driven-development]
---

# Parallel Subagent Dispatch

## Overview

Dispatch 2-3 independent tasks to subagents simultaneously, then verify cross-file consistency after completion. The critical insight: **parallel subagents cannot see each other's changes**, so import mismatches are the #1 failure mode.

## When to Use

- Tasks modify **different files** with no overlap
- Tasks are independent (no ordering dependency)
- Each task is self-contained with full context
- You want to maximize throughput

**Never parallelize** when tasks touch the same file.

## Dispatch Pattern

```python
delegate_task(tasks=[
    {
        "goal": "Rewrite app/proxy/router.py with multi-strategy routing",
        "context": "Full context for task A...",
        "toolsets": ["terminal", "file"]
    },
    {
        "goal": "Rewrite app/proxy/circuit_breaker.py with proper state machine",
        "context": "Full context for task B...",
        "toolsets": ["terminal", "file"]
    },
    {
        "goal": "Rewrite app/middleware/rate_limit.py with token bucket",
        "context": "Full context for task C...",
        "toolsets": ["terminal", "file"]
    },
])
```

## Context Template for Each Subagent

Every subagent context MUST include:
1. **Project path** — absolute path to the project root
2. **Conda/venv activation** — `source ~/miniconda3/etc/profile.d/conda.sh && conda activate <env>`
3. **Specific goal** — what file to create/modify, what behavior to implement
4. **Existing interfaces** — function signatures the subagent must preserve or rename
5. **Verification command** — exact command to verify success
6. **Commit message** — exact git commit message

## CRITICAL: Post-Parallel Import Verification

After ALL parallel subagents complete, **always** run these checks before claiming success:

```bash
# 1. Full import check
source ~/miniconda3/etc/profile.d/conda.sh && conda activate <env>
python -c "from app.main import app; print(f'Routes: {len(app.routes)}')"

# 2. Full test suite
pytest tests/ -q

# 3. Stale reference check (if any function was renamed)
grep -rn "old_function_name" app/
```

### Why This Happens

Subagent A renames `list_users` → `list_all_users` in `store/user.py`.
Subagent B writes `routers/admin/user.py` importing `list_users`.
Both succeed independently. Together they crash.

### Fix Pattern

When import mismatches are found after parallel dispatch:
1. Read the file with the stale import
2. Use `patch` to fix the function name
3. Re-run the import check
4. Commit the fix

Don't re-dispatch a subagent for trivial renames — fix manually in < 30 seconds.

## Research-Driven Refactoring

When the user provides a research document (资料.md, architecture spec):

1. **Read the full document** — don't skim, read all sections
2. **Extract key sections** — architecture, modules, security requirements, tech stack
3. **Create a plan** — map document sections to implementation tasks
4. **Each task references** the specific document section it implements
5. **Include "查阅网址" tasks** for URLs the user wants verified
6. **Document conda env** in `docs/deployment.md`

## Config Refactoring Pitfall

When restructuring config (`settings.port` → `settings.server.port`):

```python
@dataclass(frozen=True)
class Settings:
    server: ServerConfig = field(default_factory=ServerConfig)
    
    @property
    def port(self) -> int:  # backward compat — REQUIRED
        return self.server.port
```

After refactoring, verify all old paths still resolve:
```bash
grep -rn "settings\.\(port\|admin_key\|database_url\)" app/
```

## Conda Environment Discovery

Before creating new environments, check for existing ones:
```bash
conda env list | grep <project-name>
```

Document found environments in deployment docs with activation commands.

## Task Granularity

Each parallel task should be:
- **2-5 minutes** of focused work
- **One file** (or 2 tightly coupled files)
- **Self-contained** with full context
- **Verifiable** with a single command

### User Preference: Minimal Task Size

**The user strongly prefers the smallest possible task per subagent.** When in doubt, split further. Examples:
- Literature research: **1 paper per subagent**, NOT 1 direction (7 papers) per subagent
- Report writing: **1 section per subagent**, NOT the entire report
- Code changes: **1 function per subagent**, NOT 1 module

This means more subagent calls (30-50+ is normal), but each call completes reliably within the turn budget. The user explicitly stated: "宁可多调用，也不要一次塞太多" (prefer more calls over stuffing too much into one).

**Never combine multiple deliverables into one subagent call.** If the task says "write A and B", dispatch two subagents: one for A, one for B.

### Quality Check After Each Subagent

After each subagent completes, **immediately check the output**:
1. Does the file exist?
2. Is the content complete (not truncated)?
3. Does it match the expected format?

If a subagent was interrupted or timed out, retry with an even simpler task (fewer search terms, shorter context).

## References

- `references/import-mismatch-recovery.md` — Fixing import errors after parallel refactoring
- `references/literature-survey-pattern.md` — Reusable workflow for large-scale literature research with subagents

## Red Flags

- Parallel tasks that share files
- Missing import verification after parallel dispatch
- Not including conda activation in subagent context
- Forgetting to grep for stale references after renames
- Creating new conda env when one already exists

## Example: Large-Scale Refactor

```
[Read 资料.md fully]
[Create plan.md with 27 tasks across 10 phases]
[Create todo list]

--- Phase 1: Sequential (shared state) ---
Task 1.1: Init git + docs (manual)
Task 1.2: Config refactor (manual — affects all files)
Task 1.3: DB schema (manual — affects all stores)

--- Phase 2: Parallel (independent files) ---
Dispatch 3 subagents:
  A: Security module (app/security/__init__.py)
  B: Auth middleware (app/middleware/auth.py)
  C: Store updates (app/store/user.py, apikey.py, provider.py)

[Verify imports after parallel dispatch]
[Fix any mismatches manually]

--- Phase 3: Parallel (independent files) ---
Dispatch 3 subagents:
  A: Router (app/proxy/router.py)
  B: Circuit breaker (app/proxy/circuit_breaker.py)
  C: Rate limiter (app/middleware/rate_limit.py)

[Verify imports after parallel dispatch]
[Fix any mismatches manually]

... continue through all phases
```
