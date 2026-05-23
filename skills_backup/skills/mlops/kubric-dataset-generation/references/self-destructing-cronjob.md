# Self-Destructing Cronjob Pattern

When a background task has a finite queue and no need to run forever, use a self-destructing cronjob.

## Pattern

1. **Script** does its work, then checks if more work remains
2. **Queue file** lists pending tasks, one per line
3. **Cronjob** calls the script periodically
4. **Self-destruct** when queue empties: remove cronjob + delete script + delete queue file

## Implementation

```bash
# In the script, at the point where queue becomes empty:
if [ ! -s "$QUEUE_FILE" ]; then
    hermes cron remove <JOB_ID> 2>/dev/null  # remove cronjob
    rm -f "$0"                                # delete script itself
    rm -f "$QUEUE_FILE"                       # delete queue file
    exit 0
fi
```

## Key Points

- Bash loads script into memory at start, so `rm -f "$0"` doesn't affect running execution
- `hermes cron remove` uses the job ID from `hermes cron list`
- Hardcode the job ID in the script (acceptable for one-shot schedulers)
- Add self-destruct at TWO places: (1) at the top when queue is empty on entry, (2) at the bottom after consuming the last item

## Cronjob Setup

```python
cronjob(action="create",
    name="my_scheduler",
    schedule="every 30m",
    no_agent=True,
    script="bash /path/to/scheduler.sh",
    deliver="origin")
```

`no_agent=True` skips LLM — the script runs directly and its stdout becomes the notification.

## When to Use

- Docker container queue (limited GPU/CPU slots)
- Batch job dispatcher with finite work items
- One-shot cleanup tasks that should disappear after completion
- Any recurring task with a known end condition
