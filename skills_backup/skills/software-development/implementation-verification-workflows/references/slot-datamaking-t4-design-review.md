# Slot Datamaking T4 Design Review Case

A concise example for future architecture/design-document tasks that require staged AI review.

## Context

Project: `slot-datamaking`
Task: T4 architecture design for a physics video prediction model.
Governing plan: `model/分工.md` required Hermes + OpenCode iteration, then Claude Code final review before marking complete.
Deliverable: `model/architecture.md`.

## Effective Workflow

1. Read governing and reference artifacts:
   - `model/分工.md`
   - `model/research/papers.md`
   - `model/design/data_design.md`
   - `model/dataset.py`
   - `model/repos/README.md`
2. Draft the architecture doc with:
   - architecture diagram and data flow;
   - first-version in/out scope;
   - module responsibilities;
   - detailed shape table;
   - compute budget;
   - extension interfaces;
   - comparison against collected baselines/repos;
   - review log section.
3. Run OpenCode review-only. Also run a `delegate_task` reviewer as fallback if OpenCode may fail/stall.
4. Patch the doc from first-stage findings.
5. Run Claude Code final review-only.
6. Patch cheap final clarifications, then mark the task complete in `model/分工.md`.

## Review Findings That Were High-Value

The first-stage review caught gaps that are broadly useful for design-doc reviews:

- Resource budget must be concrete: target GPU memory, batch-size floor, rough parameter budget, and OOM fallback configs.
- RGB decoder designs need spatial reasoning, not just object-token aggregation.
- Extension compatibility needs explicit shapes/defaults, e.g. `view_id` defaulting to 0 when current dataset lacks it, future `[B,V,T,...]` shapes, `depth_hist`/`pred_depth` placeholders.
- Shape tables should include intermediate tensors: feature maps, resized masks, edge features, pairwise messages, temporal queries, loss masks.
- Directionality and units must be explicit for physical signals: use both `F_ij` and `F_ji` when force matrix semantics are not yet confirmed; collision labels should use raw or de-normalized force.
- Existing-code mismatches matter: Python `hash(scene) % 8` is not stable across runs, so scene embedding should be off until stable S1-S8 mapping exists.
- Static objects need an explicit state policy: copy last observed state and exclude from dynamic-state main loss, while still participating in message passing.

## Example Final Gate Outcome

Claude Code PASSed after first-stage fixes. Non-blocking advice included:

- Make RGB decoder submodule channels/shapes more concrete in later T8 design.
- Consider explicit dynamic-static collision pair categories in T9.
- If using the unused attr_dim slot, define the color-name mapping in T5.
- Clarify default hidden dim vs minimal config hidden dim.

The last item was cheap and was patched immediately.
