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
# CRITICAL: file names use the SAMPLE ID, not literal "1"
# S1/L1/1/ has 1.mp4, 1.npz; S1/L1/65/ has 65.mp4, 65.npz
expected_root = ['video.json', 'object_static.json', '{id}.mp4', '{id}.npz']
expected_per_frame = ['1.png', 'force_matrix.json',
                      'object_segment/{obj_id}.npz',
                      'object_dynamicjson/{obj_id}.json']
# Check every sample has all expected files, 36 frames, correct number of objects
```

**File naming pitfall**: mp4/npz files are named `{sample_id}.mp4` / `{sample_id}.npz`, NOT `1.mp4`. When writing validation scripts, use `f"{sid}.mp4"` not hardcoded `"1.mp4"`. A common mistake is checking for `1.mp4` which only exists in sample directory `1/`.

### 5. Cross-View Consistency (multi-view events)

Each physical event generates N consecutive video directories with different camera views. The view cycle is:

| Scene | Views/Event | View Names | Cycle Pattern |
|-------|-------------|------------|---------------|
| S1, S4 | 2 | front, top | front→top→front→top... |
| S2, S3 | 3 | front, top, left | front→top→left→front... |
| S5-S7 | 5 | front, back, left, right, top | front→back→left→right→top→... |

**Event grouping**: For a level with K sample directories and N views/event, directories `[(i*N+1) .. ((i+1)*N)]` belong to the same physical event. E.g., S5/L1 dirs 1-5 = event 0, dirs 6-10 = event 1.

**What should be identical across views** (same physics simulation):
- `object_static.json`: all keys (mass, size, shape, friction, color, etc.)
- `object_dynamicjson/{obj_id}.json`: `position`, `velocity`, `angular_velocity` at each frame
- `force_matrix.json`: force values

**What differs across views**:
- `video.json`: `cameras[0].view_name`, `cameras[0].position`, `cameras[0].look_at`
- Segment masks: different pixel regions (camera-dependent)
- Depth maps: different depth values (camera-dependent)

**Cross-view check pattern**:
```python
# Group consecutive dirs into events
events = [sample_ids[i:i+num_views] for i in range(0, len(sample_ids), num_views)]
for event in events[:3]:  # sample first 3 events
    for sid_a, sid_b in zip(event, event[1:]):
        static_a = json.load(open(f"{ld}/{sid_a}/object_static.json"))
        static_b = json.load(open(f"{ld}/{sid_b}/object_static.json"))
        # Compare: mass, size, lateralFriction, restitution, color_name should match
        # Compare: dynamic/1/object_dynamicjson positions should match (within 1e-4)
```

### 6. Rendered Image vs Data Cross-Check

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

**Collision parameter pitfall**: If S8 generates 0 accepted samples for a level, the spacing parameters are systematically too small (see `references/s8-collision-spacing-bug.md`). Randomization won't help — the parameters need adjustment. Key rule: time gap ≥ `2 * radius / speed`, spatial gap ≥ `2 * max_radius + margin`.

## Removing physics_labels.json from Scripts

All scripts (S1-S8) have been updated. Each needed only 2 lines removed (S1-S7) or 1 line (S8):
- `from physics_label_utils import compute_physics_labels` (import) — removed from S1-S7, kept in S8
- `write_json(sample_dir / "physics_labels.json", compute_physics_labels(...))` (write) — removed from all

All other physics code (`simulate_and_keyframe`, `force_payloads`, `frame_states`, `zero_force_matrix`, `add_force`, `average_force_matrix`) serves other outputs (`force_matrix.json`, `object_dynamicjson` with `resultant force`) and must NOT be deleted.

**Docker containers load scripts at startup** — modifying scripts while containers are running does NOT affect the running process. Changes take effect on next container start.

**Why removed for causal learning**: Pre-computed summary labels (stop_frame, travel_distance) are outcomes. Using them as model input causes label leakage, letting the model bypass causal reasoning. Models should learn from raw trajectories (position/velocity/force) and static properties (mass/friction/size).

## object_static.json Key Reference

When writing validation checks, use the ACTUAL keys — not assumed ones:

```json
{
  "object_id": 1,
  "segmentation_id": 1,
  "object_type": "sphere",    // NOT "shape"
  "static": false,
  "radius": 0.15,              // null for ground/box/ramp
  "size": [0.3, 0.3, 0.3],   // null for sphere; [w,d,h] for box/ramp
  "height": null,              // null for sphere/box; float for ramp
  "mass": 1.0,                 // null for ground (static)
  "lateralFriction": 0.5,
  "rollingFriction": 0.005,
  "spinningFriction": 0.001,
  "restitution": 0.0,
  "color_name": "red",
  "rgba": [0.8, 0.1, 0.1, 1.0]
}
```

**Common validation script mistake**: Checking for `shape` or `position` keys in object_static.json. These keys don't exist. The shape info is in `object_type` + `radius`/`size`/`height`. The initial position is in `dynamic/1/object_dynamicjson/{obj_id}.json` → `position`, not in static.

## Segmentation npz Key Reference

```python
d = np.load("dynamic/1/object_segment/1.npz")
# Keys: 'mask', 'object_id', 'segmentation_id', 'frame_num'
# NOT 'segmentation' — the key is 'mask'
seg = d['mask']  # shape (128,128), values 0 or 1
```

## Validation Performance

For large datasets (20K+ samples), use a **phased approach**:
1. **Phase 1: File scan** — os.listdir only, no file reads. Check existence of required files, frame count, sequence continuity. Takes ~30s for 26K samples.
2. **Phase 2: JSON structure** — Parse video.json + object_static.json on sampled subset (first/mid/last 3 per level). Check keys, num_frames, resolution.
3. **Phase 3: Depth/segment** — Load npz on sampled subset (5 per level × 3 frames). Check shapes, all-zero masks, NaN.
4. **Phase 4: Cross-view** — Compare object_static + dynamic JSON across views within sampled events.

**Python buffering pitfall**: Use `python3 -u` or `stdbuf -oL` when running validation scripts in background. Standard Python buffers stdout when not connected to a terminal, producing no output until script completion.

## Known Issues in Generated Data

| Issue | Scope | Cause | Detection |
|-------|-------|-------|-----------|
| Depth ~1e10 background values | ALL samples, all views | Expected: Kubric sentinel for background pixels (not a bug). Use `depth < 1e9` to filter. | `depth.max() > 1e9` |
| L6 32.5% / L7 23.3% still moving at 3s | S2 L6-L7 only | 3s simulation insufficient for rolling friction. Not a code bug. | `velocity[-1] > 0.01` |
| Cube visible in RGB but seg mask all-zero | S3 L1-L6 (ramp + cube) | Cube placed inside ramp geometry. Blender seg layer assigns overlapping pixels to front-most surface. | `visible_area == 0` for all frames AND all views. See `references/ramp-embedding-bug.md` for full analysis, affected scope, and fix. |
| All candidates rejected by collision filter | S8 L2,L3,L5,L7,L10,L11,L12 | Insufficient spacing parameters — objects systematically collide in simulation | `dynamic_dynamic_contact_count=1` for all candidates. See `references/s8-collision-spacing-bug.md` for per-level analysis and fixes. |
| Segmentation all-zero in final frames | S2-S7, all levels with 3+ objects | Expected: last dynamic object leaves camera view near end of 3s simulation. Only affects `object_segment/{last_obj_id}.npz` in frames 32-36. NOT a bug. | `seg[mask].sum() == 0` for last object in last 5 frames. More prevalent with more objects (S7/L10 has 45 occurrences per level). S1 unaffected (2 objects, simple geometry). |
| S3/L1/6 incomplete sample | S3/L1/6 only | Only has `dynamic/` directory; missing `6.mp4`, `6.npz`, `video.json`, `object_static.json`. Likely interrupted during S3 --overwrite rerun. Dynamic frames exist but are empty (no object_dynamicjson/object_segment data). | File existence check |
| S7/L10 variable object count | S7/L10 | Some physical events have 5 objects, others have 6. By design — different events in this generalization level use different object counts. | `len(object_static) varies between {5, 6}` |
| S1/L1 帧32缺1.png | S1/L1 samples | Some samples missing `1.png` in `dynamic/32/`. Does not affect other data. | File existence check |

**Embedded object pitfall**: When placing objects on surfaces with thickness (ramps, boxes), ensure the placement offset accounts for the surface object's half-thickness projected along the surface normal. The `ramp_surface_point` function returns the geometric center plane, not the outer surface. Fix: `extra_offset = surface_half_thickness * cos(angle)`.

## Pre-built Validation Scripts

Two scripts in `scripts/`:

### 1. `scripts/validate_s1_s7.py` — File + Data Validation
Full validation: file completeness, JSON structure, depth/segment quality, cross-view consistency. Run with:
```bash
cd /home/lzy/project/slot-datamaking
/home/lzy/miniconda3/bin/python3 -u validate_s1_s7.py
```
Modify `DB` and `VIEWS` constants for different datasets. Takes ~45s for 26K samples.

### 2. `scripts/validate_consistency.py` — Deep Consistency Check
Cross-view physics consistency (ALL events, ALL frames), object_static vs video.json matching, initial position/velocity diversity, depth npz validation, cross-level object type audit. Run with:
```bash
cd /home/lzy/project/slot-datamaking
/home/lzy/miniconda3/bin/python3 -u validate_consistency.py
```
Excludes S3 by default (`CHECK_SCENES`). Takes ~3-5 min for 24K samples.

## Reporting Findings

When writing findings to `致命错误/N.md`, follow this structure:
- Conclusion (one sentence)
- Quantified impact (X/Y samples affected)
- Evidence (actual data values, not just descriptions)
- Root cause with code reference
- Fix suggestion or status

User preference: 简洁回答, 数字说话, 不要废话. Show cleanup commands before executing; wait for user approval.
