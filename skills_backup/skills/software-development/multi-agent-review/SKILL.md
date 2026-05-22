---
name: multi-agent-review
description: "Use multiple AI agents (Hermes + Claude Code + Codex + OpenCode) to independently verify code, then cross-compare findings for higher confidence."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [code-review, verification, multi-agent, cross-validation, spec-compliance]
related_skills: ["requesting-code-review", "batch-script-generation", "subagent-driven-development", "claude-code", "codex", "opencode", "spec-verification"]
---

# Multi-Agent Review

Use multiple AI agents to independently verify the same code/artifact, then
cross-compare findings. No single agent catches everything — triangulation
dramatically reduces false negatives.

## When to Use

- Verifying generated code matches design docs/specs (batch scripts, config-driven code)
- Critical code review where missing a bug is costly
- User says "都检查一下" / "让codex也看看" / "三方验证"
- After batch code generation (validate N scripts against N config docs)
- When user explicitly requests multiple agents review

**Not for:** routine PR reviews (use `requesting-code-review`), simple tasks
where one reviewer suffices.

## Core Pattern

```
Hermes (self)     ──┐
Claude Code (-p)  ──┼──> Independent reviews ──> Cross-compare ──> Unified report
Codex (exec)      ──┤
OpenCode (run)    ──┘
```

Each agent gets the SAME prompt/task but works in isolation. Results are
compared after all complete.

## Step 1 — Prepare a self-contained review prompt

The prompt must be identical for all agents. Include:
- Exact file paths for code AND reference docs
- Specific check items (numbered list)
- Output format specification (PASS/FAIL per item, with details)
- Language instruction if non-English output needed

Example prompt structure:
```
Review {code_files} against {spec_files}.

Check:
1. [Category A]: specific things to verify
2. [Category B]: specific things to verify
...

Output: Each file/module [PASS] or [FAIL], FAIL lists mismatches (doc says X, code has Y).
Summary table at end.
```

## Agent Strengths (learned from slot-datamaking S1-S8 review)

Each agent has distinct review strengths. Assign roles accordingly:

| Agent | Model | Strength | Weakness | Best for |
|-------|-------|----------|----------|----------|
| **Codex** | GPT 5.5 | Deepest semantic understanding. Catches sampling strategy errors, pairing constraints, physics meaning. | Expensive, verbose, mixes real issues with optimization suggestions | Deep semantic review, complex fix delegation |
| **Claude Code** | DeepSeek v4 Pro | Best parameter-by-parameter table comparison. Clean formatted output. | Context window limits, misses sampling strategy issues | Structured parameter comparison, formatted reports |
| **OpenCode** | mimo-v2.5-pro | Catches details others miss (missing values, wrong pool sizes). | Sometimes stalls at 0% CPU, needs retry | Supplementary validation |
| **Hermes** | mimo-v2.5-pro | Fast automated batch checks (level counts, VIEWS syntax, global params). | Shallowest semantic understanding | Automated verification, orchestration, summary |

## Batching for Large Reviews

When reviewing 6+ files, batch agents to avoid context overflow:

- **Claude Code**: 2-4 scripts per call. More causes autocompact thrashing ($9.4 wasted on one 8-script attempt).
- **Codex**: Can handle all scripts in one call (longer but works).
- **OpenCode**: One call for all (may be slow).
- **Max 2 parallel Claude Code processes** — DeepSeek API rate limits with more.

## Step 2 — Launch agents in parallel

### Hermes (self)
Do the review directly using `read_file`, `terminal(cat)`, `execute_code`.
Extract key parameters and compare systematically.

### Claude Code
```
terminal(
  command="claude -p '<prompt>' --max-turns 25 --allowedTools 'Read,Bash' --output-format json > /tmp/claude_review.json 2>/dev/null",
  background=true,
  notify_on_complete=true,
  timeout=600
)
```

### Codex
```
terminal(
  command="codex exec --full-auto '<prompt>'",
  background=true,
  notify_on_complete=true,
  pty=true,
  timeout=600
)
```

### OpenCode
```
terminal(
  command="opencode run '<prompt>'",
  background=true,
  notify_on_complete=true,
  timeout=600
)
```
No PTY needed for `opencode run`. But OpenCode can sometimes stall at 0% CPU
with no output. If it hasn't produced output after 5 minutes, kill and retry
or skip.

Launch all four simultaneously. Claude Code, Codex, and OpenCode run in background;
Hermes works synchronously while waiting.

## Step 3 — Collect results

Poll background processes periodically:
```
process(action="poll", session_id="<id>")
process(action="wait", session_id="<id>", timeout=120)
```

Read Claude Code JSON output:
```
cat /tmp/claude_review.json | python3 -c "
import json,sys; d=json.load(sys.stdin)
print(d.get('result',''))
print(f'Cost: ${d.get(\"total_cost_usd\",0):.4f}')
"
```

Read Codex output from process log:
```
process(action="log", session_id="<id>")
```

## Step 4 — Cross-compare and produce unified report

Organize findings into three categories:

### High confidence (all 3 agree)
These are almost certainly real issues. Report prominently.

### Medium confidence (2 of 3 agree)
Likely real but worth flagging for human verification.

### Low confidence (1 of 3 only)
May be false positive. Report but recommend manual check.

Report format:
```
=== Unified Review Report ===

[Issue Category]
  S{N} [PASS/FAIL]

Cross-comparison:
  [Consensus issues — all 3 found]
  [Majority issues — 2 of 3 found]
  [Solo findings — verify manually]

Summary table with per-file status from each reviewer.
```

## Pitfalls

- **Identical prompts matter** — if prompts differ, you're comparing apples to
  oranges. Use the EXACT same prompt for all agents.
- **Don't wait sequentially** — launch all in parallel. Hermes works while
  Claude Code and Codex run in background.
- **Codex needs PTY** — always use `pty=true` for Codex.
- **Codex sandbox restrictions** — Codex runs in a `bwrap` sandbox with
  `--unshare-net`, `no-new-privileges` flag. It CANNOT: sudo, access Docker
  socket, call `wsl.exe`/PowerShell, install packages, or modify system configs.
  For tasks requiring system-level access (GPU setup, Docker config, package
  installation), Codex can only **diagnose and recommend** — it cannot execute.
  Use Hermes terminal directly for system-level operations.
- **Claude Code timeout** — 180s is often too short for complex multi-file
  reviews. Use `timeout=300` or higher. If it times out, simplify the prompt
  or reduce the number of files.
- **Claude Code needs --allowedTools** — restrict to Read,Bash for review tasks
  to prevent accidental modifications.
- **User says "don't modify"** — the prompt should explicitly say "只检查不修改"
  / "review only, do not modify any files".
- **Token cost** — Claude Code and Codex both cost tokens. For simple reviews,
  one agent + Hermes is enough. Reserve triple review for critical verification.
- **Codex output is verbose** — Codex echoes file contents in its output. The
  actual review summary is usually at the end. Parse accordingly.
- **process(action="wait") has a 60s timeout clamp** — use poll instead for
  longer waits, or notify_on_complete=true.
- **Cross-comparison is the value** — don't just concatenate three reports.
  The intersection (what multiple agents found) is the high-signal output.
- **Claude Code batching** — never send 6+ scripts in one call. Batch 2-4 per call.
  DeepSeek API's 1M context label is misleading; autocompact thrashes with large payloads.
- **Parallel Claude Code limit** — max 2 simultaneous. 4+ processes get rate-limited by DeepSeek.
- **OpenCode may stall** — if 0% CPU and 0 output after 5 min, kill it. Don't block on it.
  Use it as a supplementary checker, not a critical path.
- **OpenCode needs no PTY** — use `opencode run` (not interactive mode) for reviews.

## Integration

- **batch-script-generation**: After generating N scripts from configs, use this
  pattern to verify all scripts match their source configs. See
  `references/spec-compliance-checklist.md` for the verification methodology.
- **requesting-code-review**: This skill handles the "is the code correct vs spec"
  question. `requesting-code-review` handles the "is the code safe to commit" question.
  They're complementary.
- **subagent-driven-development**: Use multi-agent review as the quality gate
  after subagent completes implementation.
