# Kubric / Blender Rendering Bugs

## Multi-View Renderer Reuse → Corrupted Depth

**Symptom**: When a single `Blender` renderer instance is reused across multiple camera views (by switching `scene.camera` in a loop), non-primary views produce depth maps where ~64% of pixels contain the far-clip-plane value (~1e10).

**Affected**: All views except the 2nd render (which coincidentally works because Blender reinitializes some internal state between the 1st and 2nd call).

**Pattern detection**:
- S1 (2 views: front, top): odd IDs bad, even IDs good
- S2 (3 views: front, top, left): ID%3==2 good, others bad
- The "good" view is always the 2nd one rendered, regardless of which camera it is

**Root cause**: `render_view()` only switches `scene.camera` and `renderer.scratch_dir`, doesn't reinitialize the Blender depth pass buffer.

**Fix**: Create a new `Blender()` instance per view inside the loop:
```python
for view_name, output_sample, sample_dir in view_outputs:
    renderer = Blender(scene, scratch_root / f"blender_{view_name}", ...)
    rendered = render_view(scene, renderer, cameras[view_name], ...)
```

**Impact**: 50% (S1) to 67% (S2) of all depth maps corrupted.

**Segment masks are NOT affected** — only the depth pass has this bug.

## Kubric Cylinder Class

`kb.Cylinder` exists in the Docker image (`kubricdockerhub/kubruntu`). API:
```python
kb.Cylinder(scale=(radius, radius, height / 2.0), **kwargs)
```
Note: `height/2.0` because Kubric uses half-extents for scale (like Cube).

## PyBullet Ground Penetration

**Symptom**: Small-radius spheres at high speed with zero rolling friction can penetrate the ground plane (z_final < 0, sometimes -2 to -3m).

**Affected configs**: radius=0.18, speed≥2.0, rolling_friction=0.0

**Workaround**: Increase rolling friction, reduce speed, or increase sphere radius. For production, use PyBullet's CCD (continuous collision detection):
```python
client.setPhysicsEngineParameter(enableCcd=1)
```

## Blender Background / Far-Clip Depth Values

Blender's depth pass returns the far-clip distance for pixels with no geometry. In Kubric's default setup, this is ~1e10. When validating depth maps:
- Count pixels > 1000 as "background"
- Valid scene depth is typically 5-12m for tabletop setups
- Background pixels are NOT bugs per se — they're expected for perspective views where not all pixels have geometry

For orthographic top views of flat scenes, all pixels should have valid depth (no background).

## Container OOM Kill During Generation

**Symptom**: Docker container with `--rm` dies silently. Some sample directories exist but are completely empty (0 files), or have partial data.

**Root cause**: Blender rendering + system memory pressure → Linux OOM killer terminates the container's python process.

**Detection**:
```bash
dmesg -T | grep "Out of memory.*docker"
```

Look for: `Out of memory: Killed process ... (python3)` with `task_memcg=/system.slice/docker-*.scope`

**Prevention**:
- Close VSCode Server and other memory-heavy processes before running
- Set `.wslconfig` with adequate memory (12GB for 16GB host)
- Add swap (4-8GB on NVMe SSD)
- Use `--samples-per-level` to run smaller batches

**Recovery**: Empty directories are created by `make_dirs()` before rendering starts. Re-run with `--overwrite` and `--start_id` pointing to the first failed sample.
