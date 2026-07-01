# Full Codebase Review Format

When doing a full codebase review (not pre-commit diff review), use this structured format.

## Output Structure

```
## 代码审查报告

**范围：** [files reviewed]
**方法：** [how you reviewed — line-by-line, focus areas, etc.]

### 🔴 Blocking (N)
[Issues that MUST be fixed before any further work]

### 🟡 Major (N)
[Issues that should be fixed before production/full training]

### 🔵 Minor (N)
[Issues worth noting but non-blocking]

### ✅ No Issue (N)
[Confirmed correct parts — briefly list what you verified]
```

## Per-Issue Format

Every issue MUST include ALL of:

```
**M1. [Short descriptive title]**
- **文件：** `filename.py:line_number`
- **问题：** [What's wrong — be specific about the math/logic/shape]
- **影响：** [What happens if unfixed — training instability, NaN, wrong results]
- **建议：** [Concrete fix, ideally with code snippet]
```

## Severity Definitions

| Level | Definition | Example |
|-------|-----------|---------|
| 🔴 Blocking | Will crash or produce silently wrong results | Shape mismatch, division by zero in all cases |
| 🟡 Major | Will cause training instability or degraded quality in long runs | Gradient variance, scheduler mismatch, fragile runtime logic |
| 🔵 Minor | Suboptimal but won't break anything | Small window sizes, missing documentation, cosmetic issues |
| ✅ No Issue | Confirmed correct — mention to show coverage | Correct formulas, proper masking, good practices |

## Review Checklist (ML Model Code)

1. **Shape consistency** — trace tensor shapes through full forward pass
2. **Masking** — invalid objects excluded at every layer
3. **Training/inference consistency** — scheduled sampling, dropout, teacher forcing
4. **Loss normalization** — divide by actual element count, not batch size
5. **Numerical stability** — log(0), sqrt(negative), softmax overflow
6. **Checkpoint/resume** — scheduler state, optimizer state, epoch counter alignment
7. **Long-run risks** — NaN accumulation, memory leaks, gradient explosion
