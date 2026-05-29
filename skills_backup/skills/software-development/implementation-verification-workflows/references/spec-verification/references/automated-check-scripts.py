#!/usr/bin/env python3
"""Reusable verification scripts for checking code vs spec docs.

Usage: Copy and adapt for your specific project. Each function is standalone.

Patterns from slot-datamaking S1-S8 dataset verification.
"""
import re
import os


def count_levels_in_doc(doc_path):
    """Count level definitions in a spec doc.
    Handles both '## Level N' and '## [简单/复杂] Level N' formats.
    """
    with open(doc_path) as f:
        text = f.read()
    matches = re.findall(r'## \[(?:简单|复杂)\] Level (\d+)', text)
    if not matches:
        matches = re.findall(r'## Level (\d+)', text)
    return sorted(set(int(x) for x in matches))


def count_levels_in_script(script_path):
    """Count level definitions in a Python generation script."""
    with open(script_path) as f:
        text = f.read()
    matches = re.findall(r'(?:if|elif) level_id == (\d+)', text)
    return sorted(set(int(x) for x in matches))


def verify_level_counts(base, doc_names, script_pattern):
    """Verify level counts match between docs and scripts.

    Args:
        base: Project base path
        doc_names: dict mapping scene number to doc subdirectory name
        script_pattern: format string for script paths, e.g. '{base}/generate_s{i}_dataset.py'
    """
    for i, name in doc_names.items():
        doc_path = os.path.join(base, f"docs/{name}/参数配置.md")
        script_path = script_pattern.format(base=base, i=i)
        doc_levels = count_levels_in_doc(doc_path)
        script_levels = count_levels_in_script(script_path)
        status = "✓" if doc_levels == script_levels else "✗"
        print(f"  S{i}: doc={len(doc_levels)} {doc_levels}, script={len(script_levels)} {script_levels} {status}")


def verify_views_keys(script_path, expected_keys):
    """Verify VIEWS dict has the expected top-level keys (catches nesting bugs)."""
    with open(script_path) as f:
        text = f.read()
    m = re.search(r'VIEWS\s*=\s*\{(.*?)\n\}', text, re.DOTALL)
    if not m:
        return False, "VIEWS not found"
    keys = re.findall(r'^    "(\w+)"', m.group(1), re.M)
    return set(keys) == set(expected_keys), keys


def verify_ground_spec(script_path, expected_size, expected_friction):
    """Verify ground_spec function matches expected values."""
    with open(script_path) as f:
        text = f.read()
    m = re.search(r'def ground_spec\(.*?return ObjectSpec\(', text, re.DOTALL)
    if not m:
        return False, "ground_spec not found"
    # Extract size
    size_m = re.search(r'size = \(([^)]+)\)', text[m.start():m.end()+200])
    size = size_m.group(1).strip() if size_m else "?"
    return expected_size in size, f"size={size}"


def verify_level_targets(script_path, expected_targets):
    """Verify LEVEL_TARGETS dict matches expected values."""
    with open(script_path) as f:
        text = f.read()
    m = re.search(r'LEVEL_TARGETS\s*=\s*\{([^}]+)\}', text)
    if not m:
        return False, "LEVEL_TARGETS not found"
    pairs = re.findall(r'(\d+)\s*:\s*(\d+)', m.group(1))
    targets = {int(k): int(v) for k, v in pairs}
    return targets == expected_targets, targets


def verify_global_params(script_path):
    """Extract and verify global rendering parameters."""
    with open(script_path) as f:
        text = f.read()
    params = {}
    for line in text.split('\n'):
        if line.startswith('FPS ='): params['fps'] = int(line.split('=')[1].strip())
        elif line.startswith('NUM_FRAMES ='): params['frames'] = int(line.split('=')[1].strip())
        elif line.startswith('DURATION_S ='): params['duration'] = float(line.split('=')[1].strip())
        elif line.startswith('RESOLUTION ='): params['resolution'] = int(line.split('=')[1].strip())
    return params


def verify_default_views(script_path, expected_views):
    """Verify the default --views argument matches expected list."""
    with open(script_path) as f:
        text = f.read()
    m = re.search(r'--views.*default=\[([^\]]+)\]', text)
    if not m:
        return False, "no --views default"
    views = [v.strip().strip('"').strip("'") for v in m.group(1).split(",")]
    return set(views) == set(expected_views), views


def verify_label_integration(script_path):
    """Check if physics_label_utils is imported and used."""
    with open(script_path) as f:
        text = f.read()
    has_import = 'from physics_label_utils import' in text
    has_call = 'compute_physics_labels' in text
    return has_import and has_call
