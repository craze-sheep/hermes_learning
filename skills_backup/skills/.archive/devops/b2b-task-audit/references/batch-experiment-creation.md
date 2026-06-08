# Batch Experiment Directory Creation Pattern

## Problem
Need to create N experiment directories, each a copy of a base code directory with specific per-experiment modifications.

## Solution: Python automation script
Write a `create_experiments.py` that:
1. Copies base directory (e.g., `ai_model/`) to each experiment directory via `shutil.copytree`
2. Applies per-experiment modifications via `patch_file()` string replacements
3. Creates auxiliary files (config_override.py, run.sh, README.md)

## Key Implementation Details

### patch_file function
```python
def patch_file(path, replacements):
    """Apply a list of (old, new) replacements to a file."""
    with open(path, 'r', encoding='utf-8') as f:
        code = f.read()
    for old, new in replacements:
        if old in code:
            code = code.replace(old, new, 1)
        else:
            print(f"  WARNING: pattern not found in {os.path.basename(path)}: {old[:60]}...")
    with open(path, 'w', encoding='utf-8') as f:
        f.write(code)
```

### Pitfalls (learned the hard way)
1. **Multi-line string matching is fragile**. Whitespace, indentation, or line ending differences cause silent failures. Always verify patches applied by searching for the NEW content after patching.
2. **Always verify after patching**. Run `search_files` for the expected new code to confirm patches took effect.
3. **Silent failures are common**. The WARNING print helps but you must actually check the output.
4. **Write complete files when patches are complex**. For large insertions (new classes, 50+ lines), `write_file` the entire modified file is more reliable than `patch_file` with long old/new strings.

### Verification checklist
After running the creation script:
- [ ] All experiment directories exist
- [ ] Each directory has the expected number of .py files
- [ ] Each directory has auxiliary files (config_override, run.sh, README)
- [ ] Search for key modification markers in modified files (e.g., "EXP003", "EXP007")
- [ ] Run `py_compile` or syntax check on all .py files
