# ML Training Execution Patterns (Developer Role)

## FP16/AMP Overflow Fixes

PyTorch AMP (Automatic Mixed Precision) uses FP16 for forward pass. FP16 range: ±65504, min positive ~6e-8.

### Known overflow patterns

| Code | Problem | Fix |
|------|---------|-----|
| `masked_fill(mask, -1e9)` | -1e9 overflows half | Use `-1e4` |
| `masked_fill(mask, float('-inf'))` | May overflow in some ops | Use `-65504` or `-1e4` |
| Large logits in attention | Softmax input too large | Clamp or use `torch.clamp` |

Detection: `RuntimeError: value cannot be converted to type at::Half without overflow`

### Fix recipe
```bash
# Find all -1e9 occurrences in a directory
grep -rn '\-1e9' experiment_dir/model/*.py

# Apply fix to copy only
sed -i 's/-1e9)/-1e4)  # FP16-safe/' experiment_dir/model/interaction.py
```

## Path Adjustment for Copied Code

When ML training scripts use `__file__`-relative paths to find data/config:
```python
_this_dir = os.path.dirname(os.path.abspath(__file__))     # model/ai_model
_model_dir = os.path.dirname(_this_dir)                      # model
_project_root = os.path.dirname(_model_dir)                  # project root
database_root = os.path.join(_project_root, 'database')
```

If copied to `experiments/baseline/model/train.py`:
- `_this_dir` = `experiments/baseline/model/` (3 levels from project root)
- Original `_project_root` = `experiments/` (2 levels up, WRONG)
- Need: `_project_root = os.path.dirname(os.path.dirname(os.path.dirname(_model_dir)))` (4 levels up total)

### Counting levels
```
experiments/baseline/model/train.py  → _this_dir (level 0)
experiments/baseline/                → _model_dir (level 1)
experiments/                         → level 2
model/                               → level 3
slot-datamaking/                     → _project_root (level 4) ← database/ lives here
```

### Verification
```python
import os
f = os.path.abspath('experiments/baseline/model/train.py')
this_dir = os.path.dirname(f)
model_dir = os.path.dirname(this_dir)
project_root = os.path.dirname(os.path.dirname(os.path.dirname(model_dir)))
assert os.path.exists(os.path.join(project_root, 'database'))
```

## Conda + PYTHONPATH Execution

```bash
# Standard pattern for running from experiments/ directory
cd /path/to/experiments
PYTHONPATH="$(pwd)/$exp/model:$PYTHONPATH" conda run -n model python $exp/model/train.py --mode smoke

# Why PYTHONPATH needed: train.py does `from config import ...` which needs the model/ dir on sys.path
# The train.py also inserts paths via sys.path, but PYTHONPATH ensures it works from any CWD
```

**Gotcha:** `conda run` buffers stdout. Background processes show no output until completion. Use `notify_on_complete=true` and `process(action='wait')`.

## Smoke Test Pattern

Minimal config to verify training runs without errors:
```bash
# --mode smoke typically sets: small dims, 3 steps, few samples
python train.py --mode smoke  # ~1-3 seconds per experiment
```

Run all experiments sequentially:
```bash
for exp in exp001 exp002 exp003; do
  echo "=== $exp ==="
  PYTHONPATH="$(pwd)/$exp/model:$PYTHONPATH" conda run -n model python $exp/model/train.py --mode smoke 2>&1
  echo "EXIT_CODE=$?"
  echo "---"
done
```

Record: error (bool), loss_start, loss_end, decreasing (bool), val_loss.

## Metrics JSON Template

```json
{
  "baseline": {
    "description": "...",
    "command": "...",
    "source": "experiments/baseline/model/ (copy of ai_model/, source untouched)",
    "environment": {"device": "cuda (...)", "torch": "2.5.1+cu121", "amp": true},
    "model": {"parameters": 932474, "batch_size": 4, ...},
    "data": {"train_samples": 22315, "val_samples": 4783},
    "bugfixes": ["interaction.py L162: -1e9 → -1e4 (FP16 fix)"],
    "metrics": {
      "epoch_1": {"train": {...}, "val": {...}},
      "best_val_loss": 0.5451,
      "best_epoch": 2
    },
    "checkpoints": {"best": "experiments/baseline/model/checkpoints/best.pt"}
  }
}
```

## Shell Debugging Pitfall

```bash
# WRONG: second diff never runs if first returns exit code 1
diff source/file copy/file && diff source/file2 copy/file2

# RIGHT: both run regardless
diff source/file copy/file; diff source/file2 copy/file2
# or
diff source/file copy/file 2>&1; diff source/file2 copy/file2 2>&1
```

`diff` returns exit code 1 when files differ (not an error, but `&&` treats it as failure).
