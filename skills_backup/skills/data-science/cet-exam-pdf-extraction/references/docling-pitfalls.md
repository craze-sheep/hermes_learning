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
