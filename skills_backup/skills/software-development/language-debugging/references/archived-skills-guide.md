# Archived Debugging Skills — Detailed Reference

The three original debugging skills were consolidated into `language-debugging`. Their full content is preserved:

## Python Debugger (pdb + debugpy)
**Archive:** `~/.hermes/skills/.archive/software-development/python-debugpy/`

Covers: pdb quick reference, breakpoint() recipes, pytest debugging, post-mortem analysis, debugpy remote attach, remote-pdb, Hermes-specific process debugging (tui_gateway, _SlashWorker, gateway).

## Node.js Inspect Debugger
**Archive:** `~/.hermes/skills/.archive/software-development/node-inspect-debugger/`

Covers: node inspect REPL, attaching to running processes, programmatic CDP via chrome-remote-interface, debugging Hermes ui-tui, Vitest under debugger, heap snapshots, CPU profiles.

## Debugging Hermes TUI Commands
**Archive:** `~/.hermes/skills/.archive/software-development/debugging-hermes-tui-commands/`

Covers: Three-layer architecture (Python registry → tui_gateway JSON-RPC → Ink frontend), command autocomplete issues, missing command fixes, CLI vs TUI behavior differences, live UI state patching.
