---
name: dev-methodology
description: "Development methodology: TDD (red-green-refactor), spike experiments, dogfood QA, code review workflows."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Development, Methodology, TDD, Spike, Dogfood, QA, Testing, Code-Review]
---

# Development Methodology

Approaches for building software well: test-driven development, spike experiments, exploratory QA, and code review.

## 1. Test-Driven Development (TDD)

### The Cycle: RED → GREEN → REFACTOR

1. **RED:** Write a failing test that defines the desired behavior
2. **GREEN:** Write the minimum code to make the test pass
3. **REFACTOR:** Clean up the code while keeping tests green

### Rules
- **Write the test FIRST.** Never write implementation before a test defines the behavior.
- **One test at a time.** Don't write 5 tests and then implement. Write one, make it pass, repeat.
- **Smallest possible test.** Start with the simplest case, then add complexity.
- **Run the test suite after every change.** Green means go. Red means stop.
- **Refactor only on green.** Never refactor when tests are failing.

### When to Use TDD
- Bug fixes: write a test that reproduces the bug first
- New features: define behavior through tests before implementation
- Refactoring: tests protect existing behavior while you restructure

### Anti-Patterns
- Writing tests after the code (that's "testing", not TDD)
- Skipping the refactor step (accumulates technical debt)
- Writing too many tests at once (loses the tight feedback loop)
- Testing implementation details instead of behavior

## 2. Spike Experiments

When you need to validate an idea before committing to a full implementation:

### When to Spike
- Uncertain about feasibility ("can this library do X?")
- Exploring multiple approaches ("should we use A or B?")
- Estimating complexity ("how hard would this be?")
- Learning a new API or technology

### Spike Workflow
1. **Define the question** — what exactly needs to be validated?
2. **Time-box it** — set a hard limit (30 min, 1 hour, 1 day)
3. **Build the最小 viable experiment** — not production code, just enough to answer the question
4. **Document the answer** — write findings, not code
5. **Throw away the code** — spikes are disposable; the knowledge is what matters
6. **Decide** — proceed, pivot, or abandon based on findings

### Spike Output Template
```
## Spike: [Question]
**Time spent:** X minutes
**Question:** [What we needed to know]
**Answer:** [What we learned]
**Recommendation:** [Proceed / Pivot / Abandon]
**Next steps:** [If proceeding, what to build]
```

## 3. Dogfood (Exploratory QA)

Use your own product like a real user would, but with a detective's eye.

### When to Dogfood
- Before releases
- After major changes
- When onboarding new team members
- Periodically as quality maintenance

### Dogfood Workflow
1. **Start from a clean state** — fresh account, empty data, default settings
2. **Follow the happy path** — do what a new user would do
3. **Try the unhappy path** — wrong inputs, edge cases, back buttons, refresh mid-flow
4. **Document everything** — screenshots, console logs, unexpected behaviors
5. **File issues** — one issue per bug, with reproduction steps

### Issue Report Template
```
## Bug: [Short description]
**Severity:** Critical / High / Medium / Low
**Steps to reproduce:**
1. [Step 1]
2. [Step 2]
**Expected:** [What should happen]
**Actual:** [What actually happened]
**Evidence:** [Screenshot, console log, network tab]
**Environment:** [Browser, OS, device]
```

### What to Look For
- **Broken flows:** Can the user complete the primary task?
- **Error handling:** What happens when things go wrong?
- **Performance:** Does anything feel slow?
- **Accessibility:** Can you navigate with keyboard only?
- **Copy:** Are messages clear? Are there typos?
- **Edge cases:** Empty states, very long text, special characters

## 4. Code Review

### Pre-Commit Review Checklist
- [ ] Code does what it claims (correctness)
- [ ] No hardcoded secrets or credentials (security)
- [ ] Input validation on user-facing inputs (security)
- [ ] Clear naming, no unnecessary complexity (quality)
- [ ] New code paths tested (testing)
- [ ] No N+1 queries or unnecessary loops (performance)
- [ ] Public APIs documented (documentation)

### Review Output Format
```
## Code Review Summary
### Critical
- **file:line** — Issue description. Suggestion.

### Warnings
- **file:line** — Issue description.

### Suggestions
- **file:line** — Nice-to-have improvement.

### Looks Good
- What's working well.
```

## Choosing the Right Approach

| Situation | Approach |
|-----------|----------|
| Building a new feature | TDD (red-green-refactor) |
| Uncertain about feasibility | Spike experiment |
| Before a release | Dogfood QA |
| After completing a feature | Code review |
| Fixing a bug | TDD (write failing test first) |
| Exploring alternatives | Spike experiment |
| Onboarding to a new codebase | Dogfood + code review |
