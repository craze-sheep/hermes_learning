# Baidu Search Patterns

## Basic Search
```bash
curl -s "https://r.jina.ai/https://www.baidu.com/s?wd=关键词" | head -500
```

## Site-Specific Search
```bash
# Search within specific site
curl -s "https://r.jina.ai/https://www.baidu.com/s?wd=关键词+site:xiaohongshu.com"

# Search with platform name in query
curl -s "https://r.jina.ai/https://www.baidu.com/s?wd=关键词+小红书"
```

## Filtering Results
- Results are in Markdown format after Jina extraction
- Look for organic results (not ads)
- Timestamps indicate content freshness
- Image links may contain relevant visual content

## Example Output Structure
```
Title: 搜索词_百度搜索

## 网页结果
1. [标题](链接)
   摘要文本...
   时间戳

2. [标题](链接)
   摘要文本...
   时间戳

## 相关搜索
- 相关搜索词1
- 相关搜索词2
```

## Tips
- Use `| head -N` to limit output length
- Results are ordered by relevance
- Recent content appears with specific dates
- Baidu indexes Chinese platform content well
