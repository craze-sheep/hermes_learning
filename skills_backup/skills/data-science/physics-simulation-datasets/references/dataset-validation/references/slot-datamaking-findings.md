# Slot-Datamaking Dataset: Known Bugs & Statistics

Date: 2026-05-22
Location: `/home/lzy/project/slot-datamaking/database/`

## Dataset Overview

| Scenario | Levels | Samples/Level | Total | Object Type | Camera |
|----------|--------|---------------|-------|-------------|--------|
| S1 | L1-L5: 200, L6-L7: 300 | varies | 1600 | sphere | Orthographic top (pos=[0,-0.01,8], scale=5) |
| S2 | L1-L4: 240, L5-L6: 360, L7: 210 | varies | 1873 | cube (L1-L6), cylinder (L7) | Perspective front (pos=[0,-7.5,3.2]) |

All samples: 128x128 resolution, 36 frames (12fps, 3s), 2 objects (ground + dynamic).

## Critical Bug: Depth Map Corruption

### Confirmed Root Cause

**Single Blender renderer instance reused across multiple views.** The `generate_physical_sample()` function creates one `Blender()` renderer and loops over views, only switching `scene.camera` and `renderer.scratch_dir`. The Blender renderer's depth pass does not properly reinitialize between renders. Only the 2nd render gets a clean depth pass.

See `references/blender-depth-bug.md` for code-level root cause and fix.

### S1 Pattern — Odd ID Corruption (50% loss)

- Default views: `["front", "top"]` (2 views per physical sample)
- Front view = 1st render = odd ID → CORRUPTED
- Top view = 2nd render = even ID → CLEAN
- 100% consistent across all 7 levels
- **800 of 1600 samples affected**

### S2 Pattern — Every-3rd-Normal (67% loss)

- Default views: `["front", "top", "left"]` (3 views per physical sample)
- Front (1st render, ID%3=1): CORRUPTED
- Top (2nd render, ID%3=2): CLEAN
- Left (3rd render, ID%3=0): CORRUPTED
- 100% consistent across all 7 levels
- **1249 of 1873 samples affected**

### Corruption Details

- Normal depth range: 5-8m (S1 orthographic) or 5-11m (S2 perspective)
- Corrupted pixels: ~1e10 (Blender far-clipping-plane value, NOT inf/nan)
- In corrupted samples, ~64% of pixels are invalid (background), ~36% valid (object+ground)
- RGBA and segmentation outputs are NOT affected — only depth

## Bug: Docker OOM Kill

WSL2 instance has only 7.4GB RAM + 2GB swap. Blender rendering consumes ~1.6GB physical memory per container. At 17:18:01 on 2026-05-22, the OOM killer terminated the Docker container mid-generation, also killing 7 system services. Swap was 100% full.

```text
dmesg: Out of memory: Killed process 1334096 (python3)
  total-vm:8020356kB (~7.6GB), anon-rss:1716644kB (~1.6GB)
  container: docker-f6670b5e...
```

**Impact**: S2 L7/215 is an empty directory (created by `make_dirs()` but rendering never completed). 214 of 215 L7 samples are complete.

**Prevention**: Close memory-heavy processes before running, or increase WSL2 memory via `.wslconfig`.

## Bug: S2 L6 Sphere Ground Penetration

PyBullet physics simulation allows spheres to penetrate the ground plane at high speeds.

- Total sphere samples in L6: 324
- Penetrating ground (z_final < 0): **33 (10.2%)**
- Worst case: L6/139 z_final = -2.94m
- Pattern: high speed + small radius (0.18) + pure sliding (rolling=0)

```text
L6/103: z_final=-1.79  (radius=0.18, speed=2.0, rolling=0.0)
L6/13:  z_final=-2.77  (radius=0.18, speed=2.5, rolling=0.0)
L6/139: z_final=-2.94  (radius=0.18, speed=3.0, rolling=0.0)
```

## What's Correct

- **Segment masks**: Shape (128,128), uint8, values {0,1}, no overlap between objects
- **Mask alignment**: Verified via visual overlay — masks correctly cover rendered objects
- **Metadata**: video.json, object_static.json, object_dynamicjson all consistent
- **Frame completeness**: All 36 frames present per sample with correct frame_num
- **PNG renderings**: 128x128 RGB, present for every frame
- **MP4 videos**: Present for every sample (except S2 L7/215)
- **Physics motion**: S2 cubes slide correctly on ground; S1 spheres fall correctly
- **visible_area**: Matches segment mask pixel count in all checked samples
- **time field**: Consistent with (frame_num-1)/fps

## Validation Thresholds

```python
DEPTH_MAX_REASONABLE = 100  # meters, for typical scene scale
DEPTH_FAR_PLANE = 1e9       # values above this are Blender artifacts
MASK_EXPECTED_VALUES = {0, 1}
EXPECTED_FRAMES = 36
EXPECTED_RESOLUTION = (128, 128)
```
