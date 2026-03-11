# 手机交互实现方案（中文版）

## 🎯 设计目标

为 Evolution AI Agent 提供**最轻便、最简单**的手机交互方式，让你可以随时随地与你的 AI 导师对话。

---

## 💡 方案选择

经过仔细分析你的项目架构，我推荐使用 **Telegram Bot** 方案：

### 为什么是 Telegram？

| 特性 | 说明 |
|------|------|
| ✅ **零成本** | 无需服务器、域名、SSL证书 |
| ✅ **极简实现** | 仅需 200 行 Python 代码 |
| ✅ **已有基础** | 你的项目已集成 Telegram 通知 |
| ✅ **双向通信** | 支持发送和接收消息 |
| ✅ **手机体验好** | 原生 App，消息即时送达 |
| ✅ **安全可控** | 只响应你的 Chat ID |
| ✅ **无需公网 IP** | 使用 Long Polling 模式 |

### 与其他方案对比

| 方案 | 复杂度 | 成本 | 体验 | 推荐度 |
|------|--------|------|------|--------|
| **Telegram Bot** | ⭐ | 免费 | ⭐⭐⭐⭐⭐ | ✅ 强烈推荐 |
| 微信公众号 | ⭐⭐⭐⭐ | 需认证 | ⭐⭐⭐⭐ | ❌ 太复杂 |
| Web 界面 | ⭐⭐⭐ | 需服务器 | ⭐⭐⭐ | ⚠️ 适合团队 |
| 邮件回复 | ⭐⭐ | 免费 | ⭐⭐ | ❌ 体验差 |

---

## 🏗️ 架构设计

### 系统架构图

```
┌─────────────────┐
│   你的手机      │
│   (Telegram)    │
└────────┬────────┘
         │ 发送消息
         ↓
┌─────────────────────────────────────┐
│  Telegram Bot (Long Polling)        │
│  evolution/chat/telegram_bot.py     │
└────────┬────────────────────────────┘
         │
         ├─→ 解析用户意图
         │
         ├─→ 调用工具 (Tools)
         │   ├─ EvolutionMemoryTool (搜索记忆)
         │   ├─ EvolutionDBTool (日程管理)
         │   ├─ EvolutionReflectionTool (反思)
         │   └─ EvolutionIntelligenceTool (情报)
         │
         ├─→ 调用 LLM (Claude/GPT)
         │   └─ 生成导师风格的回复
         │
         └─→ 记录对话到数据库
             └─ 用于每日反思
```

### 核心流程

```python
用户消息 → 意图识别 → 工具调用 → 记忆搜索 → LLM 生成回复 → 发送回复 → 记录对话
```

---

## 📦 实现细节

### 1. 核心文件

```
evolution/
├── chat/
│   ├── __init__.py
│   └── telegram_bot.py          # 主要实现（200行）
├── config/
│   └── settings.py               # 配置管理
└── tools/
    ├── memory_tool.py            # 已有
    ├── db_tool.py                # 已有
    ├── reflection_tool.py        # 已有
    └── intelligence_tool.py      # 已有
```

### 2. 关键功能

#### 消息接收（Long Polling）

```python
async def get_updates(self, timeout: int = 30) -> list:
    """获取新消息，无需 Webhook"""
    resp = await client.post(
        f"{self.api_base}/getUpdates",
        json={
            "offset": self.last_update_id + 1,
            "timeout": timeout,
        }
    )
    return resp.json().get("result", [])
```

#### 意图识别

```python
def _parse_tool_call(self, text: str) -> Optional[dict]:
    """智能识别用户意图"""
    if "提醒" in text or "日程" in text:
        return {"tool": "db", "action": "add_schedule"}
    
    if "搜索" in text or "之前" in text:
        return {"tool": "memory", "action": "search"}
    
    # ... 更多规则
```

#### 工具调用

```python
def _execute_tool(self, tool_call: dict) -> str:
    """执行对应的工具"""
    tool = self.tools.get(tool_call["tool"])
    result = tool.execute(tool_call)
    return result.data
```

#### LLM 对话生成

```python
async def _generate_response(self, user_message: str) -> str:
    """生成 AI 回复"""
    # 1. 搜索相关记忆
    memories = self.tools["memory"].execute({
        "action": "search",
        "query": user_message
    })
    
    # 2. 调用 LLM
    response = call_claude_api(
        prompt=f"用户: {user_message}\n记忆: {memories}",
        system=SYSTEM_PROMPT
    )
    
    # 3. 记录对话
    self.db.log_conversation("user", user_message)
    self.db.log_conversation("assistant", response)
    
    return response
```

---

## 🚀 使用流程

### 第一步：创建 Telegram Bot（2分钟）

1. 打开 Telegram，搜索 `@BotFather`
2. 发送 `/newbot`
3. 设置名称：`Evolution AI`
4. 设置用户名：`your_evolution_bot`（必须以 `_bot` 结尾）
5. 保存返回的 Token

### 第二步：获取 Chat ID（1分钟）

1. 搜索你的 Bot，发送 `/start`
2. 浏览器打开：`https://api.telegram.org/bot<TOKEN>/getUpdates`
3. 找到 `"chat":{"id":123456789}`
4. 保存这个数字

### 第三步：配置环境变量（1分钟）

编辑 `.env`：

```bash
TG_ENABLED=true
TG_BOT_TOKEN=你的Token
TG_CHAT_ID=你的ChatID
```

### 第四步：测试配置（30秒）

```bash
python scripts/test_telegram_config.py
```

### 第五步：启动 Bot（10秒）

```bash
# 方式1：前台运行（测试）
python -m evolution.chat.telegram_bot

# 方式2：后台运行（生产）
./scripts/start_telegram_bot.sh
```

### 第六步：开始对话！

打开 Telegram，向你的 Bot 发送：

```
你好
```

---

## 💬 使用示例

### 场景1：日常对话

```
👤 我今天感觉很焦虑

🤖 焦虑的具体表现是什么？
   是身体反应（心跳加速、呼吸急促）
   还是思维层面（担心未来、反复思考）？
```

### 场景2：日程管理

```
👤 提醒我明天下午3点开会

🤖 已记录。明天15:00会议提醒。
   你希望提前多久收到通知？

👤 今天做什么

🤖 今日日程：
   • 15:00 团队会议
   • 18:00 健身房
   
   你昨天说今天要完成论文第三章，进展如何？
```

### 场景3：记忆搜索

```
👤 搜索我之前说的关于论文的事

🤖 找到3条相关记忆：
   • 2026-03-08: 论文截止日期是3月15日
   • 2026-03-05: 第三章数据分析遇到困难
   • 2026-03-01: 决定采用新的实验方法
```

### 场景4：情报获取

```
👤 今日情报

🤖 📡 今日情报摘要
   
   【学术】
   • arXiv 新论文：Inverse Problem 领域3篇
   • Nature 最新研究：量子计算突破
   
   【技术】
   • GitHub Trending：新的 AI 框架
   
   基于你的研究方向，重点关注第一篇论文。
```

---

## 🔧 高级配置

### 使用 Systemd 管理（推荐）

创建 `/etc/systemd/system/evolution-telegram-bot.service`：

```ini
[Unit]
Description=Evolution Telegram Bot
After=network.target

[Service]
Type=simple
User=yjh
WorkingDirectory=/home/yjh/ProjectEvolution
Environment="PATH=/home/yjh/miniconda3/envs/evolution/bin"
ExecStart=/home/yjh/miniconda3/envs/evolution/bin/python -m evolution.chat.telegram_bot
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

启动：

```bash
sudo systemctl enable evolution-telegram-bot
sudo systemctl start evolution-telegram-bot
sudo systemctl status evolution-telegram-bot
```

### 使用 Docker Compose

在 `docker-compose.yml` 添加：

```yaml
services:
  telegram-bot:
    build: .
    command: python -m evolution.chat.telegram_bot
    environment:
      - TG_ENABLED=true
      - TG_BOT_TOKEN=${TG_BOT_TOKEN}
      - TG_CHAT_ID=${TG_CHAT_ID}
    volumes:
      - ./data:/data/evolution
    restart: always
```

---

## 🛡️ 安全性

### 1. 访问控制

Bot 只响应配置的 `TG_CHAT_ID`，其他人发送消息会被忽略：

```python
if chat_id != self.chat_id:
    logger.warning(f"Unauthorized access from {chat_id}")
    return
```

### 2. Token 保护

- ❌ 不要将 Token 提交到 Git
- ✅ 使用 `.env` 文件
- ✅ 确保 `.env` 在 `.gitignore` 中

### 3. 消息加密

Telegram 使用 MTProto 协议，消息端到端加密。

---

## 📊 性能优化

### 1. 减少 LLM 调用

对于简单查询，直接返回数据：

```python
if action == "list_schedule":
    result = self.db.get_today_schedule()
    await self.send_message(result)
    return  # 跳过 LLM
```

### 2. 异步并行

```python
# 并行执行工具调用和记忆搜索
tool_task = asyncio.create_task(self._execute_tool(tool_call))
memory_task = asyncio.create_task(self._search_memory(text))
results = await asyncio.gather(tool_task, memory_task)
```

### 3. 缓存常见问题

```python
from functools import lru_cache

@lru_cache(maxsize=128)
def get_cached_response(query: str, date: str):
    # 缓存当天的查询结果
    pass
```

---

## 🐛 故障排查

### 问题1：Bot 无响应

**检查步骤**：

```bash
# 1. 确认进程运行
ps aux | grep telegram_bot

# 2. 查看日志
tail -f logs/telegram_bot.log

# 3. 测试 API
curl https://api.telegram.org/bot<TOKEN>/getMe
```

### 问题2：LLM 调用失败

**检查配置**：

```bash
# 验证 API Key
grep -E "CLAUDE_|OPENAI_" .env

# 手动测试
python -c "
from evolution.utils.llm import call_claude_api
print(call_claude_api('测试'))
"
```

### 问题3：网络问题

如果在国内，可能需要代理：

```bash
export https_proxy=http://127.0.0.1:7890
python -m evolution.chat.telegram_bot
```

---

## 📈 监控与日志

### 查看日志

```bash
# 实时查看
tail -f logs/telegram_bot.log

# 搜索错误
grep ERROR logs/telegram_bot.log

# 统计消息数
grep "Received:" logs/telegram_bot.log | wc -l
```

### 性能统计

Bot 会自动记录：
- 接收消息数
- 发送消息数
- 错误次数
- 运行时长

---

## 🎓 最佳实践

### 1. 对话记录

所有对话自动记录到 SQLite，用于每日反思：

```sql
SELECT * FROM conversation_logs 
WHERE date(timestamp) = date('now');
```

### 2. 记忆管理

重要信息自动添加到 Mem0：

```python
# 自动触发
self.tools["memory"].execute({
    "action": "add",
    "content": "用户提到论文截止日期是3月15日"
})
```

### 3. 定时任务集成

在 `bridge.py` 中，定时任务可以通过 Telegram 发送：

```python
from evolution.chat.telegram_bot import TelegramBot

async def send_morning_briefing():
    bot = TelegramBot()
    briefing = get_intelligence_briefing()
    await bot.send_message(f"📡 早间情报\n\n{briefing}")
```

---

## 🔮 未来扩展

### 1. 语音消息支持

```python
if "voice" in message:
    # 下载音频 -> Whisper API -> 转文字 -> 处理
    pass
```

### 2. 图片分析

```python
if "photo" in message:
    # 下载图片 -> GPT-4V/Claude 3 -> 分析
    pass
```

### 3. 群组支持

```python
# 支持在群组中 @Bot 触发
if message.get("chat", {}).get("type") == "group":
    if f"@{self.bot_username}" in text:
        # 处理群组消息
        pass
```

---

## 📚 技术栈

| 组件 | 技术 | 说明 |
|------|------|------|
| 消息接收 | Telegram Bot API (Long Polling) | 无需 Webhook |
| 异步处理 | asyncio + httpx | 高性能 |
| LLM 调用 | OpenAI-compatible API | 支持多种模型 |
| 工具系统 | 已有 4 个工具 | 无需修改 |
| 数据存储 | SQLite + Mem0 | 已有基础设施 |

---

## ✅ 总结

通过 **200 行 Python 代码**，你现在拥有：

✅ 随时随地与 Evolution Agent 对话  
✅ 完整的工具调用能力（日程、记忆、情报、反思）  
✅ 所有对话自动记录，用于每日反思  
✅ 零成本、零维护、即开即用  
✅ 安全可控，只响应你的消息  

**实现成本**：
- 开发时间：2小时
- 代码量：200行
- 依赖：0个新包（复用 httpx）
- 服务器：不需要
- 维护成本：几乎为零

**下一步**：

```bash
# 1. 测试配置
python scripts/test_telegram_config.py

# 2. 启动 Bot
python -m evolution.chat.telegram_bot

# 3. 开始对话！
```

---

## 📖 参考文档

- [完整使用指南](./MOBILE_CHAT_GUIDE.md)
- [Telegram Bot API](https://core.telegram.org/bots/api)
- [项目配置指南](./CONFIGURATION_GUIDE.md)
