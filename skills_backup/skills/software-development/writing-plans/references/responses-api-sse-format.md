# OpenAI Responses API — SSE Streaming Format

## Key Differences from Chat Completions

| Feature | Chat Completions (`/v1/chat/completions`) | Responses API (`/v1/responses`) |
|---------|------------------------------------------|-------------------------------|
| End marker | `data: [DONE]` | `response.completed` event (no [DONE]) |
| Event format | `data: {json}` only | `event: <type>\ndata: {json}` |
| Text deltas | `choices[0].delta.content` | `response.output_text.delta` → `.delta` field |
| Function args | `choices[0].delta.function_call.arguments` | `response.function_call_arguments.delta` → `.delta` field |
| Usage in stream | Final chunk's `usage` field | `response.completed` → `response.usage` |
| Multiple outputs | Single choice | Multiple `output[]` items (reasoning + message + tool_calls) |

## Complete Event Type List

### Lifecycle Events
- `response.created` — Response object created
- `response.in_progress` — Generation started
- `response.completed` — Finished successfully
- `response.failed` — Failed with error
- `response.incomplete` — Incomplete (truncation etc.)
- `response.cancelled` — Cancelled

### Output Events
- `response.output_item.added` — New output item started
- `response.output_item.done` — Output item completed
- `response.content_part.added` — Content part started
- `response.content_part.done` — Content part completed

### Text Events
- `response.output_text.delta` — Text token delta (`delta` field)
- `response.output_text.done` — Text finalized (`text` field)
- `response.output_text.annotation.added` — Annotation added

### Refusal Events
- `response.refusal.delta` — Refusal text delta
- `response.refusal.done` — Refusal finalized

### Function/Tool Events
- `response.function_call_arguments.delta` — Function args delta (`delta` field, `call_id` links to call)
- `response.function_call_arguments.done` — Function args finalized

### Code Interpreter Events
- `response.code_interpreter.in_progress`
- `response.code_interpreter_call.code.delta`
- `response.code_interpreter_call.code.done`
- `response.code_interpreter_call.interpreting`
- `response.code_interpreter_call.completed`

### File Search Events
- `response.file_search_call.in_progress`
- `response.file_search_call.searching`
- `response.file_search_call.completed`

### Error
- `error` — Error during streaming (can appear at any point)

## SSE Wire Format
```
event: response.output_text.delta
data: {"type":"response.output_text.delta","response_id":"resp_001","item_id":"msg_007","output_index":0,"content_index":0,"delta":"Hello"}

event: response.completed
data: {"type":"response.completed","response":{"id":"resp_001","status":"completed","usage":{"input_tokens":32,"output_tokens":18}}}
```

Note: Empty lines between events, no `[DONE]` marker.

## Proxy Implementation Notes
1. Forward `event:` and `data:` lines as-is (byte-for-byte)
2. Extract usage from `response.completed` event for billing
3. Handle `error` events mid-stream gracefully
4. `response.incomplete_details.reason` indicates truncation cause
5. Multiple output items: reasoning item + message item is common for reasoning models
6. `background: true` mode has `sequence_number` for resumption via `starting_after`

## Request Format
```json
{
  "model": "gpt-5",
  "input": "Hello!",
  "instructions": "You are helpful.",
  "stream": true,
  "temperature": 1.0,
  "max_output_tokens": 1024,
  "tools": [],
  "tool_choice": "auto",
  "text": {"format": {"type": "text"}},
  "reasoning": {"effort": "medium"}
}
```

Simple string `input` or array of `{role, content}` objects both work.
`instructions` is top-level system prompt (not inside input array).
