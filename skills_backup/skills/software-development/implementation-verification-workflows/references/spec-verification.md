---
name: spec-verification
description: "Verify code implementation matches design specification documents. Automated parameter checking, multi-agent review coordination, and structured comparison reporting."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [verification, code-review, specification, compliance, multi-agent, automation]
related_skills: ["requesting-code-review", "systematic-debugging", "claude-code", "codex", "multi-agent-review"]
---

# Spec Verification — Code vs Design Document

Systematically verify that code implementations match their design specification documents. Distinct from code review (which checks code quality) — this checks **correctness against a contract**.

## When to Use

- After code generation from design docs (S1-S8 dataset scripts, API implementations, config generators)
- When user asks "check if code matches the spec/design/文档"
- After multi-agent code generation (Codex/Claude Code wrote it, now verify)
- Before accepting auto-generated or auto-fixed code
- Periodic compliance audits of implementation vs spec

**NOT for:** general code review, security audits, or style checking.

## Reusable Scripts

See `references/automated-check-scripts.py` for ready-to-use verification functions:
- `count_levels_in_doc()` / `count_levels_in_script()` — level count verification
- `verify_views_keys()` — catch VIEWS dict nesting bugs
- `verify_ground_spec()` — ground object parameters
- `verify_level_targets()` — sample count targets
- `verify_global_params()` — FPS, resolution, duration, gravity
- `verify_default_views()` — camera view defaults
- `verify_label_integration()` — physics label utils integration

## Core Workflow

### 1. Build the Verification Matrix

Create a structured checklist from the spec doc. Each parameter gets a row:

```
| Parameter | Doc Value | Code Value | Status |
|-----------|-----------|------------|--------|
| FPS       | 12        | 12         | ✓      |
| Resolution| 128x128   | 128        | ✓      |
| L1 radius | [0.18,0.22,0.28] | [0.18,0.22,0.28] | ✓ |
| L5 mass   | [0.3,0.5,1.0,2.0,4.0] | [0.3,0.5,1.0,2.0] | ✗ |
```

### 2. Automate Repeatable Checks

Write a Python script for checks that can be automated. Manual spot-checks for complex logic.

```python
# Example: level count verification
import re, os

for scene in scenes:
    # Count levels in doc
    doc_text = open(doc_path).read()
    doc_levels = sorted(set(int(x[1]) for x in re.findall(r'## \[.*?\] Level (\d+)', doc_text)))
    
    # Count levels in script
    script_text = open(script_path).read()
    script_levels = sorted(set(int(x) for x in re.findall(r'(?:if|elif) level_id == (\d+)', script_text)))
    
    assert doc_levels == script_levels, f"Mismatch: doc={doc_levels}, script={script_levels}"
```

**Automate these (high signal, easy to verify):**
- Level/item counts
- Global parameters (FPS, resolution, duration, gravity)
- Ground/base object sizes and friction values
- Camera view configurations
- Data volume targets (LEVEL_TARGETS, sample counts)
- Import/integration checks (e.g., label utils imported)
- Dictionary syntax (nested structure bugs)

**Spot-check these (need judgment):**
- Specific parameter value ranges per level
- Quaternion formulas
- Constraint/filter logic
- Edge case handling
- Color/material coverage strategies

### 3. Multi-Agent Verification (Optional)

For large codebases (>5 files), use multiple agents in parallel:

```
Agent 1 (Hermes): Automated checks via Python scripts (fast, shallow)
Agent 2 (Codex): Deep semantic review (slowest, deepest)
Agent 3 (Claude Code): Parameter-by-parameter comparison (medium, clean output)
Agent 4 (OpenCode): Supplementary validation (catches details others miss)
```

**Model strengths:** Codex(GPT 5.5) catches sampling strategy and pairing errors.
Claude Code(DeepSeek v4 Pro) excels at value-by-value comparison. OpenCode(mimo-v2.5-pro)
found missing parameter values that both Codex and Claude Code missed.
Hermes(mimo-v2.5-pro) does fast automated batch checks.

**PITFALL:** Do NOT give Claude Code all files at once. Split into batches of 2-3 scripts.
Context window overflow happens at ~4 scripts + docs. See claude-code skill for details.

**Coordination pattern:**
1. All agents run independently (background terminal or delegate_task)
2. Collect results when all finish
3. Cross-compare findings: consensus = high confidence, single-agent = needs verification
4. Present unified report with confidence levels

### 4. Structured Report

Always present results in a table:

```
| Scene | Status | Issues Found |
|-------|--------|-------------|
| S1    | PASS   | None        |
| S2    | FAIL   | L5 mass: code=[0.3-2.0], doc=[0.3-4.0] |
```

Group by severity:
- **Critical:** Missing levels/items, wrong formulas, crashes
- **Medium:** Wrong parameter ranges, incomplete coverage
- **Minor:** Color variations, label generation missing

## Pitfalls

### 1. "Pass" on Global ≠ "Pass" Overall
Checking only global params (FPS, resolution, gravity) misses per-level parameter errors.
Always drill into individual level/item definitions.

### 2. Post-Processing Colors/Attributes
Colors applied in a post-processing loop (e.g., `replace(obj, color_name=...)`) are valid
even if the initial construction uses a default. Check the FULL code path, not just the
constructor call.

### 3. VIEWS/Config Dict Syntax
Copy-paste errors create nested dicts that parse without error but produce wrong keys:
```python
# BUG: "back" nested inside "front"
VIEWS = {
    "front": {
        "type": "Perspective",
        ...,
    "back": {  # <-- missing closing brace for "front"!
```
Verify top-level keys explicitly.

### 4. Regex Level Counting
`grep -c "elif level_id =="` undercounts if the file uses different patterns.
Use Python `re.findall(r'(?:if|elif) level_id == (\d+)', text)` for reliability.

### 5. Doc Format Variation
Some docs use `## Level N`, others use `## [简单] Level N`. Adapt regex to actual format.
Always check the doc format first before writing extraction patterns.

### 6. Claude Code Context Overflow
When checking 4+ large scripts, Claude Code hits context limits (~20min, $9 wasted).
Split into batches: check S1-S4 first, then S5-S8. Or use Hermes automated scripts only.

### 6. "Check Only" Means CHECK ONLY
When user says "只检查不修改" or "不要改代码" — DO NOT propose fixes, DO NOT edit files.
Report findings only. Let the user decide what to fix.

### 7. Direct Python Faster Than Agent Delegation
For automated parameter checking (level counts, global params, VIEWS syntax),
`execute_code` with direct Python is faster and more reliable than delegating
to Claude Code or Codex. Use agents only for deep semantic review that requires
judgment (sampling strategies, physics correctness, constraint logic).

## Quick Reference

| Step | Action | Tool |
|------|--------|------|
| 1. Extract spec | Read doc, build parameter matrix | read_file, search_files |
| 2. Automate | Write check script for repeatable items | execute_code, write_file |
| 3. Spot-check | Manually verify complex logic | read_file, terminal |
| 4. Multi-agent | Optional: delegate to Codex/Claude Code | delegate_task, terminal |
| 5. Report | Structured table with severity | Direct output |
