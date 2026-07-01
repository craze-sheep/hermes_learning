---
name: interactive-directory-cleanup
description: "Clean up messy directories with user approval per file. Present each item, explain its purpose, ask before deleting. Never batch-delete without user confirmation."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows, wsl]
metadata:
  hermes:
    tags: [file-system, cleanup, user-approval, directory-management]
    related_skills: [local-fs-exploration, codebase-inspection]
---

# Interactive Directory Cleanup

Clean up messy directories one item at a time with user approval on each deletion.

## When to Use

- User says a directory is "too messy" or "杂" and wants it cleaned up
- User wants to keep only necessary files and remove the rest
- User explicitly asks you to explain each file before deciding
- Any directory cleanup where the user wants control over what gets deleted

## Core Workflow

### 1. Survey the directory first

Before asking about anything, run a full inventory:
```
terminal: du -sh, ls -la, find for subdirectories
```
Present a high-level summary: how many items, total size, what categories exist.

### 2. Go through items ONE BY ONE

For each item, present:
- **Name and size** (du -sh or ls -lh)
- **What it does** — read the first 10-20 lines if it's code, or describe the directory contents
- **Whether it's needed** — your recommendation with reasoning
- **Ask: delete or keep?**

Use `clarify` tool with choices (e.g., ["删", "不删"]) for each item.

### 3. Execute deletions immediately after each approval

Don't batch all deletions at the end. Delete right after user confirms each item. This way if the session gets interrupted, partial progress is preserved.

### 4. For large subdirectories, ask about the PARENT first

If a directory like `research/papers/` has 50 subdirectories, don't ask about all 50 individually. Ask about the parent directory first, then drill into sub-items only if the user wants to keep the parent but clean inside it.

### 5. Final summary

After all items processed, show:
- What was deleted (with sizes)
- What was kept
- Total space saved
- Current directory structure (tree view)

## Pitfalls

1. **NEVER batch-delete without asking.** Even if something is obviously garbage (like `__pycache__`), still present it and ask. The user explicitly said "每一个文件你都得向我介绍它的作用和内容然后询问我清理不清理" (explain each file's purpose and ask whether to clean it).

2. **NEVER start running external agents (Codex, Claude Code) during cleanup.** User said "没事不要啊，我自己来" when Codex was launched without permission. During cleanup, YOU do the work. Only delegate if user explicitly asks for it.

3. **Present sub-items within a kept directory.** If user keeps `ai_model/`, then ask about its internals: `__pycache__/`, checkpoint files, report files, etc. Don't assume keeping the parent means keeping everything inside.

4. **Read file headers to explain purpose.** Don't guess what a file does — read the first 10-20 lines. For `.py` files, the docstring usually explains it. For `.md` files, the title and first paragraph.

5. **Don't skip "obvious" items.** The user wants the full tour. A 20K `__pycache__/` is still worth a 10-second explanation.

6. **Compare before recommending deletion of similar items.** If there's `ai_model/` and `ai_model_副本/`, diff them and tell the user which is better before asking which to keep. Don't just list both and ask blindly.

## Example Flow

```
User: model/ 文件夹太杂了，帮我清理一下

Agent:
  1. ls -la model/ → 7 items, 1.5G total
  2. Presents summary table
  3. For each item:
     - "__pycache__/ (20K) — Python 字节码缓存，删了自动重建。删不删？"
     - User: 删 → rm -rf
     - "ai_model/ (5.5M) — 优化版模型代码，包含..."
     - User: 保留
     - "ai_model/__pycache__/ (176K) — 字节码缓存"
     - User: 删 → rm -rf
     - ... (continue for each item)
  4. Final summary with before/after comparison
```

## Research Quality Assessment Pattern

When cleaning up directories that contain research/knowledge assets:

1. **Distinguish curated notes from raw data.** Notes/analysis files (small, structured) are high-value. Raw code clones, PDFs, caches are usually replaceable.

2. **Read sample entries to assess quality.** Read 3-4 representative files from the collection. Check: structure consistency, depth of analysis, actionable content.

3. **Report quality tiers:**
   - ⭐⭐⭐⭐⭐ Curated analysis (keep)
   - ⭐⭐⭐ Reference material (user decides)
   - ⭐⭐ Raw dumps/clones (recommend delete)

4. **Don't recommend deleting knowledge assets without reading them first.** User may have spent significant effort creating them.
