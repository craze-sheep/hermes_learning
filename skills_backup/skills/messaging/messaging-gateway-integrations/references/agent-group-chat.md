---
name: agent-group-chat
description: "Set up multi-agent group chat: platform selection (Telegram, Discord, WeChat), bot creation, agent-vs-executor patterns, and coordination strategies."
version: 1.0.0
tags: [multi-agent, telegram, discord, wechat, group-chat, orchestration, bots]
metadata:
  hermes:
    tags: [multi-agent, telegram, discord, wechat, group-chat, orchestration, bots]
    related_skills: [hermes-agent, weixin-wechat-gateway, claude-code, codex]
---

# Agent Group Chat — Multi-Agent Communication Patterns

When you want multiple AI agents to collaborate in a shared chat environment (like a group chat), you need to choose the right platform, architecture, and coordination pattern.

## Agent vs Executor — Critical Distinction

```
Agent  = can think + decide + execute + remember
Executor = can only execute, cannot decide what to do
```

| Tool | Type | Can self-direct? |
|------|------|-----------------|
| Hermes | Agent | ✅ Understands, decides, executes |
| Claude Code | Executor | ❌ You tell it what to write |
| Codex | Executor | ❌ You tell it what to write |
| OpenCode | Executor | ❌ You tell it what to write |

**Correct architecture:** Hermes is the brain, Claude Code/Codex/OpenCode are hands.

```
You → Hermes (coordinator)
         ├── Claude Code (write code)
         ├── Codex (write code)
         └── Terminal (run scripts)
```

## Platform Selection

### Comparison Matrix

| Platform | Official Bot API | Free | Ban Risk | Hermes Support | Group Chat | File Size |
|----------|-----------------|------|----------|----------------|------------|-----------|
| **Telegram** | ✅ Yes | ✅ | Low | ✅ Native | ✅ | 2GB |
| **Discord** | ✅ Yes | ✅ | Low | ✅ Native | ✅ | 25MB |
| **Slack** | ✅ Yes | ✅ | Low | ✅ Native | ✅ | 1GB |
| **WeChat** | ⚠️ Limited | ✅ | High | ✅ Via adapter | ⚠️ | 100MB |
| **QQ** | ⚠️ Enterprise | ✅ | High | ❌ No | ⚠️ | 100MB |

### Recommendation

1. **Best for agent group chat:** Telegram (official API, free, no ban risk)
2. **Alternative:** Discord (official API, strong bot ecosystem)
3. **If already using:** WeChat (works but high ban risk with third-party libs)
4. **Avoid:** QQ (requires enterprise certification, high risk)

## Telegram Setup (Recommended)

### Step 1: Create Bots

1. Open Telegram, search `@BotFather`
2. Send `/newbot`, follow prompts
3. Get bot token (format: `123456789:ABCdef...`)
4. Repeat for each agent bot

### Step 2: Create Group

1. Create new group in Telegram
2. Add all bots to the group
3. Make bots admins (for sending messages)

### Step 3: Configure Hermes

```bash
# Add Telegram platform
hermes auth add telegram
# Enter bot token when prompted
```

Or edit `~/.hermes/config.yaml`:

```yaml
platforms:
  telegram:
    - name: "hermes-coordinator"
      token: "BOT_TOKEN_1"
      allowed_chats: ["your_chat_id"]
    - name: "worker-1"
      token: "BOT_TOKEN_2"
      allowed_chats: ["your_chat_id"]
```

### Step 4: Get Chat ID

1. Search `@userinfobot` in Telegram
2. Send any message
3. It replies with your `chat_id`

### Multiple Bots in One Group

```
Telegram Group
├── @hermes_bot (coordinator)
├── @worker_1_bot (worker)
├── @worker_2_bot (worker)
├── @monitor_bot (progress)
└── You (human)
```

Each bot is a separate Hermes instance or a separate token in the same config.

## Discord Setup

### Step 1: Create Application

1. Go to https://discord.com/developers/applications
2. Create New Application
3. Go to Bot section, create bot
4. Enable **Message Content Intent** (required!)

### Step 2: Create Server & Channels

1. Create Discord server
2. Create channels: `#general`, `#progress`, `#errors`

### Step 3: Invite Bots

Generate invite URL with permissions:
```
https://discord.com/api/oauth2/authorize?client_id=YOUR_CLIENT_ID&permissions=2048&scope=bot
```

### Step 4: Configure Hermes

```yaml
platforms:
  discord:
    - name: "hermes-main"
      token: "BOT_TOKEN"
      channels: ["#general"]
```

## WeChat Limitations

**WeChat has no official Bot API for personal accounts.**

Current state:
- Hermes uses `ilinkai.weixin.qq.com` (limited API)
- Third-party libraries (WeChatFerry etc.) have high ban risk
- Multi-bot group chat is difficult (need multiple accounts)
- QQ is worse (enterprise certification required)

### WeChat ClawBot (Official Feature)

WeChat has an official **ClawBot** feature that connects **OpenClaw** to WeChat:
- Install: `npx -y @tencent-weixin/openclaw-weixin-cli@latest install`
- Use: Scan QR code in WeChat to enable the plugin
- Limitation: Only receives replies within 24 hours
- **Hermes and OpenClaw share similar architecture** — ClawBot may work with Hermes too (untested)

The ClawBot setup flow:
1. Run the install command on the machine running OpenClaw/Hermes
2. A QR code is displayed
3. Open WeChat → scan the QR code
4. Enable the ClawBot plugin
5. You can now chat with the agent via WeChat

Configuration in WeChat shows:
- **Deployment method:** Cloud server or Local computer (uses cpolar/ngrok for intranet penetration)
- **WebSocket address:** e.g. `ws://xxxxx.cpolar.top`
- **Gateway Token:** authentication token for the connection
- **Name/icon:** customize the bot appearance

If you must use WeChat:
- Single Hermes instance, simulate multiple roles via prefixes
- Try ClawBot for official support (lower ban risk than third-party libs)
- Or use WeChat Work (企业微信) which has official API

### WeChat MEDIA: Limitation

**`MEDIA:/path/to/file` does NOT work on WeChat.** It only sends the file path as a text string, not the actual file. To share file content, paste it directly in the message.

## Multi-Agent Architectures

### Pattern 1: Hermes Subagents (Simplest)

```
You → Hermes main agent
         ├── delegate_task("Generate S1 data")
         ├── delegate_task("Generate S2 data")
         └── delegate_task("Validate results")
```

- Uses `delegate_task` tool
- Children are isolated, return summaries
- Good for quick parallel subtasks
- Children die when parent finishes

### Pattern 2: Multiple Hermes Processes (Independent)

```bash
# Terminal 1
hermes --profile worker1

# Terminal 2
hermes --profile worker2

# Terminal 3 (monitor)
hermes --profile monitor
```

- Each is fully independent
- Can run for hours/days
- Coordinate via files or shared state

### Pattern 3: Hermes + Executors (Recommended for coding)

```
Hermes (brain) → Claude Code (write code)
               → Codex (write code)
               → Terminal (run scripts)
```

- Hermes decides, executors do
- Best for deterministic tasks
- Token-efficient

### Pattern 4: Kanban Board (Production)

```
Orchestrator profile → Kanban board → Worker profiles
```

- Durable task queue
- Auto-retry, blocking, heartbeats
- See `kanban-orchestrator` and `kanban-worker` skills

## When NOT to Use Multi-Agent

For **deterministic tasks** (fixed parameters, fixed flow):
- ❌ Complex agent frameworks (CrewAI, LangGraph, AutoGen)
- ✅ Simple multiprocessing + file coordination

```python
# This is often better than multi-agent for batch work
from multiprocessing import Pool

def generate_sample(args):
    scene, level, seed = args
    # ... run simulation ...

with Pool(4) as p:
    p.map(generate_sample, [(s, l, seed) for s in scenes ...])
```

Agent frameworks add overhead (LLM calls, coordination) that's unnecessary when you already know exactly what to do.

## Pitfalls

1. **WeChat/QQ third-party bots get banned** — use Telegram/Discord instead
2. **Multiple bots need multiple tokens** — one token per bot, not per group
3. **Bots must be admins** in the group to send messages freely
4. **Discord requires Message Content Intent** — without it, bot can't read messages
5. **Don't use complex frameworks for simple batch work** — multiprocessing is enough
6. **Agent ≠ Executor** — Claude Code/Codex are tools, not agents
7. **Token cost** — multi-agent means multiple LLM calls, costs multiply
8. **Coding tools inherit Hermes model** — Claude Code, Codex, and OpenCode typically use the same model/provider as the parent Hermes instance. Check with `claude -p "what model?"`, `codex exec "what model?"`, or check `~/.config/opencode/opencode.json`. See `claude-code` skill references for details.
