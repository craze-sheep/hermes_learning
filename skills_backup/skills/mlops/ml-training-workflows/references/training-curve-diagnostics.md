# Training Curve Diagnostics from TensorBoard

## When to Use

After a training run completes (or is still running), analyze the TensorBoard event files to:
- Detect overfitting (val loss rising while train loss falling)
- Find training instabilities (spikes, plateaus, NaN/Inf)
- Assess per-loss-component convergence
- Decide whether to continue, early-stop, or adjust hyperparameters

## Prerequisites

```bash
pip install tbparse matplotlib
```

## Step 1: Extract All Scalars from TensorBoard Events

```python
from tbparse import SummaryReader

reader = SummaryReader("./path/to/tb_logdir")
df = reader.scalars  # columns: step, tag, value

# List all tracked metrics
print(sorted(df['tag'].unique()))
```

**Pitfall:** `tbparse` requires `tensorboard` as a dependency. Install both if missing.
The event file is typically `events.out.tfevents.*` inside the log directory.

## Step 2: Generate Train vs Val Comparison Plots

```python
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

train_tags = [t for t in sorted(df['tag'].unique()) if 'train' in t.lower()]
val_tags   = [t for t in sorted(df['tag'].unique()) if 'val' in t.lower()]

fig, axes = plt.subplots(3, 3, figsize=(20, 15))  # adjust grid to match N metrics
epoch_ends = [...]  # from log: last step of each epoch

for idx, ttag in enumerate(train_tags):
    ax = axes[idx // 3][idx % 3]
    tdf = df[df['tag'] == ttag].sort_values('step')
    vals = tdf['value'].values

    # Raw (faded) + smoothed
    ax.plot(tdf['step'].values, vals, alpha=0.3, color='blue', linewidth=0.5)
    if len(vals) > 20:
        smoothed = np.convolve(vals, np.ones(20)/20, mode='valid')
        ax.plot(tdf['step'].values[19:], smoothed, color='blue', linewidth=2, label='Train')

    # Val (markers)
    vtag = corresponding_val_tag(ttag)
    vdf = df[df['tag'] == vtag].sort_values('step')
    if len(vdf) > 0:
        ax.plot(vdf['step'].values, vdf['value'].values, 'ro-', ms=8, lw=2, label='Val')

    for ep in epoch_ends:
        ax.axvline(x=ep, color='gray', ls='--', alpha=0.3)
    ax.set_title(ttag); ax.legend(); ax.grid(alpha=0.3)

plt.tight_layout()
plt.savefig('training_curves.png', dpi=150, bbox_inches='tight')
```

**Pitfall — Chinese font glyphs:** If matplotlib can't render CJK characters (common on
minimal Linux/WSL installs), switch to English labels or install `fonts-wqy-microhei`.
The symptom is `UserWarning: Glyph XXXX missing from font(s) DejaVu Sans` and
blank boxes in the saved PNG. Always prefer English axis labels in diagnostic plots
since font availability varies across systems.

## Step 3: Automated Diagnostics

Run this per-metric to generate a structured health report:

```python
for ttag in train_tags:
    tdf = df[df['tag'] == ttag].sort_values('step')
    vals = tdf['value'].values

    vtag = corresponding_val_tag(ttag)
    vdf = df[df['tag'] == vtag].sort_values('step')

    # --- Overfitting check ---
    if len(vdf) >= 2:
        vvals = vdf['value'].values
        if vvals[-1] > vvals[-2]:
            print(f"WARNING: Val loss INCREASING ({vvals[-2]:.6f} -> {vvals[-1]:.6f})")

    # --- Spike detection ---
    diffs = np.diff(vals)
    max_spike_idx = np.argmax(np.abs(diffs))
    if np.abs(diffs[max_spike_idx]) > 3 * np.std(diffs):
        step = tdf['step'].values[max_spike_idx]
        print(f"ANOMALY: Large spike at step ~{step}")

    # --- Plateau detection (last 30% of training) ---
    tail = vals[int(len(vals)*0.7):]
    if len(tail) > 5 and (tail.max() - tail.min()) < 0.01 * np.abs(vals.mean()):
        print("PLATEAU: Loss flat in last 30% of training")

    # --- NaN/Inf check ---
    if np.any(~np.isfinite(vals)):
        print("CRITICAL: NaN or Inf detected in training loss")
```

## Diagnostic Patterns to Report

| Signal | What It Means | Action |
|--------|---------------|--------|
| Val ↑, Train ↓ | Overfitting | Reduce epochs, add regularization, increase data |
| Val flat, Train ↓ | Memorizing noise | Same as above, but milder |
| Both flat | Plateau / dead capacity | Increase LR, add capacity, check data |
| Spikes in train | Bad batches, exploding grad | Check data for outliers, clip grad, reduce LR |
| Val ↑ late only | Mild overfitting | Early stopping is sufficient |
| One loss term >> others | Loss weight imbalance | Rebalance weights (see loss-calibration section) |
| Loss = 0.000 | Disabled / broken | Check loss weight, data pipeline, gradient flow |
| High CV (>1.0) | Oscillating / unstable | See oscillation analysis below |

## Oscillation Analysis (CV = std/mean)

When a loss curve looks "noisy" or "jagged", quantify it with the **Coefficient of Variation**:

```python
per-epoch:
    cv = std(values) / abs(mean(values))
```

**Interpretation:**
- CV < 0.3: stable, smooth convergence
- CV 0.3–1.0: moderate noise, usually fine
- CV > 1.0: unstable — standard deviation exceeds the mean
- CV > 2.0: severe instability — investigate immediately

**Per-epoch breakdown** reveals trends:
```python
for each epoch:
    mean, std, median, cv, spike_fraction (>mean+3σ)
```

If CV or spike% increases across epochs, the problem is getting worse — the model
is struggling with certain samples more as it trains.

**Cross-metric comparison** (sort by CV descending):
```
09 Energy Conserv.    CV = 1.87  <-- UNSTABLE
07 Collision Effect   CV = 1.63
06 Collision Class    CV = 1.32
05 Physics State      CV = 0.58
02 Image Recon        CV = 0.31
08 Seg Mask           CV = 0.20
```
The highest-CV metric is the bottleneck — focus diagnostics there.

### Physics-loss oscillation patterns

Physics-informed losses (energy conservation, momentum, force) are especially prone
to oscillation because they involve **squared terms** (KE = 0.5*m*v²) that amplify
velocity/force errors. A small prediction error in velocity → squared → large energy
spike.

**Root cause:** certain batches have harder physics (high velocity, collisions,
multi-body interactions). The model learns easy samples well (median drops) but
struggles with hard ones (spikes grow).

**Mitigations:**
1. Replace L1 with Huber loss on the physics term — less sensitive to outliers
2. Decay the physics loss weight over epochs — strong constraint early, relax later
3. Gradient clipping on the physics loss specifically
4. Verify denormalization scales match (see normalization audit below)

## Per-Epoch Spike Trend Analysis

When oscillation is suspected, track whether it's getting worse across epochs:

```python
epoch_ends = [1594, 3188, 4782, 6376, 7970]  # from val tag steps
prev_end = 0
for i, ep_end in enumerate(epoch_ends):
    mask = (steps > prev_end) & (steps <= ep_end)
    ep_vals = vals[mask]
    mean, std, median = np.mean(ep_vals), np.std(ep_vals), np.median(ep_vals)
    cv = std / abs(mean) if abs(mean) > 1e-10 else float('inf')
    spike_frac = np.mean(ep_vals > mean + 3 * std) * 100
    high_frac = np.mean(ep_vals > 0.05) * 100   # domain-specific threshold
    very_high_frac = np.mean(ep_vals > 0.1) * 100
    print(f"  Epoch {i+1}: mean={mean:.4f} CV={cv:.2f} "
          f">0.05={high_frac:.1f}% >0.1={very_high_frac:.1f}%")
    prev_end = ep_end
```

If spike% or high-value% increases across epochs, the model is struggling more
with hard samples as training progresses — a different failure mode from simple
overfitting (where val loss rises but train loss is smooth).

**Cross-metric CV comparison** (sort by CV descending) instantly reveals which
loss is the bottleneck:
```
09 Energy Conserv.    CV = 1.87  <-- UNSTABLE
07 Collision Effect   CV = 1.63
06 Collision Class    CV = 1.32
05 Physics State      CV = 0.58
02 Image Recon        CV = 0.31
08 Seg Mask           CV = 0.20
```

## Quick Stat Summary Template

Print this at the end for a one-screen overview:

```
Metric              | Train Start | Train End | Val Start | Val End | Trend
--------------------|-------------|-----------|-----------|---------|-------
01 Total Loss       |   1.2776    |  -9.9459  |  -3.5272  | -10.216 | OK ↓
02 RGB Recon        |   0.6346    |   0.0065  |   0.0069  |  0.0043 | OK ↓
08 Seg Mask         |   1.5524    |   0.0438  |   0.0470  |  0.0241 | ⚠ slight ↑
09 Energy Conserv   |   1.6274    |   0.0303  |   0.0023  |  0.0059 | ⚠ overfit
```

## Physics Loss vel² Amplification Pattern

Physics-informed losses involving kinetic energy (KE = 0.5*m*v²) or similar squared
quantities are especially prone to oscillation. The squaring operation amplifies small
prediction errors:

```
velocity error: 0.1 m/s → KE error amplified by v² term
velocity error: 1.0 m/s → KE error amplified 100x more
```

**Real-world example (slot-datamaking, epoch 5):**
- Energy conservation CV = 1.87 (highest of all 9 losses)
- Median energy loss = 0.015 (good — model learns easy samples)
- But max spike = 0.585 (39x the median — hard samples explode)
- Spike trend worsened: Epoch 2 max=0.092, Epoch 5 max=0.585

**Diagnosis script:**
```python
# Check if vel_scale matches data normalization
vel_scale = config.vel_scale  # e.g., 10.0
actual_vel_std = batch['dyn_state'][..., 7:10].std().item()
print(f"vel_scale={vel_scale}, actual_std={actual_vel_std}")
# If these differ >2x, the denormalized physics quantities are wrong
```

**Mitigations (in order of preference):**
1. Huber loss instead of L1 on physics terms
2. Gradient clipping specifically on the physics loss backward pass
3. Decay physics loss weight over epochs
4. Verify `vel_scale` matches `state_std[7:10]` in the dataset

## Example: Full Analysis Script

See `scripts/analyze_tb_curves.py` in this skill for a complete runnable version
that reads a TB logdir and outputs both the plot PNG and the diagnostic report.

## Normalization Audit Checklist

When training curves show instability, check whether normalization is the cause:

**What to verify:**
1. **Hardcoded vs computed scales** — Many projects hardcode normalization std
   (e.g., `state_std[7:10] = 10.0`). If the actual data distribution differs,
   the model sees mis-scaled inputs. Fix: compute mean/std from a data sample.

2. **Unnormalized inputs** — Object attributes (mass, size, friction) are often
   left raw. Mass can span orders of magnitude (0 for static, 1–10 for objects).
   MLPs struggle with mixed-scale inputs. Fix: standardize or log-transform.

3. **Denormalization in loss functions** — Physics losses (energy, momentum)
   often need physical units. The pattern:
   ```python
   vel = state_pred[..., 7:10] * vel_scale  # denormalize
   kinetic_energy = 0.5 * mass * vel**2
   ```
   If `vel_scale` doesn't match the dataset's normalization std, the physics
   quantities are wrong and the loss is meaningless.

4. **Force matrix normalization** — Force magnitudes can vary wildly (0 for
   non-contacting pairs, 100+ N for collisions). Verify the std covers the
   actual range, or the collision signal gets crushed.

**Quick audit script:**
```python
# Sample 100 batches, compute actual stats
all_states = []
for batch in dataloader:
    all_states.append(batch['dyn_state'])
all_states = torch.cat(all_states)  # [N, T, obj, 16]
print("Position  mean/std:", all_states[..., 0:3].mean(), all_states[..., 0:3].std())
print("Velocity  mean/std:", all_states[..., 7:10].mean(), all_states[..., 7:10].std())
print("Force     mean/std:", all_states[..., 13:16].mean(), all_states[..., 13:16].std())
# Compare with hardcoded values — if they differ >2x, update
```
