---
name: project-progress-review
description: "Review project completion status: scan directories, READMEs, git status, code files, and produce a structured progress summary."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Project-Management, Review, Progress-Tracking, Documentation]
    related_skills: [codebase-inspection, github-issues]
---

# Project Progress Review

Review a project's completion status by systematically scanning its structure, documentation, code, and git history. Produces a structured status matrix showing what's done, in-progress, and pending.

## When to Use

- User asks "项目完成到哪一步了" / "how far along is the project"
- User asks to review project status or check progress
- Periodic project health checks before planning next steps

## Prerequisites

- Project directory with some combination of: README files, task directories, source code, git repo
- read_file, search_files, terminal tools available

## Workflow

### Step 1: Top-Level Orientation

Get the big picture first:

```python
# 1. List top-level files (README, docs, config)
search_files(pattern="README*", target="files", path=".")
search_files(pattern="*.md", target="files", path=".")

# 2. Check git status
terminal(command="git status")

# 3. List top-level directory structure to understand task organization
search_files(pattern="*", target="files", path=".", limit=30)
```

### Step 2: Read Project Overview

Read the main project README or overview document to understand:
- Project goals and scope
- How tasks/modules are organized
- What constitutes "done" for each component

### Step 3: Scan Each Task/Module

For each major directory or task:

1. **Check for README** — read it to understand task goals, status, deliverables
2. **Check for code files** — `search_files(pattern="*.py", ...)` or other relevant extensions
3. **Check for output artifacts** — videos, images, JSON results, reports
4. **Check for validation** — test results, validation scripts, review documents

Use `execute_code` to batch-process multiple directories efficiently:

```python
from hermes_tools import search_files, read_file
import os

# Find all task directories
tasks = search_files(pattern="task*", target="files", path=".")

# For each task, check for README and key files
for task_dir in task_dirs:
    readme = read_file(f"{task_dir}/README.md")
    # analyze content...
```

### Step 4: Categorize Status

For each task/module, classify into one of:

| Status | Meaning |
|--------|---------|
| ✅ 完成 | All deliverables present, validated |
| 🔄 进行中 | Some deliverables done, work ongoing |
| ⏳ 待开始 | Design/planning done, execution pending |
| ❌ 未开始 | No work done yet |

### Step 5: Produce Summary

Output a structured summary with:

1. **Project overview** — name, goal, scope
2. **Task-by-task status table** — with specific evidence (files found, artifacts present)
3. **Overall progress percentage** — based on task completion weighting
4. **Next steps** — what needs to happen next

## Summary Format Template

```markdown
## 📊 项目进展

### ✅ 已完成
- **Task X**: [what was done] — [evidence: files, artifacts]

### 🔄 进行中
- **Task Y**: [what's done] / [what remains] — [evidence]

### ⏳ 待开始
- **Task Z**: [planning done, execution pending] — [evidence]

### 总体进度
| 阶段 | 状态 | 完成度 |
|------|------|--------|
| 设计 | ✅ | 100% |
| 实现 | 🔄 | 50% |
| 验证 | ⏳ | 0% |

### 下一步建议
1. [most important next action]
2. [second priority]
```

## Pitfalls

1. **Don't just list files** — read the content to understand actual completion. A README existing doesn't mean the task is done; read it to check if it describes completed work or just plans.

2. **Check for actual outputs vs. just specs** — A directory with only `参数配置.md` is planning; a directory with `*.mp4` or `*.json` results is execution. Distinguish design artifacts from implementation artifacts.

3. **Git status matters** — uncommitted changes may indicate work-in-progress that isn't reflected in the file structure yet.

4. **Don't assume linear progress** — some tasks may be done out of order, some may be blocked. Report what you actually find, not what the numbering suggests.

5. **Scale appropriately** — for small projects (< 10 files), read everything. For large projects, sample strategically: read READMEs fully, spot-check code/outputs.

6. **Respect the user's language** — if the user writes in Chinese, produce the summary in Chinese. Match their communication style.

## Example Usage

When user says "看看我的项目完成到哪一步了":

1. search_files for README files and directory structure
2. read_file each README to understand task goals and stated status
3. search_files for code files (*.py), output files (*.mp4, *.json, *.csv)
4. terminal git status for overall repo health
5. Synthesize into status table with evidence
