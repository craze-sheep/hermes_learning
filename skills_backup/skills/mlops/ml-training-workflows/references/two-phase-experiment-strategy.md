# Two-Phase Experiment Strategy (Iterative Development)

When you have N experiments and full training is slow, use smoke test → full training.

## User Preference (Strong)

User explicitly requested: "我要迭代开发，拿到最好的一版再开始训练啊，这么多版本每一版都训练的话太慢" (Get the best version first then train. Training every version is too slow.)

**Always use this two-phase approach when there are 5+ experiments.**

## Phase 1: Smoke Test (minutes)

Run each experiment for just 3 steps (`--mode smoke`):
- Catches code bugs (import errors, dimension mismatches, NaN losses)
- Records initial loss descent trend (loss_step1 → loss_step3)
- Experiments that crash or show no improvement are eliminated
- 10 experiments × 3 steps ≈ a few minutes total

```bash
PYTHONPATH="$(pwd)/<exp_name>/model:$PYTHONPATH" conda run -n model python <exp_name>/model/train.py --mode smoke
```

## Phase 2: Full Training (candidates only)

Run full training on the 3-5 candidates that:
- Passed smoke test without errors
- Showed positive loss descent trend
- Have promising theoretical basis (per PLAN.md)

```bash
PYTHONPATH="$(pwd)/<exp_name>/model:$PYTHONPATH" conda run -n model python <exp_name>/model/train.py --mode small --epochs 3 --max-steps 50
```

## Phase 3: Comparison Report

```markdown
| Experiment | val_loss | vs baseline | rgb | state | collision | mask |
|------------|----------|-------------|-----|-------|-----------|------|
| baseline   | 0.5451   | —           | ... | ...   | ...       | ...  |
| exp002     | 0.5123   | -6.0%       | ... | ...   | ...       | ...  |
```

## Candidate Selection Criteria

1. No runtime errors in smoke test
2. Loss decreased from step 1 to step 3
3. No NaN/Inf in any loss component
4. Theoretical basis from PLAN.md suggests meaningful improvement
