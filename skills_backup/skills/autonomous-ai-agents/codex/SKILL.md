---
name: codex
description: "Delegate coding to OpenAI Codex CLI (features, PRs)."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Coding-Agent, Codex, OpenAI, Code-Review, Refactoring]
    related_skills: [claude-code, hermes-agent]
---

# Codex CLI

Delegate coding tasks to [Codex](https://github.com/openai/codex) via the Hermes terminal. Codex is OpenAI's autonomous coding agent CLI.

## When to use

- Building features
- Refactoring
- PR reviews
- Batch issue fixing

Requires the codex CLI and a git repository.

## Prerequisites

- Codex installed: `npm install -g @openai/codex`
- OpenAI auth configured: either `OPENAI_API_KEY` or Codex OAuth credentials
  from the Codex CLI login flow
- **Must run inside a git repository** — Codex refuses to run outside one
- Use `pty=true` in terminal calls — Codex is an interactive terminal app

For Hermes itself, `model.provider: openai-codex` uses Hermes-managed Codex
OAuth from `~/.hermes/auth.json` after `hermes auth add openai-codex`. For the
standalone Codex CLI, a valid CLI OAuth session may live under
`~/.codex/auth.json`; do not treat a missing `OPENAI_API_KEY` alone as proof
that Codex auth is missing.

## One-Shot Tasks

```
terminal(command="codex exec 'Add dark mode toggle to settings'", workdir="~/project", pty=true)
```

For scratch work (Codex needs a git repo):
```
terminal(command="cd $(mktemp -d) && git init && codex exec 'Build a snake game in Python'", pty=true)
```

## Background Mode (Long Tasks)

```
# Start in background with PTY
terminal(command="codex exec --full-auto 'Refactor the auth module'", workdir="~/project", background=true, pty=true)
# Returns session_id

# Monitor progress
process(action="poll", session_id="<id>")
process(action="log", session_id="<id>")

# Send input if Codex asks a question
process(action="submit", session_id="<id>", data="yes")

# Kill if needed
process(action="kill", session_id="<id>")
```

## Key Flags

| Flag | Effect |
|------|--------|
| `exec "prompt"` | One-shot execution, exits when done |
| `--full-auto` | Sandboxed but auto-approves file changes in workspace |
| `--yolo` | No sandbox, no approvals (fastest, most dangerous) |

## PR Reviews

Clone to a temp directory for safe review:

```
terminal(command="REVIEW=$(mktemp -d) && git clone https://github.com/user/repo.git $REVIEW && cd $REVIEW && gh pr checkout 42 && codex review --base origin/main", pty=true)
```

## Parallel Issue Fixing with Worktrees

```
# Create worktrees
terminal(command="git worktree add -b fix/issue-78 /tmp/issue-78 main", workdir="~/project")
terminal(command="git worktree add -b fix/issue-99 /tmp/issue-99 main", workdir="~/project")

# Launch Codex in each
terminal(command="codex exec --yolo 'Fix issue #78: <description>. Commit when done.'", workdir="/tmp/issue-78", background=true, pty=true)
terminal(command="codex exec --yolo 'Fix issue #99: <description>. Commit when done.'", workdir="/tmp/issue-99", background=true, pty=true)

# Monitor
process(action="list")

# After completion, push and create PRs
terminal(command="cd /tmp/issue-78 && git push -u origin fix/issue-78")
terminal(command="gh pr create --repo user/repo --head fix/issue-78 --title 'fix: ...' --body '...'")

# Cleanup
terminal(command="git worktree remove /tmp/issue-78", workdir="~/project")
```

## Batch PR Reviews

```
# Fetch all PR refs
terminal(command="git fetch origin '+refs/pull/*/head:refs/remotes/origin/pr/*'", workdir="~/project")

# Review multiple PRs in parallel
terminal(command="codex exec 'Review PR #86. git diff origin/main...origin/pr/86'", workdir="~/project", background=true, pty=true)
terminal(command="codex exec 'Review PR #87. git diff origin/main...origin/pr/87'", workdir="~/project", background=true, pty=true)

# Post results
terminal(command="gh pr comment 86 --body '<review>'", workdir="~/project")
```

## User Preferences

- **User prefers Codex for code review and fixes.** When user says "让codex审查" or "让codex修复", delegate to Codex rather than doing it yourself. User explicitly said "你别操作，你让codex操作" (don't operate yourself, let Codex handle it).
- **Don't modify parameters without permission.** User said "你不要动我的参数" — respect existing configurations.
- **Read-only by default.** User said "你先在只有所有文件的只读权限，不要改动任何，除非我让你做啥" — only make changes when explicitly asked.

## Pitfalls

1. **`--full-auto` / `--yolo` must come AFTER `exec`, not before.**
   - ✅ `codex exec --full-auto "prompt"`
   - ❌ `codex --full-auto exec "prompt"` → `error: unexpected argument '--full-auto' found`

2. **Sandbox write restrictions** — Codex `--full-auto` (now `--sandbox workspace-write`) can only write to the workdir, `/tmp`, and `$TMPDIR`. It CANNOT write to `~/.hermes/`, `/usr/`, or other system paths. Workaround: have Codex write the file inside the project directory, then use Hermes to `cp`/`mv` it to the target location. Example: `codex exec --full-auto "Write config.sh to ./config.sh"` → `terminal("mv ./config.sh ~/.hermes/scripts/config.sh")`.

3. **Codex hangs with no output** — Sometimes Codex starts but produces nothing (just a shell prompt). If `process(action="log")` shows only the prompt after 60-120s, kill it and either: (a) simplify the prompt (escaped characters, long inline code blocks, or Unicode can cause issues), or (b) write the prompt content to a file in the project directory and have Codex read it: `write_file(path="project/review_input.sh", content="...")` then `codex exec --full-auto "Read review_input.sh and follow its instructions"`. This avoids shell escaping issues with complex prompts containing code blocks, multi-line strings, or special characters.

4. **Self-reliance when Codex fails** — User said "要学会" and "变通" (be flexible). If Codex fails or hangs twice on the same task, stop retrying and do it yourself. Don't get stuck in a retry loop — adapt. The user explicitly told me to learn from Codex's output quality ("你应该向他学习") and apply the patterns myself when Codex can't deliver.

4. **Self-reliance when Codex fails** — User said "要学会" and "变通" (be flexible). If Codex fails or hangs twice on the same task, stop retrying and do it yourself. Don't get stuck in a retry loop — adapt.

## Iterative Review Workflow

User's preferred pattern for code generation + review:

1. **Codex writes** — `codex exec --full-auto "Write X to ./file.sh"`
2. **Hermes evaluates** — Read the file, check for bugs, logic issues, edge cases
3. **Codex fixes** — Feed issues back: `codex exec --full-auto "Fix these issues in ./file.sh: ..."`
4. **Hermes re-evaluates** — Repeat until satisfied
5. **Deploy** — Move to final location, test, set up cron/service

This is better than either agent doing everything alone. Codex generates, Hermes evaluates with full conversation context. The user explicitly said "你让他写一份，然后自己评估一下他写的" and "你应该向他学习" (learn from Codex's code quality).

## Evaluate-Then-Fix Workflow

When the user wants Codex to first assess what needs changing before making changes, use two separate Codex runs:

1. **Evaluate (read-only)**: `codex exec "只评估，不要修改任何文件。分析..."` — no `--full-auto`, so Codex won't auto-approve changes. It will describe what it found.
2. **Fix**: `codex exec --full-auto "按以下规则操作..."` — with `--full-auto` to apply the changes.

This is useful for complex refactors where you want to see the scope of changes before committing.

## Waiting for Long Analysis Tasks

Codex analysis/evaluation runs often exceed the 60s `wait` timeout. Use multiple sequential waits:

```
process(action="wait", session_id="<id>", timeout=120)  # first wait (clamped to 60s)
process(action="wait", session_id="<id>", timeout=120)  # second wait if still running
```

Alternatively, poll periodically:
```
process(action="poll", session_id="<id>")
```

Codex reads files and runs shell commands during analysis, so response time scales with repo size. Small repos: 30-90s. Large repos with many files to inspect: 2-4 minutes.

## Rules

1. **Always use `pty=true`** — Codex is an interactive terminal app and hangs without a PTY
2. **Git repo required** — Codex won't run outside a git directory. Use `mktemp -d && git init` for scratch
3. **Use `exec` for one-shots** — `codex exec "prompt"` runs and exits cleanly
4. **`--full-auto` for building** — auto-approves changes within the sandbox. For review-only tasks, `--full-auto` still works but Codex may try to fix issues unless explicitly told "只检查不修改" (only check, don't modify)
5. **Background for long tasks** — use `background=true` and monitor with `process` tool
6. **Don't interfere** — monitor with `poll`/`log`, be patient with long-running tasks
7. **Parallel is fine** — run multiple Codex processes at once for batch work
8. **Review strictness is higher than Claude Code** — When reviewing code against specs, Codex additionally checks: sampling weight distributions, pairing constraints (e.g. "same velocity + y, vary all masses"), label completeness, post-processing filters, and geometric filters. If you need a quick parameter-value check, Claude Code is faster and cheaper. For thorough review including sampling strategy and label coverage, use Codex.
9. **Codex output is in-process log** — Unlike Claude Code (`--output-format json > file`), Codex writes to the PTY. Read results via `process(action="log")`, not from a file.
10. **Exit code 143 = SIGTERM** — If you kill a Codex process, the background notification will show exit code 143. This is normal, not an error.
