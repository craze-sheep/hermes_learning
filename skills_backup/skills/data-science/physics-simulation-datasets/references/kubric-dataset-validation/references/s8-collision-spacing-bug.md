# S8 Multi-Level Collision Spacing Bug

## Summary

S8 (泛化负样本) requires `no_dynamic_collision` — objects must NOT collide during simulation. Multiple levels had insufficient spacing parameters, causing systematic collision filter failures (all candidates rejected).

## Affected Levels

| Level | Mechanism | Root Cause | Fix |
|-------|-----------|------------|-----|
| L2 | temporal_separation | `distance = 1.8 + i * 0.35 * speed` — time gap only 0.35s | Changed to `i * 1.5 * speed` (1.5s gap) |
| L3 | speed_difference (crossing) | Head-on crossing paths collided | Removed head-on paths, increased crossing speed lower bound |
| L5 | blocked_by_obstacle | Obstacle lanes didn't actually block paths | Separated lanes properly |
| L7 | height_separation | Insufficient z-spacing + inward convergence speed | Increased height spacing, reduced convergence speed |
| L10 | near_miss | Lateral offsets too small for near-miss | Widened offsets |
| L11 | rotation_miss | Rotation didn't create enough separation | Widened spacing |
| L12 | external_impulse | Impulse too weak to avoid collision | Stronger lateral impulse, farther start positions (1.4→1.8) |

## Unaffected Levels

L1 (spatial separation, lane spacing sufficient), L4 (random with clearance check), L6 (friction stop, 3.2m gap), L8 (shield, same speed same direction), L9 (boundary bounce, different angles), L13 (all static), L14 (outward separation).

## Detection

When `candidate_count` (typically 1200 = target×10) generates 0 accepted samples, the filter is rejecting everything. Check `dynamic_dynamic_contact_count` in the error message:

```
filtered S8/L{N} candidate {M}: dynamic_dynamic_contact_count=1
```

If ALL candidates show contact_count=1+, the level's spacing parameters are systematically too small — randomization won't help.

## Verification Approach

Codex ran a geometric analysis + PyBullet collision scan (not full Kubric rendering) to verify fixes. The scan:
1. Generates candidate samples with the fixed parameters
2. Runs `simulate_and_keyframe` + `compute_physics_labels`
3. Checks `no_dynamic_collision` flag

Full Kubric rendering verification still needed — geometric analysis can miss edge cases where gravity/rotation brings objects together.

## Key Parameters for S8 Levels

When designing "objects that don't collide" scenarios:
- **Time separation**: arrival gap should be ≥ `2 * radius / speed` (diameter crossing time)
- **Spatial separation**: lane gap should be ≥ `2 * max_radius + margin`
- **Height separation**: z-gap should account for gravity pulling objects down during simulation
- **Friction stop**: ensure stopping distance < initial gap
- **Impulse deflection**: impulse must change trajectory enough before objects reach crossing point

## Status

✅ Fixed by Codex (parameter adjustments). Pending full Kubric rendering verification.
