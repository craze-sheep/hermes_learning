# Spec-vs-Code Compliance Checklist

Systematic methodology for verifying generated code matches design/spec docs.
Developed for physics simulation dataset scripts but generalizes to any
config-driven code generation.

## Layer 1: Global Parameters (fast, catches ~20% of issues)

Check these first — they're quick and catch copy-paste errors:

- [ ] Resolution / dimensions match spec
- [ ] Frame rate / timing parameters match
- [ ] Gravity / physics constants match
- [ ] Camera/view configurations match spec AND dict syntax is valid
- [ ] Sample count targets (LEVEL_TARGETS or equivalent) match spec
- [ ] Ground/base object dimensions match spec

## Layer 2: Structure (catches ~30% of issues)

- [ ] Number of levels/modules matches spec (count `if/elif level_id ==`)
- [ ] Level names/descriptions match spec section headers
- [ ] Object types used in each level match spec (sphere/cube/cylinder/etc)
- [ ] VIEWS/config dict has no nested structure bugs (check closing braces)

### Common Python dict nesting bug
```python
# BUGGY — "back" is nested inside "front"'s value:
VIEWS = {
    "front": {
        "type": "Perspective",
        ...
    "back": {        # <-- this is INSIDE front's dict!
        ...
    },
},                    # <-- this closes front, not VIEWS
    "top": {          # <-- this is a new statement, not a dict entry
```

```python
# CORRECT:
VIEWS = {
    "front": {
        "type": "Perspective",
        ...
    },
    "back": {
        ...
    },
    "top": {
        ...
    },
}
```

## Layer 3: Parameter Values (catches ~40% of issues)

For each level/module, verify specific parameter values:

- [ ] Numeric ranges match (sizes, radii, masses, speeds, angles)
- [ ] Friction/restitution values match
- [ ] Initial positions match (including derived positions like z=radius+clearance)
- [ ] Initial velocities match
- [ ] Quaternion/rotation values match
- [ ] Color/material pools match AND are actually varied (not hardcoded to one)

### Color coverage pitfall
Spec says `color: [red, blue, yellow, green]` but code may hardcode one:
```python
# BAD — only uses brown, never gray
ramp = ramp_spec(..., color_name="brown")
# GOOD — varies color
ramp = ramp_spec(..., color_name=next(color_cycle))
```

### Quaternion composition pitfall
Spec says `lying_quat = ramp_quat * [0.7071, 0, 0.7071, 0]` but code may skip:
```python
# BAD — just uses ramp quaternion for all orientations
quat = (math.cos(half_a), 0.0, math.sin(half_a), 0.0)
# GOOD — composes quaternions
lying = quaternion_multiply(ramp_quat, (0.7071, 0, 0.7071, 0))
```

## Layer 4: Derived Labels / Post-processing (catches ~10% of issues)

Often completely missing from generated code:

- [ ] Spec-defined labels are computed (e.g., stop_time, travel_distance)
- [ ] Labels are saved to output files (not just computed but discarded)
- [ ] Filtering logic matches spec (e.g., "only keep samples where contact occurred")

## Layer 5: Sampling Strategy (subtle, high-value)

- [ ] Primary variables are uniformly/balanced sampled
- [ ] Irrelevance-test variables use paired sampling (not independent random)
- [ ] Boundary values are included in sampling
- [ ] Full Cartesian products where spec requires them (e.g., 3x3 restitution pairs)
- [ ] Sampling weights match spec if specified (e.g., "0.0 weight 10%, 0.3 weight 20%")

## Cross-Review Comparison Template

When using multi-agent review, organize findings as:

| Issue | Hermes | Claude Code | Codex | Confidence |
|-------|--------|-------------|-------|------------|
| {description} | ✓/✗ | ✓/✗ | ✓/✗ | HIGH/MED/LOW |

- **HIGH** (all 3 agree): Almost certainly real
- **MEDIUM** (2/3 agree): Likely real, worth fixing
- **LOW** (1/3 only): May be false positive, verify manually
