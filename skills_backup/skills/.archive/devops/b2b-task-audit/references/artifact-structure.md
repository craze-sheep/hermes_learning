# B2B Artifact Directory Structure Reference

Standard layout for a B2B task under `artifacts/tasks/<task_id>/`.

## Directory Tree

```
B2B-YYYYMMDD-HHMMSS/
├── README.md                          # Task definition (auto-generated)
├── supervisor/                        # Supervisor dispatches & decisions
│   ├── 001-...-assign-planner.md      # Dispatch to Planner
│   ├── 002-...-assign-researcher.md   # Dispatch to Researcher
│   ├── 003-...-done.md                # Final DONE/ERROR
│   └── ...
├── planner/                           # Planner reports
│   ├── 002-...-report.md              # Planner's response
│   └── ...
├── researcher/                        # Researcher reports
│   ├── 003-...-report.md              # Researcher's response
│   └── ...
├── developer/                         # Developer reports (if used)
│   └── ...
├── tester/                            # Tester reports (if used)
│   └── ...
└── files/                             # Code files, configs, deliverables
    ├── README.md                      # Project description (if generated)
    ├── plan-*.md                      # Planning documents
    ├── *.py                           # Python scripts
    ├── *.md                           # Markdown deliverables
    └── ...
```

## File Naming Convention

Pattern: `{seq:03d}-{YYYYMMDD}-{HHMMSS}-{microseconds}-{sanitized-kind}.md`

Example: `001-20260531-001006-369117-assign-planner.md`

- `seq`: Auto-incrementing sequence number per task
- `timestamp`: When the artifact was created
- `kind`: What the artifact represents:
  - `assign-<role>`: Supervisor dispatching a worker
  - `report`: Worker's response
  - `done`: Task completion
  - `error`: Task failure
  - `status`: Status update

## Artifact Content Schema

### Supervisor ASSIGN
```markdown
# Supervisor assign-<role>
- Time: ...
- Task ID: B2B-...
- Role: Supervisor
- Kind: assign-<role>
- Skills: ...
- MCP: ...

## User Task
<original user text>

## Handoff Summary
<what the worker should do>

## Code Files Written
- None (or list)

## Telegram Message
<actual message sent to group>
```

### Worker REPORT
```markdown
# <Role> report
- Time: ...
- Task ID: B2B-...
- Role: <Role>
- Kind: report
- Skills: ...
- MCP: ...

## User Task
<original user text>

## Handoff Summary
<what was accomplished, for Supervisor>

## Code Files Written
- `files/something.py` (or None)

## Telegram Message
<actual message sent to group>
```

## Key Invariants

1. Every ASSIGN should have a corresponding REPORT from the target worker
2. Worker directories may not exist if the worker never responded
3. `files/` contains actual code/configs extracted from worker messages via `FILE:` blocks
4. README.md is auto-created on first artifact write
5. Sequence numbers are per-task, not global

## What to Check During Audit

- **Chain completeness**: supervisor/assign-*.md → worker/report-*.md
- **Fallback markers**: Search for "本地 fallback", "模型不可用", "RuntimeError" in reports
- **File extraction**: Were FILE: blocks in worker messages correctly extracted to files/?
- **Working directory**: Does the user's actual FS reflect the claimed work?
- **Timestamps**: Are there unreasonable gaps (>30min) between dispatch and report?
