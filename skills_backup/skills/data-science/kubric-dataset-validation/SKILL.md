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
  ├── object_static.json # object properties (list of 2: ground + dynamic)
  └── dynamic/{frame}/  # frames 1-36
      ├── {frame}.png   # RGB render (128x128x3 uint8)
      ├── force_matrix.json
      ├── object_segment/{obj_id}.npz  # mask: 128x128 uint8 (0 or 1)
      └── object_dynamicjson/{obj_id}.json  # physics state per frame
```

## Validation Checklist

### 1. Depth Map Quality

```python
import numpy as np
d = np.load(f"{sample_dir}/{id}.npz")['depth']
assert d.shape == (36, 128, 128)
assert d.dtype == np.float32
assert np.isfinite(d).all(), f"inf={np.isinf(d).sum()} nan={np.isnan(d).sum()}"
assert d.max() < 100, f"depth max={d.max():.2f} — values >1e6 indicate Blender far-plane bug"
```

**Known bug**: Reusing Blender renderer across multiple views corrupts depth. Values ~1e10 are Blender's far clipping plane. Only the 2nd render (top view) is correct. See `kubric-gpu-docker` skill for details.

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

## Known Issues in Generated Data

| Issue | Scope | Cause |
|-------|-------|-------|
| Depth ~1e10 (far-plane values) | S1: 50% (all odd IDs), S2: 67% (ID%3≠2) | Renderer reuse across views |
| S2 sphere z < 0 | S2 L6: 33/324 samples | PyBullet step too large for high-speed collision |
| S2 L7/215 empty directory | 1 sample | Container killed (OOM) during generation |
| S1 top-view mask unchanged | ~9 samples | Correct behavior (orthographic projection) |
