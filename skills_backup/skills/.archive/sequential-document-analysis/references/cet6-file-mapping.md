# CET-6 Exam File Name Mapping

## Answer Explanation → Original Exam File Mapping

The answer explanation files (txt_解析/) and original exam files (txt_原题/) use inconsistent naming. Here are the observed mappings:

| 解析文件名 | 原题文件名 |
|-----------|-----------|
| `2015.06英语六级考试第1套解析.txt` | `2015年06月六级真题（第1套）.txt` |
| `2015.06英语六级考试第2套解析.txt` | `2015年06月六级真题（第2套）.txt` |
| `2015.06英语六级考试第3套解析.txt` | `2015年06月六级真题（第3套）.txt` |
| `2015.12英语六级考试第1套解析.txt` | `2015年12月六级真题（第1套）.txt` |
| `2015.12英语六级考试第2套解析.txt` | `2015年12月六级真题（第2套）.txt` |
| `2015.12英语六级考试第3套解析.txt` | `2015年12月六级真题（第3套）.txt` |
| `2016.06英语六级考试第1套解析.txt` | `2016.12六级第1套试题.txt` (无2016.06原题) |
| `2016年12月六级（第1套）答案及解析.txt` | `2016.12六级第1套试题.txt` |
| `2018.12英语六级考试第1套解析.txt` | `2018.12六级真题第1套【可复制可搜索，打印首选】.txt` |

## PDF-to-TXT Conversion Notes

- `docling` works well for 2015-2016 and 2018.12+ PDFs
- `docling` produces **garbled output** for 2016.12, 2017.x, 2018.06 PDFs — use PyMuPDF OCR fallback
- `2016.06` has no original exam PDF/txt files at all (only answer explanation PDFs)
- Some years' 原题 PDFs are missing entirely (check before trying to convert)

## Key Patterns

- Year format: `20XX.XX` vs `20XX年XX月` vs `20XX.XX`
- Set format: `第N套` always present
- Some years have no original exam files (e.g., 2016.06)
- Some PDF collections have incomplete sets (missing certain years or sets)

## Listening Section Structure (CET-6)

```
Part II Listening Comprehension
├── Section A: Long Conversations (Q1-Q8)
│   ├── Conversation One (Q1-Q4)
│   └── Conversation Two (Q5-Q8)
├── Section B: Passages (Q9-Q15)
│   ├── Passage One (Q9-Q11)
│   └── Passage Two (Q12-Q15)
└── Section C: Recordings/Lectures (Q16-Q25)
    ├── Recording One (Q16-Q18)
    ├── Recording Two (Q19-Q21)
    └── Recording Three (Q22-Q25)
```

Note: Some exam sets share listening content (第3套 may reuse 第2套's listening with shuffled options). Check for "特别说明" in the file.

## 同义替换/同义转述 Variants Found in Explanations

The following phrases all indicate synonym replacement between the listening原文 and the answer选项:

- 同义替换 (most common)
- 同义转述
- 同义改写
- 同义表述
- 同义复现
- 同义概括

All should be treated as equivalent when identifying target questions.
