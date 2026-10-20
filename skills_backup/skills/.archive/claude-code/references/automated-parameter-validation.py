# Automated Parameter Validation Pattern
#
# Reusable pattern for checking scripts against spec docs.
# Use this when you need to verify N scripts match N config docs
# without reading each file manually.
#
# Adapt the `expected_*` dicts to your project.

```python
#!/usr/bin/env python3
"""Automated parameter validation: scripts vs config docs."""
import re, os

base = "/path/to/project"

# 1. LEVEL COUNT CHECK
doc_names = {1: 'S1_name', 2: 'S2_name', ...}
for i in range(1, N+1):
    script_text = open(f"{base}/generate_s{i}_dataset.py").read()
    doc_text = open(f"{base}/docs/{doc_names[i]}/参数配置.md").read()
    
    script_levels = sorted(set(int(x) for x in re.findall(r'(?:if|elif) level_id == (\d+)', script_text)))
    doc_levels = sorted(set(int(x[1]) for x in re.findall(r'## \[(简单|复杂)\] Level (\d+)', doc_text)))
    
    status = "✓" if script_levels == doc_levels else "✗"
    print(f"S{i}: doc={len(doc_levels)} script={len(script_levels)} {status}")

# 2. GLOBAL RENDERING PARAMS
for i in range(1, N+1):
    script = open(f"{base}/generate_s{i}_dataset.py").read()
    fps = re.search(r'^FPS\s*=\s*(\d+)', script, re.M)
    frames = re.search(r'^NUM_FRAMES\s*=\s*(\d+)', script, re.M)
    # ... check each param

# 3. VIEWS DICT STRUCTURE (catch nesting bugs)
for i in range(1, N+1):
    script = open(f"{base}/generate_s{i}_dataset.py").read()
    m = re.search(r'VIEWS\s*=\s*\{(.*?)\n\}', script, re.DOTALL)
    if m:
        top_keys = re.findall(r'^    "(\w+)"', m.group(1), re.M)
        # Verify expected keys

# 4. GROUND SPEC EXTRACTION
for i in range(1, N+1):
    r = terminal(f'grep -A 15 "def ground_spec" "{base}/generate_s{i}_dataset.py"')
    # Parse size, friction, rolling, spinning from output

# 5. LEVEL_TARGETS DICT COMPARISON
for i in range(1, N+1):
    script = open(f"{base}/generate_s{i}_dataset.py").read()
    m = re.search(r'LEVEL_TARGETS\s*=\s*\{([^}]+)\}', script)
    pairs = re.findall(r'(\d+)\s*:\s*(\d+)', m.group(1))
    targets = {int(k): int(v) for k, v in pairs}
    # Compare with expected
```

## When to Use
- After batch code generation, before Docker test runs
- When user says "check if scripts match docs"
- As a pre-commit validation step
- Cross-validate results from Claude Code / Codex reviews

## Key Advantage
This runs in seconds via `execute_code`, costs 0 API tokens, and catches
gross mismatches (wrong level count, wrong resolution, missing views) that
even expensive AI reviews might miss due to context limits.
