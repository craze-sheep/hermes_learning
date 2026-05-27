# GitHub API Search Patterns

## Repository Search
```bash
# Basic search
curl -s "https://api.github.com/search/repositories?q=关键词&per_page=5"

# Search with language filter
curl -s "https://api.github.com/search/repositories?q=关键词+language:python&per_page=5"

# Search with stars filter
curl -s "https://api.github.com/search/repositories?q=关键词+stars:>100&per_page=5"
```

## Response Structure
```json
{
  "total_count": 31,
  "incomplete_results": false,
  "items": [
    {
      "id": 1215153409,
      "name": "chatgpt2api",
      "full_name": "basketikun/chatgpt2api",
      "description": "ChatGPT官网接口纯协议的逆向实现...",
      "html_url": "https://github.com/basketikun/chatgpt2api",
      "stargazers_count": 3185,
      "language": "Python",
      "created_at": "2026-04-19T14:53:01Z",
      "updated_at": "2026-05-27T16:29:11Z"
    }
  ]
}
```

## Extracting README Content
```bash
# Get README via Jina reader
curl -s "https://r.jina.ai/https://github.com/owner/repo"

# Get raw README
curl -s "https://raw.githubusercontent.com/owner/repo/main/README.md"
```

## Filtering Strategies
- **By stars**: `stars:>100` for popular projects
- **By language**: `language:python`, `language:javascript`
- **By topic**: Use keywords in description
- **By freshness**: Sort by `updated` in web interface

## Example: GPT号池 Research
```bash
# Search for GPT account pool projects
curl -s "https://api.github.com/search/repositories?q=GPT号池&per_page=5"

# Results show:
# - chatgpt2api (3185 stars) - ChatGPT逆向实现
# - WindsurfPoolAPI (246 stars) - 多账号池化代理
# - gpt-plus-pool-manager - Plus/Pro账号管理
```

## Tips
- API returns JSON, parse with jq for specific fields
- Rate limit: 10 requests/minute for unauthenticated
- Use `Accept: application/vnd.github.v3+json` header for best results
- Check `description` field for Chinese content
