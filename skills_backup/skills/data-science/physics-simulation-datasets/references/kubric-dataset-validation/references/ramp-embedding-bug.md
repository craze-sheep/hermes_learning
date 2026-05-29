# Ramp Surface Embedding Bug — S3 L1-L6

## Problem

In S3 (ramp physics), cubes placed on the ramp surface are geometrically **embedded inside the ramp body**, causing Blender's segmentation layer to assign zero pixels to the cube. The cube is visible in RGB renders but has `visible_area=0` in all segmentation masks across all 36 frames and all 3 camera views.

## Root Cause

The `ramp_surface_point()` function calculates a point on the ramp's **geometric center plane**, not the outer surface:

```python
def ramp_surface_point(s, y, incline_angle, ramp_size):
    cos_a = math.cos(incline_angle)
    sin_a = math.sin(incline_angle)
    x = s * cos_a
    z = ramp_size[2] + 0.5 * ramp_size[0] * sin_a + s * sin_a
    return (x, y, z)
```

The ramp is a Cube with size (2.4, 1.0, 0.12), so it has **thickness** (0.12m, half = 0.06m). The function returns the center of the ramp body at position `s` along its length, not the top surface.

The cube is then placed with:
```python
pos = surf_pos + normal * (cube_size_z / 2)  # only offsets by half cube height
```

This places the cube's center at the ramp's center plane + half cube height along the normal. But the ramp's outer surface is `ramp_half_thickness * cos(angle)` further along the normal. Result: the cube is embedded.

## Evidence (S3/L1/26)

```
ramp_pos:  [0, 0, 0.3819]     ramp_quat: [0.994, 0, 0.1098, 0] (angle ≈ 12.6°)
cube_pos:  [-0.413, 0.2, 0.4008]

cube_bottom_z = 0.4008 - 0.12 = 0.2808
ramp_top_z   ≈ 0.3819 + 0.06 = 0.4419

Embedding depth = 0.4419 - 0.2808 = 0.1611m
Cube total height = 0.24m → 67% volume inside ramp
```

Cross-view check (all three views show the same cube position, all have visible_area=0):
```
S25 (front): cube_pos=[-0.413, 0.2, 0.4008], visible=0
S26 (top):   cube_pos=[-0.413, 0.2, 0.4008], visible=0
S27 (left):  cube_pos=[-0.413, 0.2, 0.4008], visible=0
```

## Affected Scope

| Level | Object on Ramp | Affected? | Reason |
|-------|---------------|-----------|--------|
| L1 | cube (0.24m) | ❌ Yes | Small cube fully embedded |
| L2 | cube (0.24m) | ❌ Yes | Same geometry |
| L3 | cube (0.24m) | ❌ Yes | Same geometry |
| L4 | cube (0.24m) | ❌ Yes | Same geometry |
| L5 | cube (0.18-0.30m) | ❌ Yes | All sizes affected |
| L6 | cube (0.24m) | ❌ Yes | Same geometry |
| L7 | sphere (r=0.18-0.28) | ✅ No | Sphere protrudes above ramp |
| L8 | sphere (r=0.18-0.28) | ✅ No | Sphere protrudes above ramp |
| L9 | cylinder (r=0.16-0.24, h=0.22-0.34) | ⚠️ Partial | Upright cylinders may be ok, lying ones may embed |

## Fix

Add the ramp's half-thickness projection to the normal offset:

```python
ramp_half_thickness = ramp_size[2] / 2  # 0.06m
extra_offset = ramp_half_thickness * math.cos(angle)
pos = surf_pos + normal * (cube_size_z / 2 + extra_offset)
```

Or modify `ramp_surface_point` to return the outer surface instead of the center plane.

## Detection Script

```python
#!/usr/bin/env python3
"""Find samples where a dynamic object is never visible (likely embedded)."""
import json, sys
from pathlib import Path

for scene_dir in sys.argv[1:]:
    for sample_dir in Path(scene_dir).rglob("object_static.json"):
        sample = sample_dir.parent
        statics = json.loads(sample_dir.read_text())
        dynamic_ids = [o["object_id"] for o in statics if not o["static"]]
        
        for oid in dynamic_ids:
            total_visible = 0
            for frame_dir in sorted((sample / "dynamic").iterdir()):
                dj = frame_dir / "object_dynamicjson" / f"{oid}.json"
                if dj.exists():
                    total_visible += json.loads(dj.read_text())["visible_area"]
            if total_visible == 0:
                print(f"EMBEDDED: {sample} obj_id={oid}")
```
