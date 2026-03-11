# 📱 手机交互 - 5分钟快速开始

## 🎯 目标

让你可以在手机上随时与 Evolution AI Agent 对话。

---

## ⚡ 快速配置（5分钟）

### 步骤1：创建 Telegram Bot（2分钟）

1. 打开 Telegram，搜索 **@BotFather**
2. 发送命令：`/newbot`
3. 按提示设置：
   - Bot 名称：`Evolution AI`（随意）
   - Bot 用户名：`your_evolution_bot`（必须以 `_bot` 结尾）
4. **保存 Token**（类似：`123456789:ABCdefGHIjklMNOpqrsTUVwxyz`）

### 步骤2：获取 Chat ID（1分钟）

1. 在 Telegram 搜索你刚创建的 Bot
2. 点击 **Start** 或发送任意消息
3. 浏览器打开（替换 `<YOUR_TOKEN>`）：
   ```
   https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates
   ```
4. 在返回的 JSON 中找到 `"chat":{"id":123456789}`
5. **保存这个数字**

### 步骤3：配置环境变量（1分钟）

编辑 `.env` 文件，添加：

```bash
# Telegram Bot 配置
TG_ENABLED=true
TG_BOT_TOKEN=你的Token
TG_CHAT_ID=你的ChatID
```

### 步骤4：测试配置（30秒）

```bash
python scripts/test_telegram_config.py
```

如果看到 ✅ 说明配置成功！

### 步骤5：启动 Bot（30秒）

```bash
# 方式1：前台运行（测试用）
python -m evolution.chat.telegram_bot

# 方式2：后台运行（推荐）
./scripts/start_telegram_bot.sh
# 选择 2) 后台运行
```

### 步骤6：开始对话！

打开 Telegram，找到你的 Bot，发送：

```
你好
```

Bot 会以 Evolution 导师的身份回复你！

---

## 💬 使用示例

### 日常对话
```
👤 我今天感觉很焦虑
🤖 焦虑的具体表现是什么？身体反应还是思维混乱？
```

### 日程管理
```
👤 提醒我明天下午3点开会
🤖 已记录。明天15:00会议提醒。

👤 今天做什么
🤖 今日日程：
   • 15:00 团队会议
   • 18:00 健身房
```

### 记忆搜索
```
👤 搜索我之前说的关于论文的事
🤖 找到3条相关记忆：
   • 2026-03-08: 论文截止日期是3月15日
   • 2026-03-05: 第三章数据分析遇到困难
```

### 获取情报
```
👤 今日情报
🤖 📡 今日情报摘要
   [筛选后的学术和技术情报]
```

---

## 🔧 管理命令

### 查看运行状态
```bash
./scripts/start_telegram_bot.sh
# 选择 3) 查看运行状态
```

### 停止 Bot
```bash
./scripts/start_telegram_bot.sh
# 选择 4) 停止后台进程
```

### 查看日志
```bash
tail -f logs/telegram_bot.log
```

---

## 🐛 常见问题

### Q1: Bot 不回复消息？

**检查步骤**：
```bash
# 1. 确认 Bot 在运行
ps aux | grep telegram_bot

# 2. 查看日志
tail -f logs/telegram_bot.log

# 3. 检查配置
grep -E "TG_|CLAUDE_|OPENAI_" .env
```

### Q2: 提示 "LLM 服务不可用"？

**原因**：API Key 未配置或失效

**解决**：
```bash
# 检查 .env 文件
cat .env | grep -E "CLAUDE_API_KEY|OPENAI_API_KEY"

# 手动测试 LLM
python -c "
from evolution.utils.llm import call_claude_api
print(call_claude_api('测试'))
"
```

### Q3: 在国内无法连接 Telegram？

**解决方案**：使用代理

```bash
export https_proxy=http://127.0.0.1:7890
python -m evolution.chat.telegram_bot
```

---

## 🚀 生产环境部署

### 使用 Systemd（推荐）

1. 创建服务文件：
```bash
sudo nano /etc/systemd/system/evolution-telegram-bot.service
```

2. 粘贴配置：
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

3. 启动服务：
```bash
sudo systemctl daemon-reload
sudo systemctl enable evolution-telegram-bot
sudo systemctl start evolution-telegram-bot
sudo systemctl status evolution-telegram-bot
```

---

## 📚 更多文档

- **完整使用指南**：`docs/MOBILE_CHAT_GUIDE.md`
- **实现方案详解**：`docs/MOBILE_IMPLEMENTATION_CN.md`
- **项目配置指南**：`docs/CONFIGURATION_GUIDE.md`

---

## ✅ 总结

通过 5 分钟配置，你现在可以：

✅ 在手机上随时与 Evolution 对话  
✅ 管理日程、搜索记忆、获取情报  
✅ 所有对话自动记录，用于每日反思  
✅ 零成本、零维护、即开即用  

**享受你的 7×24 AI 导师吧！** 🎉
