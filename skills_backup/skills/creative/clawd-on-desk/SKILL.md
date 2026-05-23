---
name: clawd-on-desk
description: Install and configure Clawd on Desk (pixel desktop pet) on Windows with WSL integration. Covers NSIS installer extraction, WSL hooks setup for Claude Code / Codex / OpenCode / Hermes, and cross-environment localhost communication.
tags: [desktop-pet, electron, hooks, wsl, windows, clawd]
triggers:
  - user asks to install or configure clawd-on-desk
  - user wants to set up clawd hooks for WSL agents
  - user asks about clawd desktop pet
---

# Clawd on Desk

Pixel desktop pet that reacts to AI coding agents (Claude Code, Codex, OpenCode, Hermes, etc.) in real time. Electron app, runs on Windows/macOS/Linux.

**GitHub**: https://github.com/rullerzhou-afk/clawd-on-desk

## Installation on Windows (from WSL)

### Option 1: Direct download and NSIS silent install

```bash
# Download to Windows D: drive (adjust path)
curl -L "https://github.com/rullerzhou-afk/clawd-on-desk/releases/download/v0.8.0/Clawd-on-Desk-Setup-0.8.0-x64.exe" \
  -o "/mnt/d/Clawd-on-Desk-Setup-0.8.0-x64.exe"

# NSIS silent install — /D= must be LAST param, no quotes, no space after /D=
powershell.exe -Command "Start-Process 'D:\Clawd-on-Desk-Setup-0.8.0-x64.exe' -ArgumentList '/S','/D=D:\ClawdOnDesk' -Wait"
```

**NSIS `/D=` pitfall**: Path must immediately follow `/D=` with no space, no quotes. Must be the very last argument. If the path has spaces, it still must NOT be quoted. Example: `/S /D=D:\My App`.

If silent install fails (common from WSL), use manual extraction:

### Option 2: Manual NSIS extraction with 7z

```bash
sudo apt-get install -y p7zip-full

# Extract outer NSIS package
7z x /mnt/d/Clawd-on-Desk-Setup-0.8.0-x64.exe -o/mnt/d/ClawdOnDesk -y

# The actual app is inside $PLUGINSDIR/app-64.7z
7z x "/mnt/d/ClawdOnDesk/\$PLUGINSDIR/app-64.7z" -o/mnt/d/ClawdOnDesk -y

# Clean up NSIS scaffolding
rm -rf "/mnt/d/ClawdOnDesk/\$PLUGINSDIR" "/mnt/d/ClawdOnDesk/\$R0"
```

After extraction, the app runs but lacks Windows integration (no Start Menu shortcut, no uninstaller). Run the NSIS installer again with `Start-Process -Wait` to get proper registration.

## Starting Clawd from WSL

```powershell
# MUST set working directory to a Windows path — WSL UNC paths break cmd.exe
powershell.exe -Command "Set-Location 'D:\ClawdOnDesk'; Start-Process '.\Clawd on Desk.exe' -WorkingDirectory 'D:\ClawdOnDesk'"
```

**Pitfall**: Running `cmd.exe /c "D:\ClawdOnDesk\Clawd on Desk.exe"` from WSL fails because cmd.exe inherits the WSL UNC working directory (`\\wsl.localhost\...`), which is unsupported. Always use `powershell.exe` with explicit `-WorkingDirectory`.

Verify it's running: `tasklist.exe | grep -i clawd` (should show 6+ Electron processes).

## WSL Hooks Configuration

Clawd runs on Windows, listens on `127.0.0.1:23333`. WSL2 with `networkingMode=mirrored` shares localhost, so hooks POST directly — no SSH tunnel needed.

### Prerequisites

Check `/mnt/c/Users/<winuser>/.wslconfig`:
```ini
[wsl2]
networkingMode=mirrored
```

Verify connectivity: `curl -v http://127.0.0.1:23333/` should connect (404 is fine = server listening).

### Setup steps (run inside WSL)

```bash
# 1. Copy hook files from Windows install
mkdir -p ~/.claude/hooks
cp /mnt/d/ClawdOnDesk/resources/app.asar.unpacked/hooks/*.js ~/.claude/hooks/
cp -r /mnt/d/ClawdOnDesk/resources/app.asar.unpacked/hooks/hermes-plugin ~/.claude/hooks/ 2>/dev/null

# 2. Register Claude Code hooks (remote mode = POST to localhost:23333)
node ~/.claude/hooks/install.js --remote
# Output: 15 hooks registered (SessionStart, SessionEnd, PreToolUse, PostToolUse, etc.)

# 3. Register Codex CLI hooks (remote mode)
node ~/.claude/hooks/codex-install.js --remote
# Output: 6 hooks registered, features.hooks enabled in config.toml

# 4. Register OpenCode plugin
node ~/.claude/hooks/opencode-install.js
# Output: plugin path added to ~/.config/opencode/opencode.json

# 5. Register Hermes plugin
node ~/.claude/hooks/hermes-install.js
# Output: plugin installed to ~/.hermes/plugins/clawd-on-desk, enabled
```

### What each agent registers

| Agent | Config file | Hook count | Mode |
|-------|------------|------------|------|
| Claude Code | `~/.claude/settings.json` | 15 events + 1 HTTP (PermissionRequest) | command hooks POST to localhost:23333 |
| Codex CLI | `~/.codex/hooks.json` + `config.toml` | 6 hooks | official hooks, remote mode |
| OpenCode | `~/.config/opencode/opencode.json` | plugin entry | plugin integration |
| Hermes | `~/.hermes/plugins/clawd-on-desk/` | plugin | managed plugin directory |

### Multi-environment behavior

When both Windows-side and WSL-side agents are configured:
- Clawd tracks ALL sessions independently
- Animations show the highest-priority state across all active sessions
- Windows hooks use `powershell` shell + direct path to `clawd-hook.js`
- WSL hooks use `node` + POST to `localhost:23333` (remote mode)

## CLI vs VS Code Extensions

Clawd monitors **CLI versions** only. VS Code extensions (Copilot, Claude Code extension, Codex extension) use different communication mechanisms and do NOT trigger Clawd hooks.

| Agent | CLI (terminal) | VS Code extension | Cursor |
|-------|---------------|-------------------|--------|
| Claude Code | ✅ | ❌ | N/A |
| Codex | ✅ | ❌ | N/A |
| Copilot | ✅ | ❌ | N/A |
| Cursor | N/A | N/A | ✅ (has native Agent Hooks) |
| OpenCode | ✅ | N/A | N/A |
| Hermes | ✅ | N/A | N/A |

## Key paths

| Item | Windows | WSL |
|------|---------|-----|
| Install dir | `D:\ClawdOnDesk` | N/A (Windows app) |
| Hook scripts | `D:\ClawdOnDesk\resources\app.asar.unpacked\hooks\` | `~/.claude/hooks/` |
| Clawd server | `127.0.0.1:23333` | same (mirrored networking) |
| Uninstaller | `D:\ClawdOnDesk\Uninstall Clawd on Desk.exe` | N/A |
