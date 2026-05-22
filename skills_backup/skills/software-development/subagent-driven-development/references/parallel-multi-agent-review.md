# Parallel Multi-Agent Review

When you need high-confidence review of code, design docs, or implementations, run multiple AI agents independently on the same task and compare their findings.

## When to Use

- Verifying code against design specifications (code-vs-doc audit)
- High-stakes review where missing an issue is costly
- User explicitly asks for multiple agents to review
- Cross-validation of complex logic or parameter matching

## The Pattern

### 1. Prepare the Review Task

Write a self-contained review prompt that includes:
- Exact file paths for all artifacts to review
- Specific checklist of what to verify (don't leave it vague)
- Output format specification (PASS/FAIL per item, with details)

### 2. Launch Agents in Parallel

Run all agents as background processes simultaneously:

```
# Claude Code (print mode, background)
terminal(command="claude -p '<review prompt>' --max-turns N --allowedTools 'Read,Bash' --output-format json > /tmp/claude_review.json", background=true, notify_on_complete=true)

# Codex (exec mode, background)
terminal(command="codex exec --full-auto '<review prompt>'", background=true, pty=true, notify_on_complete=true)

# Do your own review in parallel (don't wait for them)
```

### 3. Do Your Own Review Simultaneously

Don't just wait for the other agents — do your own thorough review in parallel. Use `execute_code` or `terminal` to read files and extract parameters systematically.

**Pitfall: Shallow self-review.** If you only check high-level params (counts, global settings) while the other agents check per-item details, your results will look wrong by comparison. Be equally granular.

### 4. Compare Results

After all agents finish, produce a cross-comparison report:

```
============================================================
         三方交叉对比：共识 vs 分歧
============================================================

【三方共识的问题】(高置信度 — fix these first)
...

【两方发现的问题】(中置信度 — verify these)
...

【仅一方发现的问题】(需人工复核)
...
```

**Consensus = high confidence.** Issues found by all agents are almost certainly real.
**Single-agent findings = verify.** May be false positive or genuine deep find.

### 5. Report Without Modifying (If Requested)

When user says "review only" or "don't modify":
- All agents must be explicitly told "只检查不修改" in the prompt
- Report findings only
- Let the user decide who fixes what

## Checklist for Code-vs-Document Verification

When comparing code against design docs, check ALL of these:

1. **Global parameters**: resolution, fps, frame count, duration, gravity, units
2. **Camera/view configurations**: which views defined, which are defaults
3. **Object counts per scenario**: number of dynamic/static objects
4. **Shape types**: sphere, cube, cylinder — which are actually used vs documented
5. **Size ranges**: radius, dimensions — exact values, not just "approximately"
6. **Mass ranges**: exact values per level/scenario
7. **Position ranges**: initial positions, including derived positions (e.g., surface + offset)
8. **Velocity ranges**: linear and angular, per level
9. **Material properties**: friction (lateral, rolling, spinning), restitution — per object per level
10. **Color/visual variables**: which colors are used, are they all covered or hardcoded
11. **Level/scenario counts**: doc N levels vs code M levels
12. **Level content mapping**: does code Level N match doc Level N (not just count)
13. **Constraint/filter logic**: are documented filters/validations implemented
14. **Label/tag generation**: are documented output labels actually produced
15. **Data volume**: total samples matching doc plan
16. **Dictionary/structure syntax**: especially when code was copy-pasted between files

## Pitfalls

- **Don't stop at level counts.** "Doc has 9 levels, code has 9 levels ✓" is insufficient. Check that Level N in code matches Level N in doc.
- **Don't trust parameter names alone.** "friction=0.2" might be on the wrong object (ramp vs ball).
- **Check variable coverage.** If doc says color=[red,blue,yellow,green] but code only uses "red", that's a bug even though no error is thrown.
- **Watch for copy-paste artifacts.** When scripts are generated from templates, dictionary structures may have nesting bugs from the template.
- **Your own review is the baseline, not the gold standard.** The other agents may find things you missed. Don't dismiss their findings.
