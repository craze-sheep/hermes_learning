# Docling PDF Conversion Pitfalls for CET Exam Papers

## Garbled Output (2016.12, 2017 era PDFs)

Certain Chinese CET exam PDFs convert to completely garbled Unicode despite docling's OCR:
- **Affected years**: Primarily 2016.12 and 2017 (all 3 suites each year)
- **Symptom**: First lines are unreadable symbols like `౽ ౼ Ꭱ ᰵ๔႓` or `ਠ ਴ ੉ ੋਙ`
- **Cause**: Non-standard font encoding or pure image-only layouts that defeat OCR
- **Action**: If first 5 lines are garbled, skip the file entirely. Re-conversion won't help.
- **Workaround**: These PDFs may need manual OCR with different tools (e.g., marker-pdf, PaddleOCR) or the user may have alternative sources.

## File Naming Mapping Between Directories

解析 and 原题 directories have inconsistent naming conventions:

| 解析文件名 | 原题文件名 |
|-----------|-----------|
| `2015.06英语六级考试第1套解析.txt` | `2015年06月六级真题（第1套）.txt` |
| `2016.06英语六级考试第1套解析.txt` | (no 2016.06 原题 exists) |
| `2016年12月六级（第1套）答案及解析.txt` | `2016.12六级第1套试题【可复制可搜索，打印首选】.txt` |
| `2017.06英语六级考试第1套解析.txt` | `2017.06六级真题第1套【可复制可搜索，打印首选】.txt` |

**Strategy**: Match by year + suite number, not by filename pattern. List both directories first, then build a mapping table before processing.

## Missing Original Exam Files

Some 解析 files have no corresponding 原题 file:
- 2016.06 — no 原题 PDF or txt exists at all
- When original is missing, extract option text from the 解析 file's "听前预测" section and mark as "原题文件缺失，选项内容根据解析推断"

## Background Docling Process Hangs

When running docling conversion in background via `terminal(background=true)`, the Python script can hang silently (0% CPU, 6KB memory, no output for 10+ minutes).

**Root cause:** Using `python3 -c "..."` with complex multi-line scripts causes quoting/escaping issues that prevent the script from executing properly.

**Fix:** Use heredoc format instead:
```bash
python3 << 'PYEOF'
import os
from docling.document_converter import DocumentConverter
# ... rest of script ...
PYEOF
```

**Verification:** If a background process shows no output after 5 minutes, check with `process(action='poll')`. If `uptime_seconds` is high but `output_preview` is empty, the process is likely hung. Kill it and restart with heredoc format.

**First-file test:** Before running a full batch conversion, test with a single file first to verify docling initializes correctly:
```python
converter = DocumentConverter()
result = converter.convert("test.pdf")
print(f"Success: {len(result.document.export_to_markdown())} chars")
```

## Long Initialization Time (First Run)

docling's `DocumentConverter()` loads multiple ML models (RapidOCR PP-OCRv4 for detection, classification, recognition). First initialization takes **2-5 minutes** and appears to hang (0% CPU, minimal memory, no output). This is NORMAL.

**Signs of normal loading vs. actual hang:**
- Normal: `ps aux` shows the process exists with some memory; RapidOCR INFO logs appear eventually
- Hang: process has 0% CPU and only ~6KB memory after 10+ minutes; no RapidOCR logs

**RapidOCR initialization logs (NORMAL, not errors):**
```
[INFO] Using engine_name: torch
[INFO] Using GPU device with ID: 0
[INFO] File exists and is valid: .../ch_PP-OCRv4_det_infer.pth
Loading weights: 100%|██████████| 770/770 [00:00<00:00, 1301.22it/s]
```

**Tip:** Run a single-file test first to verify initialization succeeds before starting a batch:
```python
converter = DocumentConverter()
result = converter.convert("test.pdf")
print(f"Success: {len(result.document.export_to_markdown())} chars")
```

## Invalid PDF Documents

Some PDFs fail with `Input document <filename>.pdf is not valid`:
```
ERROR: 2016.12六级第2套试题.pdf: Input document ... is not valid.
ERROR: 2022.06六级真题第1套.pdf: Input document ... is not valid.
```

This is NOT a docling bug — the PDF file itself is corrupted or has an incompatible structure. **Do not retry** — the error is deterministic. Mark these files as unconvertible and move on. In a batch of 50+ PDFs, expect 1-3 to fail this way.

## Background Process OOM Kill (Exit Code 137)

If a background conversion process exits with code 137, it was killed by the OS (SIGKILL, likely OOM). docling loads multiple ML models that consume significant memory. Mitigations:
- Process PDFs one at a time (already in the serial pattern)
- Don't run other memory-intensive tasks alongside docling
- If batch crashes midway, it resumes from where it left off (existing txt files are skipped)

## nvidia-smi Not Available in WSL

Even when `torch.cuda.is_available()` returns True and GPU is detected (e.g., RTX 4060), `nvidia-smi` may not be available as a command in WSL. This is normal — PyTorch accesses the GPU through the CUDA runtime, not through nvidia-smi. Don't panic if nvidia-smi fails; verify GPU via PyTorch instead:
```python
python3 -c "import torch; print(torch.cuda.is_available()); print(torch.cuda.get_device_name(0))"
```
