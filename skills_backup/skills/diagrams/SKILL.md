---
name: diagrams
description: "Generate diagrams: dark-themed SVG architecture diagrams or hand-drawn Excalidraw JSON diagrams."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Diagrams, Architecture, SVG, Excalidraw, Flowcharts, Visualization, HTML]
---

# Diagrams

Two diagramming approaches: dark-themed SVG HTML files (architecture diagrams) and hand-drawn Excalidraw JSON files.

## 1. Architecture Diagrams (Dark SVG HTML)

Standalone HTML files with inline SVG. No external tools, no API keys. Best for: software architecture, cloud infrastructure, microservice topology.

**Workflow:** Describe system → generate HTML → save with `write_file` → open in browser.

### Color Palette

| Component | Fill | Stroke |
|-----------|------|--------|
| Frontend | `rgba(8,51,68,0.4)` | `#22d3ee` |
| Backend | `rgba(6,78,59,0.4)` | `#34d399` |
| Database | `rgba(76,29,149,0.4)` | `#a78bfa` |
| Cloud | `rgba(120,53,15,0.3)` | `#fbbf24` |
| Security | `rgba(136,19,55,0.4)` | `#fb7185` |

Font: JetBrains Mono. Background: `#020617` with 40px grid. Components: rounded rects (`rx="6"`), 1.5px strokes. Full HTML template: `templates/template.html`.

---

## 2. Excalidraw Diagrams (Hand-drawn JSON)

Write Excalidraw element JSON → save as `.excalidraw` → drag to excalidraw.com.

### Labeled Shapes (Container Binding)
**Do NOT use** `"label": {"text": "..."}` — silently ignored. Use container binding:
```json
{ "type": "rectangle", "id": "r1", "x": 100, "y": 100, "width": 200, "height": 80,
  "roundness": {"type": 3}, "backgroundColor": "#a5d8ff", "fillStyle": "solid",
  "boundElements": [{"id": "t_r1", "type": "text"}] },
{ "type": "text", "id": "t_r1", "x": 105, "y": 110, "width": 190, "height": 25,
  "text": "Hello", "fontSize": 20, "fontFamily": 1, "strokeColor": "#1e1e1e",
  "textAlign": "center", "verticalAlign": "middle",
  "containerId": "r1", "originalText": "Hello", "autoResize": true }
```

### Arrow Bindings
```json
{ "type": "arrow", "id": "a1", "x": 300, "y": 150, "width": 150, "height": 0,
  "points": [[0,0],[150,0]], "endArrowhead": "arrow",
  "startBinding": {"elementId": "r1", "fixedPoint": [1, 0.5]},
  "endBinding": {"elementId": "r2", "fixedPoint": [0, 0.5]} }
```

### Colors (Light)
Primary `#a5d8ff` | Success `#b2f2bb` | Warning `#ffd8a8` | Processing `#d0bfff` | Error `#ffc9c9` | Storage `#c3fae8`

### Rules
- Min font: 16 body, 20 titles. Never below 14.
- Z-order: array order. Emit: bg → shape → its text → its arrows → next shape
- No emoji. Min text contrast on white: `#757575`
- Upload for shareable link: `scripts/upload.py`

## Choosing Format

| Need | Format |
|------|--------|
| Tech infrastructure | SVG HTML (dark, professional) |
| Whiteboard sketch | Excalidraw (hand-drawn, collaborative) |
| Quick flowchart | Excalidraw (faster to author) |
| Presentation-ready | SVG HTML (polished) |
