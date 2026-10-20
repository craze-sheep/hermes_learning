# Literature Survey — Paper Notes Template (8 Sections)

Each paper's `notes.md` MUST contain all 8 sections. Section 7 (可借鉴的点) is the most important — it must contain concrete code snippets mapped to the model's actual codebase.

## Template

```markdown
# Paper Title

## 基本信息
- 作者：
- 年份：
- 会议/期刊：
- 论文链接：
- 代码链接：
- PDF：filename.pdf（已下载/需下载）

## 核心贡献
- （3-5 条，每条一句话）

## 模型架构
- Encoder：
- Decoder：
- 交互模块：
- 时序模块：
- （如有代码，标注关键实现细节）

## 损失函数
- （列出所有损失项，公式简述）

## 关键设计选择
- （为什么这样设计，与其他方案对比）

## 与当前模型的对比
- 相似之处：
- 不同之处：

## 可借鉴的点（最重要！）

### 1. [改进名称] → 改进 [具体模块名]
**映射位置**：`model/ai_model/xxx.py` → `ClassName`

**当前问题**：
- （具体描述当前实现的不足）

**具体改进**：
```python
# 当前代码（从实际代码中复制）
class Current(nn.Module):
    ...

# 改进后（完整的、可直接使用的代码）
class Improved(nn.Module):
    ...
```

**预期收益**：
- （量化的预期提升）

**实现难度**：低/中/高
**代码改动**：（具体文件列表）

## 实验结果（关键指标）
| 数据集 | 指标 | 本文 | Baseline A | Baseline B |
|--------|------|------|-----------|-----------|
```

## Writing Rules

1. **Section 7 must have 3-5 concrete suggestions**, each with:
   - Exact file path (e.g., `model/ai_model/encoder.py`)
   - Exact class/function name (e.g., `VisualEncoder`)
   - Current code snippet (copy from actual code)
   - Improved code snippet (complete, runnable)
   - Expected impact (quantified when possible)
   - Implementation difficulty

2. **Do NOT write generic suggestions** like "可以考虑用更好的特征提取器" — this is worthless.
   Instead: "将 `VisualEncoder` 的 4 层 CNN 替换为 DINOv2-ViT-S/14，具体改动在 `encoder.py` 第 45-67 行..."

3. **Every suggestion must reference a specific paper section** — don't invent improvements, cite where the idea comes from in the paper.

4. **Quantify when possible**: "预计 mask IoU 提升 5-10%" rather than "提升性能".

5. **Include implementation difficulty**: helps prioritize. Low = change 1-5 lines. Medium = new module (10-50 lines). High = new architecture or training pipeline change.
