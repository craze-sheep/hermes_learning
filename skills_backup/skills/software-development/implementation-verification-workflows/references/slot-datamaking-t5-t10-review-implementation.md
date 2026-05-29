# Slot Datamaking T5-T10 Review and Implementation Notes

Concrete case notes from `/home/lzy/project/slot-datamaking` for future physics/video model implementation verification. Keep as patterns, not project-specific rules.

## Design review loop patterns

For module design docs T5-T9, the successful loop was:

1. Draft the design from the governing plan plus architecture/dataset/upstream module docs.
2. Run a first-stage strict reviewer (OpenCode when available) and a subagent fallback when a reviewer is unavailable or slow.
3. Patch must-fix issues directly into the design doc.
4. Run final Claude Code review after first-stage fixes.
5. Update the governing task file only after PASS.

Useful review dimensions by module:

- Input encoder: RGB encoder choice, GT mask ROI pooling vs slots, static attrs, dynamic state slices, force passthrough, padding, time/view embeddings, depth extension, output shape completeness.
- Interaction module: dense vs sparse/message/attention, force matrix directionality, static objects, zero-force and far-distance edges, visual-physical fusion boundaries, `edge_dim`, edge masks, valid-mask passthrough.
- Output decoder: non-accumulated state delta semantics, quaternion normalization in normalized state space, mask logits/prob masking, RGB alpha/background composition, pair masks, static mask fallback.
- Loss: RGB reduction, LPIPS disabled behavior, state component weights, denormalized collision labels, standard focal alpha_t, mask BCE+Dice masking, time-weight normalization, padding/static pair rules, GAN deferral.

## Implementation verification patterns

The T10 core implementation used module-scoped tests for:

- config defaults and separate train/test convenience configs;
- encoder shapes, padding zeroing, static/dynamic masks, history/force passthrough;
- interaction edge feature shapes, self/padding masks, bidirectional force, relative pos/vel, zero-force edges, static senders, aggregation direction;
- temporal predictor output shapes, padding zeroing, key-padding mask semantics, all-invalid guard;
- decoder output keys/shapes, pair masks, static state copy, dynamic state delta anchored to last state, quaternion unit norm, alpha/background composition;
- loss components, static/padding masking, denormalized force labels, pair masks, time weights, zero-valid no-NaN, weighted total;
- end-to-end wrapper shapes and future leakage.

A useful full targeted command was:

```bash
conda run -n slotformer pytest \
  model/tests/test_config.py \
  model/tests/test_encoder.py \
  model/tests/test_interaction.py \
  model/tests/test_temporal.py \
  model/tests/test_decoder.py \
  model/tests/test_loss.py \
  model/tests/test_physics_pred.py -q
```

## Durable gotchas

- Do not use a Transformer with every key padded for a sample; many implementations return NaN. Temporarily unmask an internal dummy token and zero final outputs with the original validity mask.
- Keep `valid_mask` propagation and output zeroing separate: downstream attention needs mask booleans, while tests should also assert padding tensors are zero.
- When a model consumes normalized features but labels use physical thresholds, document and implement denormalization at label construction, not in the feature module.
- If reviewer feedback says a field source is missing, verify before patching; it may already be documented in another section. Record the verification instead of duplicating contradictory text.
- Separate `minimal_12gb()`/resource configs from `tiny_test()` configs; naming tiny tests as “minimal” misleads review and future training setup.
