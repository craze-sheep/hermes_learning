---
name: experiment-execution-workflow
description: "Workflow for executing ML/AI experiments: baseline training, experiment comparison, metrics collection, and result analysis."
version: 1.0.0
tags: [ml, experiments, training, comparison, baseline]
---

# Experiment Execution Workflow

When tasked with running and comparing ML/AI experiments, follow this workflow.

## Phase 1: Baseline

1. **Copy source code to working directory** — never modify the original
2. **Run baseline training** with standard parameters
3. **Record baseline metrics** (val_loss, individual loss components, training time)
4. **Save to baseline_metrics.json** for later comparison

```bash
# Example
cd /path/to/experiments
PYTHONPATH="$(pwd)/baseline/model:$PYTHONPATH" conda run -n env python baseline/model/train.py --mode small --epochs 3 --max-steps 50
```

## Phase 2: Smoke Test (Quick Screening)

Before full training, run a **smoke test** on all experiments to quickly identify which ones work and which have the best initial loss trends.

```bash
# Smoke test: just 3 steps per experiment
for exp in exp001_lpips_loss exp002_energy_conservation exp003_more_physics_features; do
  echo "=== $exp ==="
  PYTHONPATH="$(pwd)/$exp/model:$PYTHONPATH" conda run -n env python $exp/model/train.py --mode smoke 2>&1 | tail -10
  echo "---"
done
```

**Selection criteria:**
1. **Must pass** — no errors (EXIT_CODE=0)
2. **Loss decreasing** — initial loss should drop over 3 steps
3. **val_loss ranking** — compare val_loss across experiments; lower is better

**Save results** to `smoke_results.json`:
```json
{
  "exp002_energy_conservation": {"error": false, "loss_start": 0.99, "loss_end": 0.90, "decreasing": true, "val_loss": 0.75},
  "exp003_more_physics_features": {"error": false, "loss_start": 0.86, "loss_end": 0.80, "decreasing": true, "val_loss": 0.67}
}
```

**Select top 2-3 candidates** for full training based on:
- Lowest val_loss in smoke test
- Loss trend (decreasing preferred)
- No external dependency issues

## Phase 3: Full Training (Selected Candidates Only)

Only full-train the candidates that passed smoke test and ranked highest. This saves significant time vs training all experiments.

For each candidate:
1. **Run full training** with same parameters as baseline
2. **Record metrics** to expNNN_metrics.json
3. **Compare with baseline** — which metrics improved/declined?
4. **Report** to Supervisor with specific numbers

### Execution Order
- **Low-risk experiments first** — those with no external dependencies
- **High-risk experiments last** — those requiring external packages or architecture changes
- **One experiment at a time** — don't run multiple simultaneously (resource contention)

### Metrics Format
```json
{
  "experiment": "exp001_lpips_loss",
  "val_loss": 0.52,
  "rgb_loss": 0.15,
  "state_loss": 0.02,
  "collision_loss": 0.01,
  "mask_loss": 1.2,
  "lpips_loss": 0.03,
  "epochs": 3,
  "max_steps": 50,
  "baseline_val_loss": 0.5451,
  "improvement": "4.6%"
}
```

## Phase 3: Comparison Report

Create comparison_report.md with:
- Baseline metrics
- Each experiment's metrics
- Improvement/decline percentages
- Which experiments had errors
- Recommendation for best experiment

## Common Pitfalls

### Training Parameter Mismatch
If experiments use different epochs/steps than baseline, comparison is invalid. Always align parameters.

### External Dependency Failures
Some experiments need packages not in the base environment (lpips, mamba_ssm, dinov2). Check and install before running.

### Patch Application Failures
When experiment code was auto-generated via string patching, verify critical code sections exist after generation. Patch failures can cause runtime errors (dimension mismatches, missing classes, wrong return types).

### Source Code Modification
Never modify the original source code. Always work in copies. Verify with `diff` after copying.

### Long Requirements in Messages
When dispatching experiment execution to workers, write detailed requirements (commands, parameters, expected outputs) to a file like `requirements.md` in the working directory. The @ message should only reference the file path and give a one-line summary. This avoids Telegram message length limits (~4096 chars).

## Related Skills

- `messaging-gateway-integrations` → `references/b2b-supervisor-dispatch-patterns.md` — Supervisor dispatch patterns
