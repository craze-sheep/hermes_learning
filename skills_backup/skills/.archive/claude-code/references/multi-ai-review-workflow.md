# Multi-AI Code Review Workflow

When reviewing code against specification docs, use multiple AI tools for cross-validation. Each tool has different strengths.

## Model Assignments (current config)

| Tool | Model | Provider | Strengths |
|------|-------|----------|-----------|
| Hermes | mimo-v2.5-pro | Xiaomi | Automation, scripting, orchestration |
| Claude Code | deepseek-v4-pro[1M] | DeepSeek API | Parameter comparison, formatted reports |
| Codex | GPT 5.5 | OpenAI | Deep review, sampling strategy, labels |
| OpenCode | mimo-v2.5-pro | Xiaomi | Implementation (unstable for review) |

## Tool Strictness Levels

### Claude Code (lenient)
- Checks: parameter values match spec, level count, global rendering params, VIEWS syntax
- Misses: sampling weight distributions, pairing constraints, label completeness, post-processing filters
- Best for: quick sanity check, catching gross mismatches

### Codex (strict)
- Checks: everything Claude Code checks PLUS:
  - Sampling weights (e.g. "restitution 0:10%, 0.3:20%, ...")
  - Pairing constraints (e.g. "same velocity + y, vary all masses")
  - Label completeness (physics_labels fields vs doc requirements)
  - Post-processing filters (e.g. "only keep samples with no collision")
  - Geometric filters (miss distance, contact radius checks)
- Best for: thorough review, catching subtle specification drift

### OpenCode (moderate)
- Between Claude Code and Codex in strictness
- Good at catching structural issues and missing implementations

## Batching Strategy

When reviewing 6+ scripts:
- Split into batches of 2-4 scripts per AI invocation
- Run max 2 Claude Code processes in parallel (API rate limit)
- Codex can run 1 at a time (uses PTY)
- OpenCode runs 1 at a time

## Cross-Validation Pattern

1. Run all three AIs on the same codebase
2. Items flagged by ALL three = high confidence bugs
3. Items flagged by two = medium confidence, verify manually
4. Items flagged by one only = check if it's a strictness difference or real bug
5. Compile a merged report showing each AI's verdict per check item

## Output Format

Each AI should produce: `S{N} [PASS/FAIL]` with specific mismatch details.
Final report: table with columns for each AI's verdict + merged verdict.

## Cost Awareness

- Claude Code with DeepSeek: ~$0.85-1.15 per 2-script batch
- Codex: ~$0.50-1.00 per full review
- OpenCode: varies by provider
- Total for 8 scripts across 3 AIs: ~$8-15
