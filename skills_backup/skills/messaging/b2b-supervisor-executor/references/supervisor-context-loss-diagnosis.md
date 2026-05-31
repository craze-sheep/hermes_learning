# Supervisor Context Loss Diagnosis (2026-05-31)

## Symptom

Supervisor marks task as DONE after first Worker report, even though the task has multiple phases (e.g., R1 + R2). User complains: "你都设置done了但是任务还没完成啊".

## Root Cause (code-level)

In `code/bot2bot/service.py`, `manager_decide()` (line 563) builds the Supervisor LLM prompt with:

```python
user_prompt = f"""任务 ID：{state.task_id}
用户需求：{state.user_text}
当前短摘要：{state.summary}
已联系过的角色：{', '.join(state.contacted_roles) or '无'}
新收到的信息：{incoming}
...
"""
```

### Problems:

1. **`state.summary` is overwritten each turn** (line 604: `state.summary = summary`). After R1 completes, the summary only contains R1's handoff summary — not the original task decomposition or progress.

2. **No subtask/progress tracking.** The TaskState has no field for "how many subtasks completed vs total". The LLM sees "Researcher reported done" but doesn't see "15/20 papers completed, 5 remaining".

3. **`contacted_roles` only tracks workers** (line 776-777). It records `["Planner", "Researcher"]` but not what each role accomplished or what remains.

4. **`state.completed` is set by LLM output** (line 605-606). If LLM outputs `TARGET_ROLE: DONE`, the code sets `state.completed = True` with zero validation. Subsequent messages hit `if state.completed: return` (line 791-793) and are silently ignored.

### Why the LLM outputs DONE prematurely:

The LLM sees:
- "用户需求：完成20篇论文分析..."
- "当前短摘要：[R1的handoff summary]"
- "新收到的信息：[R1报告说完成了]"

It doesn't see:
- "R1完成了15篇，还剩5篇需要R2"
- "子任务列表：R0 ✅, R1 ✅, R2 ❌"

So it reasonably concludes "the worker said it's done, task is done".

## Fix Options

### Option A: Code-level guard (recommended)
In `manager_decide()`, before allowing `TARGET_ROLE: DONE`:
1. Check if the original task has identifiable subtasks/phases
2. If subtasks exist and not all are complete, override DONE → dispatch next worker
3. Inject progress info into the prompt (e.g., "已完成：15/20篇，剩余：#16-20")

### Option B: Enhanced prompt
Add to `manager_decide()` system_prompt:
```
收到 worker 回报后，检查用户需求是否完全满足。
如果任务包含多批次/多阶段工作（如"20篇论文"分多批完成），
只有当所有批次/阶段都完成时才能 DONE。
在 HANDOFF_SUMMARY 中记录当前进度（如"15/20完成"）。
```

### Option C: Structured goal tracking
Add `/goal` command that creates a structured subtask list in TaskState.
The prompt then includes: "目标进度：3/5 子任务完成".
Supervisor CANNOT output DONE until all subtasks are checked.

## Related Code Locations

- `service.py:534` — `manager_start_task()` creates TaskState
- `service.py:563` — `manager_decide()` builds LLM prompt
- `service.py:605` — `state.completed = True` on DONE
- `service.py:776` — `contacted_roles.append(role)` in worker_reply
- `service.py:791` — `if state.completed: return` blocks re-dispatch
