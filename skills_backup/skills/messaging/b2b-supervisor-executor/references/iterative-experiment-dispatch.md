# Iterative Experiment Dispatch Pattern

When dispatching ML experiment execution to Developer, use the two-phase approach.

## User Preference (Strong)

User: "我要迭代开发，拿到最好的一版再开始训练啊，这么多版本每一版都训练的话太慢"
(I want iterative development — get the best version first then train.)

**Never dispatch full training for all experiments sequentially.** Use smoke test filtering first.

## Dispatch Sequence

### Round 1: Smoke Test All
```
[B2B-...][Supervisor][ASSIGN] @crazysheep_developer_bot
运行所有实验的 smoke test（3 步）：
for exp in exp001 exp002 ... exp010; do
  PYTHONPATH="$(pwd)/$exp/model:$PYTHONPATH" conda run -n model python $exp/model/train.py --mode smoke
done
报告：哪些通过、哪些报错、初始 loss 趋势
```

### Round 2: Full Training on Candidates
```
[B2B-...][Supervisor][ASSIGN] @crazysheep_developer_bot
smoke test 结果：exp002/003/005/007 通过。执行完整训练：
对每个候选实验运行 --mode small --epochs 3 --max-steps 50
记录 val_loss + 各项指标，对比 baseline
```

### Round 3: Comparison Report
```
[B2B-...][Supervisor][ASSIGN] @crazysheep_developer_bot
生成 comparison_report.md，包含：
- baseline 指标
- 每个候选实验的指标
- 改善百分比排名
- 推荐最优方案
```

## Pitfall: Don't Dispatch One Experiment at a Time

Dispatching "run exp002, wait, run exp003, wait..." is extremely slow. Batch the smoke test in one dispatch, then batch the full training in another.
