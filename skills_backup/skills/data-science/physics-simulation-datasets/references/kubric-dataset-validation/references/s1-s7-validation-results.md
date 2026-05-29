# S1-S7 Validation Results (May 2026)

## Summary

| Metric | Result |
|--------|--------|
| Total samples checked | 26,708 (S1/S2/S4/S5/S6/S7) |
| Total errors | 0 (after correcting file naming bugs in v1 script) |
| Total warnings | 64 (segmentation all-zero in final frames) |
| Cross-view consistency | 5,580 physical events, 0 errors |
| Depth map issues | 0 |
| JSON structure issues | 0 |

## File Completeness

All samples complete except S3/L1/6 (only has `dynamic/` dir, missing mp4/npz/video.json/object_static.json).

## Segmentation All-Zero Pattern

64 warnings, all in final frames (frame 32/36) of last dynamic object:
- Only affects `object_segment/{last_obj_id}.npz`
- Object leaves camera view near end of 3s simulation
- More prevalent with more objects (S7/L10: 45 occurrences)
- S1 unaffected (2 objects, simple geometry)
- **NOT a bug** — expected physics simulation boundary

## Cross-View Consistency

All 5,580 events passed. Checked:
- object_static.json (mass, size, friction, color, etc.)
- dynamic first/mid/last frame (position, velocity, angular_velocity)
- View name uniqueness per event

## Object Types per Scene

| Scene | Objects | Types |
|-------|---------|-------|
| S1 | 2 | ground + cube/sphere |
| S2 | 2 | ground + cube/sphere |
| S4 | 3 | ground + ramp + sphere/cube |
| S5-S6 | 3 | ground + 2 dynamic |
| S7 | 4-6 | ground + wall + spheres (L10 variable) |

## Validation Script Issues (v1 → v2)

v1 script had two bugs causing false positives:
1. Checked for `1.mp4` / `1.npz` instead of `{id}.mp4` / `{id}.npz`
2. Checked for `shape`/`position` keys in object_static.json (actual keys: `object_type`/`size`/`mass`)
3. Checked depth shape == (128,128) instead of (36,128,128)

v2 corrected all three. Always use the v2 script.
