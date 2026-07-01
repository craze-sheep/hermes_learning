---
name: local-fs-exploration
description: "Explore local file systems using Hermes tools — directory listings, project discovery, file metadata extraction. Use when the user asks 'what's in this directory', 'list projects', 'what does this folder contain', or any task requiring local directory traversal."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows, wsl]
metadata:
  hermes:
    tags: [file-system, directory-listing, project-discovery, local-files, browser-file-protocol]
    related_skills: [codebase-inspection, web-access]
---

# Local File System Exploration

Explore local directories and discover project structure using Hermes built-in tools.

## When to Use

- User asks "what projects are in this directory"
- User wants to know what a folder contains
- Task requires traversing local directories to find files or understand structure
- `search_files` times out on large directories
- Need to identify project types (Python, Node.js, Java, etc.) by inspecting key files

## Tool Selection Guide

| Scenario | Tool | Notes |
|----------|------|-------|
| List files in a specific directory | `browser_navigate` to `file:///path/` | Renders HTML index page with names, sizes, dates |
| Find files by name pattern | `search_files` (target=files) | Glob patterns like `*.py`, `*README*` |
| Search file contents | `search_files` (target=content) | Regex search, may timeout on large dirs |
| Read a specific file | `read_file` | Works on files ONLY, not directories |
| Quick file metadata | `browser_navigate` + snapshot | Shows size and modification date |

## Step-by-Step: Directory Listing

### 1. Navigate to the directory with browser

```python
# Use file:// protocol — browser renders a local HTML index
browser_navigate(url="file:///home/user/project/")
```

This returns a table with:
- Directory entries (folders end with `/`)
- File sizes
- Last modified dates

### 2. Read the snapshot to identify entries

The snapshot shows interactive elements with ref IDs. Directories have trailing `/` in their names. Skip hidden dirs like `.git/`, `__pycache__/`, `.vscode/`.

### 3. Explore subdirectories for project understanding

For each project directory, check for:
- `README.md` / `README` — primary description
- `package.json` — Node.js project (check `name`, `description` fields)
- `pom.xml` / `build.gradle` — Java project
- `Cargo.toml` — Rust project
- `go.mod` — Go project
- `pyproject.toml` / `setup.py` / `requirements.txt` — Python project
- `Makefile` — C/C++ or build system
- `Dockerfile` / `docker-compose.yml` — containerized project
- `.env` / `.env.example` — has configuration (check for clues about purpose)

### 4. Read README files for descriptions

```python
read_file(path="/home/user/project/SomeProject/README.md", limit=30)
```

## Critical Pitfalls

### 1. `read_file` DOES NOT WORK on directories

```
# WRONG — returns "File not found"
read_file(path="/home/user/project/some-directory")

# CORRECT — use browser to list directory contents
browser_navigate(url="file:///home/user/project/some-directory/")
```

This is the #1 mistake. `read_file` is for files only. For directories, always use `browser_navigate` with `file://` protocol.

### 2. `search_files` may timeout on large directories

When `search_files` returns `[Command timed out after 60s]`, fall back to `browser_navigate` with `file://` protocol. This is common in directories with many files (e.g., `node_modules`, `.git`, large project trees).

### 3. `browser_console` runs in BROWSER context, not Node.js

```javascript
// WRONG — require() is not available in browser context
const fs = require('fs');

// CORRECT — use browser DOM APIs or file:// navigation
document.querySelectorAll('a').length
```

The browser console has access to DOM, window, document — but NOT Node.js APIs like `fs`, `path`, `child_process`.

### 4. URL encoding for non-ASCII paths

Paths with Chinese characters or spaces need URL encoding:
```python
# Works for ASCII paths
browser_navigate(url="file:///home/user/project/my-project/")

# For non-ASCII paths, the browser auto-encodes, but verify the URL in the response
browser_navigate(url="file:///home/lzy/project/口语练习/")
# Browser navigates to: file:///home/lzy/project/%E5%8F%A3%E8%AF%AD%E7%BB%83%E4%B9%A0/
```

### 5. WSL path mapping

In WSL, Windows drives are at `/mnt/c/`, `/mnt/d/`, etc.:
```python
# Windows C:\Users\lzy\Desktop → WSL path
browser_navigate(url="file:///mnt/c/Users/lzy/Desktop/")
```

## Pattern: Project Inventory

When asked to "list all projects" in a directory:

1. `browser_navigate` to the directory → get listing
2. Filter out hidden dirs (`.git/`, `.agents/`, `__pycache__/`)
3. For each project dir:
   a. Navigate into it to see files
   b. Check for README.md → `read_file` first 30 lines
   c. If no README, check for key config files (package.json, pom.xml, etc.)
   d. Infer purpose from file names, directory structure, and config files
4. Compile results into a structured list with:
   - Project name
   - Type (academic, tool, library, app, etc.)
   - Brief description
   - Tech stack (if determinable)
   - Last modified date (from directory listing)

## Batch File Operations

When the task involves copying/moving files from a directory tree with inconsistent subfolder naming (common with Chinese exam archives, downloaded datasets, multi-year collections), see `references/batch-file-operations.md` for the discovery-then-multi-pattern-copy workflow, including WSL path translation and special-case handling.

## Example: Full Project Inventory

```python
# Step 1: Get top-level listing
browser_navigate(url="file:///home/user/projects/")
# → snapshot shows: project-a/, project-b/, project-c/

# Step 2: Explore each project
browser_navigate(url="file:///home/user/projects/project-a/")
# → snapshot shows: README.md, src/, package.json, ...

# Step 3: Read description
read_file(path="/home/user/projects/project-a/README.md", limit=20)

# Step 4: Check package.json for Node.js projects
read_file(path="/home/user/projects/project-a/package.json", limit=15)

# Repeat for each project...
```

## Interactive Directory Cleanup

When the user says a directory is "too messy" or "杂" and wants it cleaned up:

### Workflow
1. **Survey first:** `du -sh`, `ls -la`, `find` for subdirectories. Present summary.
2. **Go through items ONE BY ONE:** For each item, present name/size, what it does (read first 10-20 lines), whether it's needed, ask "delete or keep?" via `clarify`.
3. **Execute deletions immediately** after each approval (don't batch at end).
4. **For large subdirectories**, ask about the parent first, then drill in if user wants to keep it.
5. **Final summary:** What deleted (with sizes), what kept, total space saved, current tree view.

### Rules
- **NEVER batch-delete without asking** — even `__pycache__` gets a question
- **Read file headers to explain purpose** — don't guess
- **Compare before recommending deletion** of similar items (diff `ai_model/` vs `ai_model_副本/`)
- **Present sub-items within kept directories** — keeping parent ≠ keeping everything inside
- **Don't skip "obvious" items** — user wants the full tour

### Research Quality Assessment
When cleaning research/knowledge assets:
1. Curated notes (small, structured) = high-value → keep
2. Raw code clones, PDFs, caches = usually replaceable → recommend delete
3. Read 3-4 representative files before assessing quality
4. Don't recommend deleting knowledge assets without reading them first
