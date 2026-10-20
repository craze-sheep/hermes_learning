# Training Curve Analysis with tbparse

## Quick Analysis Pattern

When TensorBoard events file exists but tensorboard CLI isn't installed:
```bash
pip install tbparse
```

```python
from tbparse import SummaryReader
import numpy as np

reader = SummaryReader("./model/runs/<run_dir>")
df = reader.scalars
print(sorted(df["tag"].unique()))  # list all logged metrics

# Per-metric summary
for tag in df["tag"].unique():
    vals = df[df["tag"] == tag]["value"].values
    print(f"{tag}: start={vals[0]:.4f}, end={vals[-1]:.4f}, min={vals.min():.4f}, max={vals.max():.4f}")

# Oscillation detection via coefficient of variation
for tag in train_tags:
    vals = df[df["tag"] == tag]["value"].values
    cv = np.std(vals) / abs(np.mean(vals)) if abs(np.mean(vals)) > 1e-10 else float('inf')
    print(f"{tag}: CV={cv:.2f}")
# CV > 1.0 means std > mean — highly unstable
```

## Energy Conservation Loss Oscillation (2026-06-01)

**Symptom:** Energy loss CV=1.87 (highest of all 9 losses), spikes worsening per epoch:
- Epoch 2: max spike 0.092, >0.05 = 9.8%, >0.1 = 0.0%
- Epoch 5: max spike 0.585, >0.05 = 18.3%, >0.1 = 17.1%

**Root cause:** `KE = 0.5 * m * v²` — squaring amplifies velocity prediction errors. Certain batches with high velocities or collisions produce outlier energy diffs.

**Mitigation options:**
1. Huber loss instead of L1 on energy_diff
2. Energy weight decay over epochs
3. Separate gradient clipping for physics losses
4. Verify vel_scale matches data normalization std
