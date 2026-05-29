#!/usr/bin/env python3
"""
Reusable verification script for checking code against design specs.
Adapt the data structures for your specific project.

Usage: python3 verify_spec.py
"""
import re, os, sys

# ============================================
# CONFIGURATION - Adapt to your project
# ============================================
BASE = "/path/to/project"

SCRIPTS = {
    "S1": ("scripts/generate_s1.py", "docs/S1_spec.md"),
    "S2": ("scripts/generate_s2.py", "docs/S2_spec.md"),
    # ... add more
}

EXPECTED_VIEWS = {
    "S1": ["front", "top"],
    "S2": ["front", "top", "left"],
}

EXPECTED_GROUND = {
    "S1": {"size": "(8.0, 6.0, 0.08)", "friction": "0.5"},
}

EXPECTED_LEVEL_TARGETS = {
    "S1": {1: 100, 2: 100, 3: 150},
}

# ============================================
# CHECK FUNCTIONS
# ============================================
issues = []

def check(scene, msg):
    issues.append(f"{scene}: {msg}")
    print(f"  ✗ {scene}: {msg}")

def ok(scene, msg):
    print(f"  ✓ {scene}: {msg}")

def read(path):
    with open(os.path.join(BASE, path)) as f:
        return f.read()

def check_global_params(scenes):
    """Check FPS, frames, duration, resolution, gravity."""
    print("=" * 60)
    print("CHECK: Global Rendering Parameters")
    print("=" * 60)
    for name, (script_path, _) in scenes.items():
        text = read(script_path)
        fps = re.search(r'^FPS\s*=\s*(\d+)', text, re.M)
        frames = re.search(r'^NUM_FRAMES\s*=\s*(\d+)', text, re.M)
        dur = re.search(r'^DURATION_S\s*=\s*([\d.]+)', text, re.M)
        res = re.search(r'^RESOLUTION\s*=\s*(\d+)', text, re.M)
        grav = re.search(r'^GRAVITY\s*=\s*\(([^)]+)\)', text, re.M)

        vals = {
            "FPS": fps.group(1) if fps else "?",
            "frames": frames.group(1) if frames else "?",
            "duration": dur.group(1) if dur else "?",
            "resolution": res.group(1) if res else "?",
            "gravity": grav.group(1) if grav else "?",
        }
        all_ok = (vals["FPS"] == "12" and vals["frames"] == "36"
                  and vals["duration"] == "3.0" and vals["resolution"] == "128"
                  and "-9.8" in vals["gravity"])
        if all_ok:
            ok(name, f"FPS={vals['FPS']} frames={vals['frames']} dur={vals['duration']} res={vals['resolution']}")
        else:
            check(name, f"Global params mismatch: {vals}")

def check_level_counts(scenes):
    """Check level/item counts match between doc and script."""
    print("\n" + "=" * 60)
    print("CHECK: Level/Item Counts")
    print("=" * 60)
    for name, (script_path, doc_path) in scenes.items():
        text = read(script_path)
        script_levels = sorted(set(int(x) for x in re.findall(r'(?:if|elif) level_id == (\d+)', text)))

        doc_text = read(doc_path)
        # Adapt regex to your doc format
        doc_levels = sorted(set(int(x[1]) for x in re.findall(r'## \[.*?\] Level (\d+)', doc_text)))

        if not doc_levels:
            # Try alternative format
            doc_levels = sorted(set(int(x) for x in re.findall(r'## Level (\d+)', doc_text)))

        if set(script_levels) == set(doc_levels):
            ok(name, f"{len(script_levels)} levels match")
        else:
            missing = set(doc_levels) - set(script_levels)
            extra = set(script_levels) - set(doc_levels)
            if missing:
                check(name, f"Missing levels in script: {sorted(missing)}")
            if extra:
                check(name, f"Extra levels in script: {sorted(extra)}")

def check_views(scenes):
    """Check VIEWS dict top-level keys and default views."""
    print("\n" + "=" * 60)
    print("CHECK: Camera Views")
    print("=" * 60)
    for name, (script_path, _) in scenes.items():
        text = read(script_path)
        m = re.search(r'VIEWS\s*=\s*\{(.*?)\n\}', text, re.DOTALL)
        if m:
            top_keys = re.findall(r'^    "(\w+)"', m.group(1), re.M)
            expected = EXPECTED_VIEWS.get(name, [])
            if set(top_keys) == set(expected):
                ok(name, f"VIEWS: {top_keys}")
            else:
                check(name, f"VIEWS keys={top_keys}, expected={expected}")
        else:
            check(name, "VIEWS dict not found")

        # Check default views arg
        dm = re.search(r'--views.*default=\[([^\]]+)\]', text)
        if dm:
            defaults = [v.strip().strip('"').strip("'") for v in dm.group(1).split(",")]
            expected_default = EXPECTED_VIEWS.get(name, [])
            if set(defaults) == set(expected_default):
                ok(name, f"Default views: {defaults}")
            else:
                check(name, f"Default views={defaults}, expected={expected_default}")

def check_ground_params(scenes):
    """Check ground/base object size and friction."""
    print("\n" + "=" * 60)
    print("CHECK: Ground Parameters")
    print("=" * 60)
    for name, (script_path, _) in scenes.items():
        text = read(script_path)
        gs = re.search(r'def ground_spec\([^)]*\)\s*(?:->[^:]*):?\s*\n(.*?)(?:\n    return|\n\ndef)', text, re.DOTALL)
        if gs:
            body = gs.group(1)
            size_m = re.search(r'size\s*=\s*\(([^)]+)\)', body)
            if size_m:
                size = f"({size_m.group(1).strip()})"
                expected_size = EXPECTED_GROUND.get(name, {}).get("size", "")
                if expected_size and expected_size not in size:
                    check(name, f"Ground size={size}, expected={expected_size}")
                else:
                    ok(name, f"Ground size={size}")

def check_label_integration(scenes):
    """Check if physics/analysis labels are integrated."""
    print("\n" + "=" * 60)
    print("CHECK: Label Integration")
    print("=" * 60)
    for name, (script_path, _) in scenes.items():
        text = read(script_path)
        if "physics_label" in text or "compute_labels" in text or "label_utils" in text:
            ok(name, "Labels integrated")
        else:
            check(name, "Labels NOT integrated")

# ============================================
# MAIN
# ============================================
if __name__ == "__main__":
    check_global_params(SCRIPTS)
    check_level_counts(SCRIPTS)
    check_views(SCRIPTS)
    check_ground_params(SCRIPTS)
    check_label_integration(SCRIPTS)

    print("\n" + "=" * 60)
    print(f"Total issues: {len(issues)}")
    print("=" * 60)
    for issue in issues:
        print(f"  {issue}")
    if not issues:
        print("  All checks passed!")
    sys.exit(1 if issues else 0)
