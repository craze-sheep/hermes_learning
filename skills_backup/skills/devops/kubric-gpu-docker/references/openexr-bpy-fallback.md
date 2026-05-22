# OpenEXR Bypass: Use Blender's OpenImageIO

## Problem
pip OpenEXR (3.4.x) segfaults with Blender 3.6 due to Iex ABI mismatch (3.1 vs 3.0).
`OpenEXR.cpython-310-x86_64-linux-gnu.so: undefined symbol: _ZN7Iex_3_113throwErrnoExcERKSs`

## Solution
Blender 3.6 bundles OpenImageIO 2.4.15 (`import OpenImageIO` works inside Blender's Python).

## Patched code in `kubric/renderer/blender_utils.py`

### 1. Import guard
```python
try:
  import OpenEXR
  import Imath
except ImportError:
  OpenEXR = None
  Imath = None
```

### 2. EXR reader using OpenImageIO
```python
def _read_exr_with_bpy(filename):
  import OpenImageIO as oiio
  inp = oiio.ImageInput.open(str(filename))
  if not inp:
    raise IOError(f"Cannot open EXR: {filename}")
  spec = inp.spec()
  w, h = spec.width, spec.height
  n_channels = spec.nchannels
  channel_names = [spec.channel_name(i) for i in range(n_channels)]
  px = inp.read_image(0, 0, 0, n_channels, "float")
  inp.close()
  return np.array(px, dtype=np.float32).reshape(h, w, n_channels), w, h, n_channels, channel_names
```

### 3. Dispatch in get_render_layers_from_exr
```python
def get_render_layers_from_exr(filename):
  if OpenEXR is None:
    return _get_render_layers_from_exr_bpy(filename)
  return _get_render_layers_from_exr_openexr(filename)
```

### 4. Channel name mapping (replaces positional indexing)
```python
def _get_render_layers_from_exr_bpy(filename):
  px, w, h, nch, ch_names = _read_exr_with_bpy(filename)
  ch_map = {name: i for i, name in enumerate(ch_names)}
  output = {}
  # Map by name: "Image.R", "Depth.V", "Vector.R", "Normal.X", etc.
  # See kubric-gpu-docker SKILL.md for full channel list
```

### 5. Type annotation fix
```python
# OLD: def read_channels_from_exr(exr: OpenEXR.InputFile, ...)
# NEW: def read_channels_from_exr(exr, ...)
```

## Kubric multilayer EXR channel names
- Image.R, Image.G, Image.B, Image.A (RGBA, float32)
- Depth.V (single channel, float32, 1e10 = background/infinity)
- Vector.R, Vector.G, Vector.B, Vector.A (optical flow)
- Normal.X, Normal.Y, Normal.Z
- UV.X, UV.Y, UV.Z
- CryptoObject00.R, CryptoObject00.G, ... (segmentation indices + alphas)
- ObjectCoordinates.R, .G, .B
