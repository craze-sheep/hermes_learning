---
name: kubric-dataset-validation
description: Validate Kubric-generated physics simulation datasets — check depth maps, segment masks, physics data, file completeness, and identify rendering bugs.
trigger:
  - kubric dataset validation check quality
  - check depth map segment mask physics data
  - validate kubric output database S1 S2
tags: [kubric, dataset, validation, depth, segment, physics]
---

# Kubric Dataset Validation

Validate Kubric-generated physics simulation datasets for correctness.

## Directory Structure

```
database/S{scene}/L{level}/{sample_id}/
  ├── {id}.mp4          # rendered video
  ├── {id}.npz          # depth map: shape=(36, 128, 128) float32, unit='m'
  ├── video.json        # metadata (fps, resolution, camera, physics params)
  ├── object_static.json # object properties (list of 2+: ground + dynamic objects)
  └── dynamic/{frame}/  # frames 1-36
      ├── {frame}.png   # RGB render (128x128x3 uint8)
      ├── force_matrix.json
      ├── object_segment/{obj_id}.npz  # mask: 128x128 uint8 (0 or 1)
      └── object_dynamicjson/{obj_id}.json  # physics state per frame
```

**8 file types per sample** — matches `task/task5-输出参数探究/文件路径系统.md` exactly.

## Validation Checklist

### 1. Depth Map Quality

```python
import numpy as np
d = np.load(f"{sample_dir}/{id}.npz")['depth']
assert d.shape == (36, 128, 128)
assert d.dtype == np.float32
assert np.isfinite(d).all(), f"inf={np.isinf(d).sum()} nan={np.isnan(d).sum()}"

# Background pixels have sentinel depth ~1e10 (Kubric intentional, NOT a bug).
# Filter foreground before checking reasonable range.
fg = d[d < 1e9]
assert len(fg) > 0, "no foreground pixels (all background)"
assert fg.min() > 0.01, f"depth min={fg.min():.6f} (suspicious)"
assert fg.max() < 50, f"foreground depth max={fg.max():.2f} (suspicious)"
```

**Background depth ~1e10 m is EXPECTED** — Kubric uses `1e10` as a sentinel for background/infinity pixels (see `kubric/renderer/blender_utils.py:324`). The `z_to_depth` conversion applies per-pixel scaling (`sqrt(1 + d²/f²)`), producing 1000+ unique background values between 1.0e10 and 1.19e10. Foreground/background gap is ~7 orders of magnitude; use `depth < 1e9` as filter threshold.

**Background % varies by camera type**:
- Perspective (front/left): 40-65% background (depends on FOV vs scene extent)
- Orthographic (top): 0% background (all rays hit scene)

These are normal percentages, not bugs.

### 2. Segment Mask Correctness

```python
seg1 = np.load(f"{sample_dir}/dynamic/1/object_segment/1.npz")  # ground
seg2 = np.load(f"{sample_dir}/dynamic/1/object_segment/2.npz")  # dynamic object
assert seg1['mask'].shape == (128, 128)
assert set(np.unique(seg1['mask'])) <= {0, 1}
assert np.logical_and(seg1['mask'], seg2['mask']).sum() == 0, "masks overlap"
# visible_area in json should match mask pixel count
```

- S1 top view: sphere mask may not change between frames (correct — orthographic projection)
- S1 front view: sphere mask center should move downward as sphere falls
- S2 front view: cube mask should move horizontally as cube slides

### 2b. Embedded Object Detection (visible_area=0 trap)

**If a dynamic object has `visible_area=0` for ALL 36 frames AND from ALL views**, it's likely geometrically embedded inside another object — not just out of frame. This is a silent data corruption: RGB renders may still show the object (Blender's color renderer handles overlapping geometry differently), but the segmentation layer assigns overlapping pixels to the front-most surface only.

**Detection pattern:**
```python
# For each dynamic object, check if it's ever visible
for obj_id in dynamic_object_ids:
    total_visible = sum(
        load_json(f"dynamic/{f}/object_dynamicjson/{obj_id}.json")["visible_area"]
        for f in range(1, 37)
    )
    if total_visible == 0:
        # Object is NEVER visible — likely embedded in another object
        # Verify by checking position vs parent object geometry
        report_embedded_object(sample_dir, obj_id)
```

**Root cause diagnostic**: Compare the object's z-position with the surface z of the object it might be embedded in. If `object_bottom_z < parent_surface_top_z`, the object is clipping into the parent.

**Key insight**: Check ALL views, not just one. If the object has zero visible_area from front, top, AND left views, it's a geometry problem, not a camera angle problem. See `references/ramp-embedding-bug.md` for the S3 L1-L6 case study.

**Why RGB vs segmentation diverge**: Blender's path tracer renders overlapping surfaces by compositing (the inner object may show through transparency/refraction), but the segmentation pass assigns each pixel to the nearest surface's segmentation_id. When object A is inside object B, all of A's pixels get B's segmentation_id.

### 3. Physics Data Consistency

```python
import json
with open(f"{sample_dir}/dynamic/{frame}/object_dynamicjson/2.json") as f:
    d = json.load(f)
assert not any(np.isnan(v) or np.isinf(v) for v in d['position'])
assert d['time'] == (int(frame) - 1) / 12.0  # fps=12
assert d['visible_area'] == int(np.load(seg_path)['mask'].sum())
```

- S1 (free fall): sphere z should decrease from initial height to ~radius
- S2 (sliding friction): cube z should stay constant at size[2]/2 (on ground)
- S2 sphere penetrating ground (z_final < 0): known PyBullet issue at high speed

### 4. File Completeness (full scan)

```python
import os
expected_root = ['video.json', 'object_static.json', '{id}.mp4', '{id}.npz']
expected_per_frame = ['{frame}.png', 'force_matrix.json',
                      'object_segment/1.npz', 'object_segment/2.npz',
                      'object_dynamicjson/1.json', 'object_dynamicjson/2.json']
# Check every sample has all expected files, 36 frames, both objects
```

### 5. Rendered Image vs Data Cross-Check

Visual overlay: apply segment mask as colored overlay on PNG to verify alignment.
```python
from PIL import Image
vis = np.array(Image.open(png_path))
vis[seg_mask > 0, 0] = 255  # red overlay
Image.fromarray(vis).save('/tmp/overlay.png')
```

## Canonical Output Spec (task5)

The **authoritative** file list is in `task/task5-输出参数探究/文件路径系统.md`. It defines 8 file types per sample:
`{id}.mp4`, `{id}.npz`, `video.json`, `object_static.json`, plus 4 per-frame types under `dynamic/{n}/`.

**`physics_labels.json` is NOT in the canonical spec.** It was removed from ALL scripts (S1-S8) as of May 2026. For causal learning, pre-computed summary labels cause label leakage — models should learn from raw trajectories. S8 retains `compute_physics_labels` internally for negative sample filtering only (checks `no_dynamic_collision`), but does not write the file.

## S8 Filtering Dependency

S8 (泛化负样本) uses `compute_physics_labels()` to filter invalid negative samples:
```python
labels = compute_physics_labels(sample, frame_states, force_payloads, FPS)
if not labels.get("no_dynamic_collision", False):
    raise FilteredNegativeSample(...)
```
When modifying S8 scripts, keep this import and call — only the `write_json` line was removed.

## Removing physics_labels.json from Scripts

All scripts (S1-S8) have been updated. Each needed only 2 lines removed (S1-S7) or 1 line (S8):
- `from physics_label_utils import compute_physics_labels` (import) — removed from S1-S7, kept in S8
- `write_json(sample_dir / "physics_labels.json", compute_physics_labels(...))` (write) — removed from all

All other physics code (`simulate_and_keyframe`, `force_payloads`, `frame_states`, `zero_force_matrix`, `add_force`, `average_force_matrix`) serves other outputs (`force_matrix.json`, `object_dynamicjson` with `resultant force`) and must NOT be deleted.

**Docker containers load scripts at startup** — modifying scripts while containers are running does NOT affect the running process. Changes take effect on next container start.

**Why removed for causal learning**: Pre-computed summary labels (stop_frame, travel_distance) are outcomes. Using them as model input causes label leakage, letting the model bypass causal reasoning. Models should learn from raw trajectories (position/velocity/force) and static properties (mass/friction/size).

## Known Issues in Generated Data

| Issue | Scope | Cause | Detection |
|-------|-------|-------|-----------|
| Depth ~1e10 background values | ALL samples, all views | Expected: Kubric sentinel for background pixels (not a bug). Use `depth < 1e9` to filter. | `depth.max() > 1e9` |
| L6 32.5% / L7 23.3% still moving at 3s | S2 L6-L7 only | 3s simulation insufficient for rolling friction. Not a code bug. | `velocity[-1] > 0.01` |
| Cube visible in RGB but seg mask all-zero | S3 L1-L6 (ramp + cube) | Cube placed inside ramp geometry. Blender seg layer assigns overlapping pixels to front-most surface. | `visible_area == 0` for all frames AND all views. See `references/ramp-embedding-bug.md` for full analysis, affected scope, and fix. |

**Embedded object pitfall**: When placing objects on surfaces with thickness (ramps, boxes), ensure the placement offset accounts for the surface object's half-thickness projected along the surface normal. The `ramp_surface_point` function returns the geometric center plane, not the outer surface. Fix: `extra_offset = surface_half_thickness * cos(angle)`.

## Reporting Findings

When writing findings to `致命错误/N.md`, follow this structure:
- Conclusion (one sentence)
- Quantified impact (X/Y samples affected)
- Evidence (actual data values, not just descriptions)
- Root cause with code reference
- Fix suggestion or status

User preference: 简洁回答, 数字说话, 不要废话. Show cleanup commands before executing; wait for user approval.
