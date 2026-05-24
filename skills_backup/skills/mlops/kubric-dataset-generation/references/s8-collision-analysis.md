# S8 Multi-Level Collision Analysis

## Problem

S8 (泛化样本) generates negative samples where objects must NOT collide (`no_dynamic_collision` filter). Multiple levels had insufficient spacing parameters, causing systematic collision and 100% rejection rate.

## Affected Levels

| Level | Mechanism | Root Cause | Fix |
|-------|-----------|------------|-----|
| L2 | temporal_separation | `distance = 1.8 + i * 0.35 * speed` — time gap only 0.35s | Changed to `i * 1.5 * speed` |
| L3 | speed_difference (crossing) | Head-on crossing paths at origin | Removed head-on paths, increased speed lower bound |
| L5 | blocked_by_obstacle | Obstacle lanes not actually blocking | Separated lanes properly |
| L7 | height_separation | Z spacing too small, convergence speed too high | Increased height spacing, reduced convergence |
| L10 | near_miss | Lateral offset too small for tiny spheres | Widened lateral offsets |
| L11 | rotation_miss | Rotation not sufficient to avoid contact | Widened spacing |
| L12 | external_impulse | Impulse too weak to redirect objects | Stronger lateral impulse, farther start positions |

## Unaffected Levels

- L1 (spatial_separation): Lane spacing 0.60m ≥ 2×radius, safe
- L4 (random_space): Has `initial_clearance ≥ 0.18` check
- L6 (friction_stop): Objects 3.2m apart, friction stops them
- L8 (shielded_by_object): Three spheres same speed same direction
- L9 (boundary_bounce): Different angles, bouncing dynamics
- L13 (static_multi_object): Has `clearance ≥ 0.18` check
- L14 (outward_separation): Radial outward motion

## Verification Method

Codex ran a PyBullet collision scan with 1200 candidates per level. After fixes, changed levels showed 0 modeled collisions. Full Kubric simulation needed for final validation.

## Lesson Learned

When designing "near miss" or "non-collision" scenarios in physics simulation, always verify with actual simulation — geometric analysis alone is insufficient because:
1. Object rotation during motion changes effective radius
2. Multiple objects on convergent paths have non-linear collision dynamics
3. Small margin errors compound when objects are near the collision threshold
