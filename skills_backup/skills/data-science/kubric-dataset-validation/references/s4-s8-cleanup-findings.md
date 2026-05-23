# S4-S8 Code Cleanup Findings (2026-05-23)

## S4 First-Sample Structure Check
- S4/L1/1 generated successfully after removing physics_labels.json
- 8 file types matching task5 spec exactly, no extra files
- 3 objects per sample (ground + sphere + wall): 3 dynamicjson + 3 segment per frame
- Syntax check passed on all 5 modified scripts (S4-S8)

## Codex Evaluation: No Further Removable Code in S4-S7
Functions that look physics-label-related but serve other outputs:

| Function | Used By |
|----------|---------|
| `simulate_and_keyframe()` → `frame_states` | `object_dynamicjson/{id}.json` (position/velocity/quaternion/angular_velocity) |
| `simulate_and_keyframe()` → `force_payloads` | `force_matrix.json` + `resultant force` in dynamicjson |
| `zero_force_matrix()`, `add_force()`, `average_force_matrix()` | Same as above |
| `level_name`, `subtask`, `main_variable` in SampleSpec | Written into `video.json` |

Conclusion: physics_labels.json removal is clean — no orphaned code remains.
