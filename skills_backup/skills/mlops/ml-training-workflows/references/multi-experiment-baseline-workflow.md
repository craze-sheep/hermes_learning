# Multi-Experiment Baseline Workflow

Pattern for running a baseline + N experiments on the same model architecture.

## Directory Layout

```
model/
├── ai_model/              # SOURCE (never modified)
│   ├── train.py
│   ├── config.py
│   ├── model.py
│   ├── encoder.py
│   ├── decoder.py
│   ├── loss.py
│   ├── temporal.py
│   ├── interaction.py
│   ├── dataset.py
│   ├── data_adapter.py
│   └── __init__.py
├── experiments/
│   ├── baseline/
│   │   └── model/         # Copy of ai_model/ with bugfixes only
│   │       └── checkpoints/
│   ├── exp001_lpips_loss/
│   │   └── model/         # Copy with LPIPS loss patches
│   ├── exp002_.../
│   │   └── model/
│   └── baseline_metrics.json
└── create_experiments.py   # Automation script
```

## create_experiments.py Pattern

```python
EXPERIMENTS = ['exp001_lpips_loss', 'exp002_energy_conservation', ...]

def copy_base(exp_name):
    dst = os.path.join(EXPERIMENTS_DIR, exp_name, 'model')
    if os.path.exists(dst):
        shutil.rmtree(dst)
    shutil.copytree(AI_MODEL_DIR, dst)

def patch_file(path, replacements):
    """Apply list of (old, new) string replacements."""
    with open(path) as f:
        code = f.read()
    for old, new in replacements:
        if old in code:
            code = code.replace(old, new, 1)
        else:
            print(f"  WARNING: pattern not found in {os.path.basename(path)}: {old[:60]}...")
    with open(path, 'w') as f:
        f.write(code)
```

## Pitfall: patch_file Pattern Matching Failures

String-based patching is fragile. Common failure modes:

1. **Whitespace mismatch**: Source uses tabs, pattern uses spaces (or vice versa)
2. **Truncation in pattern**: Pattern string is too long, minor difference breaks match
3. **Escape characters**: `'` vs `\'` in the replacement string vs file content
4. **Multi-line patterns**: Leading/trailing whitespace on each line must match exactly

**Mitigation:** Always check the WARNING output. After running create_experiments.py:
```bash
python create_experiments.py 2>&1 | grep WARNING
```

For each WARNING, verify whether the patch was critical:
```bash
grep -c 'EXP0' experiments/exp001/model/loss.py  # markers present?
```

## Baseline Metrics JSON Schema

```json
{
  "baseline": {
    "description": "...",
    "command": "conda run -n model python ...",
    "source": "experiments/baseline/model/ (copy of ai_model/)",
    "environment": { "device": "...", "torch": "...", "cuda": true, "amp": true },
    "model": { "parameters": 0, "batch_size": 0, ... },
    "data": { "train_samples": 0, "val_samples": 0 },
    "bugfixes": ["list of fixes applied to copy only"],
    "metrics": {
      "epoch_1": {
        "train": { "total_loss": 0, "rgb_loss": 0, "state_loss": 0, "collision_loss": 0, "mask_loss": 0 },
        "val": { ... }
      },
      "best_val_loss": 0,
      "best_epoch": 1
    },
    "checkpoints": { "best": "path/to/best.pt" }
  }
}
```

## Experiment Comparison Workflow

1. Run baseline → record in baseline_metrics.json
2. **Smoke test all experiments first** (3 steps each) — see `references/two-phase-experiment-strategy.md`
3. Select 3-5 candidates that pass smoke test + show loss descent
4. Full training only on candidates with same hyperparameters (--mode small --epochs N --max-steps M)
5. Rank by improvement percentage vs baseline
6. Select top-K for longer training run
