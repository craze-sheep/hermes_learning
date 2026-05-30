#!/usr/bin/env python3
"""Quick triage scan for B2B task artifacts.

Usage: python3 triage.py <task_dir>

Checks:
1. Execution chain completeness (all dispatched workers have reports?)
2. Fallback detection (any worker used local fallback?)
3. Template vs deliverable (files/ has real content?)
4. Working directory state (does actual FS reflect claimed work?)
5. Handoff summary length violations

Output: structured findings to stdout.
"""

import re
import sys
from pathlib import Path


def scan_task(task_dir: str) -> None:
    p = Path(task_dir)
    if not p.exists():
        print(f"ERROR: {task_dir} does not exist")
        sys.exit(1)

    print(f"=== B2B Task Triage: {p.name} ===\n")

    # 1. Check README for task definition
    readme = p / "README.md"
    if readme.exists():
        content = readme.read_text()
        # Extract working directory from user task
        wd_match = re.search(r"工作目录[是为：:\s]+(\S+)", content)
        work_dir = wd_match.group(1) if wd_match else None
        print(f"[INFO] Working directory: {work_dir or 'not specified'}")
    else:
        work_dir = None
        print("[WARN] No README.md found")

    # 2. Check execution chain
    print("\n--- Execution Chain ---")
    supervisor_dir = p / "supervisor"
    if supervisor_dir.exists():
        assigns = list(supervisor_dir.glob("assign-*.md"))
        for assign_file in sorted(assigns):
            content = assign_file.read_text()
            # Extract target role
            role_match = re.search(r"assign-(\w+)", assign_file.name)
            role = role_match.group(1) if role_match else "unknown"
            
            # Check if worker has a report
            worker_dir = p / role.replace("planner", "planner").replace("researcher", "researcher")
            # Try multiple directory name patterns
            found_report = False
            for candidate in [role, role.replace("assign-", "")]:
                candidate_dir = p / candidate
                if candidate_dir.exists() and list(candidate_dir.glob("*.md")):
                    found_report = True
                    break
            
            status = "OK" if found_report else "MISSING REPORT"
            print(f"  ASSIGN -> {role}: {status}")
            
            # Check for fallback in any worker report
            for worker_name in ["planner", "researcher", "developer", "tester"]:
                wdir = p / worker_name
                if wdir.exists():
                    for report in wdir.glob("*.md"):
                        rcontent = report.read_text()
                        if "本地 fallback" in rcontent or "模型不可用" in rcontent:
                            print(f"  [CRITICAL] Fallback detected in {worker_name}/{report.name}")
    else:
        print("  No supervisor directory found")

    # 3. Check files/ directory
    print("\n--- Files Directory ---")
    files_dir = p / "files"
    if files_dir.exists():
        all_files = list(files_dir.rglob("*"))
        md_files = [f for f in all_files if f.suffix == ".md"]
        print(f"  Total files: {len(all_files)}, Markdown: {len(md_files)}")
        
        for md in md_files:
            content = md.read_text()
            # Check for placeholders
            placeholders = re.findall(r"<[^>]+>", content)
            empty_cells = content.count("||") 
            todo_markers = len(re.findall(r"待填写|TODO|placeholder|待执行|待验证", content, re.I))
            
            if placeholders or empty_cells > 5 or todo_markers:
                print(f"  [WARN] {md.relative_to(files_dir)}: {len(placeholders)} placeholders, {empty_cells} empty cells, {todo_markers} TODO markers")
            else:
                print(f"  [OK] {md.relative_to(files_dir)}: appears complete")
    else:
        print("  No files/ directory")

    # 4. Check working directory
    print("\n--- Working Directory ---")
    if work_dir:
        wd = Path(work_dir)
        if wd.exists():
            contents = list(wd.rglob("*"))
            if contents:
                print(f"  {len(contents)} files found in {work_dir}")
            else:
                print(f"  [CRITICAL] Working directory exists but is EMPTY")
        else:
            print(f"  [CRITICAL] Working directory does NOT exist: {work_dir}")
    else:
        print("  [SKIP] No working directory specified")

    # 5. Check handoff summary lengths
    print("\n--- Handoff Summary Lengths ---")
    for md_file in p.rglob("*.md"):
        content = md_file.read_text()
        summary_match = re.search(r"## Handoff Summary\s*\n\s*\n(.+?)(?=\n##|\Z)", content, re.DOTALL)
        if summary_match:
            summary = summary_match.group(1).strip()
            if len(summary) > 300:
                print(f"  [WARN] {md_file.relative_to(p)}: summary is {len(summary)} chars (limit: 300)")

    print("\n=== Triage Complete ===")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <task_dir>")
        sys.exit(1)
    scan_task(sys.argv[1])
