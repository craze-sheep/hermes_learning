# Prompt Template: CET-6 Listening Synonym Replacement Extraction

Use this template when asked to write a prompt (not execute it) for extracting synonym replacement questions from CET-6 listening answer explanations.

---

## 任务：提取英语六级听力真题中的"同义替换/同义转述"题目

### 背景
`<base_dir>/` 目录结构：
- `答案解析/`：答案解析 PDF
- `原题/`：原题 PDF
- `txt_解析/`：答案解析 txt（可能已有部分）
- `txt_原题/`：原题 txt（可能已有部分）

### 阶段一：PDF 转 txt（docling）

**第零步：确认 GPU 可用**
```bash
python3 -c "import torch; print(torch.cuda.is_available())"
```
如果 False，安装匹配的 torch CUDA 版本：
```bash
pip install torch==2.6.0+cu124 torchvision==0.21.0+cu124 --index-url https://download.pytorch.org/whl/cu124
```

**第一/二步：用 docling Python API 串行转换**（NOT CLI — CLI 没有 `--gpu` 参数）
```python
import os, warnings, logging
warnings.filterwarnings("ignore")
logging.disable(logging.CRITICAL)
from docling.document_converter import DocumentConverter

converter = DocumentConverter()
# 对 答案解析/ 和 原题/ 两个目录分别执行
for pdf in sorted(os.listdir(pdf_dir)):
    if not pdf.endswith('.pdf'): continue
    txt = pdf.replace('.pdf', '.txt')
    if os.path.exists(os.path.join(txt_dir, txt)): continue
    result = converter.convert(os.path.join(pdf_dir, pdf))
    with open(os.path.join(txt_dir, txt), 'w') as f:
        f.write(result.document.export_to_markdown())
```

- docling 自动使用 GPU（通过 PyTorch），无需 `--gpu` 参数
- 串行处理，一次一个文件，避免显存溢出
- 跳过已有同名 txt 文件
- 在后台运行转换（`terminal background=true notify_on_complete=true`），同时开始处理已转换的文件

### 阶段二：逐文件阅读分析

用 read_file 逐个读取 txt_解析/ 下的文件。**禁止用脚本/grep 批量搜索。**

在每个文件中定位听力部分（共三个 Section，不是两个）：
- **Section A**（长对话，Q1–Q8）
- **Section B**（短文，Q9–Q15）
- **Section C**（讲座/讲话，Q16–Q25，含 Recording One / Two / Three）

通过 AI 语义理解判断哪些题目涉及同义转述/同义替换。注意：
- "同义转述" / "同义替换" 是最常见标记
- "选项是对原文的改写" / "换一种说法" 等表述也算
- 阅读理解部分的"同义词辨析"不算，必须确认是听力部分

对每个目标题目提取：试卷时间+套数、题号及所属 Section、听力原文关键句（英文）、正确答案。

然后读取对应原题 txt，补充四个选项 A/B/C/D 的英文原文。

**边读边写入输出文件**：每分析完一个文件，立即用 `patch` 将发现的题目追加到输出 .md 文件。不要等到全部读完再写。

### 输出格式

```markdown
# 六级听力真题 —— 同义替换/同义转述题目汇总

## 2015年6月 第1套

### Q1（Section A · 长对话）
- **听力原文关键句**：xxx（英文）
- **正确答案**：C
- **选项内容**：
  - A. xxx
  - B. xxx
  - C. xxx
  - D. xxx
- **同义替换说明**：选项C中 xxx 对应听力原文中 xxx，是"xxx"到"xxx"的同义转述。

### Q18（Section C · 讲座）
- **听力原文关键句**：xxx
- **正确答案**：B
- **选项内容**：...
- **同义替换说明**：xxx

---

## 2015年6月 第2套
（听力部分无同义替换/同义转述相关题目）
```

按试卷时间排序，每套内按题号排序。如果某套试卷听力部分没有同义替换题，也要记录"无"。

### 注意事项
1. docling 自动使用 GPU，无 `--gpu` 参数
2. 必须逐文件 read_file，禁止 grep/脚本
3. 必须通过 AI 语义理解，非字符串匹配
4. 听力原文只提取英文部分
5. 覆盖 Section A + B + C 三个部分
6. 边读边写，不要攒到最后
7. 如果原题文件缺失，从解析中推断选项并标注"原题文件缺失"
8. **乱码跳过**：2016.12 和 2017 年的 PDF 转换后可能完全乱码，如果前几行是乱码符号直接跳过
9. **文件名映射**：解析和原题文件名格式不统一，需按年份+套数模糊匹配
