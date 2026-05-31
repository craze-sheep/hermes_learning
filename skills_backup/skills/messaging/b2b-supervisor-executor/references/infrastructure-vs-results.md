# Infrastructure vs Actual Results — A Common Supervisor Trap

## The Trap

When a task says "优化模型" (optimize model), there are two very different levels:

### Level 1: Infrastructure (code preparation)
- Writing experiment plans (PLAN.md)
- Creating experiment directories with modified code
- Writing automation scripts (create_experiments.py)
- Config files, run scripts, READMEs

### Level 2: Actual optimization (execution + results)
- Running baseline training, recording metrics
- Running each experiment's training
- Comparing experiment metrics vs baseline
- Selecting the best configuration

**Level 1 without Level 2 is NOT optimization.** It's planning.

## How to Recognize the Trap

User signals that indicate Level 2 is expected:
- "真的优化了吗" (did it really get optimized?)
- "有没有结果" (are there results?)
- "跑了吗" (did you run it?)
- "对比一下" (compare them)
- "哪个更好" (which is better?)

If you only completed Level 1, don't claim DONE. Instead:
1. Acknowledge that infrastructure is ready
2. State explicitly what Level 2 steps are needed
3. Ask if the user wants to proceed with execution

## Correct Supervisor Flow for Optimization Tasks

1. @Planner — decompose the optimization task
2. @Developer — run baseline training, record metrics
3. @Developer — run exp001, compare with baseline
4. @Developer — run exp002, compare with baseline
5. ... (one experiment at a time)
6. @Tester — verify all results, compare metrics
7. Supervisor — summarize which experiment is best → DONE

## Key Principle

**"写了代码" ≠ "优化了模型"**
**"Wrote code" ≠ "Optimized model"**

The user cares about RESULTS, not CODE. Code is a means to results.
