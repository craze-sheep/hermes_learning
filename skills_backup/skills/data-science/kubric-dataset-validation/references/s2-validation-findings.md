# S2 Validation Findings (2026-05-23)

## File Completeness
- L1-L4: 240 samples each (80 physical × 3 views) ✅
- L5-L7: 360 samples each (120 physical × 3 views) ✅
- Total: 2160 samples, all files present
- Each sample: 5 top-level files + 36 frames × 6 files = 221 files

## Depth Map
- Foreground (depth < 1e9): range 5.5~16.1m — correct for camera at (0, -7.5, 3.2)
- Background (depth ≥ 1e9): ~1e10 sentinel, 1429 unique values
- No transition artifacts (0 pixels between 20m and 1e9m)
- Depth varies across frames (31 pixels differ in L1, 115 in L6) ✅

## Segmentation Masks
- Strict 0/1 values ✅
- Pixel counts: cube ~20px, sphere ~76px, cylinder ~44px (at 128×128)
- Object center tracks physical motion ✅
- Ground mask: 36~58% depending on view

## Physics: Objects Still Moving at End (3s)

| Level | Not Stopped | Worst Speed | Severity |
|-------|------------|-------------|----------|
| L1-L3 | 0/720 | — | ✅ |
| L4 | 6/240 (2.5%) | 0.021 m/s | negligible |
| L5 | 3/360 (0.8%) | 0.022 m/s | negligible |
| L6 | 117/360 (32.5%) | 2.14 m/s | ⚠️ sphere rolling |
| L7 | 84/360 (23.3%) | 7.16 m/s | ⚠️ lying cylinder |

Root cause: 3-second simulation insufficient for rolling friction scenarios. Not a code bug.

## physics_labels.json Structure
- Summary-level (NOT per-frame), ~986 lines per file
- 90% of bulk is `contact_pair_sequence` (36 entries) and `wall_contact_sequence` (36 entries)
- Per-frame physics data is in `dynamic/{frame}/object_dynamicjson/{obj_id}.json`
