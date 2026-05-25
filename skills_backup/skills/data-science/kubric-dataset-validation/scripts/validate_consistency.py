#!/usr/bin/env python3
"""
S1-S7 Dataset Consistency Validation (v2 — corrected file naming)
Checks: cross-view physics consistency, JSON structure, depth maps, object types.
Excludes S3 by default. Run with miniconda3 python.
"""
import json, os, sys, numpy as np
from collections import defaultdict, Counter

DB = "/home/lzy/project/slot-datamaking/database"
VIEWS = {'S1':2,'S2':3,'S4':2,'S5':5,'S6':5,'S7':5}
FRAMES = 36
CHECK_SCENES = ['S1','S2','S4','S5','S6','S7']

errors = []
warnings = []
stats = {}

def err(msg): errors.append(msg)
def warn(msg): warnings.append(msg)
def log(msg): print(msg, flush=True)

log("=" * 60)
log("S1/S2/S4-S7 全面一致性验证 (排除S3)")
log("=" * 60)

for scene in CHECK_SCENES:
    sd = os.path.join(DB, scene)
    if not os.path.isdir(sd): continue
    nv = VIEWS[scene]
    levels = sorted([d for d in os.listdir(sd) if os.path.isdir(os.path.join(sd, d))],
                   key=lambda x: int(x[1:]) if x[1:].isdigit() else 0)
    
    for lv in levels:
        ld = os.path.join(sd, lv)
        sample_ids = sorted([int(d) for d in os.listdir(ld) if os.path.isdir(os.path.join(ld, str(d)))])
        if not sample_ids: continue
        n = len(sample_ids)
        
        events = []
        for i in range(0, len(sample_ids), nv):
            group = sample_ids[i:i+nv]
            if len(group) == nv: events.append(group)
        
        cross_view_errors = 0
        cross_view_checked = 0
        
        for ev in events:
            statics = []
            views = []
            for sid in ev:
                oj = os.path.join(ld, str(sid), 'object_static.json')
                vj = os.path.join(ld, str(sid), 'video.json')
                if not os.path.isfile(oj) or not os.path.isfile(vj):
                    err(f"{scene}/{lv}/{sid}: 文件缺失")
                    continue
                try:
                    sdata = json.load(open(oj))
                    vdata = json.load(open(vj))
                    statics.append((sid, sdata))
                    views.append(vdata['cameras'][0]['view_name'])
                except Exception as e:
                    err(f"{scene}/{lv}/{sid}: 读取失败 {e}")
            
            if len(statics) < 2: continue
            cross_view_checked += 1
            
            if len(set(views)) < len(views):
                err(f"{scene}/{lv} 事件{ev}: 视角重复 {views}")
                cross_view_errors += 1
            
            ref_id, ref = statics[0]
            for sid, sdata in statics[1:]:
                if len(sdata) != len(ref):
                    err(f"{scene}/{lv} 事件{ev}: 物体数不一致")
                    cross_view_errors += 1
                    continue
                for i_obj, (rob, tob) in enumerate(zip(ref, sdata)):
                    for k in ['object_type', 'mass', 'size', 'lateralFriction', 'rollingFriction',
                              'spinningFriction', 'restitution', 'color_name', 'rgba', 'radius', 'height']:
                        if k in rob and k in tob:
                            rv, tv = rob[k], tob[k]
                            if rv is None and tv is None: continue
                            if rv != tv:
                                err(f"{scene}/{lv} 事件{ev}: obj[{i_obj}].{k}不一致")
                                cross_view_errors += 1
                
                check_frames_list = [1, FRAMES//2, FRAMES]
                for fn in check_frames_list:
                    ref_dyn = os.path.join(ld, str(ref_id), 'dynamic', str(fn), 'object_dynamicjson')
                    sid_dyn = os.path.join(ld, str(sid), 'dynamic', str(fn), 'object_dynamicjson')
                    if not os.path.isdir(ref_dyn) or not os.path.isdir(sid_dyn): continue
                    ref_files = sorted([f for f in os.listdir(ref_dyn) if f.endswith('.json')])
                    sid_files = sorted([f for f in os.listdir(sid_dyn) if f.endswith('.json')])
                    if ref_files != sid_files:
                        err(f"{scene}/{lv} 事件{ev} frame{fn}: 动态文件列表不一致")
                        cross_view_errors += 1
                        continue
                    for jf in ref_files:
                        try:
                            rd = json.load(open(os.path.join(ref_dyn, jf)))
                            td = json.load(open(os.path.join(sid_dyn, jf)))
                            for pk in ['position', 'velocity', 'angular_velocity']:
                                if pk in rd and pk in td:
                                    rv, tv = rd[pk], td[pk]
                                    if isinstance(rv, list) and isinstance(tv, list):
                                        for j, (a, b) in enumerate(zip(rv, tv)):
                                            if isinstance(a, (int,float)) and isinstance(b, (int,float)):
                                                if abs(a - b) > 1e-3:
                                                    err(f"{scene}/{lv} 事件{ev} frame{fn} {jf}.{pk}[{j}]: {ref_id}={a:.6f} vs {sid}={b:.6f}")
                                                    cross_view_errors += 1
                        except: pass
        
        obj_counts_in_level = set()
        for sid in sample_ids[:20]:
            oj = os.path.join(ld, str(sid), 'object_static.json')
            if os.path.isfile(oj):
                try:
                    od = json.load(open(oj))
                    obj_counts_in_level.add(len(od))
                except: pass
        
        log(f"  {scene}/{lv}: {len(events)}事件, 跨视角检查{cross_view_checked}个, 错误={cross_view_errors}, "
            f"物体数={obj_counts_in_level}")
        stats[f'{scene}/{lv}_events'] = len(events)
        stats[f'{scene}/{lv}_cross_errors'] = cross_view_errors

log("\n--- 跨level物体类型检查 ---")
for scene in CHECK_SCENES:
    sd = os.path.join(DB, scene)
    if not os.path.isdir(sd): continue
    levels = sorted([d for d in os.listdir(sd) if os.path.isdir(os.path.join(sd, d))],
                   key=lambda x: int(x[1:]) if x[1:].isdigit() else 0)
    for lv in levels:
        ld = os.path.join(sd, lv)
        sample_ids = sorted([int(d) for d in os.listdir(ld) if os.path.isdir(os.path.join(ld, str(d)))])
        if not sample_ids: continue
        oj = os.path.join(ld, str(sample_ids[0]), 'object_static.json')
        if os.path.isfile(oj):
            try:
                od = json.load(open(oj))
                types = [o.get('object_type', '?') for o in od]
                log(f"  {scene}/{lv}: 物体类型={types}")
            except: pass

log("\n--- 深度图抽样检查 ---")
for scene in CHECK_SCENES:
    sd = os.path.join(DB, scene)
    if not os.path.isdir(sd): continue
    levels = sorted([d for d in os.listdir(sd) if os.path.isdir(os.path.join(sd, d))],
                   key=lambda x: int(x[1:]) if x[1:].isdigit() else 0)
    for lv in levels:
        ld = os.path.join(sd, lv)
        sample_ids = sorted([int(d) for d in os.listdir(ld) if os.path.isdir(os.path.join(ld, str(d)))])
        if not sample_ids: continue
        n = len(sample_ids)
        indices = [0, n//4, n//2, 3*n//4, n-1]
        indices = sorted(set(i for i in indices if 0 <= i < n))
        for idx in indices:
            sid = sample_ids[idx]
            npz = os.path.join(ld, str(sid), f'{sid}.npz')
            if os.path.isfile(npz):
                try:
                    d = np.load(npz)
                    if 'depth' in d:
                        dep = d['depth']
                        if dep.shape not in [(36,128,128),(128,128)]:
                            err(f"{scene}/{lv}/{sid}: depth shape={dep.shape}")
                        if np.all(dep == 0):
                            err(f"{scene}/{lv}/{sid}: depth全零")
                        if np.any(np.isnan(dep)):
                            err(f"{scene}/{lv}/{sid}: depth含NaN")
                except Exception as e:
                    err(f"{scene}/{lv}/{sid}: depth读取失败 {e}")

cross_err_total = sum(v for k,v in stats.items() if k.endswith('_cross_errors'))
log(f"\n跨视角一致性: 共检查{sum(v for k,v in stats.items() if k.endswith('_events'))}个物理事件, 错误={cross_err_total}")
log(f"总错误: {len(errors)}, 总警告: {len(warnings)}")

if errors:
    log(f"\n--- 错误 ({len(errors)}条) ---")
    for e in errors:
        log(f"  ❌ {e}")
