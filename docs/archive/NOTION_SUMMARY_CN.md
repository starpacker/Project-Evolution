# Notion 作用总结

## 🎯 一句话总结

**Notion 是你的 AI 助手的"长期记忆库"，负责静默归档低优先级信息，并为所有重要信息提供结构化的长期存储。**

---

## 📊 三通道对比

| 特性 | Email 📧 | Telegram 📱 | Notion 📓 |
|------|---------|------------|----------|
| **实时性** | 中等（分钟级） | 高（秒级） | 低（不需要实时） |
| **打扰程度** | 中等 | 高 | 零打扰 |
| **存储能力** | 低（邮箱容量有限） | 低（聊天记录难检索） | 高（无限存储） |
| **检索能力** | 低（邮件搜索弱） | 低（无结构化） | 高（数据库+搜索） |
| **适用场景** | 日常推送 | 紧急提醒 | 知识归档 |

---

## 🔄 优先级路由逻辑

```
LOW (情报摘要)
  └─→ 仅 Notion ✅
      理由：不打扰用户，静默积累

NORMAL (每日反思、周报)
  ├─→ Email ✅ (即时阅读)
  └─→ Notion ✅ (长期存档)

HIGH (日程提醒)
  ├─→ Email ✅
  ├─→ Telegram ✅ (即时通知)
  └─→ Notion ❌ (无需归档)

CRITICAL (异常告警)
  ├─→ Email ✅
  ├─→ Telegram ✅
  └─→ Notion ✅ (全通道轰炸)
```

---

## 💡 核心价值

### 1. 静默归档（不打扰）

**问题：** 每天自动抓取大量 RSS 信息（arXiv、Nature、技术博客），如果全部发邮件/Telegram，会淹没真正重要的消息。

**解决：** 情报摘要设为 `LOW` 优先级，仅写入 Notion，用户可以在空闲时批量浏览。

```python
# 每天早上自动运行
notifier.send(
    Notification(
        title="📡 早间情报",
        body="今天有 5 篇相关论文...",
        priority=NotifyPriority.LOW,  # ← 仅 Notion
        category="intelligence",
    )
)
```

### 2. 结构化存储（分类管理）

Notion 支持 5 个独立数据库，每个对应一个知识类别：

- `intelligence` - 情报摘要（每日 RSS 汇总）
- `reflection` - 每日反思（情绪、任务、建议）
- `skills` - 技能学习记录
- `weekly_report` - 周报
- `schedule` - 日程提醒

**好处：**
- 想看反思记录？直接打开 `reflection` 数据库
- 想回顾学习历程？打开 `skills` 数据库
- 支持 Notion 的强大搜索、筛选、关联功能

### 3. 长期记忆（模式发现）

**场景：** 你想知道"过去一个月我的情绪变化趋势"

- Email：需要翻阅 30 封邮件，手动整理
- Telegram：聊天记录难以检索
- **Notion**：打开 `reflection` 数据库，按日期排序，一目了然

**更进一步：**
- 在 Notion 中创建 Dashboard，可视化情绪趋势
- 使用 Notion AI 分析历史数据，发现模式
- 关联不同数据库（如反思 + 技能学习），发现相关性

---

## 🛠️ 技术实现

### 按类别路由到不同数据库

```python
class NotionChannel(BaseChannel):
    def send(self, notification: Notification) -> bool:
        # 根据 category 选择目标数据库
        db_id = self.databases.get(notification.category)
        
        # 创建 Notion 页面
        payload = {
            "parent": {"database_id": db_id},
            "properties": {
                "Name": {"title": [{"text": {"content": notification.title}}]},
                "Date": {"date": {"start": date_val}},
            },
            "children": [
                {"type": "paragraph", "paragraph": {"rich_text": [...]}}
            ],
        }
        
        httpx.post("https://api.notion.com/v1/pages", json=payload)
```

### 配置示例

```bash
# .env
NOTION_ENABLED=true
NOTION_TOKEN=secret_xxxxxxxxxxxxx

# 5 个数据库 ID
NOTION_DB_INTEL=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
NOTION_DB_REFLECTION=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
NOTION_DB_SKILLS=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
NOTION_DB_REPORT=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
NOTION_DB_SCHEDULE=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

---

## 🤔 常见问题

### Q1: 为什么不用 Notion 做双向聊天？

**A:** Notion 是知识管理工具，不是即时通讯工具：
- 没有实时推送机制（需要轮询）
- 不支持 Webhook（无法接收用户输入）
- API 有速率限制（3 requests/second）
- 交互体验差（需要创建页面/评论）

**所以：**
- 双向交互 → Web Chat / Telegram Bot
- 知识归档 → Notion

### Q2: 不配置 Notion 会影响其他功能吗？

**A:** 不会！
- 保持 `NOTION_ENABLED=false`
- 框架会自动跳过 Notion 通道
- Email 和 Telegram 正常工作

### Q3: 我需要配置 Notion 吗？

**A:** 看你的需求：

**需要配置的情况：**
- 想要长期积累知识库
- 需要回顾历史数据、发现模式
- 希望减少邮件/Telegram 的打扰

**可以不配置的情况：**
- 只需要即时通知，不需要归档
- 不使用 Notion
- 暂时想简化配置

---

## 🎯 实际使用示例

### 示例 1：早晨查看情报

```bash
# 定时任务每天早上 8:00 运行
python -m evolution.tools.intelligence_tool

# 结果：
# - Notion 中新增一条情报记录
# - 不发邮件/Telegram（不打扰）
# - 你在吃早餐时打开 Notion，浏览今天的情报
```

### 示例 2：晚上反思

```bash
# 定时任务每天晚上 22:00 运行
python -m evolution.tools.reflection_tool

# 结果：
# - 邮件收到反思提醒（立即阅读）
# - Notion 中存档（未来可以回顾）
```

### 示例 3：异常告警

```python
# 检测到严重异常（连续 3 天未完成任务）
notifier.send(
    Notification(
        title="⚠️ 异常检测",
        body="连续 3 天未完成任务，建议调整计划",
        priority=NotifyPriority.CRITICAL,
        category="anomaly",
    )
)

# 结果：
# - Email 立即收到 ✅
# - Telegram 立即推送 ✅
# - Notion 中存档 ✅（记录异常历史）
```

---

## 📈 长期价值

使用 Notion 一段时间后，你会拥有：

1. **完整的情报库** - 所有 RSS 订阅的历史记录
2. **反思日记** - 每天的情绪、任务、建议
3. **学习轨迹** - 技能学习的完整历程
4. **异常记录** - 所有告警的历史数据

**这些数据可以用于：**
- 回顾过去，发现模式
- 分析趋势，优化习惯
- 训练个性化 AI 模型
- 生成年度报告

---

## 🚀 快速开始

### 1. 创建 Notion Integration

1. 访问 https://www.notion.so/my-integrations
2. 点击 "New integration"
3. 复制 `Internal Integration Token`

### 2. 创建数据库

在 Notion 中创建 5 个数据库，每个包含：
- `Name` (Title)
- `Date` (Date)
- `Category` (Select)

### 3. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env，填入 Notion Token 和数据库 ID
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

## 📚 相关文档

- [完整技术报告](../technical_report_CN.md) - 第 8 章：通知路由系统
- [配置指南](./CONFIGURATION_GUIDE.md) - Notion 配置详解
- [Notion 角色详解](./NOTION_ROLE_EXPLANATION.md) - 深入理解 Notion 的作用

---

## 💬 总结

> **"不是所有信息都需要立即打扰用户，但所有信息都值得被妥善保存。"**

Notion 让你的 AI 助手从"即时工具"升级为"长期伙伴"：
- 📚 静默积累知识
- 🧠 记录思考轨迹
- 📊 发现长期模式
- 🔍 随时检索回顾

**Notion 是可选的，但强烈推荐！**
