# Checking What Model Each AI Coding Tool Uses

When you have Claude Code, Codex, and OpenCode installed, each tool may use a different model. Use these commands to check:

## Claude Code

```bash
claude -p "你用的是什么模型？请直接告诉我模型名称。" --max-turns 1
```

Claude Code inherits the model from its configuration. If configured through Hermes, it may use the same provider/model as Hermes.

## Codex

```bash
codex exec "你用的是什么模型？请直接告诉我模型名称。"
```

Codex shows its config at startup:
```
OpenAI Codex v0.132.0
--------
model: gpt-5.5
provider: my_codex
```

## OpenCode

OpenCode is an interactive TUI — use tmux to query it:

```bash
tmux new-session -d -s opencode-test -x 120 -y 30
tmux send-keys -t opencode-test 'opencode' Enter
sleep 5
tmux send-keys -t opencode-test '你用的是什么模型？请直接告诉我模型名称。' Enter
sleep 10
tmux capture-pane -t opencode-test -p -S -30
tmux send-keys -t opencode-test '/exit' Enter
tmux kill-session -t opencode-test
```

Or check the config file directly:
```bash
cat ~/.config/opencode/opencode.json
```

Look for the `provider` section to find the model name.

## Common Patterns

- Tools configured through Hermes often inherit the same provider/model
- Each tool has its own config file and can be set independently
- The model shown at startup (Codex) or in config is the authoritative source
- Asking the tool via prompt may return the "display name" which differs from the config name
