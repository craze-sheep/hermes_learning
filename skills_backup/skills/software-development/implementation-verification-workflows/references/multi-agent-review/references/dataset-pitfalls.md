# Physics Video Dataset Implementation Pitfalls

## Data Format Surprises

1. **Frame image naming varies**: Some samples use `{frame_id}.png`, others use `1.png`. Try both.
2. **Force matrix JSON structure**: Not `{"obj1_obj2": [x,y,z]}` but `{"object_order": [1,2], "force_matrix": [[null, ...]]}`. Check for `force_matrix` key.
3. **31880 samples**: Scanning takes 15s+. Use pickle cache with root_dir validation.

## Object Type Encoding

- 4 types: ground(0), sphere(1), box(2), cylinder(3)
- One-hot encoding, NOT sequential integers
- Silent truncation if type not in map (bad for debugging)

## Normalization Strategy

- RGB: /255 then (x-0.5)/0.5
- Position/velocity/force: fixed std values as placeholder
- Quaternion: do NOT normalize (keep unit quaternion)

## Sliding Window

- 36 frames total, use history=12, predict=12
- stride=6 gives good data augmentation
- Random start for train, fixed start=0 for val/test
