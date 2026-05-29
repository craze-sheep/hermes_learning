---
name: wsl-python-dev
description: "Python development on WSL2: conda environments, CJK path pitfalls, port binding issues, and project setup patterns."
version: 1.0.0
tags: [wsl, python, conda, devops, fastapi]
metadata:
  hermes:
    tags: [wsl, python, conda, devops, fastapi, environment]
---

# Python Development on WSL2

Covers common pitfalls when developing Python projects in WSL2, especially with conda environments, CJK paths, and port management.

## Conda Environment Setup

Always use conda for project isolation — never install project deps on system Python.

```bash
# Create environment
conda create -n <project-name> python=3.11 -y

# Activate in terminal tool (conda activate doesn't work without sourcing)
source ~/miniconda3/etc/profile.d/conda.sh && conda activate <env-name>

# Install deps
pip install -r requirements.txt

# Verify
python -c "import fastapi; print('OK')"
```

**Pitfall — conda activate fails silently:** The `conda activate` command requires prior sourcing of conda.sh. Always prefix with `source ~/miniconda3/etc/profile.d/conda.sh &&`.

**Pitfall — system Python pollution:** Before creating a conda env, check if the user already installed deps on system Python. If so, uninstall them first:
```bash
# Check
pip3 list | grep -iE "fastapi|uvicorn|httpx"
# Remove (from /tmp — see CJK pitfall below)
pip3 uninstall -y fastapi uvicorn httpx
```

## PITFALL: CJK (Chinese) Directory Paths Break pip

**Severity: HIGH** — causes terminal tool to hang with "appears to start a long-lived server/watch process"

When the current working directory contains Chinese characters (e.g., `/home/lzy/project/项目-api中转站`), `pip install` and `pip uninstall` commands hang or get killed by the terminal tool's process detector.

**Root cause:** The terminal tool's watchdog detects pip's subprocess spawning as a "long-lived process" when the CWD contains multibyte characters. This is likely a path-encoding issue in the watchdog logic.

**Fix:** Always use `workdir=/tmp` for pip commands:
```bash
# WRONG — hangs
cd /home/lzy/project/项目-api中转站 && pip install fastapi

# RIGHT — use workdir
pip install fastapi   # with workdir=/tmp in terminal tool
```

For pip uninstall, run individual packages (batch commands with `for` loops also hang):
```bash
# RIGHT — one at a time, workdir=/tmp
pip3 uninstall -y fastapi    # workdir=/tmp
pip3 uninstall -y uvicorn    # workdir=/tmp
```

**Alternative:** Use `execute_code` with `from hermes_tools import terminal` and set workdir there.

**Pitfall — batch pip commands also hang:** Even individual `pip3 uninstall -y pkg1 pkg2` or `for` loops in shell can hang under CJK paths. Run each package uninstall as a separate `terminal()` call with `workdir=/tmp`. Using `background=true` with `notify_on_complete=True` works as a fallback for multi-package uninstalls.

## PITFALL: Port Binding Race Conditions

When restarting a server quickly (kill → restart), TIME-WAIT TCP connections accumulate and cause `OSError: [Errno 98] error while attempting to bind on address: address already in use`.

**Symptoms:**
- Server exits, but port still shows as unavailable
- `ss -tlnp | grep PORT` shows no LISTEN but many TIME-WAIT
- Happens especially on 0.0.0.0 binds

**Fixes:**
1. **Use a different port** — simplest workaround
2. **Wait 60s** for TIME-WAIT to clear (kernel default)
3. **Bind to 127.0.0.1** instead of 0.0.0.0 — fewer TIME-WAIT issues
4. **Set SO_REUSEADDR** in your server code:
   ```python
   # uvicorn
   uvicorn.run("app.main:app", host="127.0.0.1", port=8080)
   ```
5. **Kill + verify port is free** before restarting:
   ```bash
   ss -tlnp | grep :8080 || echo "port free"
   ```

## Project Setup Pattern (FastAPI)

Standard structure for a Python API project:

```
project/
├── app/
│   ├── __init__.py
│   ├── main.py          # FastAPI app + uvicorn entry
│   ├── config.py         # Settings from .env
│   ├── database.py       # aiosqlite / SQLAlchemy
│   ├── models/
│   │   └── schemas.py    # Pydantic request/response models
│   ├── routers/
│   │   ├── __init__.py
│   │   └── admin/
│   │       └── __init__.py
│   ├── middleware/
│   │   └── __init__.py
│   ├── proxy/
│   │   └── __init__.py
│   └── store/
│       └── __init__.py   # Data access layer
├── static/
│   └── index.html        # Optional embedded frontend
├── data/                 # SQLite DB (gitignored)
├── .env                  # Local config (gitignored)
├── .env.example          # Template
├── .gitignore
├── requirements.txt
└── README.md
```

**Key patterns:**
- `config.py`: Use `dataclass(frozen=True)` + `python-dotenv` (lighter than pydantic BaseSettings)
- `database.py`: aiosqlite with `async def get_db()` returning connection (caller closes)
- Store layer: async functions, each opens+closes its own connection
- Middleware: FastAPI `Depends()` for auth, `BaseHTTPMiddleware` for logging
- Static files: `app.mount("/", StaticFiles(directory="static", html=True))` — register LAST (catch-all)

## Git Workflow

Commit after each logical unit. Use conventional commits:
```bash
git add -A && git commit -m "feat: description"
git push origin main
```

**Push verification:** Always verify push works early:
```bash
git push --dry-run origin main
```

## References

- `references/fastapi-api-gateway.md` — Proven architecture for API relay/gateway (file map, design decisions, testing)
- `references/fastapi-production-hardening.md` — Production hardening patterns (httpx pool, security headers, SSE streaming, error handling)

## .gitignore for Python + conda projects

```
.venv/
__pycache__/
*.pyc
data/
.env
*.db
*.egg-info/
dist/
build/
```
