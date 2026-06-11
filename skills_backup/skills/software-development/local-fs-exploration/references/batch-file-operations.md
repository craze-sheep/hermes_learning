# Batch File Operations with Inconsistent Directory Naming

When copying/moving files from a complex directory tree where subfolder names vary across entries (common with Chinese educational resources, exam archives, downloaded datasets).

## Problem

Source tree has many directories (e.g., one per year), each containing a target subfolder — but the subfolder name isn't consistent:

```
source/
  2019年06月CET6题+解+音频/03、答案解析/  ← "03、"
  2020年12月CET6题+解+音频/03、答案解析/  ← "03、"
  2024年12月CET6题+解+音频/02、答案解析/  ← "02、"
  2020年07月CET6题+解+音频/               ← no subfolder, file at root
  1990年-2018年真题资料【合集】/            ← nested sub-tree
```

## Strategy

### Phase 1: Discover naming variants

```bash
# List all top-level entries and their first few children
cd "/path/to/source" && for dir in */; do echo "=== $dir"; ls "$dir" | head -5; done
```

Look for patterns: the target subfolder might be "02、X", "03、X", "X解析", or files may be at root level.

### Phase 2: Multi-pattern copy loop

```bash
cd "/path/to/source" && for dir in */; do
  if [ -d "$dir/02、答案解析" ]; then
    cp "$dir/02、答案解析/"*.pdf "/dest/" 2>/dev/null
  fi
  if [ -d "$dir/03、答案解析" ]; then
    cp "$dir/03、答案解析/"*.pdf "/dest/" 2>/dev/null
  fi
done
```

### Phase 3: Handle special cases

```bash
# Files at root level (no subfolder) — grep for target keyword
cd "/path/to/source/2020年07月CET6题+解+音频/" && ls | grep -i "解析"
# → "2020.07英语六级考试全1套解析.pdf"
# Copy manually or add another pattern to the loop

# Nested sub-trees — recurse into known structure
cd "/path/to/source/1990年-2018年真题资料【合集】" && for dir in */; do
  if [ -d "$dir/03、答案解析" ]; then
    cp "$dir/03、答案解析/"*.pdf "/dest/" 2>/dev/null
  fi
done
```

### Phase 4: Verify

```bash
ls "/dest/" | wc -l   # total count
ls -la "/dest/"        # check file sizes (non-zero), names look correct
```

## Pitfalls

1. **Don't assume uniform naming.** Always discover first with Phase 1. Numbering prefixes (01、, 02、, 03、) change across years/sources.

2. **Don't forget root-level files.** Some directories have the target file directly, not in a subfolder. Use `grep -i` to find them.

3. **Nested archives.** Some directories contain another level of year-organized directories. Explore with `ls` before writing the copy loop.

4. **File extension case.** PDF files might be `.pdf` or `.PDF`. Use `2>/dev/null` on both patterns, or use case-insensitive glob (`shopt -s nocaseglob`).

5. **Chinese filenames in WSL.** Paths with Chinese characters work fine in bash — no encoding issues. But `browser_navigate` with `file://` protocol will URL-encode them.

6. **Windows → WSL path translation.** `D:\folder\subfolder` → `/mnt/d/folder/subfolder`. Backslashes become forward slashes, drive letter becomes `/mnt/<letter>`.

## WSL-Specific: Windows Path Translation

```bash
# Windows: D:\6级\1.大学英语CET6-历年真题\01六级历年真题及答案解析+听力音频
# WSL:    /mnt/d/6级/1.大学英语CET6-历年真题/01六级历年真题及答案解析+听力音频
```

Common gotcha: the user may type the path with spaces or slight variations from the actual directory name. Always `ls` the parent first to discover the exact name.
