# Blender Renderer Depth Pass Bug — Root Cause & Fix

## Bug Description

When a single `Blender` renderer instance is reused to render multiple camera views of the same scene, the depth output is corrupted for all renders except the 2nd one. The corruption manifests as ~64% of pixels having values around 1e10 (Blender's far clipping plane), while only ~36% retain valid depth values (the actual objects and ground).

## Evidence

### S1 (2 views: front, top)
- Pattern: ALL odd-ID samples corrupted, ALL even-ID samples clean
- 50% corruption rate (800/1600 samples)
- Front view (1st render, odd ID): CORRUPTED
- Top view (2nd render, even ID): CLEAN

### S2 (3 views: front, top, left)
- Pattern: Only ID%3==2 (top, 2nd render) is clean
- 67% corruption rate (1249/1873 samples)
- Front (1st render, ID%3=1): CORRUPTED
- Top (2nd render, ID%3=2): CLEAN
- Left (3rd render, ID%3=0): CORRUPTED

### Corruption Details
- Bad depth values: ~1.0e10 to ~1.2e10 (Blender far plane)
- Valid depth range: 5-8m (orthographic) or 5-11m (perspective)
- The ~36% valid pixels correspond to actual objects/ground visible in frame
- RGBA and segmentation outputs are NOT affected — only depth

## Root Cause

In `generate_physical_sample()`:
```python
# ONE renderer created for ALL views
renderer = Blender(scene, scratch_root / f"blender_{args.views[0]}", ...)

for view_name, output_sample, sample_dir in view_outputs:
    rendered = render_view(scene, renderer, cameras[view_name], ...)
```

In `render_view()`:
```python
scene.camera = camera                              # camera switches OK
renderer.scratch_dir = scratch_root / f"blender_{view_name}"  # dir switches OK
frames = renderer.render(return_layers=("rgba", "depth", "segmentation"))
# depth output is CORRUPTED for non-2nd renders
```

The Blender renderer's internal state (likely the depth compositing node tree or the depth pass buffer) is not fully reinitialized when switching cameras. Only the 2nd render happens to get a clean depth pass — possibly because the first render "warms up" the compositing pipeline.

## Fix

**Option A — New renderer per view (recommended, cleanest):**
```python
for view_name, output_sample, sample_dir in view_outputs:
    renderer = Blender(
        scene,
        scratch_root / f"blender_{view_name}",
        adaptive_sampling=True,
        use_denoising=True,
        samples_per_pixel=args.samples_per_pixel,
    )
    rendered = render_view(scene, renderer, cameras[view_name], ...)
```

**Option B — Dummy render to prime the pipeline:**
```python
# Before the view loop, do a throwaway render to "warm up" the depth pass
dummy_camera = cameras[args.views[0]]
scene.camera = dummy_camera
renderer.render(return_layers=("depth",))  # prime the pipeline
# Then proceed with the real loop
```

Option A is preferred — it's cleaner and avoids any residual state issues.

## Files Affected
- `generate_s1_dataset.py` (line ~809-832)
- `generate_s2_dataset.py` (line ~910-932)
- `generate_s3_dataset.py` through `generate_s8_dataset.py` (same pattern)

## Verification After Fix
```python
# Re-check a few samples: ALL depth maps should have max < 100
d = np.load("{id}.npz")["depth"]
assert d.max() < 100, f"Depth still corrupted: max={d.max()}"
```
