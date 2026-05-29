# Codex Depth Map Analysis (2026-05-23)

## Technique: Delegate Data Analysis to Codex

When validating depth maps with unusual values (e.g., extreme background depth), Codex can trace the issue to source code level. Provide:
1. Raw statistics (min/max/distribution/histogram)
2. Scene setup (camera params, object positions, resolution)
3. A specific question ("is this value expected?")

Codex will read the source code and provide exact explanations.

## Kubric z_to_depth Formula

Found in `kubric/renderer/blender_utils.py:324` and `kubric/cameras.py:167`:

```python
# Raw Blender depth pass range: [0, 10000000000.0]
# The value 1e10 is used for background / infinity

# Conversion from z-buffer to true depth:
depth_scaling = sqrt(1 + d² / f²)
depth = z * depth_scaling
```

Where:
- `z` = raw z-buffer value from Blender
- `d` = pixel distance from optical center (in sensor-space units)
- `f` = focal length

This explains:
- **Background ~1e10 m**: z=1e10 for background pixels
- **1429 unique background values**: each pixel has different `d`, so different `depth_scaling`
- **Center pixel**: d≈0 → scaling≈1.00 → depth≈1.00e10
- **Corner pixel**: d=max → scaling≈1.188 → depth≈1.19e10
- **Clean separation**: foreground (5-16m) vs background (1e10) has 7 orders of magnitude gap

## Validation Threshold

```python
# Safe foreground/background separator
FOREGROUND_THRESHOLD = 1e9
valid_mask = depth < FOREGROUND_THRESHOLD
depth_foreground = depth[valid_mask]
```

No transition artifacts exist between 20m and 1e9m — the gap is clean.
