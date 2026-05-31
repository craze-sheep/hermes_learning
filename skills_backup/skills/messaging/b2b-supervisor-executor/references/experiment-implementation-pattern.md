# Experiment Implementation Automation Pattern

## When to Use

When a B2B task requires implementing N experiments where each experiment:
1. Copies a base code directory
2. Applies specific modifications to 1-3 files
3. Creates standard new files (config_override.py, run.sh, README.md)

## Problem: Manual File Creation is O(N × Files)

Creating 10 experiments × 11 files = 110 file writes. Writing each file individually is extremely slow and error-prone.

## Solution: Python Automation Script

Write a single `create_experiments.py` script that:
1. Copies base directory to each experiment
2. Applies targeted string patches per experiment
3. Creates standard boilerplate files

```python
# Core pattern:
import shutil

def copy_base(exp_name):
    dst = os.path.join(EXPERIMENTS_DIR, exp_name, 'model')
    shutil.copytree(AI_MODEL_DIR, dst)

def patch_file(path, replacements):
    """Apply list of (old, new) string replacements."""
    with open(path) as f:
        code = f.read()
    for old, new in replacements:
        code = code.replace(old, new, 1)
    with open(path, 'w') as f:
        f.write(code)

# Per experiment: copy base, then patch specific files
for exp_name, apply_func in experiments:
    copy_base(exp_name)
    apply_func(exp_name)
```

## Key Design Decisions

1. **Patch, don't rewrite**: Use find-and-replace on copied files, not full file rewrites. This preserves all unchanged code.
2. **Each experiment is independent**: No cross-experiment dependencies.
3. **ai_model/ is never modified**: All changes go to experiment copies.
4. **Standard boilerplate**: Every experiment gets run.sh, config_override.py, README.md with consistent format.

## Pitfall: String Replacement Fragility

If the base code changes, string patches may break. Mitigate by:
- Including enough context in the old_string (3-5 lines)
- Testing the script after any base code update
- Using `if old in code:` guards with warnings

## Critical: Post-Run Verification

String replacements in `patch_file()` can silently fail — `str.replace()` returns the original string if the pattern isn't found, with no error. After running the script:

1. Search each modified file for expected markers (e.g., `grep "EXP003" encoder.py`)
2. Verify critical code was injected (class definitions, return tuples, feature computations)
3. If any patch missed, use the `patch` tool to manually apply the missing code

Known failure patterns:
- Multi-line strings with inconsistent indentation
- Whitespace differences (tabs vs spaces)
- Trailing whitespace or newline mismatches
- Code that was already modified by a previous patch in the same file
