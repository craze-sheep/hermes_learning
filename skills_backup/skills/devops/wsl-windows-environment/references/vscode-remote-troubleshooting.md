# VS Code Remote + WSL Troubleshooting

## Duplicate Language Server Instances

**Symptom:** Two or more Pylance (or other LSP) processes consuming high CPU.

**Cause:** Each VS Code window connected to the same WSL spawns its own Extension Host and language server. If you open multiple windows (or reconnect without closing the old one), duplicates pile up.

**Diagnosis:**
```bash
# List all Pylance processes with their client process IDs
ps aux | grep pylance | grep -v grep | awk '{print $2, substr($0, index($0,$11))}'

# The --clientProcessId=X flag tells you which Extension Host owns each Pylance
# Map back to Extension Hosts:
ps aux | grep extensionHost | grep -v grep
```

Each Pylance PID maps to a `--clientProcessId` which is the Extension Host PID it serves. If you see two Pylance processes with different clientProcessIds, you have two VS Code windows open.

**Fix:** Kill the orphaned/unused Pylance PID:
```bash
kill <unused_pylance_pid>
```

## Reading VS Code Extension Logs

Logs are stored at:
```
~/.vscode-server/data/logs/<YYYYMMDDTHHMMSS>/exthost<N>/<publisher.extension>/<Name>.log
```

Example for Codex:
```bash
# Find latest log directory
ls ~/.vscode-server/data/logs/ | sort | tail -1

# Find Codex log
find ~/.vscode-server/data/logs/ -name "Codex.log" | sort | tail -1

# Read it
cat ~/.vscode-server/data/logs/<latest>/exthost1/openai.chatgpt/Codex.log
```

## Codex Plugin Authentication (as of 2026)

The OpenAI Codex VS Code extension now requires **ChatGPT account login** (Plus/Pro/Team). Pure API key authentication is no longer supported for the plugin catalog.

Error signature in Codex.log:
```
chatgpt authentication required for remote plugin catalog; api key auth is not supported
```

**Fix:** Sign in via the Codex sidebar in VS Code using a ChatGPT account (not just an API key).

## Cross-Environment Debugging: Windows vs WSL Extension Issues

When a VSCode extension works on Windows but fails in WSL (or vice versa), systematically compare both environments before guessing at fixes.

### Step 1: Compare Extension Versions
```bash
# WSL side
code --list-extensions --show-versions 2>/dev/null | grep <extension-name>

# Windows side
ls /mnt/c/Users/<winuser>/.vscode/extensions/ | grep <extension-name>
```
Version mismatches (e.g. `26.5616` on WSL vs `26.616` on Windows) are a common root cause.

### Step 2: Compare Config and Auth Files
For Codex specifically, configs live at `~/.codex/` on WSL and `/mnt/c/Users/<winuser>/.codex/` on Windows. Compare both:
```bash
diff <(cat ~/.codex/config.toml) <(cat /mnt/c/Users/<winuser>/.codex/config.toml)
diff <(cat ~/.codex/auth.json) <(cat /mnt/c/Users/<winuser>/.codex/auth.json)
```
Key things to check: `base_url` (local proxy vs remote), API key values, provider settings.

### Step 3: Compare Logs Side by Side
WSL logs: `~/.vscode-server/data/logs/<timestamp>/exthost<N>/<publisher.extension>/<Name>.log`
Windows logs: `/mnt/c/Users/<winuser>/AppData/Roaming/Code/logs/<timestamp>/window<N>/exthost/<publisher.extension>/<Name>.log`

Read both and compare the initialization sequence line by line. Focus on:
- Whether `Initialize received` appears and how long after `Spawning`
- Whether `[IpcRouter] I am the router` appears (absence = IPC router didn't start)
- Any timeout errors (`[IpcClient] Initialize failed errorMessage=timeout`)

### Codex IPC Timeout Root Cause Pattern

The Codex extension's 401/plugin-catalog errors are **non-blocking warnings** that appear on both Windows and WSL. They do NOT prevent the extension from working.

The **real blocker** is the IPC handshake timeout between the VSCode extension and the `codex app-server` binary:
```
[IpcClient] Initialize failed errorMessage=timeout
```

On Windows, `Initialize received` typically arrives within ~2ms. On WSL, the linux binary may take 3+ seconds, exceeding the extension's timeout window. The fix is to ensure the WSL extension version matches Windows (reinstall/update), since different builds may have different timeout thresholds or initialization paths.

**Quick fix:** Remove and reinstall the extension in WSL:
```bash
rm -rf ~/.vscode-server/extensions/<publisher.extension>-*
# Then reopen the WSL window to trigger automatic reinstall
```

## Proxy Issues in WSL

If git or extensions fail with `Failed to connect to 127.0.0.1:7897` (or similar proxy port):

1. Check if proxy env vars are set: `env | grep -i proxy`
2. Check if the proxy is actually reachable: `curl -s --connect-timeout 3 http://127.0.0.1:7897`
3. In WSL, the proxy usually runs on the Windows side and is reachable via localhost due to mirrored networking. If not, check `/etc/wsl.conf` for `networkingMode=mirrored`.
