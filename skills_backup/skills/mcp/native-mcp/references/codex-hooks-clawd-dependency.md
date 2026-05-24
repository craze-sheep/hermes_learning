# Codex Hooks + Clawd Dependency

## Problem
Codex's `hooks.json` fires Clawd hooks on every event (SessionStart, PreToolUse, PermissionRequest, PostToolUse, Stop). All hooks call:
```
CLAWD_REMOTE='1' "/home/lzy/miniconda3/bin/node" "/home/lzy/.claude/hooks/codex-hook.js"
```

If Clawd is not running on `localhost:23333`, the `PermissionRequest` hook hangs for 600 seconds (the timeout configured in hooks.json).

## Detection

```bash
# From WSL — ss won't show Windows ports even in mirrored mode
curl -s --connect-timeout 3 http://localhost:23333/ && echo "Clawd OK" || echo "Clawd down"

# From Windows PowerShell
powershell.exe -Command "Get-NetTCPConnection -LocalPort 23333"
```

## Workaround
Temporarily disable hooks:
```bash
mv ~/.codex/hooks.json ~/.codex/hooks.json.bak
codex exec --sandbox workspace-write "prompt..."
mv ~/.codex/hooks.json.bak ~/.codex/hooks.json
```

## WSL2 Port Visibility Pitfall
In WSL2 with `networkingMode=mirrored`, Windows ports are accessible via `curl`/`nc` but do NOT appear in `ss -tlnp` or `netstat`. This is by design — `ss` shows only WSL-native sockets.

## Affected Events
- `SessionStart` — fires on every Codex session start
- `UserPromptSubmit` — fires on every prompt
- `PreToolUse` — fires before EVERY tool call (including MCP)
- `PermissionRequest` — fires when Codex needs approval for MCP tools (600s timeout!)
- `PostToolUse` — fires after every tool call
- `Stop` — fires on session end

The `PermissionRequest` hook is the most dangerous because it has a 600s timeout (vs 30s for others) and fires when Codex tries to use MCP tools like holographic/fact_store.

## Fix Options
1. Start Clawd on Windows before using Codex
2. Temporarily rename hooks.json (workaround above)
3. Edit hooks.json to remove the PermissionRequest hook (keeps other hooks)
4. Set CLAWD_REMOTE='' in hooks.json to skip remote calls
