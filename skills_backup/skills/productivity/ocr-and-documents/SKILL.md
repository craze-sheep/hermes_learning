---
name: ocr-and-documents
description: "Extract text from PDFs/scans (pymupdf, marker-pdf)."
version: 2.3.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [PDF, Documents, Research, Arxiv, Text-Extraction, OCR]
    related_skills: [powerpoint]
---

# PDF & Document Extraction

For DOCX: use `python-docx` (parses actual document structure, far better than OCR).
For PPTX: see the `powerpoint` skill (uses `python-pptx` with full slide/notes support).
This skill covers **PDFs and scanned documents**.

## Step 1: Remote URL Available?

If the document has a URL, **always try `web_extract` first**:

```
web_extract(urls=["https://arxiv.org/pdf/2402.03300"])
web_extract(urls=["https://example.com/report.pdf"])
```

This handles PDF-to-markdown conversion via Firecrawl with no local dependencies.

Only use local extraction when: the file is local, web_extract fails, or you need batch processing.

## Step 2: Choose Local Extractor

| Feature | pymupdf (~25MB) | markitdown (~50MB) | marker-pdf (~3-5GB) | docling (~1GB+) |
|---------|-----------------|--------------------|--------------------|-----------------|
| **Text-based PDF** | ✅ | ✅ | ✅ | ✅ |
| **Scanned PDF (OCR)** | ❌ | ❌ | ✅ (90+ languages) | ✅ |
| **Tables** | ✅ (basic) | ⭐⭐ OK | ✅ (high accuracy) | ✅ (best) |
| **Equations / LaTeX** | ❌ | ❌ | ⭐⭐ medium | ✅ (native LaTeX) |
| **Multi-column layout** | ⭐ messy | ⭐ messy | ✅ (good) | ✅ (best) |
| **Chinese PDF** | ⭐⭐ | ⭐⭐ | ✅ (good) | ⭐⭐ OK |
| **Images extraction** | ✅ (embedded) | ❌ | ✅ (with context) | ✅ |
| **Images → text (OCR)** | ❌ | ❌ | ✅ | ✅ |
| **JSON output** | ❌ | ❌ | ✅ | ✅ (native structured) |
| **Markdown output** | ✅ (via pymupdf4llm) | ✅ (native) | ✅ (native) | ✅ |
| **Install size** | ~25MB | ~50MB | ~3-5GB (PyTorch+models) | ~1GB+ |
| **GPU acceleration** | N/A | N/A | Optional (CUDA) | Optional (CUDA) |
| **Speed** | Instant | Fast | ~1-14s/page (CPU), ~0.2s/page (GPU) | Medium |
| **License** | AGPL | MIT | GPL-3.0 | MIT |

### Tool selection guide

| Need | Use |
|------|-----|
| Quick text extraction, no frills | **pymupdf** |
| Fast Markdown, lightweight, API-friendly | **markitdown** |
| Scanned PDF, OCR, complex layout, images | **marker-pdf** |
| Academic papers, heavy tables, LaTeX formulas | **docling** |
| PDF→JSON with structure preservation | **marker** or **docling** |
**Decision**: Use pymupdf unless you need OCR, equations, forms, or complex layout analysis. For quick Markdown conversion, try markitdown first (lighter than marker). For academic/technical docs with heavy tables and formulas, docling is the best choice.

If the user needs marker/docling capabilities but the system lacks disk:
> "This document needs [marker-pdf/docling], which requires ~[X]GB. Your system has [Y]GB free. Options: free up space, provide a URL so I can use web_extract, or I can try pymupdf/markitdown which works for text-based PDFs but not scanned documents or equations."

---

## markitdown (lightweight Markdown)

```bash
pip install markitdown
```

```bash
# CLI
markitdown document.pdf

# Python
from markitdown import MarkItDown
md = MarkItDown()
result = md.convert("document.pdf")
print(result.text_content)
```

**Best for**: Quick text extraction to Markdown, API pipelines, lightweight environments.
**Limitations**: No OCR, weak on complex tables/multi-column, no image extraction, no JSON output.

---

## docling (academic/scientific)

```bash
pip install docling
```

```bash
# CLI
docling document.pdf --to json
docling document.pdf --to md

# Python
from docling.document_converter import DocumentConverter
converter = DocumentConverter()
result = converter.convert("document.pdf")
print(result.document.export_to_json())  # structured JSON
print(result.document.export_to_markdown())  # Markdown
```

**Best for**: Academic papers, technical reports, documents with heavy tables and LaTeX formulas.
**Limitations**: Heavier install (~1GB+), slower on CPU, Chinese support is OK but not great.
**GPU**: Supports NVIDIA CUDA for acceleration. Requires PyTorch CUDA version ≤ driver CUDA version (see WSL skill `references/wsl2-gpu-support.md` for version mismatch diagnosis).
**License**: MIT — safe for commercial use.

---

## pymupdf (lightweight)

```bash
pip install pymupdf pymupdf4llm
```

**Via helper script**:
```bash
python scripts/extract_pymupdf.py document.pdf              # Plain text
python scripts/extract_pymupdf.py document.pdf --markdown    # Markdown
python scripts/extract_pymupdf.py document.pdf --tables      # Tables
python scripts/extract_pymupdf.py document.pdf --images out/ # Extract images
python scripts/extract_pymupdf.py document.pdf --metadata    # Title, author, pages
python scripts/extract_pymupdf.py document.pdf --pages 0-4   # Specific pages
```

**Inline**:
```bash
python3 -c "
import pymupdf
doc = pymupdf.open('document.pdf')
for page in doc:
    print(page.get_text())
"
```

---

## marker-pdf (high-quality OCR)

```bash
# Check disk space first
python scripts/extract_marker.py --check

pip install marker-pdf
```

**Via helper script**:
```bash
python scripts/extract_marker.py document.pdf                # Markdown
python scripts/extract_marker.py document.pdf --json         # JSON with metadata
python scripts/extract_marker.py document.pdf --output_dir out/  # Save images
python scripts/extract_marker.py scanned.pdf                 # Scanned PDF (OCR)
python scripts/extract_marker.py document.pdf --use_llm      # LLM-boosted accuracy
```

**CLI** (installed with marker-pdf):
```bash
marker_single document.pdf --output_dir ./output
marker /path/to/folder --workers 4    # Batch
```

---

## Arxiv Papers

```
# Abstract only (fast)
web_extract(urls=["https://arxiv.org/abs/2402.03300"])

# Full paper
web_extract(urls=["https://arxiv.org/pdf/2402.03300"])

# Search
web_search(query="arxiv GRPO reinforcement learning 2026")
```

## Split, Merge & Search

pymupdf handles these natively — use `execute_code` or inline Python:

```python
# Split: extract pages 1-5 to a new PDF
import pymupdf
doc = pymupdf.open("report.pdf")
new = pymupdf.open()
for i in range(5):
    new.insert_pdf(doc, from_page=i, to_page=i)
new.save("pages_1-5.pdf")
```

```python
# Merge multiple PDFs
import pymupdf
result = pymupdf.open()
for path in ["a.pdf", "b.pdf", "c.pdf"]:
    result.insert_pdf(pymupdf.open(path))
result.save("merged.pdf")
```

```python
# Search for text across all pages
import pymupdf
doc = pymupdf.open("report.pdf")
for i, page in enumerate(doc):
    results = page.search_for("revenue")
    if results:
        print(f"Page {i+1}: {len(results)} match(es)")
        print(page.get_text("text"))
```

No extra dependencies needed — pymupdf covers split, merge, search, and text extraction in one package.

---

## Exam PDF Extraction

For extracting structured content (word banks, answer keys, question lists) from Chinese English exam PDFs (CET-4/6, IELTS, TOEFL), see `references/exam-pdf-extraction.md` — includes regex patterns, multi-page handling, and batch processing.

## Notes

- `web_extract` is always first choice for URLs
- pymupdf is the safe default — instant, no models, works everywhere
- marker-pdf is for OCR, scanned docs, equations, complex layouts — install only when needed
- Both helper scripts accept `--help` for full usage
- marker-pdf downloads ~2.5GB of models to `~/.cache/huggingface/` on first use
- **docling VRAM**: models ~500MB, inference ~1-2GB. 8GB GPU is more than sufficient for single-document processing.
- For Word docs: `pip install python-docx` (better than OCR — parses actual structure)
- For PowerPoint: see the `powerpoint` skill (uses python-pptx)
