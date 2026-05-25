# Zero Segmentation Mask Root Cause Analysis

May 2026 analysis of S1-S8 validation report (`validation_report_s1_s8.txt`).

## Summary

ALL zero segmentation masks have deterministic explanations. No rendering bugs found.

**S8 breakdown**:
| Root Cause | Count | % | Typical Scenes |
|-----------|-------|---|----------------|
| Fallen off ground | 69 | 36.3% | S3/L8, S5/L4, S8/L2 |
| Outside camera FOV | 32 | 16.9% | S8/L2, S5/L4, S6/L4 |
| Occluded by walls | 89 | 46.8% | S8/L9 (all 3 walls) |
| Unknown / rendering bug | 0 | 0.0% | — |

**S3-S7 breakdown** (corrected with orthographic camera fix):
| Root Cause | Count | % |
|-----------|-------|---|
| Fallen off ground | 180 | 30.5% |
| Outside camera FOV | 404 | 68.5% |
| Occluded by walls | 0 | 0.0% |
| Rendering edge case | 6 | 1.0% |

The 6 remaining unknowns are S3 left-view cases where a small sphere (r=0.18) is hidden behind a ramp structure — genuine rendering result.

## Critical Pitfall: Orthographic Camera FOV

The **top camera** uses `type=Orthographic, orthographic_scale=5.0`, seeing a 5×5 unit area.
But ground is 9×6 or 8×6 — **ground is LARGER than top camera FOV**.

Using the perspective projection formula for the orthographic camera produces WRONG results:
objects appear in-FOV when they're actually outside. This was the #1 source of "unknown"
zero-mask cases before the fix.

**Fix**: Check `cam_info.get("type") == "Orthographic"` and use world-space extent comparison:
```python
if cam_info.get("type") == "Orthographic":
    scale = cam_info.get("orthographic_scale", 5.0)
    half = scale / 2
    x_local = np.dot(to_obj, right)
    y_local = np.dot(to_obj, up)
    return abs(x_local) < half and abs(y_local) < half
```

## Scene-by-Scene Breakdown

### S1/S2: Clean
- No zero masks at all. S1 has vertical-only motion, S2 has controlled horizontal motion.

### S3: Mostly fallen + 6 edge cases
- S3/L1-L5: clean or near-clean
- S3/L7-L9: objects with horizontal velocity fall off ground edge
- 6 cases from left-view where small sphere (r=0.18) occluded by ramp

### S4: Mixed
- S4/L1-L5: mostly clean
- S4/L6-L9: fallen objects dominate

### S5-S7: Fallen + FOV (dominant)
- 5 views including orthographic top view
- Top view accounts for majority of FOV-out cases (ground > top camera extent)
- Objects with zero friction slide off ground edges

### S8: All 3 categories
- S8/L1-L8 (no walls): fallen + FOV-out
- S8/L9 (3 walls): 89/89 zero masks are wall occlusion
- S8/L10-L14: mostly clean

## S8/L9 Wall Occlusion Deep Dive

Wall height: 1.2 (z=0 to z=1.2), sphere top at z≈0.44, camera at z=3.2.

Same physical event, different visibility per view:
| View | obj 2 | obj 3 | obj 4 |
|------|-------|-------|-------|
| front | ✗ bottom wall | ✗ bottom wall | ✗ bottom wall |
| back | ✓ | ✓ | ✓ |
| left | ✗ left wall | ✗ left wall | ✓ |
| right | ✓ | ✓ | ✗ right wall |
| top | ✓ | ✓ | ✓ |

Ray-cast verification confirms wall intersection at z=0.99 (inside wall z=[0,1.2]).

## Full Classification Code

```python
import numpy as np

CAMERAS = {
    "front": {"pos": (0, -7.5, 3.2), "look_at": (0, 0, 0.35)},
    "back":  {"pos": (0, 7.5, 3.2),  "look_at": (0, 0, 0.35)},
    "left":  {"pos": (-7.5, 0, 3.2), "look_at": (0, 0, 0.35)},
    "right": {"pos": (7.5, 0, 3.2),  "look_at": (0, 0, 0.35)},
    "top":   {"pos": (0, -0.01, 8.0),"look_at": (0, 0, 0.0),
              "type": "Orthographic", "orthographic_scale": 5.0},
}
GROUND_X, GROUND_Y = (-4.5, 4.5), (-3.0, 3.0)

def check_in_fov(cam_info, pos):
    cam = np.array(cam_info["pos"], dtype=np.float64)
    look = np.array(cam_info["look_at"], dtype=np.float64)
    obj = np.array(pos, dtype=np.float64)
    forward = look - cam; forward /= np.linalg.norm(forward)
    right = np.cross(forward, [0,0,1]); right /= np.linalg.norm(right)
    up = np.cross(right, forward)
    to_obj = obj - cam

    if cam_info.get("type") == "Orthographic":
        scale = cam_info.get("orthographic_scale", 5.0)
        half = scale / 2
        return abs(np.dot(to_obj, right)) < half and abs(np.dot(to_obj, up)) < half
    else:
        depth = np.dot(to_obj, forward)
        if depth <= 0: return False
        u = 64 + np.dot(to_obj, right)/depth * 35/32 * 128
        v = 64 - np.dot(to_obj, up)/depth * 35/32 * 128
        return 0 <= u < 128 and 0 <= v < 128

def check_wall_occlusion(cam_pos, obj_pos, wall_planes):
    cam, obj = np.array(cam_pos, dtype=np.float64), np.array(obj_pos, dtype=np.float64)
    direction = obj - cam
    d_norm = direction / np.linalg.norm(direction)
    t_obj = np.linalg.norm(direction)
    for axis, wall_val, ortho_range, z_range in wall_planes:
        idx = 0 if axis == 'x' else 1
        if abs(d_norm[idx]) < 1e-10: continue
        t = (wall_val - cam[idx]) / d_norm[idx]
        if t <= 0 or t >= t_obj: continue
        hit = cam + t * d_norm
        other_idx = 1 - idx
        if (ortho_range[0] <= hit[other_idx] <= ortho_range[1] and
            z_range[0] <= hit[2] <= z_range[1]):
            return True
    return False

def classify_zero_mask(pos, cam_info, wall_planes=None):
    if pos[2] < -0.5 or pos[0] < GROUND_X[0] or pos[0] > GROUND_X[1] or pos[1] < GROUND_Y[0] or pos[1] > GROUND_Y[1]:
        return 'fallen'
    if not check_in_fov(cam_info, pos):
        return 'fov_out'
    if wall_planes and check_wall_occlusion(cam_info["pos"], pos, wall_planes):
        return 'occluded'
    return 'unknown'

S8L9_WALLS = [
    ('y', -1.6, (-2.5, 2.5), (0, 1.2)),
    ('x', -2.2, (-2.5, 2.5), (0, 1.2)),
    ('x',  2.2, (-2.5, 2.5), (0, 1.2)),
]
```

## Why This Is NOT a Rendering Bug

Blender's cryptomatte pass correctly reports zero pixels for objects that are not visible.
The issue is in the generation pipeline: it doesn't filter samples where objects become invisible.
