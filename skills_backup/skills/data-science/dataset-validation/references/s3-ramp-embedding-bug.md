# S3 Ramp Embedding Bug — Segmentation All-Zeros

**Date**: 2026-05-23
**Affected**: S3 (斜面物理), L1-L6 (ramp + cube scenarios)
**Not affected**: S3 L7/L8 (sphere on ramp — sphere geometry doesn't fully embed), S2/S4/S5 (no ramp or different placement)

## Symptom

`visible_area = 0` for cube (object_id=2) across ALL 36 frames and ALL 3 views (front/top/left). RGB renders show the cube is visually present.

## Example: S3/L1/26

```
Static config:
  ground: 4.0×4.0×0.08 (seg_id=1)
  ramp:   2.4×1.0×0.12  (seg_id=3)
  cube:   0.24×0.24×0.24 (seg_id=2)

Frame 1 dynamic data:
  ramp_pos: [0, 0, 0.3819]   quat: [0.994, 0, 0.1098, 0] (angle≈12.6°)
  cube_pos: [-0.413, 0.2, 0.4008]

  cube_bottom_z = 0.4008 - 0.12 = 0.2808
  ramp_top_z    ≈ 0.3819 + 0.06 = 0.4419
  embedding_depth = 0.4419 - 0.2808 = 0.1611m  (67% of cube height)
```

Segmentation masks:
- ground: 8844 pixels ✅
- ramp: 1560 pixels ✅
- cube: 0 pixels ❌

## Root Cause

In `generate_s3_dataset.py`, the cube placement:
```python
surf_pos = ramp_surface_point(ramp_s, ramp_y, angle, ramp_size)
normal = ramp_normal(angle)
pos = surf_pos + normal * (cube_size_z / 2)
```

`ramp_surface_point` computes a point on the ramp's geometric center-plane, not its outer surface. The ramp has thickness 0.12m, so the center-plane is 0.06m below the top surface. The cube is placed 0.12m above the center-plane, but the ramp surface at that tilted angle is 0.06m above the center-plane → cube bottom is 0.06m inside the ramp.

## Fix

```python
ramp_half_thickness = ramp_size[2] / 2  # 0.06
extra_offset = ramp_half_thickness * math.cos(angle)
pos = surf_pos + normal * (cube_size_z / 2 + extra_offset)
```

## Investigation Method

1. Check `visible_area` in `object_dynamicjson` — if 0 for all frames across all views, suspect embedding
2. Compare object z-position with enclosing object's top surface
3. Verify by loading RGB frame with `vision_analyze` — if cube is visually present but mask is zero, confirms segmentation clipping
4. Check `np.load('object_segment/{id}.npz')['mask'].sum()` for exact pixel count

## Status

- ❌ Not fixed in code
- ❌ Affected samples not regenerated
- Written to `致命错误/4.md`
