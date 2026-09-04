# Case Study: GPT号池搭建 Research (2026-05-27)

## Objective
Research "GPT号池搭建" (GPT account pool building) from 小红书 and other Chinese sources.

## Execution Flow

### Step 1: Direct CDP Access (Failed)
```bash
# Tried browser_navigate to xiaohongshu.com
# Result: IP risk detection, error code 300012
# Platform blocked automated access
```

### Step 2: CDP Proxy Troubleshooting (Failed)
```bash
# Tried check-deps script
node "/home/lzy/.hermes/skills/web-access/scripts/check-deps.mjs"
# Result: Connection timeout, proxy issues

# Tried killing and restarting proxy
pkill -f cdp-proxy.mjs
# Result: Still failed
```

### Step 3: Baidu Search (Success)
```bash
# General search
curl -s "https://r.jina.ai/https://www.baidu.com/s?wd=GPT号池搭建" | head -400

# Results revealed:
# - GPT号池 = batch registered/shared overseas GPT accounts
# - Used for token resale, time-sharing, rate limit evasion
# - Methods: batch registration, free tier abuse, regional pricing
```

### Step 4: Baidu Tutorial Search (Success)
```bash
# More specific search
curl -s "https://r.jina.ai/https://www.baidu.com/s?wd=GPT号池搭建+教程" | head -500

# Found:
# - Docker-based GPT service setup
# - CSDN blog posts with tutorials
# - Video tutorials on Bilibili
# - Technical implementation details
```

### Step 5: GitHub API Search (Success)
```bash
# Search for related projects
curl -s "https://api.github.com/search/repositories?q=GPT号池&per_page=5"

# Found key projects:
# 1. basketikun/chatgpt2api (3185 stars)
#    - ChatGPT逆向实现
#    - 支持注册机维持号池额度
#    - 兼容OpenAI接口协议
#
# 2. guanxiaol/WindsurfPoolAPI (246 stars)
#    - 多账号池化API代理
#    - 支持113+模型
#
# 3. AlexANSO/gpt-plus-pool-manager
#    - GPT Plus/Pro账号池管理工具
```

## Key Findings

### What is GPT号池?
- Batch registration of overseas GPT accounts
- Shared token quotas across multiple users
- Methods: virtual identities, overseas IPs, regional pricing
- Used for: resale, time-sharing, rate limit evasion

### Technical Implementation
1. **账号获取**: Batch registration with virtual phone/email
2. **代理服务**: Reverse proxy with load balancing
3. **号池管理**: Account status monitoring, quota distribution
4. **API封装**: OpenAI-compatible interface

### Risks Identified
- Violates platform terms of service
- Legal issues (fraud, illegal business operations)
- Account bans
- Data security concerns
- Service instability

## Lessons Learned

1. **小红书 is heavily protected**: Even CDP access fails
2. **Baidu is reliable**: For Chinese content search
3. **GitHub API works well**: For technical topic research
4. **Jina reader is essential**: For extracting search results
5. **Multiple fallback strategies needed**: When primary methods fail

## Related Skills
- `web-access` - For general web access patterns
- `chinese-platform-research` - This skill, for Chinese platform research
