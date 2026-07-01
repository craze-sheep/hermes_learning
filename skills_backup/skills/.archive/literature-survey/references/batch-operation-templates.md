# Batch Operation Templates for Literature Surveys

Templates for batch downloading PDFs and cloning code repositories during literature surveys.

## PDF Download Script Template

```bash
#!/bin/bash
# Batch PDF download from arXiv
# Usage: bash download_pdfs.sh [target_dir]

set +e  # Continue on errors — critical for batch operations

PAPER_DIR="${1:-.}/papers"
mkdir -p "$PAPER_DIR"
cd "$PAPER_DIR"

download() {
    local url="$1"
    local dest="$2"
    # Skip if already downloaded and valid
    if [ -f "$dest" ] && [ -s "$dest" ] && [ $(stat -c%s "$dest") -gt 5000 ]; then
        echo "EXISTS: $dest"
        return 0
    fi
    rm -f "$dest"
    curl -sL --connect-timeout 30 --max-time 120 -o "$dest" "$url" 2>/dev/null
    if [ $? -eq 0 ] && [ -s "$dest" ] && [ $(stat -c%s "$dest") -gt 5000 ]; then
        echo "OK: $dest ($(du -h "$dest" | cut -f1))"
        return 0
    else
        rm -f "$dest"
        echo "FAIL: $dest"
        return 1
    fi
}

# Add entries in format:
# download "https://arxiv.org/pdf/XXXX.XXXXX" "NN_Author_Year_ShortName.pdf"

# Skip entries for papers without formal publications:
# echo "SKIP: NN_Name (reason)"

echo ""
echo "=== Download Summary ==="
echo "Total PDFs: $(ls -1 *.pdf 2>/dev/null | wc -l)"
ls -lh *.pdf 2>/dev/null
```

## Git Clone Script Template

```bash
#!/bin/bash
# Batch git clone for paper code repos
# Usage: bash clone_repos.sh [target_dir]

set +e  # Continue on errors

CODE_DIR="${1:-.}/code"
mkdir -p "$CODE_DIR"
cd "$CODE_DIR"

clone_repo() {
    local dir="$1"
    local url="$2"
    local note="$3"
    
    # Skip if already cloned
    if [ -d "$dir" ] && [ "$(ls -A "$dir" 2>/dev/null)" ]; then
        echo "EXISTS: $dir"
        return 0
    fi
    
    rm -rf "$dir"
    echo "Cloning $dir from $url ..."
    git clone --depth 1 "$url" "$dir" 2>/dev/null
    
    if [ -d "$dir" ] && [ "$(ls -A "$dir" 2>/dev/null)" ]; then
        echo "OK: $dir"
        return 0
    else
        rm -rf "$dir"
        echo "FAIL: $dir ($note)"
        return 1
    fi
}

# Add entries in format:
# clone_repo "NN_ShortName" "https://github.com/user/repo.git" "官方/非官方"

# Skip entries for closed-source papers:
# echo "SKIP: NN_Name (reason)"

echo ""
echo "=== Clone Summary ==="
echo "Total repos: $(ls -1d */ 2>/dev/null | wc -l)"
ls -d */ 2>/dev/null
```

## Download Report Template

```markdown
# 论文下载报告

> 任务 ID：<task_id>
> 报告日期：<date>
> 调研员：<role>

---

## 执行状态

### 任务概述
根据指令，本批次任务为：
1. 下载N篇论文的PDF到 `papers/` 目录
2. Clone代码仓库到 `code/` 目录
3. 生成下载报告

### 当前状态
**下载脚本已创建，待执行。**

已创建以下脚本文件：
- `download_pdfs.sh` — PDF下载脚本（N篇）
- `clone_repos.sh` — 代码仓库Clone脚本（M个）

**执行方式**：
```bash
bash download_pdfs.sh
bash clone_repos.sh
```

---

## PDF下载清单

| # | 简称 | 文件名 | PDF链接 | 预期大小 | 状态 |
|---|------|--------|---------|---------|------|
| 1 | ... | ... | ... | ... | 待执行 |

---

## 代码仓库Clone清单

| # | 简称 | 目录名 | GitHub链接 | 备注 | 状态 |
|---|------|--------|-----------|------|------|
| 1 | ... | ... | ... | 官方/非官方 | 待执行 |

---

## 跳过项

- **#N Name** — 跳过原因

---

## 注意事项

1. **网络环境**：WSL环境下GitHub可能较慢，脚本已设置 `--depth 1` 浅克隆
2. **闭源论文**：部分论文无公开代码，已标注跳过
3. **非官方复现**：部分代码仓库为社区复现版本

---

## 后续批次建议

供 Supervisor 决策参考：
- 下载完成后可开始逐篇深度分析
```

## Key Design Decisions

1. **`set +e` not `set -e`** — Batch operations must continue even if individual downloads fail. One failed download should not abort the entire batch.

2. **File size check > 5000 bytes** — arXiv error pages are small. Checking file size > 5000 bytes catches most download failures (HTML error pages, empty files, partial downloads).

3. **Sequential, not parallel** — arXiv and GitHub throttle parallel connections. Sequential downloads with timeouts are more reliable in slow network environments (WSL, VPN, etc.).

4. **Skip, don't fail** — For papers without formal publications (e.g., Sora) or closed-source code (e.g., GAIA-1), explicitly skip with a reason rather than treating as failure.

5. **Idempotent operations** — Both scripts check if files/directories already exist before downloading, allowing safe re-runs.

## When Terminal Is Not Available

If the agent doesn't have a terminal/shell tool to execute scripts:
1. Create the scripts as files
2. Document execution instructions in the report
3. Mark status as "待执行" (pending execution)
4. Provide clear instructions for manual execution
