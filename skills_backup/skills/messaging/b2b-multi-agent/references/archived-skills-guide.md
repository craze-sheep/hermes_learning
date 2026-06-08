# Archived B2B Skills — Detailed Reference

The three original B2B skills were consolidated into `b2b-multi-agent`. Their full content is preserved in the archive for reference:

## Supervisor Details
**Archive:** `~/.hermes/skills/.archive/messaging/b2b-supervisor-executor/`

Key reference files:
- `references/tmux-dispatch-mechanism.md` — how tmux pane capture routes output to Telegram
- `references/supervisor-context-loss-diagnosis.md` — why premature DONE happens (manager_decide prompt only shows last summary)
- `references/ml-experiment-execution-workflow.md` — baseline → experiments → comparison workflow
- `references/iterative-experiment-dispatch.md` — smoke test → full training pattern
- `references/experiment-implementation-pattern.md` — automating multi-directory experiment creation
- `references/slot-datamaking-task-pattern.md` — slot data-making task pattern

## Worker Details
**Archive:** `~/.hermes/skills/.archive/messaging/b2b-team-worker/`

Key reference files:
- `references/tester-verification-template.md` — reusable verification report template
- `references/rejection-examples.md` — examples of messages that get rejected by the outbound filter
- `references/researcher-github-fact-check.md` — GitHub project verification workflow
- `references/ml-training-execution.md` — PyTorch AMP pitfalls, conda run gotchas, metrics JSON templates

## Audit Details
**Archive:** `~/.hermes/skills/.archive/devops/b2b-task-audit/`

Key reference files:
- `references/failure-modes.md` — full taxonomy of B2B failure modes
- `references/batch-experiment-creation.md` — automating multi-directory experiment creation
- `references/artifact-structure.md` — how to read artifact directories
- `references/b2b-dispatch-debugging.md` — debugging dispatch issues
- `scripts/triage.py` — artifact triage script
