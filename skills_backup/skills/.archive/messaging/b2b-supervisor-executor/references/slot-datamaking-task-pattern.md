# Slot-Datamaking Model Optimization Task

## Task Pattern: Literature Learning + Experiment Planning

A recurring B2B task type where the Supervisor must:
1. Read a prompt.md that defines a multi-step research task
2. Read N paper notes.md files (often 20+)
3. Read model source code files
4. Synthesize into an experiment plan (PLAN.md)

## Phase 1: Literature Learning + PLAN.md

### Execution Sequence (proven)

1. Read 3 summary reports first (literature_survey_summary, optimization_proposals, ROADMAP)
2. Read all code files in parallel (config, model, encoder, interaction, temporal, decoder, loss, train, dataset)
3. Read paper notes in batches of 6 (parallel reads)
4. Write PLAN.md with: architecture assessment, paper summaries, experiment proposals

### Output Structure for PLAN.md

```markdown
# Experiment Plan
## 架构评估 (architecture assessment)
## 文献学习摘要 (paper summaries as tables)
## 推荐实验顺序 (experiment proposals with: 改动文件, 改动内容, 对应论文, 验证方法, 风险)
## 总结 (summary table with 预期提升, 实现难度, 改动量)
```

### Key Constraint (Phase 1)

"不要在 ai_model/ 里改任何代码。只做分析和规划。" — only analysis and planning, no code changes.

## Phase 2: Experiment Implementation (promptv2.md)

A follow-up task file (promptv2.md) asks to implement the experiments from PLAN.md.

### Key Constraint (Phase 2)

- ai_model/ is read-only, never modified
- Each experiment gets its own directory: experiments/expNNN_name/model/
- Copy ai_model/ as base, then apply PLAN.md modifications
- Each experiment is independent

### Automation Approach

Write create_experiments.py that:
1. Copies ai_model/ to each experiment's model/ directory
2. Applies targeted string patches per experiment
3. Creates config_override.py, run.sh, README.md

This is ~10x faster than manual file creation (1 script vs 110+ individual writes).

### Pitfall: Manual File Creation

Do NOT write each file individually for each experiment. The Python automation script approach saves enormous time and reduces errors.

## Phase 3: Baseline Training + Experiment Execution

After creating experiment code, the task requires ACTUAL training and comparison.

### Baseline Training Setup

1. Copy ai_model/ to experiments/baseline/model/ (never modify source)
2. Fix known issues in the copy (FP16 overflow: interaction.py -1e9 → -1e4)
3. Run training from the experiments/ working directory
4. Save metrics to experiments/baseline_metrics.json

### Experiment Execution Pattern

For each experiment (one at a time, sequential):
1. Install dependencies if needed (e.g., pip install lpips)
2. Run training with PYTHONPATH pointing to the experiment's model/
3. Record metrics (val_loss, rgb, state, collision, mask + experiment-specific)
4. Compare with baseline metrics
5. Report: improvement/regression per metric, any errors

### Known Technical Issues

- FP16 overflow: masked_fill with -1e9 can overflow in FP16. Use -1e4 instead.
- PYTHONPATH setup: Each experiment needs its own model/ on PYTHONPATH
- conda environment: Training uses conda run -n model python ...
