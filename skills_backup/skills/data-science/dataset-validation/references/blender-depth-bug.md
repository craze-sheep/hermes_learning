# Depth ~1e10 in Kubric: Expected Behavior (NOT a bug)

## Summary

Depth values of ~1e10 meters in Kubric-generated datasets are **expected sentinel values** for background/sky pixels. They are NOT caused by renderer reuse, Blender bugs, or rendering corruption.

## Evidence

Kubric source code (`kubric/renderer/blender_utils.py:324`):
```python
# range [0, 10000000000.0]  # the value 1e10 is used for background / infinity
```

The `z_to_depth` conversion applies per-pixel scaling:
```python
# cameras.py:167
depth_scaling = sqrt(1 + d² / f²)
depth = z * depth_scaling
```

This produces:
- Center pixels: ~1.00e10 (scaling ≈ 1.00)
- Corner pixels: ~1.19e10 (scaling ≈ 1.188)
- 1000+ unique background values between 1.0e10 and 1.19e10

## Background % by Camera Type

| Camera Type | Background % | Why |
|------------|-------------|-----|
| Perspective (front) | ~63% | FOV cone extends beyond scene geometry |
| Perspective (left) | ~42% | Different angle, different coverage |
| Orthographic (top) | 0% | All parallel rays hit the scene |

These percentages are normal for 128×128 resolution with small objects on a ground plane.

## How to Filter

```python
import numpy as np
depth = np.load(f"{id}.npz")["depth"]

# Foreground: actual scene content
fg_mask = depth < 1e9
foreground = depth[fg_mask]  # range: ~5-16m for typical scenes

# Background: sentinel values (safe to set to 0 or NaN)
depth[~fg_mask] = 0.0  # or np.nan
```

## Previously Misidentified As

This was previously documented as a "Blender renderer reuse bug" where reusing the renderer across multiple camera views allegedly corrupted depth output. Investigation by Codex confirmed the values trace to Kubric's intentional sentinel, not to renderer state leakage. The orthographic top view having 0% background was mistaken for "only the 2nd render is clean" — orthographic cameras simply don't produce background pixels by design.
