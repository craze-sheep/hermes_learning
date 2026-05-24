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
terminal(command="codex exec 'Add dark mode toggle to settings'", workdir="~/project")
```

For scratch work (Codex needs a git repo):
```
terminal(command="cd $(mktemp -d) && git init && codex exec 'Build a snake game in Python'")
```

**Note**: `codex exec` is non-interactive — do NOT use `pty=true`. PTY is only needed for interactive `codex` (without `exec`).

## Background Mode (Long Tasks)

```
# Start in background (no pty needed for exec)
terminal(command="codex exec --sandbox workspace-write 'Refactor the auth module'", workdir="~/project", background=true)
# Returns session_id

# Monitor progress
process(action="poll", session_id="<id>")
process(action="log", session_id="<id>")

# Kill if needed
process(action="kill", session_id="<id>")
```

## Prompt Delivery — Avoid Shell Pipe Failures

Long prompts via shell argument can cause `write_stdin failed: stdin is closed` errors. **Always write prompts to a file and redirect**:

```python
# ✅ Correct: write prompt to file, redirect stdin
write_file(path="/tmp/codex_prompt.md", content="Fix these issues...")
terminal(command="codex exec --sandbox workspace-write - < /tmp/codex_prompt.md", workdir="~/project", background=True)

# ❌ Wrong: long prompt as shell argument
terminal(command='codex exec --sandbox workspace-write "very long prompt with code blocks..."', ...)
```

This is especially important for prompts containing code blocks, multi-line strings, Unicode, or special characters.

## Key Flags

| Flag | Effect |
|------|--------|
| `exec "prompt"` | One-shot execution, exits when done |
| `--sandbox workspace-write` | Replaces deprecated `--full-auto`. Sandboxed, auto-approves changes in workspace |
| `--sandbox read-only` | Read-only sandbox for analysis/review tasks |
| `--sandbox danger-full-access` | No sandbox (use with caution) |

### Deprecated Flags (v0.132+)

| Old | New | Notes |
|-----|-----|-------|
| `--full-auto` | `--sandbox workspace-write` | Still works but prints deprecation warning |
| `--yolo` | `--sandbox danger-full-access` | Still works but prints deprecation warning |

## PR Reviews

Clone to a temp directory for safe review:

```
terminal(command="REVIEW=$(mktemp -d) && git clone https://github.com/user/repo.git $REVIEW && cd $REVIEW && gh pr checkout 42 && codex review --base origin/main")
```

## Parallel Issue Fixing with Worktrees

```
# Create worktrees
terminal(command="git worktree add -b fix/issue-78 /tmp/issue-78 main", workdir="~/project")
terminal(command="git worktree add -b fix/issue-99 /tmp/issue-99 main", workdir="~/project")

# Launch Codex in each
terminal(command="codex exec --sandbox workspace-write 'Fix issue #78: <description>. Commit when done.'", workdir="/tmp/issue-78", background=True)
terminal(command="codex exec --sandbox workspace-write 'Fix issue #99: <description>. Commit when done.'", workdir="/tmp/issue-99", background=True)

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
terminal(command="codex exec --sandbox workspace-write 'Review PR #86. git diff origin/main...origin/pr/86'", workdir="~/project", background=True)
terminal(command="codex exec --sandbox workspace-write 'Review PR #87. git diff origin/main...origin/pr/87'", workdir="~/project", background=True)

# Post results
terminal(command="gh pr comment 86 --body '<review>'", workdir="~/project")
```

## User Preferences

- **User prefers Codex for code review and fixes.** When user says "让codex审查" or "让codex修复", delegate to Codex rather than doing it yourself. User explicitly said "你别操作，你让codex操作" (don't operate yourself, let Codex handle it).
- **Don't modify parameters without permission.** User said "你不要动我的参数" — respect existing configurations.
- **Read-only by default.** User said "你先在只有所有文件的只读权限，不要改动任何，除非我让你做啥" — only make changes when explicitly asked.
- **Show prompt to user before sending.** Always preview the Codex prompt for user approval before executing.
- **Prompt must be precise and minimal.** User corrected verbose prompts: "不是在项目里搜，是要查docker的配置" — say exactly what to check, include relevant file paths, no unnecessary explanation. One sentence is usually enough. Bad: 3 paragraphs explaining background. Good: "S3 L3缺样本18，样本17是空目录。脚本: task/task6-脚本编写/generate_s3_dataset.py。数据: database/S3/L3/。seed=7确定性生成。分析：同样seed重跑能否生成和原来一样的样本？"

## Pitfalls

-1. **Codex hooks hang when Clawd is not running.** Codex's `hooks.json` calls Clawd on `localhost:23333` for every event (SessionStart, PreToolUse, PermissionRequest, etc.). If Clawd is not running, `PermissionRequest` hooks hang for 600s timeout. **Detection:** `curl -s --connect-timeout 3 http://localhost:23333/` — empty response means OK, connection refused means Clawd is down. **Fix:** Temporarily rename `~/.codex/hooks.json` to `hooks.json.bak`, run Codex, then restore. **WSL2 note:** `ss -tlnp | grep 23333` does NOT show Windows ports even in mirrored mode — use `curl` or `powershell.exe -Command "Get-NetTCPConnection -LocalPort 23333"` to verify Clawd is listening.

0. **Reviewing Codex-generated scripts — always verify import paths.** Codex frequently writes helper scripts that `import` from other project modules but forgets `sys.path.insert` for the script directory. Before saying "script looks correct", run `python -c "import module_name"` or check that the script has the same `sys.path` setup as the original module it's importing from. Logical correctness ≠ runnable correctness.

1. **`--sandbox` / `--full-auto` / `--yolo` must come AFTER `exec`, not before.**
   - ✅ `codex exec --sandbox workspace-write "prompt"`
   - ❌ `codex --sandbox workspace-write exec "prompt"` → `error: unexpected argument`

2. **Sandbox write restrictions** — `--sandbox workspace-write` can only write to the workdir, `/tmp`, and `$TMPDIR`. It CANNOT write to `~/.hermes/`, `/usr/`, or other system paths. Workaround: have Codex write the file inside the project directory, then use Hermes to `cp`/`mv` it to the target location.

3. **`write_stdin failed` error** — Long prompts passed as shell arguments can cause stdin pipe failures. Write the prompt to a file and redirect: `codex exec --sandbox workspace-write - < /tmp/prompt.md`. See "Prompt Delivery" section above.

4. **ACP mode does NOT work with codex CLI** — `delegate_task(acp_command='codex')` passes `--acp --stdio` which codex doesn't support. ACP is designed for GitHub Copilot CLI (`copilot --acp --stdio`). Always use terminal `codex exec` instead.

5. **Codex hangs with no output** — Sometimes Codex starts but produces nothing. If `process(action="log")` shows only the prompt after 60-120s, kill it and either simplify the prompt or write it to a file (see pitfall #3).

6. **Self-reliance when Codex fails** — User said "要学会" and "变通" (be flexible). If Codex fails or hangs twice on the same task, stop retrying and do it yourself. Don't get stuck in a retry loop.

## Iterative Review Workflow

User's preferred pattern for code generation + review:

1. **Codex writes** — `codex exec --sandbox workspace-write "Write X to ./file.sh"`
2. **Hermes evaluates** — Read the file, check for bugs, logic issues, edge cases
3. **Codex fixes** — Feed issues back: `codex exec --sandbox workspace-write "Fix these issues in ./file.sh: ..."`
4. **Hermes re-evaluates** — Repeat until satisfied
5. **Deploy** — Move to final location, test, set up cron/service

This is better than either agent doing everything alone. Codex generates, Hermes evaluates with full conversation context. The user explicitly said "你让他写一份，然后自己评估一下他写的" and "你应该向他学习" (learn from Codex's code quality).

## Evaluate-Then-Fix Workflow

When the user wants Codex to first assess what needs changing before making changes, use two separate Codex runs:

1. **Evaluate (read-only)**: `codex exec "只评估，不要修改任何文件。分析..."` — no `--sandbox workspace-write`, so Codex won't auto-approve changes. It will describe what it found.
2. **Fix**: `codex exec --sandbox workspace-write "按以下规则操作..."` — with `--sandbox workspace-write` to apply the changes.

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

1. **No PTY for `exec`** — `codex exec` is non-interactive, do NOT use `pty=true`. PTY is only needed for interactive `codex` (without `exec` subcommand).
2. **Git repo required** — Codex won't run outside a git directory. Use `mktemp -d && git init` for scratch
3. **Use `exec` for one-shots** — `codex exec "prompt"` runs and exits cleanly
4. **`--sandbox workspace-write` for building** — replaces deprecated `--full-auto`. For review-only tasks, omit sandbox flag or use `--sandbox read-only`
5. **Background for long tasks** — use `background=true` and monitor with `process` tool
6. **Don't interfere** — monitor with `poll`/`log`, be patient with long-running tasks
7. **Parallel is fine** — run multiple Codex processes at once for batch work
8. **Review strictness is higher than Claude Code** — When reviewing code against specs, Codex additionally checks: sampling weight distributions, pairing constraints, label completeness, post-processing filters, and geometric filters. If you need a quick parameter-value check, Claude Code is faster and cheaper. For thorough review including sampling strategy and label coverage, use Codex.
9. **Codex output is in-process log** — Unlike Claude Code (`--output-format json > file`), Codex writes to the terminal. Read results via `process(action="log")`, not from a file.
10. **Exit code 143 = SIGTERM** — If you kill a Codex process, the background notification will show exit code 143. This is normal, not an error.
11. **Codex can run simulations** — For analysis tasks, Codex can write and execute Python scripts to verify hypotheses (e.g., running physics simulations). It's not limited to static code analysis.
