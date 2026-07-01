# TDD Edge-Case Review Pattern: Masked Transformer / Structured Prediction

Session learning from a physics-video prediction model implementation:

## What happened

A module suite passed its main unit tests, but subagent review found a missing edge case: a Transformer encoder/decoder received an all-True key padding mask when `valid_mask` was all False. PyTorch attention over all-masked keys can produce NaNs. The fix was not to mark the tool/environment as broken; the durable lesson is the edge-case pattern.

## Durable rule

When TDDing modules that use masks, padding, graph edges, attention, or object validity:

1. Add a test for the normal mixed-valid case.
2. Add a test for all-invalid / all-padding input.
3. Assert both:
   - outputs are finite (`torch.isfinite(...).all()`), and
   - final masked outputs are zero where required.
4. For Transformer attention specifically, use a *safe internal mask* that temporarily unmasks one harmless token for all-invalid samples, then reapply the original mask to outputs.

## Example fix shape

```python
valid = valid_mask.to(device=device, dtype=torch.bool)
safe_valid = valid.clone()
all_invalid = ~safe_valid.any(dim=1)
if all_invalid.any():
    safe_valid[all_invalid, 0] = True
padding_mask = ~safe_valid[:, None, :].expand(B, T, N).reshape(B, T * N)

# run attention with padding_mask
future_token = transformer(...)

# restore original semantic mask on outputs
future_token = future_token * valid[:, None, :, None].to(future_token.dtype)
```

## Review checklist addition

For each new module with structured masks, include tests for:

- mixed valid/padding objects
- all invalid objects
- empty pair masks / no edges
- static-only objects when dynamic masks drive loss
- no future-target leakage if the module should use history only
- finite loss/output under empty masks

## Why this belongs in TDD

Mainline shape tests can all pass while a masked module still contains a NaN trap. The RED test must include the degenerate valid-mask case before the module is considered complete.
