# Block-Based Code Review with Claude Code

When doing iterative code review across a multi-module project, split the review into focused blocks instead of one massive prompt. Each block gets its own Claude Code invocation.

## User Preference

**Keep prompts SHORT.** One question/topic per invocation. The user will explicitly correct you if you pack too much into one prompt ("一次问太多了，下次分点提问").

## Block Split Pattern

For a typical ML project with encoder/decoder/loss/training modules:

| Block | Scope | Focus |
|-------|-------|-------|
| 1. Data | dataset.py, data_adapter.py | Data loading, shapes, future leak, padding |
| 2. Encoder/Interaction | encoder.py, interaction.py, temporal.py | Shape flow, masks, device |
| 3. Decoder/Loss | decoder.py, loss.py, model.py | Output-loss match, NaN risk, static objects |
| 4. Training | train.py | OOM, AMP, checkpoint, real data |
| 5. Tests/Report | EXPERIMENT_REPORT.md, tests/ | Evidence quality, honesty |
| 6. Summary | All files | Cross-module Blocking/Major only |

## Optimal Flags for Review

```bash
claude -p "Review file.py. Check X. Brief." --bare --effort low --max-turns 5
```

- `--bare`: Fastest startup, skips CLAUDE.md/plugins/hooks
- `--effort low`: Reviews don't need deep reasoning
- `--max-turns 5`: Enough to read 1-2 files + respond. 3 is too tight (reads in turn 1, responds in turn 2, but if it needs to re-read it hits the limit).
- Skip `--output-format` for direct terminal output; use `head -N` to truncate if needed.

## Saving Results

Redirect output to per-block log files:
```bash
claude -p "Review X" --bare --effort low --max-turns 5 2>&1 > review_logs/iter_01_block_01_data.md
```

Then apply your own judgment (Blocking/Major/Minor/Suggestion) before fixing.

## Pitfalls

- `--max-turns 3` is too tight — Claude needs at least 1 turn to read files and 1 to respond. If it needs to re-read (file too long, multiple files), 3 breaks. Use 5.
- Don't pipe output through `python3 -c "import json..."` for parsing — the approval prompt adds latency and the output format may vary. Just redirect to file and read with `head`.
- Claude Code sometimes times out at 120s with `--effort medium` or `--max-turns 10`. Keep effort low and turns at 5 for reviews.
- If Claude Code says "Error: Reached max turns (N)", increase max-turns. It consumed turns reading files.
