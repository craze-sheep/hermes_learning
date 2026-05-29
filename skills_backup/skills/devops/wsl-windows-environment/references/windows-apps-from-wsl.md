---
name: windows-apps-from-wsl
description: Install, run, and manage Windows GUI applications from WSL. Covers NSIS/Inno installers, process management, screenshots, and UNC path pitfalls.
triggers:
  - installing Windows software from WSL
  - running .exe installers in WSL
  - NSIS silent install
  - extracting NSIS/Inno Setup installers
  - taking Windows screenshots from WSL
  - managing Windows processes from WSL
---

# Windows Apps from WSL

Install and manage Windows desktop applications from WSL2 without needing physical access to the Windows desktop.

## Prerequisites

- WSL2 with Windows interop enabled (default in modern WSL)
- `p7zip-full` for extracting installers: `sudo apt install p7zip-full`
- PowerShell accessible as `powershell.exe`

## Installing NSIS Installers (Silent Mode)

NSIS (Nullsoft Scriptable Install System) is the most common Electron app installer format.

### Detect NSIS

```bash
strings installer.exe | grep -i "Nullsoft.NSIS"
# or
file installer.exe  # shows "PE32 executable"
```

### Silent Install Flags

```bash
# /S = silent, /D=path = install directory (NO quotes, MUST be last arg)
powershell.exe -Command "Start-Process 'D:\installer.exe' -ArgumentList '/S /D=D:\InstallDir' -Wait"
```

**Critical NSIS `/D=` rules:**
- Path must be **immediately** after `/D=` with NO space
- Path must NOT be quoted
- `/D=` must be the **last** argument on the command line
- Use `Start-Process -Wait` to block until install completes

### If Silent Install Fails → Extract Manually with 7z

```bash
sudo apt install p7zip-full

# Extract outer NSIS wrapper
7z x installer.exe -o/tmp/installer_extract -y

# The actual app is usually in $PLUGINSDIR/app-64.7z (or app-32.7z)
7z x /tmp/installer_extract/\$PLUGINSDIR/app-64.7z -o/TargetDir -y

# Cleanup temp NSIS files
rm -rf /tmp/installer_extract/\$PLUGINSDIR /tmp/installer_extract/\$R0
```

After manual extraction, run the installer properly to create shortcuts/registry:
```bash
# Re-run with silent install pointing to same dir (will register shortcuts)
powershell.exe -Command "Start-Process 'D:\installer.exe' -ArgumentList '/S /D=D:\TargetDir' -Wait"
```

## Running Windows GUI Apps from WSL

### Launch with Correct Working Directory

**⚠️ PITFALL: UNC path error.** WSL's current directory maps to `\\wsl.localhost\...` which `cmd.exe` doesn't support. Always set a Windows working directory:

```bash
# ❌ Hangs with "UNC paths are not supported"
cmd.exe /c "start D:\App\app.exe"

# ✅ Set Windows working directory first
powershell.exe -Command "Set-Location 'D:\App'; Start-Process '.\app.exe' -WorkingDirectory 'D:\App'"
```

Or use `workdir` parameter in terminal tool:
```bash
# terminal(workdir="/mnt/d") and then run from there
```

### Check if App is Running

```bash
tasklist.exe 2>/dev/null | grep -i "appname"
# or
ps aux | grep -i "appname" | grep -v grep
```

### Kill Windows Processes from WSL

```bash
taskkill.exe /F /IM "appname.exe" 2>/dev/null
# or
pkill -f "appname" 2>/dev/null
```

## Taking Windows Screenshots from WSL

```powershell
powershell.exe -Command "
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
\$screen = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds
\$bitmap = New-Object System.Drawing.Bitmap(\$screen.Width, \$screen.Height)
\$graphics = [System.Drawing.Graphics]::FromImage(\$bitmap)
\$graphics.CopyFromScreen(\$screen.Location, [System.Drawing.Point]::Empty, \$screen.Size)
\$bitmap.Save('D:\screenshot.png')
\$graphics.Dispose()
\$bitmap.Dispose()
"
```

Then view with `vision_analyze(image_url='/mnt/d/screenshot.png')`.

## Path Translation Cheat Sheet

| Windows | WSL |
|---------|-----|
| `D:\` | `/mnt/d/` |
| `C:\Users\<user>\` | `/mnt/c/Users/<user>/` |
| `%LOCALAPPDATA%` | `/mnt/c/Users/<user>/AppData/Local/` |
| `%APPDATA%` | `/mnt/c/Users/<user>/AppData/Roaming/` |

## Linux GUI Apps in WSL (Tauri, GTK, Electron-Linux)

WSL2 can run Linux-native GUI apps via WSLg, but GPU rendering often fails:

```
MESA: error: ZINK: failed to choose pdev
libEGL warning: egl: failed to create dri2 screen
Gtk-CRITICAL: gtk_widget_get_scale_factor: assertion 'GTK_IS_WIDGET (widget)' failed
```

### Fix: Force Software Rendering

```bash
LIBGL_ALWAYS_SOFTWARE=1 ./app
```

This bypasses GPU (ZINK/MESA) and uses llvmpipe software renderer. Works for Tauri apps, GTK apps, and most Electron-based Linux builds.

### Alternative: Force X11 Backend

```bash
GDK_BACKEND=x11 ./app
```

### When to Use Which

| Symptom | Fix |
|---------|-----|
| `ZINK: failed to choose pdev` | `LIBGL_ALWAYS_SOFTWARE=1` |
| Blank/black window | `LIBGL_ALWAYS_SOFTWARE=1` or `GDK_BACKEND=x11` |
| Window appears but crashes on interaction | Try both env vars together |
| App works but is slow/choppy | Software rendering is the cost; no GPU acceleration in WSLg for these apps |

## Pitfalls

1. **NSIS `/D=` with quotes breaks silently** — installer runs but ignores the path, installs to default location
2. **`cmd.exe /c "start ..."` hangs** — UNC path issue, always use PowerShell with `-WorkingDirectory`
3. **`powershell.exe` vsock errors** — transient WSL<->Windows IPC issue, retry or use `cmd.exe /c` for simple commands
4. **Long-running PowerShell commands timeout** — use `Start-Process -Wait` instead of blocking shell commands
5. **`tasklist.exe` is slow** — it works but takes a few seconds; `ps aux | grep` is faster for quick checks
6. **WSL nvidia-smi path** — use `/usr/lib/wsl/lib/nvidia-smi` not bare `nvidia-smi`
7. **GUI apps from WSL need display** — Windows 11 WSLg handles this automatically; older WSL needs VcXsrv
