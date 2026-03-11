# Notion 在 ProjectEvolution 框架中的作用

## 🎯 核心定位：**知识归档与结构化存储中心**

Notion 在整个框架中扮演的是 **"静默的知识管理员"** 角色，与其他通知通道形成互补：

```
┌─────────────────────────────────────────────────────────────┐
│                    通知路由器架构                              │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  📧 Email      → 日常推送，需要阅读但不紧急                    │
│  📱 Telegram   → 即时提醒，需要立即行动                        │
│  📓 Notion     → 知识归档，长期存储与检索                      │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

---

## 📊 优先级路由矩阵

| 优先级 | 使用场景 | Email | Telegram | Notion | 设计理念 |
|--------|---------|-------|----------|--------|---------|
| **LOW** | 情报摘要 | ❌ | ❌ | ✅ | 不打扰用户，静默归档 |
| **NORMAL** | 每日反思、周报 | ✅ | ❌ | ✅ | 邮件通知 + Notion 存档 |
| **HIGH** | 日程提醒 | ✅ | ✅ | ❌ | 即时通知，无需归档 |
| **CRITICAL** | 异常检测 | ✅ | ✅ | ✅ | 全通道轰炸，确保看到 |

---

## 🔍 Notion 的三大核心作用

### 1️⃣ **静默归档 - 不打扰的知识积累**

**场景：情报工具 (Intelligence Tool)**

```python
# evolution/tools/intelligence_tool.py
notifier.send(
    Notification(
        title=f"📡 早间情报 | {date}",
        body=briefing_text,
        priority=NotifyPriority.LOW,  # ← 仅发送到 Notion
        category="intelligence",
    )
)
```

**为什么这样设计？**
- 每天早上自动抓取 RSS 订阅（arXiv、Nature、Science、技术博客等）
- 生成情报摘要，但**不需要立即打扰用户**
- 用户可以在空闲时打开 Notion，批量浏览积累的情报
- 避免邮件/Telegram 被大量信息淹没

**实际效果：**
```
Notion Database: intelligence
├── 2026-03-11 | 📡 早间情报 | arXiv 新论文 3 篇
├── 2026-03-10 | 📡 早间情报 | Nature 最新研究
├── 2026-03-09 | 📡 早间情报 | 技术博客精选
└── ...
```

---

### 2️⃣ **结构化存储 - 按类别分库管理**

Notion 支持 **5 个独立的 Database**，每个对应一个知识类别：

```python
# evolution/config/settings.py
"databases": {
    "schedule": "xxx",        # 日程提醒
    "reflection": "xxx",      # 每日反思
    "skills": "xxx",          # 技能学习记录
    "weekly_report": "xxx",   # 周报
    "intelligence": "xxx",    # 情报摘要
}
```

**路由逻辑：**
```python
# evolution/notification/router.py
db_id = self.databases.get(notification.category)  # 根据 category 自动路由
```

**为什么需要分库？**
- **便于检索**：想看反思记录？直接打开 `reflection` 数据库
- **结构化管理**：每个数据库可以有不同的属性（Date、Tags、Status 等）
- **长期积累**：形成个人知识库，支持 Notion 的强大搜索和关联功能

---

### 3️⃣ **双通道备份 - 邮件 + Notion 互补**

**场景：每日反思 (Reflection Tool)**

```python
# evolution/tools/reflection_tool.py
self.notifier.send(
    Notification(
        title=f"🧠 每日反思 | {date}",
        body=evening_message,
        priority=NotifyPriority.NORMAL,  # ← Email + Notion
        category="reflection",
    )
)
```

**为什么同时发送？**
- **Email**：即时推送，晚上收到反思提醒
- **Notion**：长期存档，可以回顾历史反思，发现模式

**实际效果：**
```
📧 邮件收件箱：
  [Evolution] 🧠 每日反思 | 2026-03-11
  今天完成了 3 个任务，情绪良好...

📓 Notion Database: reflection
  ├── 2026-03-11 | 🧠 每日反思 | 情绪: 良好 | 建议: 继续保持
  ├── 2026-03-10 | 🧠 每日反思 | 情绪: 焦虑 | 建议: 减少任务量
  └── ...
```

---

## 🏗️ 技术实现细节

### Notion API 调用

```python
class NotionChannel(BaseChannel):
    def send(self, notification: Notification) -> bool:
        # 1. 根据 category 选择目标数据库
        db_id = self.databases.get(notification.category)
        
        # 2. 构造 Notion Page 数据
        payload = {
            "parent": {"database_id": db_id},
            "properties": {
                "Name": {"title": [{"text": {"content": notification.title[:100]}}]},
                "Date": {"date": {"start": date_val}},  # 自动添加日期属性
            },
            "children": [
                {
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [{"text": {"content": notification.body[:2000]}}]
                    }
                }
            ],
        }
        
        # 3. 调用 Notion API 创建页面
        resp = httpx.post(
            "https://api.notion.com/v1/pages",
            headers={"Authorization": f"Bearer {self.token}"},
            json=payload,
        )
```

**关键特性：**
- 使用 Notion API v2022-06-28
- 自动截断标题（100 字符）和正文（2000 字符）
- 支持添加 `Date` 属性（从 `metadata` 中提取）
- 失败时记录日志，不影响其他通道

---

## 🎭 实际使用场景

### 场景 1：早晨起床，查看情报摘要

```bash
# 自动运行（定时任务）
python -m evolution.tools.intelligence_tool

# 结果：
# - Notion 中新增一条情报记录（不发邮件/Telegram）
# - 用户在吃早餐时打开 Notion，浏览今天的情报
```

### 场景 2：晚上反思，收到邮件 + Notion 存档

```bash
# 自动运行（定时任务）
python -m evolution.tools.reflection_tool

# 结果：
# - 邮件收到反思提醒（立即阅读）
# - Notion 中存档（未来可以回顾）
```

### 场景 3：异常检测，全通道告警

```python
# 检测到严重异常（severity > 0.6）
self.notifier.send(
    Notification(
        title=f"⚠️ 异常检测 | {date}",
        body="连续 3 天未完成任务，建议调整计划",
        priority=NotifyPriority.CRITICAL,  # ← Email + Telegram + Notion
        category="anomaly",
    )
)

# 结果：
# - 邮件立即收到
# - Telegram 立即推送
# - Notion 中存档（记录异常历史）
```

---

## 🤔 为什么不用 Notion 做双向交互？

你可能会问：既然 Notion 这么强大，为什么不用它做聊天界面？

**原因：**

1. **Notion API 限制**
   - 没有实时推送机制（需要轮询）
   - 不支持 Webhook（无法接收用户输入）
   - API 调用有速率限制（3 requests/second）

2. **交互体验差**
   - 需要在 Notion 中创建页面/评论来发送消息
   - 无法实时对话，延迟高
   - 不适合快速问答场景

3. **定位不同**
   - Notion 是**知识管理工具**，不是**即时通讯工具**
   - 适合存储和检索，不适合实时交互

**所以：**
- **双向交互** → 使用 Web Chat（你刚才选择的方案）
- **知识归档** → 使用 Notion

---

## 📝 配置示例

### 1. 获取 Notion Token

1. 访问 https://www.notion.so/my-integrations
2. 创建新的 Integration
3. 复制 `Internal Integration Token`

### 2. 创建 Notion Databases

在 Notion 中创建 5 个数据库，每个包含以下属性：
- `Name` (Title)
- `Date` (Date)
- `Category` (Select)

### 3. 配置环境变量

```bash
# .env
NOTION_ENABLED=true
NOTION_TOKEN=secret_xxxxxxxxxxxxx

# 5 个数据库 ID（从 URL 中获取）
NOTION_DB_SCHEDULE=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
NOTION_DB_REFLECTION=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
NOTION_DB_SKILLS=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
NOTION_DB_REPORT=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
NOTION_DB_INTEL=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### 4. 测试

```python
from evolution.notification.router import NotificationRouter, Notification, NotifyPriority

router = NotificationRouter()
router.send(
    Notification(
        title="测试消息",
        body="这是一条测试消息",
        priority=NotifyPriority.LOW,
        category="intelligence",
    )
)
```

---

## 🎯 总结

### Notion 的核心价值

| 维度 | 作用 |
|------|------|
| **信息过滤** | 低优先级信息静默归档，不打扰用户 |
| **知识管理** | 按类别分库存储，形成结构化知识库 |
| **长期记忆** | 支持历史回顾、模式发现、趋势分析 |
| **双通道备份** | 与邮件互补，确保重要信息不丢失 |

### 与其他通道的对比

| 通道 | 实时性 | 打扰程度 | 存储能力 | 检索能力 | 适用场景 |
|------|--------|---------|---------|---------|---------|
| **Email** | 中 | 中 | 低 | 低 | 日常推送 |
| **Telegram** | 高 | 高 | 低 | 低 | 即时提醒 |
| **Notion** | 低 | 低 | 高 | 高 | 知识归档 |

### 设计哲学

> **"不是所有信息都需要立即打扰用户，但所有信息都值得被妥善保存。"**

Notion 让你的 AI 助手能够：
- 📚 **静默积累知识**（情报摘要）
- 🧠 **记录思考轨迹**（每日反思）
- 📊 **发现长期模式**（历史数据分析）
- 🔍 **随时检索回顾**（强大的搜索功能）

---

## 🚀 下一步

如果你想充分利用 Notion：

1. **配置 Notion Integration**（参考上面的配置示例）
2. **创建 5 个数据库**（intelligence、reflection、skills、weekly_report、schedule）
3. **启用 Notion 通道**（`NOTION_ENABLED=true`）
4. **运行情报工具**（`python -m evolution.tools.intelligence_tool`）
5. **打开 Notion，查看自动归档的情报**

**如果暂时不需要 Notion：**
- 保持 `NOTION_ENABLED=false`
- 框架会自动跳过 Notion 通道
- 不影响其他功能的使用

---

**最后：Notion 是可选的，但强烈推荐！** 它能让你的 AI 助手从"即时工具"升级为"长期伙伴"。
