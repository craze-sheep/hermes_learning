# Iterative Experiment Workflow

## Problem
Training every experiment variant is too slow. Users want to find the best version before committing to full training.

## Solution: Two-Phase Screening

### Phase 1: Smoke Test (fast filter)
```bash
# For each experiment, run 3 steps to verify no errors
for exp in exp001_xxx exp002_yyy exp003_zzz; do
  echo "=== $exp ==="
  PYTHONPATH="$(pwd)/$exp/model:$PYTHONPATH" conda run -n model python $exp/model/train.py --mode smoke 2>&1 | tail -10
done
```

**Selection criteria:**
- PASS: No errors, loss decreasing over 3 steps
- FAIL: Any RuntimeError, NaN/Inf loss, import errors
- BORDERLINE: No errors but loss not decreasing (may need more steps)

**Output**: `smoke_results.json`
```json
{
  "exp001_xxx": {"error": false, "loss_start": 70.0, "loss_end": 65.0, "decreasing": true},
  "exp002_yyy": {"error": true, "error_msg": "ImportError: No module named 'lpips'", "decreasing": false}
}
```

### Phase 2: Full Training (candidates only)
Train only the top 3-5 candidates with matching baseline parameters:
```bash
# Same params as baseline for fair comparison
PYTHONPATH="$(pwd)/$exp/model:$PYTHONPATH" conda run -n model python $exp/model/train.py --mode small --epochs 3 --max-steps 50
```

**Output**: `expXXX_metrics.json` per experiment

### Phase 3: Comparison Report
Generate `comparison_report.md`:
| Experiment | val_loss | rgb_loss | state_loss | collision_loss | mask_loss | vs baseline |
|------------|----------|----------|------------|----------------|-----------|-------------|
| baseline   | 0.5451   | ...      | ...        | ...            | ...       | -           |
| exp003     | 0.5100   | ...      | ...        | ...            | ...       | -6.4%       |

## Key Rules
1. **Same training parameters** for all experiments (epochs, max_steps, batch_size)
2. **Don't modify source code** — work on copies only
3. **Use virtual environment** — `conda run -n model` for all Python execution
4. **Record everything** — even failed experiments get recorded in smoke_results.json
5. **File-based communication** — write requirements to file, reference in short @ messages

## User Feedback Patterns
- "真的优化了吗" → Be honest about what was actually done vs planned
- "你咋不回复" → Report status even when blocked/waiting
- "一次只能@一个" → One worker per dispatch, wait for report
- "不要输出DONE" → Don't mark DONE until task truly complete
- "记得使用虚拟环境" → Always use conda run -n model
- "不要修改源码" → Work on copies, never touch original code
- "把要求写在一个地方" → File-based requirements for long instructions
