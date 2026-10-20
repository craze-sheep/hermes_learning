# MCP Tool Patterns for ML Model Evaluation

## Context7 — Library Documentation

### Resolve library ID first
```python
# Always resolve before querying
mcp_context7_resolve_library_id(
    libraryName="PyTorch Geometric",
    query="message passing edge features physics simulation"
)
# Returns: /pyg-team/pytorch_geometric (with benchmark score and snippet count)
```

### Query with specific task context
```python
mcp_context7_query_docs(
    libraryId="/pyg-team/pytorch_geometric",
    query="message passing layer with edge features, attention mechanism, aggregation for physics simulation"
)
# Returns: GCNConv, PointNet++, custom MessagePassing examples
```

### Known good library IDs
| Library | ID | Coverage |
|---------|-----|----------|
| PyTorch Geometric | /pyg-team/pytorch_geometric | 495 snippets, High reputation |
| Mamba | /state-spaces/mamba | 27 snippets, Low reputation |
| PyTorch | /pytorch/pytorch | 6294 snippets, High reputation |
| MambaIR | /csguoh/mambair | 79 snippets, High reputation |

**Pitfall**: Mamba has low coverage on Context7. For Mamba-specific docs, read local `repos/mamba/` files directly.

## CodeGraph — Code Structure Analysis

### Best for: understanding call chains and impact
```python
# Start with context for the task
mcp_codegraph_codegraph_context(
    task="How does the interaction module process edge features",
    projectPath="/path/to/project"
)

# Then explore related symbols
mcp_codegraph_codegraph_explore(
    query="EdgeFeatureBuilder MessagePassingLayer edge_feat",
    projectPath="/path/to/project"
)

# Impact analysis before suggesting changes
mcp_codegraph_codegraph_impact(
    symbol="InteractionModule",
    depth=2,
    projectPath="/path/to/project"
)
```

**Pitfall**: CodeGraph requires initialization (`codegraph init`). For reference repos that aren't initialized, use `search_files` + `read_file` instead. Do NOT retry CodeGraph — it will keep failing.

## Parallel Delegation Pattern

Split ML evaluation into 3 independent subtasks:

```python
delegate_task(tasks=[
    {
        "goal": "Analyze encoder and interaction modules against mainstream approaches",
        "context": "Project path, current architecture summary, list of reference repos",
        "toolsets": ["terminal", "file", "web"]
    },
    {
        "goal": "Analyze temporal, decoder, and loss modules against mainstream approaches",
        "context": "Project path, current architecture summary, key design docs",
        "toolsets": ["terminal", "file", "web"]
    },
    {
        "goal": "Search latest papers (2024-2026) for optimization inspirations",
        "context": "Current model architecture, search keywords",
        "toolsets": ["web", "search"]
    }
])
```

Each subagent reads its own files and produces independent analysis. The parent agent synthesizes results into the final document.

## Web Search Fallbacks

When `mcp_fetch_fetch` fails on arXiv/Google Scholar (robots.txt blocking):
1. Fall back to existing `papers.md` if available in the project
2. Use Context7 library docs as proxy for latest implementation patterns
3. Use local reference repo code as evidence of mainstream approaches
4. Draw on model knowledge for 2024-2026 paper summaries
