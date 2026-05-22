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
- `depth.max()` should be within scene scale (typically < 100m for tabletop scenes)
- Values ~1e10 indicate Blender far-clip-plane bleed (broken render)

```python
import numpy as np
d = np.load(path)["depth"]
assert d.ndim == 3 and d.dtype == np.float32
assert np.isfinite(d).all(), "NaN or Inf in depth"
assert d.max() < 100, f"depth max={d.max():.2e} looks like far-clip bleed"
```

### 3. Segment Mask Correctness

- Shape matches depth H×W
- dtype=uint8, values ∈ {0, 1}
- No overlap between objects in same frame
- `visible_area` in dynamicjson matches `mask.sum()`
- frame_num in npz matches directory name

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
