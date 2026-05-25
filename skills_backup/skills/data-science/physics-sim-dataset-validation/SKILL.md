---
name: physics-sim-dataset-validation
description: "Systematic validation of physics simulation video datasets — depth maps, segmentation masks, physics trajectories, force matrices, rendering quality, file completeness."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [dataset, validation, physics, simulation, kubric, blender, rendering, depth, segmentation]
    related_skills: []
---

# Physics Simulation Dataset Validation

Systematic checklist for validating physics simulation video datasets (e.g. Kubric/Blender pipelines). Catches rendering bugs, physics anomalies, data corruption, and file completeness issues before they poison downstream training.

## When to Use

- After a batch generation run, before committing data as "ready"
- When debugging unexpected training behavior on a physics dataset
- When investigating container crashes during generation (OOM, GPU errors)

## Validation Checklist (ordered by priority)

### 1. File Completeness

Check every sample has all expected files. Typical structure:

```
S{x}/L{y}/{id}/
  {id}.mp4          # rendered video
  {id}.npz          # depth map (36, H, W) float32
  video.json        # metadata: fps, frames, camera, units
  object_static.json # object properties (list of dicts)
  dynamic/{1..36}/
    {frame}.png      # per-frame RGB render
    force_matrix.json
    object_segment/{obj_id}.npz  # per-object binary mask
    object_dynamicjson/{obj_id}.json  # per-object physics state
```

Script pattern:
```python
import os
for sample_dir in all_samples:
    missing = []
    for expected in expected_files:
        if not os.path.exists(os.path.join(sample_dir, expected)):
            missing.append(expected)
    if missing:
        report(sample_dir, missing)
```

### 2. Depth Map Sanity

Most common failure mode. Check:
- `depth.shape == (num_frames, H, W)`
- `depth.dtype == float32`
- `np.isfinite(depth).all()` — no NaN/Inf
- Foreground depth should be within scene scale (typically < 50m for tabletop)
- Background pixels (~1e10 m) are Kubric's sentinel for sky — NOT a bug

```python
import numpy as np
d = np.load(path)["depth"]
assert d.ndim == 3 and d.dtype == np.float32
assert np.isfinite(d).all(), "NaN or Inf in depth"

# Separate foreground (actual scene) from background (sentinel ~1e10)
fg = d[d < 1e9]
assert len(fg) > 0, "no foreground pixels"
assert fg.max() < 50, f"foreground depth max={fg.max():.2f} looks wrong"
# Background %: perspective views ~40-65%, orthographic ~0%
```

### 3. Segment Mask Correctness

- Shape matches depth H×W
- dtype=uint8, values ∈ {0, 1}
- No overlap between objects in same frame
- `visible_area` in dynamicjson matches `mask.sum()`
- frame_num in npz matches directory name
- **Critical**: If a dynamic object has `visible_area=0` for ALL 36 frames AND from ALL camera views, it's likely **geometrically embedded** inside another object (not just out of frame). RGB renders may still show the object, but segmentation assigns overlapping pixels to the front-most surface. Check object z-position vs parent surface z to confirm. See `references/ramp-embedding-bug.md` in `kubric-dataset-validation` skill for the S3 case study.

### 4. Physics Trajectory Plausibility

- Static objects: position should not change between frame 1 and frame N
- Dynamic objects: should show motion (position change) unless physically resting
- Falling objects: z should decrease over time (toward ground)
- Sliding objects: horizontal position should change
- No ground penetration: z_final should be ≥ object's resting height
- Check for NaN/Inf in position, velocity, angular_velocity

```python
p1 = load_json("dynamic/1/object_dynamicjson/2.json")["position"]
p36 = load_json("dynamic/36/object_dynamicjson/2.json")["position"]
assert not any(np.isnan(v) or np.isinf(v) for v in p1 + p36)
```

### 5. Rendering vs Data Cross-Check

- PNG renders should not be all-black
- Segment mask center should roughly correspond to object position in rendered image
- Depth map spatial pattern should match rendered scene (objects closer = smaller depth)

### 6. Metadata Consistency

- video.json: `num_frames` matches actual frame count, `fps` correct
- video.json: `depth_path` and `video_path` match actual filenames
- object_static.json: `segmentation_id` == `object_id`
- time field in dynamicjson: `(frame_num - 1) / fps`

### 7. Multi-View ID Pattern Detection

When a script generates multiple views per physical sample (e.g. front, top, left), verify each view's data independently. Common pattern: ID assignment interleaves views, so bugs manifest as systematic patterns on specific ID residues (odd/even, mod 3, etc.).

```python
# Detect view-correlated corruption
for sid, depth_max in all_samples:
    if depth_max > threshold:
        bad_ids.append(int(sid))
# Check mod patterns
from collections import Counter
mod_counts = Counter(i % n_views for i in bad_ids)
```

## Pitfalls

### File Naming: `{id}.mp4` vs `1.mp4`

Actual dataset naming convention: files are named after the **sample directory ID**, not a constant `1`.

```
S1/L1/1/  → 1.mp4, 1.npz
S1/L1/2/  → 2.mp4, 2.npz
S1/L1/200/ → 200.mp4, 200.npz
```

**Bug pattern:** Hardcoding `1.mp4` / `1.npz` in validation scripts only checks sample 1, silently skipping all others. Always use `f'{sid}.mp4'` where `sid` is the sample directory name.

### Comparing Script Versions

When a project has multiple validation script versions (v1, v2, ...), diff the **file existence checks** first — that's where silent coverage gaps hide. A script that passes all samples but only checks `1.mp4` reports zero errors while missing 99% of broken data.

### Depth Map Shape: `(36,128,128)` vs `(128,128)`

Both shapes are valid depending on the pipeline stage:
- `(128,128)` — single-frame depth (static render or per-frame npz)
- `(36,128,128)` — full sequence depth in one file

Validation should accept both. Rejecting `(36,128,128)` as "wrong shape" is a false positive.

## Known Kubric/Blender Pitfalls

See `references/kubric-rendering-bugs.md` for documented issues.

## OOM-Related Data Corruption

When Docker containers are killed by OOM during generation, the result is:

1. **Empty directories**: `make_dirs()` runs before rendering, so directories exist but have zero files
2. **Partial samples**: Some frames written, others missing
3. **No error logs**: `--rm` containers vanish on kill, no trace in Docker

Detection:
```python
# Find samples with 0 files (empty directory)
for sample_dir in all_samples:
    file_count = sum(len(f) for _, _, f in os.walk(sample_dir))
    if file_count == 0:
        report(f"{sample_dir}: completely empty")
    elif file_count < expected_minimum:
        report(f"{sample_dir}: only {file_count} files (expected {expected_minimum})")
```

Diagnosis: check `dmesg -T | grep oom` for kill timestamps, compare with file mtimes.

## After Validation: Reporting

Write findings to a structured markdown file (e.g. `致命错误/N.md`) with:
- Conclusion (one sentence)
- Quantified impact (X/Y samples affected)
- Evidence (actual data values, not just descriptions)
- Root cause with code reference
- Fix suggestion

User preference: 简洁回答, 数字说话, 不要废话.
