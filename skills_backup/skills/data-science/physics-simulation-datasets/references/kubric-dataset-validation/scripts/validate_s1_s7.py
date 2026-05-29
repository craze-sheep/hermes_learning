#!/usr/bin/env python3
"""
S1-S7 Dataset Validation Script (validated version)
Checks: file completeness, JSON structure, depth maps, segmentation masks, cross-view consistency.

Usage: /home/lzy/miniconda3/bin/python3 -u validate_s1_s7.py

Key design decisions:
- File naming: {id}.mp4 / {id}.npz (NOT 1.mp4)
- object_static.json keys: object_type/size/mass (NOT shape/position)
- Depth npz: (36,128,128) all frames, NOT (128,128)
- Seg npz key: 'mask', NOT 'segmentation'
- Phased approach for performance on 20K+ samples
"""

import json, os, sys, numpy as np
from collections import defaultdict, Counter

DB = "/home/lzy/project/slot-datamaking/database"
VIEWS = {'S1':2,'S2':3,'S3':3,'S4':2,'S5':5,'S6':5,'S7':5}
FRAMES = 36

errors = []
warnings = []
stats = {}

def err(msg): errors.append(msg)
def warn(msg): warnings.append(msg)
def log(msg): print(msg, flush=True)

log("=" * 60)
log("S1-S7 Data Validation")
log("=" * 60)

for scene in ['S1','S2','S3','S4','S5','S6','S7']:
    sd = os.path.join(DB, scene)
    if not os.path.isdir(sd):
        err(f"{scene}: directory not found"); continue
    levels = sorted([d for d in os.listdir(sd) if os.path.isdir(os.path.join(sd, d))],
                   key=lambda x: int(x[1:]) if x[1:].isdigit() else 0)

    for lv in levels:
        ld = os.path.join(sd, lv)
        sample_ids = sorted([int(d) for d in os.listdir(ld) if os.path.isdir(os.path.join(ld, str(d)))])
        if not sample_ids: continue

        n = len(sample_ids)
        stats[f'{scene}/{lv}_count'] = n

        # Sequence continuity
        expected = list(range(1, n+1))
        if sample_ids != expected:
            gaps = sorted(set(expected) - set(sample_ids))
            if gaps: err(f"{scene}/{lv}: missing IDs {gaps[:20]}")

        # File completeness for ALL samples
        missing_mp4, missing_npz, missing_vjson, missing_sjson, missing_dyn = [], [], [], [], []
        bad_frame_count = []

        # Sampling for depth/seg checks
        sample_indices = set()
        for i in range(min(5, n)): sample_indices.add(i)
        for i in range(max(0, n//2-2), min(n//2+3, n)): sample_indices.add(i)
        for i in range(max(0, n-5), n): sample_indices.add(i)

        seg_zero_samples = []
        depth_issues = []

        for idx in range(n):
            sid = sample_ids[idx]
            sp = os.path.join(ld, str(sid))

            # File existence (using correct naming: {id}.mp4 not 1.mp4)
            if not os.path.isfile(os.path.join(sp, f'{sid}.mp4')): missing_mp4.append(sid)
            if not os.path.isfile(os.path.join(sp, f'{sid}.npz')): missing_npz.append(sid)
            if not os.path.isfile(os.path.join(sp, 'video.json')): missing_vjson.append(sid)
            if not os.path.isfile(os.path.join(sp, 'object_static.json')): missing_sjson.append(sid)

            dyn = os.path.join(sp, 'dynamic')
            if not os.path.isdir(dyn):
                missing_dyn.append(sid)
                continue

            frames = [int(f) for f in os.listdir(dyn) if f.isdigit()]
            if len(frames) != FRAMES:
                bad_frame_count.append((sid, len(frames)))

            # Sampled depth/seg checks
            if idx in sample_indices:
                npz_path = os.path.join(sp, f'{sid}.npz')
                if os.path.isfile(npz_path):
                    try:
                        d = np.load(npz_path)
                        if 'depth' in d:
                            dep = d['depth']
                            if dep.shape not in [(36,128,128), (128,128)]:
                                depth_issues.append(f"{sid}: shape={dep.shape}")
                            if np.all(dep == 0):
                                depth_issues.append(f"{sid}: depth all-zero")
                    except Exception as e:
                        depth_issues.append(f"{sid}: read failed {e}")

                check_frames = [frames[0], frames[len(frames)//2], frames[-1]] if len(frames) >= 3 else frames
                for fn in check_frames:
                    fp = os.path.join(dyn, str(fn))
                    seg_dir = os.path.join(fp, 'object_segment')
                    if os.path.isdir(seg_dir):
                        for sf in os.listdir(seg_dir):
                            if sf.endswith('.npz'):
                                try:
                                    sg = np.load(os.path.join(seg_dir, sf))
                                    keys = list(sg.keys())
                                    if keys:
                                        arr = sg[keys[0]]
                                        if np.all(arr == 0):
                                            seg_zero_samples.append(f"{sid}/dynamic/{fn}/seg/{sf}")
                                except: pass

        # Report per-level
        if missing_mp4: err(f"{scene}/{lv}: missing mp4 ({len(missing_mp4)}): {missing_mp4[:10]}")
        if missing_npz: err(f"{scene}/{lv}: missing npz ({len(missing_npz)}): {missing_npz[:10]}")
        if missing_vjson: err(f"{scene}/{lv}: missing video.json ({len(missing_vjson)}): {missing_vjson[:10]}")
        if missing_sjson: err(f"{scene}/{lv}: missing object_static.json ({len(missing_sjson)}): {missing_sjson[:10]}")
        if missing_dyn: err(f"{scene}/{lv}: missing dynamic/ ({len(missing_dyn)}): {missing_dyn[:10]}")
        if bad_frame_count: err(f"{scene}/{lv}: bad frame count ({len(bad_frame_count)}): {bad_frame_count[:5]}")
        if depth_issues: err(f"{scene}/{lv}: depth issues: {depth_issues}")
        if seg_zero_samples:
            if len(seg_zero_samples) > 10:
                warn(f"{scene}/{lv}: seg all-zero ({len(seg_zero_samples)}): {seg_zero_samples[:5]}...")
            else:
                warn(f"{scene}/{lv}: seg all-zero ({len(seg_zero_samples)}): {seg_zero_samples}")

        stats[f'{scene}/{lv}_seg_zero'] = len(seg_zero_samples)
        log(f"  {scene}/{lv}: {n} samples, seg_zero={len(seg_zero_samples)}, missing_files={len(missing_mp4)+len(missing_vjson)}")

# JSON structure (sampled)
log("\n--- JSON Structure ---")
for scene in ['S1','S2','S3','S4','S5','S6','S7']:
    sd = os.path.join(DB, scene)
    if not os.path.isdir(sd): continue
    levels = sorted([d for d in os.listdir(sd) if os.path.isdir(os.path.join(sd, d))],
                   key=lambda x: int(x[1:]) if x[1:].isdigit() else 0)
    for lv in levels:
        ld = os.path.join(sd, lv)
        sample_ids = sorted([int(d) for d in os.listdir(ld) if os.path.isdir(os.path.join(ld, str(d)))])
        if not sample_ids: continue
        n = len(sample_ids)
        indices = list(range(min(3, n))) + list(range(n//2, min(n//2+3, n))) + list(range(max(0,n-3), n))
        indices = sorted(set(i for i in indices if 0 <= i < n))

        views, obj_counts = [], []
        for idx in indices:
            sid = sample_ids[idx]
            sp = os.path.join(ld, str(sid))
            vj = os.path.join(sp, 'video.json')
            if os.path.isfile(vj):
                try:
                    vd = json.load(open(vj))
                    nf = vd.get('num_frames', 0)
                    if nf != FRAMES: err(f"{scene}/{lv}/{sid}: num_frames={nf}")
                    cam = vd.get('cameras', [{}])[0]
                    views.append(cam.get('view_name', '?'))
                    res = cam.get('resolution', [])
                    if res != [128,128]: warn(f"{scene}/{lv}/{sid}: resolution {res}")
                except: err(f"{scene}/{lv}/{sid}: video.json parse error")
            oj = os.path.join(sp, 'object_static.json')
            if os.path.isfile(oj):
                try:
                    od = json.load(open(oj))
                    obj_counts.append(len(od))
                except: err(f"{scene}/{lv}/{sid}: object_static.json parse error")

        if views:
            log(f"  {scene}/{lv}: views={Counter(views).most_common()}, obj_count={set(obj_counts)}")

# Cross-view consistency
log("\n--- Cross-View Consistency ---")
for scene in ['S1','S2','S3','S4','S5','S6','S7']:
    sd = os.path.join(DB, scene)
    if not os.path.isdir(sd): continue
    nv = VIEWS[scene]
    levels = sorted([d for d in os.listdir(sd) if os.path.isdir(os.path.join(sd, d))],
                   key=lambda x: int(x[1:]) if x[1:].isdigit() else 0)
    for lv in levels:
        ld = os.path.join(sd, lv)
        sample_ids = sorted([int(d) for d in os.listdir(ld) if os.path.isdir(os.path.join(ld, str(d)))])
        if len(sample_ids) < nv: continue
        events = [sample_ids[i:i+nv] for i in range(0, len(sample_ids), nv)]
        events = [e for e in events if len(e) == nv]

        check = events[:3] + (events[-1:] if len(events) > 3 else [])
        issues = 0
        for ev in check:
            statics, views = [], []
            for sid in ev:
                oj = os.path.join(ld, str(sid), 'object_static.json')
                vj = os.path.join(ld, str(sid), 'video.json')
                if os.path.isfile(oj) and os.path.isfile(vj):
                    try:
                        sdata = json.load(open(oj))
                        vdata = json.load(open(vj))
                        statics.append((sid, sdata))
                        views.append(vdata['cameras'][0]['view_name'])
                    except: pass
            if len(set(views)) < len(views):
                err(f"{scene}/{lv} event{ev}: duplicate views {views}"); issues += 1
            if len(statics) >= 2:
                ref_id, ref = statics[0]
                for sid, sdata in statics[1:]:
                    if len(sdata) != len(ref):
                        err(f"{scene}/{lv} event{ev}: object count mismatch"); issues += 1; continue
                    for i, (rob, tob) in enumerate(zip(ref, sdata)):
                        for k in ['object_type','mass','size','lateralFriction','restitution','color_name']:
                            if k in rob and k in tob:
                                rv, tv = rob[k], tob[k]
                                if rv is None and tv is None: continue
                                if rv != tv:
                                    err(f"{scene}/{lv} event{ev}: obj[{i}].{k} mismatch: {rv} vs {tv}"); issues += 1
            # Dynamic frame 1 consistency
            dyn_objs = []
            for sid in ev:
                dp = os.path.join(ld, str(sid), 'dynamic', '1', 'object_dynamicjson')
                if os.path.isdir(dp):
                    objs = {}
                    for jf in sorted(os.listdir(dp)):
                        if jf.endswith('.json'):
                            try: objs[jf] = json.load(open(os.path.join(dp, jf)))
                            except: pass
                    dyn_objs.append((sid, objs))
            if len(dyn_objs) >= 2:
                ref_id, ref_d = dyn_objs[0]
                for sid, dd in dyn_objs[1:]:
                    for k in set(ref_d.keys()) & set(dd.keys()):
                        for pk in ['position','velocity','angular_velocity']:
                            if pk in ref_d[k] and pk in dd[k]:
                                rv, tv = ref_d[k][pk], dd[k][pk]
                                if isinstance(rv,list) and isinstance(tv,list):
                                    for j,(a,b) in enumerate(zip(rv,tv)):
                                        if isinstance(a,(int,float)) and isinstance(b,(int,float)):
                                            if abs(a-b) > 1e-4:
                                                err(f"{scene}/{lv} event{ev} frame1 {k}.{pk}[{j}]: {ref_id}={a:.6f} vs {sid}={b:.6f}")
                                                issues += 1
        status = "✅" if issues == 0 else f"❌ ({issues} issues)"
        log(f"  {scene}/{lv}: cross-view {status} ({len(events)} events, checked {len(check)})")

# Summary
log("\n" + "=" * 60)
log("VALIDATION SUMMARY")
log("=" * 60)
log(f"Total errors: {len(errors)}")
log(f"Total warnings: {len(warnings)}")
if errors:
    log(f"\n--- ERRORS ({len(errors)}) ---")
    for e in errors: log(f"  ❌ {e}")
if warnings:
    log(f"\n--- WARNINGS ({len(warnings)}) ---")
    for w in warnings[:50]: log(f"  ⚠️ {w}")
    if len(warnings) > 50: log(f"  ... and {len(warnings)-50} more")
log("\n--- STATS ---")
for k,v in sorted(stats.items()): log(f"  {k}: {v}")
