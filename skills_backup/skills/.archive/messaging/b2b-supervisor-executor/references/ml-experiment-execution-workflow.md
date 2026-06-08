# ML Experiment Execution Workflow

## When to Use

After creating experiment code (Phase 2), the task requires ACTUAL training and metric comparison. This covers Phase 3: baseline training → experiment execution → comparison.

## Step 1: Baseline Training

1. Copy source code to working directory (NEVER modify source):
   ```bash
   cp -r /path/to/ai_model /path/to/experiments/baseline/model
   ```
2. Fix known issues in the copy:
   - FP16 overflow: interaction.py masked_fill with -1e9 → -1e4
   - Path fixes in train.py if needed
3. Run training from the experiments/ directory:
   ```bash
   cd /path/to/experiments
   PYTHONPATH="$(pwd)/baseline/model:$PYTHONPATH" conda run -n model python baseline/model/train.py --mode small --epochs 3 --max-steps 50
   ```
4. Save metrics to experiments/baseline_metrics.json:
   - val_loss, rgb_loss, state_loss, collision_loss, mask_loss
   - Epoch number, best checkpoint path

## Step 2: Experiment Execution (Sequential)

For each experiment ONE AT A TIME:
1. Install experiment-specific dependencies (e.g., pip install lpips)
2. Run training with PYTHONPATH pointing to experiment model/
3. Record metrics (same fields as baseline + experiment-specific)
4. Compare with baseline: improvement/regression per metric
5. Report to Supervisor with concrete numbers

## Step 3: Comparison and Selection

After all experiments run:
1. Build comparison table: baseline vs exp001 vs exp002 vs ...
2. Identify which experiments improved which metrics
3. Select best overall configuration
4. Report final recommendation

## Pitfalls

### Source Code Modification
NEVER modify ai_model/ source. All work happens in copies under experiments/.

### FP16 Overflow
masked_fill with -1e9 causes overflow in FP16 (AMP). Use -1e4 instead. This affects interaction.py attention masking.

### Working Directory
Run from experiments/ directory, not from model/ or ai_model/. The PYTHONPATH must point to the experiment model/ subdirectory.

### Dependencies
Some experiments require external packages (lpips, mamba_ssm). Install before training. If installation fails, report the error rather than skipping.
