# S8 Collision Fixes (2026-05-24)

S8 (泛化样本) requires `no_dynamic_collision` — objects must NOT collide. Multiple levels had systematic collision failures.

## Levels Fixed

| Level | Mechanism | Problem | Fix |
|-------|-----------|---------|-----|
| L2 | temporal_separation | distance = 1.8 + i * 0.35 * speed, time gap too small | Changed to i * 1.5 * speed |
| L3 | speed_difference | head-on crossing paths collide | Removed head-on paths, raised crossing speed floor |
| L5 | blocked_by_obstacle | obstacle lanes not actually blocking | Separated lanes properly |
| L7 | height_separation | height spacing too small, convergence speed too high | Increased z spacing, reduced convergence |
| L10 | near_miss | lateral offset too small | Widened offsets |
| L11 | rotation_miss | rotation not enough to avoid contact | Widened spacing |
| L12 | external_impulse | impulse too weak to deflect | Stronger lateral impulse, farther start positions |

## Verification

- Codex ran 1200-candidate collision scan after fixes: 0 collisions on modified levels
- Full Kubric simulation confirmed: S8 L2 passing no_dynamic_collision filter during actual generation
- All fixes were parameter-only (no structural changes)

## Key Insight

S8's collision filter runs `compute_physics_labels` after PyBullet simulation. If `dynamic_dynamic_contact_count > 0`, the candidate is rejected. With 1200 candidates and low pass rates, levels can exhaust all candidates without producing enough samples. Always verify collision rates before committing to a full generation run.
