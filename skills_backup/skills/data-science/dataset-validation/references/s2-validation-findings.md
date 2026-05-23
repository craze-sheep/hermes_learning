# S2 Validation Findings (2026-05-23)

## Summary
S2 (horizontal sliding) dataset: 7 levels, 2160 total samples. File completeness and JSON structure fully correct. Two notable findings: background depth values and physics stopping time.

## File Completeness
All 2160 samples have all expected files (mp4, npz, video.json, object_static.json, physics_labels.json, 36 frames × 6 files each = 221 files/sample).

## Depth Map Analysis

### Background depth (~10^10 m) is EXPECTED
- Front view: 63.3% background pixels, 36.7% foreground (5.5~11.8m)
- Top view (orthographic): 100% foreground, no background
- Left view: 41.8% background, 58.2% foreground (4.5~16.1m)
- Clean separation: 0 pixels in 20m~1e9m transition zone
- Depth varies across frames (not static): L1 has 31 pixel changes between frames
- Background values aren't all identical: 1429 unique values due to z_to_depth pixel-level scaling (see `codex-depth-analysis.md`)

### Foreground depth ranges
- Front: 5.52~11.79m (camera at y=-7.5, z=3.2)
- Top: 7.76~8.00m (orthographic, ~8m height)
- Left: 4.51~16.09m

## Segmentation Mask Analysis

### Object pixel counts (128×128 resolution)
| Level | Object | Pixels/frame | Notes |
|-------|--------|-------------|-------|
| L1-L4 | cube 0.24m | 20~25 | Expected: ~30×30 proj, visible face ~20px |
| L5 | cube 0.24m | 20~25 | Same cube, different velocity directions |
| L6 | sphere | 74~83 | Larger projection than cube |
| L7 | cylinder | 42~47 | Between cube and sphere |

### Mask tracking quality
- L1 cube: center moves 6.3 pixels over 36 frames (0.4m travel)
- L3 cube: center moves 11.6 pixels (larger travel distance)
- L6 sphere: center moves 58.5 pixels (rolling, long distance)
- Mask pixel count varies ±2-9 per frame (rotation/perspective changes)

## Physics Stopping Time

### is_static_at_end threshold: linear_speed < 0.05 AND angular_speed < 0.1

| Level | Not stopped / Total | Worst speed | Severity |
|-------|-------------------|-------------|----------|
| L1-L3 | 0/720 | — | ✅ OK |
| L4 | 6/240 (2.5%) | 0.021 m/s | Marginal |
| L5 | 3/360 (0.8%) | 0.022 m/s | Marginal |
| L6 | 117/360 (32.5%) | 2.14 m/s | ⚠️ Significant |
| L7 | 84/360 (23.3%) | 7.16 m/s | ⚠️ Significant |

### L6 breakdown (sphere rolling)
- pure_sliding_to_rolling_transition: 66 samples, 0.29~2.14 m/s
- near_rolling_to_rolling_transition: 51 samples, 0.08~1.29 m/s

### L7 breakdown (cylinder sliding)
- lying_axis_x: 39 samples, 0.12~7.16 m/s (worst)
- lying_axis_y: 42 samples, 0.02~1.33 m/s
- upright: 3 samples, 0.02 m/s (marginal)

### Root cause
3-second simulation (36 frames @ 12fps) insufficient for objects with low rolling friction. Not a code bug.

## travel_distance statistics
| Level | Range | Mean |
|-------|-------|------|
| L1 | 0.33~1.35m | 0.70m |
| L2 | 0.08~1.52m | 0.58m |
| L3 | 0.10~1.52m | 0.68m |
| L4 | 0.08~1.14m | 0.44m |
| L5 | 0.23~1.06m | 0.55m |
| L6 | 0.68~6.44m | 2.32m |
| L7 | 0.38~3.96m | 1.14m |
