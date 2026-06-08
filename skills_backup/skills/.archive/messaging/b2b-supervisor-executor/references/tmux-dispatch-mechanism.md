# Tmux Dispatch Mechanism — How B2B Supervisor Actually Works

## The Full Flow

```
User message in Telegram group
  → B2B service (service.py) receives update
  → service.py creates job JSON at artifacts/tmux-jobs/supervisor-<ts>-<hash>.job.json
  → service.py constructs a prompt that references the job JSON path
  → service.py pastes prompt into Supervisor's tmux session via `tmux paste-buffer`
  → Supervisor Hermes agent reads the job JSON, processes it, outputs response
  → service.py captures tmux pane output via `tmux capture-pane -p -S -5000`
  → service.py parses the captured output for B2B markers
  → service.py posts the MESSAGE section to the Telegram group as the Supervisor bot
```

## Key Implication

**Your output IS the Telegram group message.** You don't need `send_message`, `send_as`, or any messaging tool. The B2B service captures your tmux pane and posts it.

## What You See vs What Happens

| What you do | What the service does |
|---|---|
| Output `<<<B2B_RESPONSE:job_id>>>` | Marks start of your response |
| Output `TARGET_ROLE: Researcher` | Service sees ASSIGN, routes to Researcher |
| Output `MESSAGE: @bot task desc...` | Service posts this to Telegram group |
| Output `<<<B2B_DONE:job_id>>>` | Marks end; service stops capturing |

## Worker Response Flow

```
Worker sees @mention in Telegram group
  → Worker's Hermes agent gets a job JSON (e.g., researcher-<ts>-<hash>.job.json)
  → Worker processes task, outputs with B2B markers
  → Service captures Worker's tmux pane
  → Service posts Worker's REPORT to group
  → Service detects @TeamSupervisor_bot in Worker report
  → Service creates NEW supervisor job JSON for the incoming report
  → Cycle continues until Supervisor outputs TARGET_ROLE: DONE
```

## When Telegram Is NOT Configured in Hermes

If `send_message(action='list')` shows no Telegram target, this is **normal and expected** for B2B deployments. The B2B service handles Telegram routing through tmux pane capture — the agent's Hermes instance doesn't need Telegram configured.

**Do NOT conclude you can't dispatch.** If the task arrived via a job JSON file, the B2B service is active and will capture your output. Just output the B2B response format directly.

**Only execute directly when:**
- No job JSON was provided (plain CLI session, not B2B)
- The B2B service is confirmed not running (no `supervisor-*.job.json` files being created)
- Workers have failed to respond after 1-2 dispatch attempts (pivot to direct execution)

## Role Contract File

The role contract is injected at session startup. Read it at:
`artifacts/hermes-role-prompts/supervisor.md`

It contains the exact output format (TARGET_ROLE/MESSAGE/HANDOFF_SUMMARY) and dispatch rules.
