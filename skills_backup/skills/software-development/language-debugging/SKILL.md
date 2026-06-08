---
name: language-debugging
description: "Debug Python (pdb/debugpy), Node.js (inspect/CDP), and Hermes TUI slash commands. Covers breakpoints, remote debugging, post-mortem analysis, and cross-layer TUI command diagnosis."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [debugging, python, nodejs, pdb, debugpy, node-inspect, cdp, tui, breakpoints, dap]
    related_skills: [systematic-debugging, test-driven-development, hermes-agent]
---

# Language Debugging

Unified reference for debugging Python, Node.js, and Hermes TUI applications. When `console.log` / `print()` isn't enough, use the language-appropriate debugger to step through code, inspect state, and trace issues.

## When to Use

- A test fails and tracebacks don't reveal why
- You need to step through a function and watch state mutate
- A long-running process (gateway, daemon) misbehaves and can't be restarted
- Post-mortem: exception fired and you want locals at the crash site
- Hermes TUI slash commands don't work or show in autocomplete
- ui-tui crashes or behaves wrong

**Don't use for:** things `print()` / `logging.debug` solve in under a minute.

## Quick Decision Table

| Situation | Tool | Section |
|-----------|------|---------|
| Python: quick breakpoint | `breakpoint()` + pdb | [Python: pdb](#python-pdb) |
| Python: launch script under debugger | `python -m pdb` | [Python: pdb](#python-pdb) |
| Python: debug pytest test | `pytest --pdb` | [Python: pdb](#python-pdb) |
| Python: attach to running process | `debugpy` / `remote-pdb` | [Python: debugpy](#python-debugpy) |
| Python: post-mortem on exception | `pdb.post_mortem()` | [Python: pdb](#python-pdb) |
| Node.js: quick breakpoint | `node inspect` | [Node.js: inspect](#nodejs-inspect) |
| Node.js: attach to running process | `kill -SIGUSR1` + `node inspect` | [Node.js: inspect](#nodejs-inspect) |
| Node.js: scriptable debugging | CDP via `chrome-remote-interface` | [Node.js: CDP](#nodejs-cdp) |
| Node.js: heap snapshot / CPU profile | CDP Profiler/HeapProfiler | [Node.js: CDP](#nodejs-cdp) |
| Hermes TUI: command not working | Check Python registry + Ink handler | [Hermes TUI](#hermes-tui-debugging) |
| Hermes TUI: command missing from autocomplete | Add to COMMAND_REGISTRY | [Hermes TUI](#hermes-tui-debugging) |

---

## Python: pdb

### Quick Reference

| Command | Action |
|---------|--------|
| `n` | next line (step over) |
| `s` | step into |
| `r` | return from current function |
| `c` | continue |
| `l` / `ll` | list source / full function |
| `w` | where (stack trace) |
| `u` / `d` | move up / down in stack |
| `p expr` / `pp expr` | print / pretty-print |
| `b file:line` | set breakpoint |
| `b func` | break on function entry |
| `cl N` | clear breakpoint N |
| `!stmt` | execute arbitrary Python |
| `interact` | drop into full Python REPL in current scope |
| `q` | quit |

### Recipe: Local breakpoint

```python
def compute(x, y):
    result = some_helper(x)
    breakpoint()           # <-- drops into pdb here
    return result + y
```

Run normally. You land at `breakpoint()` with full locals access. **Remove before committing.**

### Recipe: Launch script under pdb

```bash
python -m pdb path/to/script.py arg1 arg2
# Lands at first line
(Pdb) b path/to/script.py:42
(Pdb) c
```

### Recipe: Debug pytest test

```bash
# Drop to pdb on failure:
pytest tests/test.py::test_name --pdb -p no:xdist

# Drop to pdb at START of test:
pytest tests/test.py::test_name --trace

# Show locals without pdb:
pytest tests/test.py --showlocals --tb=long
```

**PITFALL:** pdb does NOT work under pytest-xdist. Always add `-p no:xdist` or use `-n 0`.

### Recipe: Post-mortem on exception

```python
import pdb, sys
try:
    run_the_thing()
except Exception:
    pdb.post_mortem(sys.exc_info()[2])
```

Or wrap a script:
```bash
python -m pdb -c continue script.py
# When it crashes, pdb catches it at the exception frame
```

---

## Python: debugpy

For **remote/headless** debugging — attach to already-running processes, long-lived daemons, subprocess workers.

### Recipe: Attach to running process (no source edit)

```bash
pip install debugpy
python -m debugpy --listen 127.0.0.1:5678 --pid <pid>
# debugpy injects into the process. Then attach a client.
```

**PITFALL:** ptrace injection needs `/proc/sys/kernel/yama/ptrace_scope = 0`. Fix: `echo 0 | sudo tee /proc/sys/kernel/yama/ptrace_scope`

### Recipe: Source-edit (wait for debugger at launch)

```python
import debugpy
debugpy.listen(("127.0.0.1", 5678))
debugpy.wait_for_client()  # blocks until attached
```

### Recipe: remote-pdb (cleanest for terminal agents)

```bash
pip install remote-pdb
```

```python
from remote_pdb import set_trace
set_trace(host="127.0.0.1", port=4444)
```

Then: `nc 127.0.0.1 4444` — you get a `(Pdb)` prompt.

### Hermes-Specific Processes

- **`run_agent.py` / CLI**: add `breakpoint()` near suspect line, run `hermes` normally
- **`tui_gateway` subprocess**: use `remote-pdb` at handler entry, trigger the slash command, then `nc 127.0.0.1 4444`
- **`_SlashWorker` subprocess**: `remote-pdb` with `set_trace()` inside the worker's `exec` path
- **Gateway (`gateway/run.py`)**: `remote-pdb` at handler, or `debugpy --wait-for-client` if restarting

---

## Node.js: inspect

### Quick Reference

| Command | Action |
|---------|--------|
| `c` / `cont` | continue |
| `n` / `next` | step over |
| `s` / `step` | step into |
| `o` / `out` | step out |
| `sb('file.js', 42)` | set breakpoint |
| `sb('functionName')` | break on function call |
| `cb('file.js', 42)` | clear breakpoint |
| `bt` | backtrace (call stack) |
| `list(5)` | show 5 lines around current position |
| `repl` | drop into REPL in current scope |
| `exec expr` | evaluate expression once |
| `watch('expr')` | evaluate on every pause |
| `pause` | pause running code |
| `restart` | restart script |
| `kill` | kill the script |

### Recipe: Launch paused

```bash
node inspect path/to/script.js
# or with tsx:
node --inspect-brk $(which tsx) path/to/script.ts
```

### Recipe: Attach to running process

```bash
# 1. Enable inspector on existing process
kill -SIGUSR1 <pid>
# Node prints: Debugger listening on ws://127.0.0.1:9229/<uuid>

# 2. Attach
node inspect -p <pid>
# or by URL
node inspect ws://127.0.0.1:9229/<uuid>
```

### Recipe: Debug Hermes ui-tui

```bash
# 1. Build TUI
cd hermes-agent/ui-tui && npm run build

# 2. Launch with inspector
node --inspect-brk dist/entry.js

# 3. In another terminal
node inspect -p <node pid>
# debug> sb('dist/app.js', 220)
# debug> cont
# Paused. repl → inspect props, state, etc.
```

### Recipe: Debug running `hermes --tui`

```bash
TUI_PID=$(pgrep -f 'ui-tui/dist/entry' | head -1)
kill -SIGUSR1 "$TUI_PID"
curl -s http://127.0.0.1:9229/json/list | jq -r '.[0].webSocketDebuggerUrl'
node inspect ws://127.0.0.1:9229/<uuid>
```

---

## Node.js: CDP

For **scriptable** debugging — automate breakpoints, capture state, script repros.

```bash
npm i -g chrome-remote-interface  # or project-local
node --inspect-brk=9229 target.js &
```

### Driver script pattern

```javascript
const CDP = require('chrome-remote-interface');
(async () => {
  const client = await CDP({ port: 9229 });
  const { Debugger, Runtime } = client;
  Debugger.paused(async ({ callFrames }) => {
    const top = callFrames[0];
    // Walk scopes, evaluate expressions, resume
    await Debugger.resume();
  });
  await Debugger.enable();
  await Debugger.setBreakpointByUrl({ urlRegex: '.*app\\.tsx$', lineNumber: 119 });
  await Runtime.runIfWaitingForDebugger();
})();
```

### Heap snapshots & CPU profiles

```javascript
// CPU profile for 5 seconds
await client.Profiler.enable();
await client.Profiler.start();
await new Promise(r => setTimeout(r, 5000));
const { profile } = await client.Profiler.stop();
require('fs').writeFileSync('/tmp/cpu.cpuprofile', JSON.stringify(profile));
```

---

## Hermes TUI Debugging

Hermes slash commands span three layers:

```
Python backend (hermes_cli/commands.py)     <- canonical COMMAND_REGISTRY
       │
       ▼
TUI gateway (tui_gateway/server.py)         <- slash.exec / command.dispatch
       │
       ▼
TUI frontend (ui-tui/src/app/slash/)        <- local handlers + fallthrough
```

### Common Issues

1. **Command shows in TUI but not in autocomplete** → missing from `COMMAND_REGISTRY` in `hermes_cli/commands.py`
2. **Command in autocomplete but doesn't work** → check `tui_gateway/server.py` handler and `createSlashHandler.ts`
3. **Behavior differs CLI vs TUI** → different implementations; check both `cli.py::process_command` and TUI local handler
4. **Persists config but doesn't apply live** → also patch nanostore state (`patchUiState(...)`)
5. **Gateway silently ignores command** → check `GATEWAY_KNOWN_COMMANDS` includes canonical name

### Fix: Add missing command

1. Add `CommandDef` to `COMMAND_REGISTRY` in `hermes_cli/commands.py`
2. Add handler in `cli.py` → `process_command()`
3. For gateway commands: add handler in `gateway/run.py`
4. Rebuild TUI: `npm --prefix ui-tui run build`

### Debugging tactics

- **Python side hangs**: use `python-debugpy` section above — `remote-pdb` at handler entry
- **Ink side not reacting**: use `node-inspect-debugger` section — `sb('dist/app.js', N)` after build
- **Registry mismatch**: compare `COMMAND_REGISTRY` entry against TUI's local command list

---

## Common Pitfalls (All Languages)

1. **Wrong line numbers in TS source** — breakpoints hit emitted JS, not `.ts`. Build first, break in `dist/*.js`.
2. **`--inspect` vs `--inspect-brk`** — `--inspect` doesn't pause; script races past breakpoint. Use `--inspect-brk`.
3. **Port collisions** — default 9229. Use `--inspect=0` for random port, read from `/json/list`.
4. **pdb under xdist** — silently does nothing. Always `-p no:xdist` or `-n 0`.
5. **`breakpoint()` in CI** — hangs the process. Safe locally; never commit it.
6. **`PYTHONBREAKPOINT=0`** — disables all `breakpoint()` calls. Check env.
7. **Attach to PID fails** — hardened kernels block ptrace. Fix: `echo 0 > /proc/sys/kernel/yama/ptrace_scope`.
8. **Threads** — pdb only debugs current thread. Use debugpy for multithreaded code.
9. **Security** — `--inspect=0.0.0.0:9229` exposes arbitrary code execution. Always bind to `127.0.0.1`.

## Verification Checklist

After debugging session:

- [ ] No stray `breakpoint()` / `set_trace()` / `debugpy.listen` in committed code
  ```bash
  rg -n 'breakpoint\(\)|set_trace\(|debugpy\.listen' --type py
  ```
- [ ] Inspector port confirmed: `curl -s http://127.0.0.1:9229/json/list`
- [ ] First breakpoint actually hits (if not: check `--inspect-brk`, PYTHONBREAKPOINT, xdist)
- [ ] `where` / `bt` shows expected call stack
