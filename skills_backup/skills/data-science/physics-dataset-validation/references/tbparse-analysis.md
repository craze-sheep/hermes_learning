# Reading TensorBoard Events with tbparse

## Install

```bash
pip install tbparse
```

## Usage

```python
from tbparse import SummaryReader

reader = SummaryReader("./path/to/tensorboard_dir")
df = reader.scalars

# Available columns: step, tag, value
tags = sorted(df['tag'].unique())

# Filter by tag
total_loss = df[df['tag'] == '训练/01 总损失'].sort_values('step')

# Per-epoch analysis
epoch_ends = [1594, 3188, 4782, 6376, 7970]
for i, ep_end in enumerate(epoch_ends):
    mask = (steps > prev_end) & (steps <= ep_end)
    ep_vals = vals[mask]
    print(f"Epoch {i+1}: mean={ep_vals.mean():.4f} std={ep_vals.std():.4f}")
```

## Oscillation analysis

```python
# Coefficient of variation (CV = std/mean) — higher = more unstable
cv = std / mean

# Spike detection
spike_mask = ep_vals > mean + 3 * std
n_spikes = spike_mask.sum()
```

## Pitfalls

- `tbparse` reads `.tfevents` files directly — no TensorBoard server needed
- Tags are strings like '训练/01 总损失' — Chinese names common in non-English projects
- Epoch boundaries must be known from the training log (step numbers)
- Each epoch has a duplicate step at boundary (last step of epoch N = first step of epoch N+1)
