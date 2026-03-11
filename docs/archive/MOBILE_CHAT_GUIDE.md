# Evolution 手机交互指南

## 🎯 方案概述

通过 **Telegram Bot** 实现与 Evolution Agent 的双向对话，无需额外服务器或复杂配置。

### 为什么选择 Telegram？

- ✅ **零成本**：无需服务器、域名、SSL证书
- ✅ **轻量级**：使用 Long Polling，不需要 Webhook
- ✅ **已集成**：你已经有 Telegram 通知通道
- ✅ **体验好**：手机端原生支持，消息即时送达
- ✅ **安全**：只响应你配置的 chat_id

---

## 📱 快速开始（5分钟）

### 第一步：创建 Telegram Bot

1. **打开 Telegram**，搜索 `@BotFather`
2. **发送命令** `/newbot`
3. **设置名称**：
   - Bot 名称：`Evolution AI` （可自定义）
   - Bot 用户名：`your_evolution_bot` （必须以 `_bot` 结尾）
4. **保存 Token**：BotFather 会返回类似这样的 token：
   ```
   123456789:ABCdefGHIjklMNOpqrsTUVwxyz
   ```

### 第二步：获取你的 Chat ID

1. **搜索你刚创建的 Bot**（例如 `@your_evolution_bot`）
2. **点击 Start** 或发送任意消息（例如 `/start`）
3. **在浏览器打开**：
   ```
   https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates
   ```
   将 `<YOUR_BOT_TOKEN>` 替换为第一步获得的 token
4. **找到 chat_id**：在返回的 JSON 中找到 `"chat":{"id":123456789}`
5. **保存这个数字**（例如 `123456789`）

### 第三步：配置环境变量

编辑 `.env` 文件：

```bash
# Telegram Bot 配置
TG_ENABLED=true
TG_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
TG_CHAT_ID=123456789
```

### 第四步：启动 Bot

```bash
# 方式1：直接运行（推荐用于测试）
python -m evolution.chat.telegram_bot

# 方式2：后台运行（生产环境）
nohup python -m evolution.chat.telegram_bot > logs/telegram_bot.log 2>&1 &

# 方式3：使用 systemd（最稳定）
sudo systemctl start evolution-telegram-bot
```

### 第五步：开始对话

打开 Telegram，找到你的 Bot，直接发送消息：

```
你好
```

Bot 会以 Evolution 导师的身份回复你！

---

## 💬 使用示例

### 日常对话

```
用户: 我今天感觉很焦虑
Bot: 焦虑的具体表现是什么？身体反应还是思维混乱？
```

### 日程管理

```
用户: 提醒我明天下午3点开会
Bot: 已记录。明天15:00会议提醒。你希望提前多久收到通知？

用户: 今天做什么
Bot: 今日日程：
     1. 15:00 团队会议
     2. 18:00 健身房
     你昨天说今天要完成论文第三章，进展如何？
```

### 记忆搜索

```
用户: 搜索我之前说的关于论文的事
Bot: 找到3条相关记忆：
     - 2026-03-08: 你说论文截止日期是3月15日
     - 2026-03-05: 你提到第三章的数据分析遇到困难
     - 2026-03-01: 你决定采用新的实验方法
```

### 情报获取

```
用户: 今日情报
Bot: [调用 intelligence tool，返回筛选后的情报摘要]
```

### 每日反思

```
用户: 今日反思
Bot: [生成今日反思报告]
```

---

## 🔧 高级配置

### 使用 Systemd 管理（推荐生产环境）

创建服务文件 `/etc/systemd/system/evolution-telegram-bot.service`：

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

启动服务：

```bash
sudo systemctl daemon-reload
sudo systemctl enable evolution-telegram-bot
sudo systemctl start evolution-telegram-bot

# 查看状态
sudo systemctl status evolution-telegram-bot

# 查看日志
sudo journalctl -u evolution-telegram-bot -f
```

### 使用 Docker Compose

在 `docker-compose.yml` 中添加：

```yaml
services:
  telegram-bot:
    build: .
    command: python -m evolution.chat.telegram_bot
    environment:
      - TG_ENABLED=true
      - TG_BOT_TOKEN=${TG_BOT_TOKEN}
      - TG_CHAT_ID=${TG_CHAT_ID}
      - CLAUDE_API_KEY=${CLAUDE_API_KEY}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    volumes:
      - ./data:/data/evolution
    restart: always
```

启动：

```bash
docker-compose up -d telegram-bot
```

---

## 🛡️ 安全建议

### 1. 限制访问

Bot 只会响应配置的 `TG_CHAT_ID`，其他人发送消息会被忽略。

### 2. 保护 Token

- ❌ 不要将 Bot Token 提交到 Git
- ✅ 使用 `.env` 文件管理敏感信息
- ✅ 确保 `.env` 在 `.gitignore` 中

### 3. 定期更新 Token

如果 Token 泄露，在 BotFather 中使用 `/revoke` 命令撤销旧 Token。

---

## 🐛 故障排查

### 问题1：Bot 无响应

**检查步骤**：

```bash
# 1. 确认 Bot 进程在运行
ps aux | grep telegram_bot

# 2. 查看日志
tail -f logs/telegram_bot.log

# 3. 测试 API 连接
curl https://api.telegram.org/bot<YOUR_TOKEN>/getMe
```

### 问题2：收到消息但不回复

**可能原因**：
- LLM API Key 未配置或失效
- Chat ID 不匹配

**解决方法**：

```bash
# 检查环境变量
grep -E "TG_|CLAUDE_|OPENAI_" .env

# 手动测试 LLM
python -c "
from evolution.utils.llm import call_claude_api
print(call_claude_api('测试'))
"
```

### 问题3：Long Polling 超时

**现象**：日志中频繁出现 timeout 错误

**解决方法**：
- 检查网络连接
- 如果在国内，可能需要配置代理：

```bash
export https_proxy=http://127.0.0.1:7890
python -m evolution.chat.telegram_bot
```

---

## 🚀 进阶功能

### 1. 添加自定义命令

编辑 `evolution/chat/telegram_bot.py`，在 `handle_message` 方法中添加：

```python
if text == "/status":
    # 返回系统状态
    await self.send_message("系统运行正常 ✅", chat_id)
    return
```

### 2. 支持语音消息

Telegram Bot API 支持语音转文字，可以集成 Whisper API：

```python
# 在 handle_message 中添加
if "voice" in message:
    file_id = message["voice"]["file_id"]
    # 下载音频 -> 调用 Whisper -> 转为文字 -> 处理
```

### 3. 支持图片分析

如果使用支持视觉的 LLM（如 GPT-4V、Claude 3），可以处理图片：

```python
if "photo" in message:
    # 下载图片 -> 发送给 LLM -> 分析内容
```

---

## 📊 性能优化

### 1. 减少 LLM 调用

对于简单查询（如 "今天做什么"），直接返回数据库结果，不调用 LLM：

```python
if tool_call and tool_call.get("action") == "list_schedule":
    result = self._execute_tool(tool_call)
    await self.send_message(result, chat_id)
    return  # 跳过 LLM
```

### 2. 异步处理

当前实现已使用 `asyncio`，可以进一步优化：

```python
# 并行执行工具调用和记忆搜索
tool_task = asyncio.create_task(self._execute_tool_async(tool_call))
memory_task = asyncio.create_task(self._search_memory_async(user_message))
tool_result, memory_result = await asyncio.gather(tool_task, memory_task)
```

### 3. 缓存常见问题

对于高频问题（如 "今天做什么"），可以缓存结果：

```python
from functools import lru_cache
from datetime import date

@lru_cache(maxsize=128)
def get_today_schedule(user_id: str, today: date):
    # 缓存当天的日程查询
    pass
```

---

## 🔄 与现有系统集成

### 定时任务触发

在 `evolution/utils/bridge.py` 中，定时任务可以通过 Telegram 发送结果：

```python
from evolution.chat.telegram_bot import TelegramBot

async def send_morning_briefing():
    bot = TelegramBot()
    briefing = get_intelligence_briefing()
    await bot.send_message(f"📡 早间情报\n\n{briefing}")
```

### 异常告警

在关键操作失败时，通过 Telegram 发送告警：

```python
try:
    critical_operation()
except Exception as e:
    bot = TelegramBot()
    asyncio.run(bot.send_message(f"🚨 系统异常: {str(e)}"))
```

---

## 📈 监控与日志

### 日志配置

在 `evolution/chat/telegram_bot.py` 中已配置日志，查看方式：

```bash
# 实时查看
tail -f logs/telegram_bot.log

# 搜索错误
grep ERROR logs/telegram_bot.log

# 统计消息数量
grep "Received:" logs/telegram_bot.log | wc -l
```

### 性能监控

添加简单的统计：

```python
class TelegramBot:
    def __init__(self):
        # ...
        self.stats = {
            "messages_received": 0,
            "messages_sent": 0,
            "errors": 0,
            "start_time": datetime.now()
        }
    
    async def handle_message(self, message):
        self.stats["messages_received"] += 1
        # ...
```

---

## 🎓 最佳实践

### 1. 对话记录

所有对话已自动记录到 SQLite（`conversation_logs` 表），用于每日反思。

### 2. 记忆管理

重要信息会自动添加到 Mem0，但你也可以手动触发：

```
用户: 记住：我的论文截止日期是3月15日
Bot: 已记录到长期记忆。
```

### 3. 多设备同步

Telegram 支持多设备，你可以在手机、电脑、平板上同时使用。

### 4. 消息历史

Telegram 会保存所有聊天记录，即使 Bot 重启也不会丢失。

---

## 🆚 方案对比

| 方案 | 优点 | 缺点 | 适用场景 |
|------|------|------|----------|
| **Telegram Bot** | 零成本、轻量、即时 | 依赖 Telegram | 个人使用 ✅ |
| 微信公众号 | 用户多 | 需要企业认证、审核严格 | 企业应用 |
| Web 界面 | 自由度高 | 需要服务器、域名、SSL | 团队协作 |
| 钉钉/飞书 Bot | 企业集成好 | 配置复杂 | 企业内部 |

**推荐**：个人使用首选 Telegram Bot，简单高效。

---

## 📚 参考资源

- [Telegram Bot API 官方文档](https://core.telegram.org/bots/api)
- [BotFather 使用指南](https://core.telegram.org/bots#botfather)
- [Long Polling vs Webhook](https://core.telegram.org/bots/api#getting-updates)

---

## 🎉 总结

通过 **200 行 Python 代码**，你现在可以：

✅ 在手机上随时与 Evolution Agent 对话  
✅ 管理日程、搜索记忆、获取情报  
✅ 所有对话自动记录，用于每日反思  
✅ 零成本、零维护、即开即用  

**下一步**：运行 `python -m evolution.chat.telegram_bot`，开始你的第一次对话！
