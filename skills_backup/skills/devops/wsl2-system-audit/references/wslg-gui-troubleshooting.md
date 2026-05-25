# WSLg GUI Application Troubleshooting — Case Studies

## Case: cc-switch window invisible (2026-05-25)

### Symptoms
- cc-switch (Tauri app with WebKitGTK) launches successfully
- Logs show "正常启动模式：主窗口已显示"
- No window visible on Windows desktop
- `xdotool search --name ""` returns 0 windows

### Errors in app output
```
MESA: error: ZINK: failed to choose pdev
libEGL warning: egl: failed to create dri2 screen
libEGL warning: failed to get driver name for fd -1
libEGL warning: MESA-LOADER: failed to retrieve device information
Gtk-CRITICAL: gtk_widget_get_scale_factor: assertion 'GTK_IS_WIDGET (widget)' failed
```

### Root cause
WSLg shared memory corruption. Weston log:
```
rdp_allocate_shared_memory: Failed to open "/mnt/shared_memory/{UUID}" with error: Input/output error
```
This repeated for every frame the app tried to render.

### What didn't work (wasted time)
1. `LIBGL_ALWAYS_SOFTWARE=1` — no effect (issue isn't GL rendering)
2. `GALLIUM_DRIVER=llvmpipe` — no effect
3. `MESA_LOADER_DRIVER_OVERRIDE=d3d12` — no effect
4. `WEBKIT_DISABLE_COMPOSITING_MODE=1` — no effect
5. `GDK_BACKEND=x11` — no effect

### What worked
```powershell
# Windows PowerShell
wsl --shutdown
# Then reopen WSL terminal and relaunch cc-switch
```

### When you can't do `wsl --shutdown`
If the user has running services (Docker containers, Hermes gateway, long-running jobs) and can't restart WSL:
- There is **no workaround** — shared memory corruption requires a full WSLg restart
- Tell the user the root cause and let them decide when to restart
- Don't keep trying rendering env vars — they won't help
- Clean up any temp scripts or config changes you made during debugging

### Key lesson
**Always check `/mnt/wslg/weston.log` FIRST** when GUI apps are invisible. The rendering environment variables are red herrings when the compositor's shared memory is broken.

### Diagnostic checklist (fast path)
```bash
# 1. Is Weston running and healthy?
tail -20 /mnt/wslg/weston.log | grep -i "error\|fail"

# 2. Are display sockets present?
ls -la /tmp/.X11-unix/X0 $XDG_RUNTIME_DIR/wayland-0

# 3. Is /dev/dxg present? (D3D12 device)
ls -la /dev/dxg

# 4. Can Weston allocate shared memory?
grep "rdp_allocate_shared_memory" /mnt/wslg/weston.log | tail -5
```

## Environment Reference

Typical healthy WSLg environment:
```
/dev/dxg                    → D3D12 device (EXISTS)
/dev/dri                    → should NOT exist (WSLg uses D3D12, not DRM)
/tmp/.X11-unix/X0           → X11 socket
$XDG_RUNTIME_DIR/wayland-0  → Wayland socket (symlink to /mnt/wslg/runtime-dir/)
/mnt/wslg/weston.log        → Weston compositor log
/mnt/wslg/runtime-dir/      → Wayland runtime
```

Available Mesa drivers for WSLg:
```
d3d12_dri.so    → Primary driver (uses /dev/dxg)
swrast_dri.so   → Software fallback (slow)
kms_swrast_dri.so → KMS software fallback
```
