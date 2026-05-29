# Blender --python argv Fix

When running `blender --background --python script.py -- --arg1 val`, sys.argv becomes:
```python
['blender', '--background', '--python', 'script.py', '--', '--arg1', 'val']
```

This breaks argparse. Fix with a module imported before argparse:

## blender_argv_fix.py

```python
"""Fix sys.argv when running under Blender's --python mode.
Import this BEFORE argparse.parse_args().
"""
import sys

def fix_argv_for_blender():
    """Strip Blender's CLI args, keeping only args after '--'."""
    if '--' in sys.argv:
        idx = sys.argv.index('--')
        sys.argv = [sys.argv[0]] + sys.argv[idx + 1:]

# Auto-fix on import
fix_argv_for_blender()
```

## Integration

In each generation script, after sys.path setup:
```python
SCRIPT_DIR = str(Path(__file__).resolve().parent)
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)
import blender_argv_fix  # must come before argparse
```
