# Experiment Plan Template

> Use this template when the task is "read existing notes + code → produce experiments/PLAN.md"
> Not for writing new notes — use the 8-section template for that.

## Structure

```markdown
# Experiment Plan

> Based on N papers deep reading + code analysis
> Date: YYYY-MM-DD
> Model: <ModelName>

---

## Architecture Evaluation

### Current Architecture Overview
(ASCII diagram of the full pipeline)

### Advantages
(What the current design does well, with paper references)

### Bottlenecks
(What limits performance, with paper references)

### Should We Do a Major Overhaul?
Yes/No with reasoning. Default to "No" unless literature strongly suggests otherwise.

---

## Literature Summary

### Category 1: Incremental Improvements (N papers)
| # | Paper | Core Idea | Relevance to Code | Key Implementation |
|---|-------|-----------|-------------------|-------------------|

### Category 2: Architecture Alternatives (N papers)
| # | Paper | Core Idea | Comparison with Current | Replacement Value |
|---|-------|-----------|------------------------|-------------------|

### Category 3: Loss/Eval/Training (N papers)
| # | Paper | Core Idea | Relevance |
|---|-------|-----------|-----------|

---

## Recommended Experiment Order

### Phase 1: Incremental Optimization (low risk)
#### exp001_name — description
- **Rationale**: why this experiment, which paper
- **Expected improvement**: quantified
- **Files to change**: list
- **Change overview**: what to do
- **Corresponding paper**: research/papers/xxx/notes.md
- **Verification method**: how to validate
- **Risk**: low/medium/high + explanation

### Phase 2: Architecture Alternatives (high risk, high reward)
(same format)

---

## Summary

### Recommended Order
(numbered list)

### Diff from ROADMAP.md
| Original Plan | Adjustment | Reason |
|---------------|-----------|--------|

### Expected Impact Summary
| Experiment | Expected Improvement | Difficulty | Lines Changed |
|-----------|---------------------|-----------|--------------|
```

## Key Principles

1. **Check existing code FIRST** — don't propose experiments for things already implemented
2. **Incremental before architectural** — low-risk wins first, then ambitious changes
3. **Each experiment must have**: files, changes, paper reference, verification, risk
4. **Diff from ROADMAP** — explicitly show what changed vs the original plan
5. **Quantify everything** — "state MSE -10%" not "improve performance"
