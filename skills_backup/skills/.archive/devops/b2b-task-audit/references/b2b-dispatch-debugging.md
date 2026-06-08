# B2B Dispatch Flow Debugging

## Full Dispatch Architecture

```
User → Telegram @Supervisor → Supervisor Bot Polling → process_update()
  → manager_start_task() → manager_decide() → LLM → TARGET_ROLE
  → send_manager_decision() → normalize_manager_message() → [ASSIGN] format
  → send_as("Supervisor") → Telegram Group

Telegram Group → Researcher Bot Polling → process_update()
  → is_mentioned() && is_supervisor_assignment() && is_from_role()
  → worker_reply() → TmuxHermesClient.complete()
  → tmux paste-buffer → Hermes Agent processes → B2B_DONE
  → send_as(role, report) → Telegram Group

Telegram Group → Supervisor Bot Polling → manager_receive_report()
  → manager_decide() → LLM → DONE or next dispatch
```

## Key Code Locations (service.py)

| Line | Function | Purpose |
|------|----------|---------|
| 534 | `manager_start_task()` | Creates TaskState, calls manager_decide |
| 563 | `manager_decide()` | Sends prompt to Supervisor LLM, parses TARGET_ROLE |
| 600 | `complete_role()` | Calls TmuxHermesClient.complete() for Supervisor |
| 605 | DONE handling | `state.completed = True` when TARGET_ROLE == "DONE" |
| 636 | `send_manager_decision()` | Routes DONE/ASSIGN to Telegram |
| 680 | `worker_reply()` | Dispatches to worker tmux, waits for response |
| 783 | `manager_receive_report()` | Receives worker report, calls manager_decide again |
| 791 | **Blocking check** | `if state.completed: return` — blocks all post-DONE |
| 841-846 | Worker routing | `is_mentioned && is_supervisor_assignment && is_from_role` |

## Premature DONE Pattern

### Symptom
- Task state shows `completed: true` with `turns: 1`
- Supervisor tmux shows "dispatching R2 to researcher" but no researcher job created
- User complains task isn't done

### Root Cause Chain
1. Worker sends R1 report
2. `manager_receive_report()` → `manager_decide()` with R1 report as `incoming`
3. Supervisor LLM outputs `TARGET_ROLE: DONE` (misinterprets partial completion as full)
4. `state.completed = True` (line 605-606)
5. User sends follow-up → new task created (different task_id)
6. Or: user's message hits `manager_receive_report()` → `if state.completed: return` (line 791-793)
7. R2 never dispatched

### Why LLM Outputs DONE Prematurely
- Prompt only shows `当前短摘要` (last handoff summary), not cumulative progress
- No structured subtask/milestone tracking
- LLM sees "R1 completed" and interprets as "task done"
- No code-level guard against DONE when work remains

### Diagnostic Commands
```bash
# 1. Check task state
cat artifacts/tasks/<task_id>/state.json | python3 -m json.tool

# 2. Check if worker jobs exist after DONE
ls -lt artifacts/tmux-jobs/<role>-* | head -5

# 3. Check supervisor tmux for TARGET_ROLE output
tmux capture-pane -t telegrambots-supervisor -p -S -100 | grep "TARGET_ROLE"

# 4. Check bot privacy mode
python3 -c "
from telegram import Bot; import asyncio
bot = Bot('<TOKEN>')
me = asyncio.run(bot.get_me())
print(f'can_read_all_group_messages: {me.can_read_all_group_messages}')
"

# 5. Check pending updates per bot
python3 -c "
from telegram import Bot; import asyncio
bot = Bot('<TOKEN>')
updates = asyncio.run(bot.get_updates(timeout=0, limit=10))
print(f'Pending: {len(updates)}')
"
```

## Bot-to-Bot Message Routing

### Worker receives dispatch when:
1. `is_mentioned(role, text)` — message contains `@crazysheep_researcher_bot`
2. `is_supervisor_assignment(text)` — matches `[B2B-...][Supervisor][ASSIGN]`
3. `is_from_role(user.id, "Supervisor", self.user_ids)` — sender is Supervisor bot

### Common routing failures:
- **Privacy mode disabled** (`can_read_all_group_messages=True`) — all bots should have this
- **Bot token mismatch** — check `.env` has correct tokens for each role
- **`normalize_manager_message()` format** — must produce `[task_id][Supervisor][ASSIGN]` header
- **`is_supervisor_assignment()` regex** — matches `^\s*\[B2B-\d{8}-\d{6}\]\[Supervisor\]\[(ASSIGN|DONE|ERROR)\]`

## Process State Reference

| ps state | Meaning | For bot2bot |
|----------|---------|-------------|
| S+ | Sleeping, foreground | Normal — waiting for network IO |
| R | Running | Brief — only during actual computation |
| D | Disk IO wait | Abnormal if prolonged |
| Z | Zombie | Process died, parent didn't reap |
