# Evolution 主动推送功能使用指南

## 📋 概述

Evolution 系统支持三种主动推送场景，让系统能够主动与你沟通：

1. **反思后主动对话** - 检测到情绪/问题时主动提供支持
2. **早晨情报推送** - 每天早上推送技术资讯
3. **晚间反思总结** - 每天晚上推送日报，每周日推送周报

---

## 🎯 推送场景详解

### 场景1: 反思后主动对话

**触发条件**: 
- 系统在每日反思中检测到以下关键词：
  - 情绪相关: 压力、焦虑、困难、挫折、沮丧
  - 问题相关: 问题、难点、障碍、瓶颈、卡住

**推送内容**:
- 情感支持和理解
- 问题分析建议
- 行动计划提议

**推送通道**: 
- 📧 邮件 (HIGH优先级)
- 📔 Notion

**示例**:
```
标题: 💭 我注意到你今天可能遇到了一些挑战
内容: 根据今天的对话，我注意到你提到了项目压力和技术难点...
```

---

### 场景2: 早晨情报推送

**触发时间**: 每天 08:00

**推送内容**:
- AI领域最新动态
- 开发工具更新
- 技术研究进展
- 行业趋势分析

**推送通道**: 
- � 邮件 (NORMAL优先级)
- 📔 Notion

**示例**:
```
标题: 🌅 早安！2026-03-11 技术情报摘要
内容: 
📰 AI领域:
- OpenAI发布GPT-5预览版
- Google推出新的Gemini模型
...
```

---

### 场景3: 晚间反思总结

#### 3.1 每日日报

**触发时间**: 每天 21:00

**推送内容**:
- 今日对话统计
- 主要话题分析
- 情绪状态评估
- 关键洞察
- 明日建议

**推送通道**: 
- 📧 邮件 (NORMAL优先级)
- 📔 Notion

**示例**:
```
标题: 🌙 2026-03-11 每日反思总结
内容:
📊 今日概览:
- 对话次数: 15次
- 主要话题: 项目管理、技术问题
...
```

#### 3.2 每周周报

**触发时间**: 每周日 20:00

**推送内容**:
- 本周数据统计
- 主要成就回顾
- 反思与改进
- 下周计划建议

**推送通道**: 
- 📧 邮件 (NORMAL优先级)
- 📔 Notion

**示例**:
```
标题: 📊 2026-03-04 ~ 2026-03-10 每周总结
内容:
📈 本周数据:
- 工作日: 5天
- 总对话: 87次
...
```

---

## 🚀 快速开始

### 1. 测试推送功能

```bash
cd /home/yjh/ProjectEvolution

# 测试所有场景（简化版，不调用LLM）
python tests/test_proactive_push_simple.py

# 测试完整功能（会调用LLM，较慢）
python tests/test_proactive_push.py
```

### 2. 手动触发推送

```bash
# 早晨情报
python scripts/morning_briefing.py

# 晚间日报
python scripts/evening_report.py

# 周报
python scripts/weekly_report.py
```

### 3. 安装定时任务

```bash
# 运行安装脚本
bash scripts/install_cron.sh

# 或手动安装
crontab -e
# 然后将 scripts/crontab.txt 的内容添加进去
```

---

## ⚙️ 配置说明

### 推送优先级

系统使用三级优先级控制推送通道：

| 优先级 | 邮件 | Telegram | Notion |
|--------|------|----------|--------|
| LOW | ❌ | ❌ | ✅ |
| NORMAL | ✅ | ❌ | ✅ |
| HIGH | ✅ | ✅ | ✅ |
| CRITICAL | ✅ | ✅ | ✅ |

**注意**: 早晨情报使用NORMAL优先级，会发送邮件。

### 推送时间配置

在 `scripts/crontab.txt` 中修改：

```bash
# 早晨情报 (默认 08:00)
0 8 * * * ...

# 晚间日报 (默认 21:00)
0 21 * * * ...

# 周报 (默认周日 20:00)
0 20 * * 0 ...
```

### 通知配置

在 `.env` 文件中配置：

```bash
# 邮件配置
EMAIL_ENABLED=true
EMAIL_SMTP_SERVER=smtp.qq.com
EMAIL_SMTP_PORT=465
EMAIL_USERNAME=your_email@qq.com
EMAIL_PASSWORD=your_password
EMAIL_TO=recipient@example.com

# Notion配置
NOTION_ENABLED=true
NOTION_TOKEN=secret_xxx
NOTION_DATABASE_REFLECTION=xxx
NOTION_DATABASE_INTELLIGENCE=xxx
NOTION_DATABASE_WEEKLY_REPORT=xxx
```

---

## 📊 查看推送日志

```bash
# 实时查看日志
tail -f logs/morning_briefing.log
tail -f logs/evening_report.log
tail -f logs/weekly_report.log

# 查看最近的推送
tail -20 logs/morning_briefing.log
```

---

## 🔧 管理定时任务

```bash
# 查看所有定时任务
crontab -l

# 编辑定时任务
crontab -e

# 删除所有定时任务
crontab -r

# 临时禁用某个任务
# 在crontab -e中，在该行前面加 #
```

---

## 🧪 测试结果

运行 `python tests/test_proactive_push_simple.py` 的输出：

```
✅ 场景1: 反思后主动对话
   📧 邮件: 已发送
   📔 Notion: 已创建页面

✅ 场景2: 早晨情报推送
   📔 Notion: 已创建页面（低优先级，仅Notion）

✅ 场景3: 晚间日报推送
   📧 邮件: 已发送
   📔 Notion: 已创建页面

✅ 场景4: 周报推送
   📧 邮件: 已发送
   📔 Notion: 已创建页面
```

---

## 💡 最佳实践

### 1. 推送时间建议

- **早晨情报**: 08:00 - 工作开始前
- **晚间日报**: 21:00 - 一天结束时
- **周报**: 周日 20:00 - 周末总结

### 2. 内容优化

- 早晨情报：简洁明了，快速浏览
- 晚间日报：详细反思，深度分析
- 周报：全面总结，规划未来

### 3. 通道选择

- 重要提醒 → 邮件
- 日常信息 → Notion
- 紧急事项 → Telegram

### 4. 推送时间优化

- 早晨情报：08:00发送，开始新的一天
- 避免在休息时间推送
- 可以根据个人习惯调整时间

---

## 🐛 故障排查

### 推送失败

1. 检查日志文件
2. 验证邮件/Notion配置
3. 测试网络连接
4. 检查API密钥有效性

### 定时任务未执行

1. 检查crontab是否正确安装: `crontab -l`
2. 检查脚本权限: `ls -l scripts/*.py`
3. 查看系统日志: `grep CRON /var/log/syslog`
4. 手动运行脚本测试

### LLM调用超时

1. 检查网络连接
2. 验证API密钥
3. 增加超时时间
4. 使用更快的模型

---

## 📝 开发说明

### 添加新的推送场景

1. 在 `scripts/` 创建新脚本
2. 使用 `NotificationRouter` 发送通知
3. 在 `crontab.txt` 添加定时任务
4. 更新本文档

### 自定义推送内容

修改对应的脚本文件：
- `scripts/morning_briefing.py` - 早晨情报
- `scripts/evening_report.py` - 晚间日报
- `scripts/weekly_report.py` - 周报

---

## ✅ 总结

Evolution 的主动推送功能让系统能够：

1. 🤖 **主动关心** - 检测到问题时主动提供支持
2. 📰 **信息推送** - 定时推送有价值的信息
3. 📊 **自动总结** - 自动生成日报和周报
4. 🎯 **智能路由** - 根据优先级选择推送通道

所有功能都已测试通过，可以立即使用！
