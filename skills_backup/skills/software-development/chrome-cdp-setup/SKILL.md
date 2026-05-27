---
name: chrome-cdp-setup
description: "Launch Chrome with remote debugging port for CDP (Chrome DevTools Protocol) access. Use when you need to start Chrome headless or headed with --remote-debugging-port, check port availability, health-check the CDP endpoint, or troubleshoot port conflicts. Prerequisite for Playwright, web-access proxy, puppeteer, and other CDP-based tools when Chrome isn't already running with debugging enabled."
tags: [chrome, cdp, debugging, browser, remote-debugging, devtools-protocol]
related_skills: [web-access, playwright, node-inspect-debugger]
---

# Chrome CDP Setup

Launch Chrome with `--remote-debugging-port` so CDP clients (Playwright, web-access proxy, puppeteer, `chrome-remote-interface`, Hermes browser tools) can connect.

## When to Use

- User asks to "open Chrome with debug port" or "start Chrome for automation"
- A CDP-based tool (web-access, Playwright) fails because no Chrome is listening
- You need to verify Chrome's debug port is up and responding
- Port conflict troubleshooting (`bind() failed: Address already in use`)

## Quick Start

```bash
# 1. Find Chrome
which google-chrome google-chrome-stable chromium chromium-browser 2>/dev/null

# 2. Check if target port is free
ss -tlnp | grep <PORT>
curl -s http://localhost:<PORT>/json/version

# 3. Launch (use terminal(background=true), NOT shell &)
google-chrome --remote-debugging-port=<PORT> --no-first-run --no-default-browser-check --user-data-dir=/tmp/chrome-debug-profile

# 4. Health check (after ~3s)
curl -s http://localhost:<PORT>/json/version | python3 -m json.tool
```

## Step-by-Step

### 1. Find Chrome binary

```bash
which google-chrome google-chrome-stable chromium chromium-browser 2>/dev/null
```

Typical paths:
- `/usr/bin/google-chrome` → symlink to `/opt/google/chrome/google-chrome`
- `/usr/bin/chromium-browser` (snap transitional)
- WSL Windows path: `/mnt/c/Program Files/Google/Chrome/Application/chrome.exe`

### 2. Check if Chrome is already running

```bash
pgrep -fa chrome
```

If Chrome is running without a debug port, the user must close it first or enable remote debugging manually.

### 3. Verify port availability

```bash
ss -tlnp | grep <PORT>
curl -s http://localhost:<PORT>/json/version
```

If port is occupied: kill the process or pick a different port.

### 4. Launch Chrome

**Critical**: Use `terminal(background=true)` — Hermes blocks shell-level `&`, `nohup`, `disown` in foreground mode.

```bash
google-chrome \
  --remote-debugging-port=<PORT> \
  --no-first-run \
  --no-default-browser-check \
  --user-data-dir=/tmp/chrome-debug-profile
```

Flag reference:
| Flag | Purpose |
|------|---------|
| `--remote-debugging-port=<PORT>` | Enable CDP on this port |
| `--no-first-run` | Skip first-run wizard |
| `--no-default-browser-check` | Don't prompt to set as default |
| `--user-data-dir=<PATH>` | Isolated profile (avoids conflicts with user's normal session) |
| `--headless=new` | Headless mode (no window, for servers/WSL without display) |
| `--no-sandbox` | Sometimes needed in Docker/CI (security tradeoff) |

Common ports: 9222 (Chrome default), 7897 (user forwarding), 9223, 9224.

### 5. Health check

Wait ~3 seconds after launch, then:

```bash
curl -s http://localhost:<PORT>/json/version | python3 -m json.tool
```

Expected JSON response:
```json
{
  "Browser": "Chrome/148.0.7778.178",
  "Protocol-Version": "1.3",
  "User-Agent": "...",
  "V8-Version": "...",
  "WebKit-Version": "...",
  "webSocketDebuggerUrl": "ws://127.0.0.1:7897/devtools/browser/..."
}
```

To list available targets (tabs):
```bash
curl -s http://localhost:<PORT>/json/list | python3 -m json.tool
```

## Troubleshooting

### `bind() failed: Address already in use (98)`
Port is taken. Find and resolve:
```bash
ss -tlnp | grep <PORT>
# Kill the PID occupying the port, or use a different one
```

### `Cannot start http server for devtools`
Same root cause as port conflict.

### Chrome exits immediately
- **Same user-data-dir**: another Chrome instance using the same profile path. Use a unique `--user-data-dir`.
- **No display** (WSL/Docker): add `--headless=new` or set `DISPLAY` env var.
- **Sandbox issues** (Docker/CI): add `--no-sandbox`.

### Empty response from `/json/version`
Chrome may still be starting. Wait 2-3 more seconds and retry. If consistently empty, Chrome may have crashed — check stderr output.

## WSL-Specific Notes

- Prefer WSL-native Chrome (`/usr/bin/google-chrome`) over Windows Chrome for simplicity
- If CDP client is on Windows side, port forwarding from WSL to Windows may be needed (`netsh interface portproxy`)
- Without X server (`DISPLAY` not set), use `--headless=new`
- User may have a preferred forwarding port (e.g., 7897) for cross-boundary access
