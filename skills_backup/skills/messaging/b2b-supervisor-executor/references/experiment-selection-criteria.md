# Iterative Experiment Selection Criteria

After smoke testing, select candidates for full training based on:

## Selection Rules

1. **PASS all smoke tests**: No errors during 3-step training
2. **Loss decreasing**: Initial loss trend should be downward (not required but preferred)
3. **Rank by val_loss**: Lower val_loss in smoke mode = better candidate
4. **Select top N**: Usually top 2-3 candidates for full training

## Example Selection

From smoke test results:
| Experiment | val_loss | Loss Decreasing | Selected |
|-----------|----------|-----------------|----------|
| exp003 | 0.6675 | YES | ✅ Top 1 |
| exp007 | 0.6969 | NO (3 steps too few) | ✅ Top 2 |
| exp005 | 0.6983 | YES | ✅ Top 3 |
| exp002 | 0.7510 | YES | ❌ |
| exp004 | 0.7523 | NO | ❌ |

## Full Training Command Template

```bash
cd /path/to/experiments
for exp in exp003_more_physics_features exp007_collision_effect; do
  echo "=== Training $exp ==="
  PYTHONPATH="$(pwd)/$exp/model:$PYTHONPATH" conda run -n model python $exp/model/train.py --mode small --epochs 3 --max-steps 50 2>&1 | tee ${exp}_train.log
  echo "---"
done
```

## Comparison Report Template

```markdown
# Experiment Training Comparison Report

## Winner: expNNN_name

- **val_loss:** X.XXXX (baseline Y.YYYY, improvement -Z.Z%)
- **Best epoch:** N
- **Parameters:** NNN,NNN

## Full Training Metrics

| Epoch | Train Loss | Val Loss | RGB | State | Collision | Mask |
|-------|-----------|----------|-----|-------|-----------|------|
| 1 | ... | ... | ... | ... | ... | ... |
| 2 | ... | ... | ... | ... | ... | ... |

## Smoke Test Summary (all experiments)

| Experiment | Loss Start | Loss End | Decreasing | Val Loss | Error |
|-----------|-----------|---------|-----------|---------|-------|
| exp002 | ... | ... | ... | ... | ... |
| exp003 | ... | ... | ... | ... | ... |
```

## Pitfall: Smoke Mode vs Full Mode Config Differences

Smoke mode uses tiny config (fused_dim=32, history=4, predict=4) while full training uses larger config (fused_dim=96, history=12, predict=12). The absolute val_loss values are NOT comparable between modes. Only compare:
- Smoke results with other smoke results (same mode)
- Full results with other full results (same mode)
- Full results with baseline (same mode)
