# 📡 情报收集者功能分析报告

## 🔍 当前实现状态

### ✅ 已实现的功能

#### 1. **定时自动推送**（08:00）
- **触发方式**: CowAgent 定时任务（Cron: `0 8 * * *`）
- **工作流程**:
  1. 自动拉取 RSS 订阅源（30+ 源）
  2. 搜索用户兴趣（从 Mem0 记忆）
  3. LLM 筛选最相关的 1-3 条信息
  4. 用导师口吻生成推送文本
  5. 通过 NotificationRouter 推送（优先级: LOW → 仅 Notion）

#### 2. **手动查询功能**
- **调用方式**: 用户主动询问
- **工具调用**: `[TOOL:intelligence]fetch_latest[/TOOL]`
- **问题**: ❌ **Web Chat 中的实现有 BUG**

---

## ⚠️ 发现的问题

### 问题 1: Web Chat 中的工具调用错误

**当前代码**（`evolution/chat/web_chat.py` 第 150-154 行）:
```python
elif tool_name == "intelligence":
    if "fetch_latest" in params:
        result = intelligence_tool.execute({"action": "fetch_latest"})
        return f"最新情报：\n{result.result if result.status == 'success' else result.result}"
    else:
        return "情报工具参数：fetch_latest"
```

**问题分析**:
1. ❌ `action='fetch_latest'` **不存在**
2. ✅ 正确的 action 应该是 `action='briefing'`
3. ❌ 工具说明文档也写错了（第 94 行）

**正确的 action 列表**（从 `intelligence_tool.py` 第 55 行）:
```python
"enum": ["briefing", "raw_feeds", "add_feed", "list_feeds"]
```

### 问题 2: 响应方式

**当前行为**: 
- 用户询问 → 调用工具 → **立即返回结果**
- 不需要等待，不需要再次询问

**工作流程**:
```
用户: "帮我收集一下最新的 AI 研究进展"
  ↓
LLM 识别意图 → 调用 intelligence 工具
  ↓
工具执行（拉取 RSS + LLM 筛选，约 10-30 秒）
  ↓
返回结果 → 用户立即看到
```

**不是异步的**: 
- ❌ 不会说"我去收集一下，稍后告诉你"
- ✅ 会等待收集完成后直接回复

---

## 🔧 修复方案

### 修复 1: 更正 Web Chat 中的 action 名称

```python
# 修改前
if "fetch_latest" in params:
    result = intelligence_tool.execute({"action": "fetch_latest"})

# 修改后
if "briefing" in params or "fetch" in params or "latest" in params:
    result = intelligence_tool.execute({"action": "briefing"})
```

### 修复 2: 更新工具说明

```python
# 修改前
- `intelligence` - 情报工具：`[TOOL:intelligence]fetch_latest[/TOOL]`

# 修改后
- `intelligence` - 情报工具：`[TOOL:intelligence]briefing[/TOOL]`
```

### 修复 3: 改进用户体验（可选）

**方案 A: 保持同步**（当前方式）
- 优点: 简单直接
- 缺点: 用户需要等待 10-30 秒

**方案 B: 改为异步**（推荐）
```python
# 1. 立即回复
"好的，我正在为你收集最新信息，这需要约 20 秒..."

# 2. 后台执行
async_task = intelligence_tool.execute({"action": "briefing"})

# 3. 完成后推送
"收集完成！以下是今天最值得关注的信息：..."
```

---

## 📊 功能对比

| 特性 | 定时推送 | 手动查询 |
|------|---------|---------|
| **触发方式** | 自动（08:00） | 用户主动询问 |
| **数据源** | 30+ RSS 源 | 同左 |
| **筛选逻辑** | LLM + 用户兴趣 | 同左 |
| **推送方式** | Notion（LOW 优先级） | 对话中直接返回 |
| **响应时间** | 定时执行 | 10-30 秒 |
| **当前状态** | ✅ 正常工作 | ❌ 有 BUG（action 名称错误） |

---

## 🎯 用户使用指南

### 方式 1: 等待定时推送（推荐）
- **时间**: 每天早上 08:00
- **位置**: Notion Database（intelligence 分类）
- **内容**: 1-3 条最相关信息 + 导师口吻点评

### 方式 2: 主动询问（修复后可用）
**正确的询问方式**:
```
"帮我看看今天有什么值得关注的信息"
"收集一下最新的 AI 研究进展"
"今天有什么新闻吗？"
```

**AI 会**:
1. 识别意图
2. 调用 intelligence 工具
3. 等待 10-30 秒收集和筛选
4. 直接在对话中返回结果

**不需要**:
- ❌ 不需要说"请汇报"
- ❌ 不需要等待后再次询问
- ❌ 不会异步执行（除非我们改进）

---

## 🔍 技术细节

### 数据源（30+ RSS 订阅）

**学术研究** (5 个):
- arXiv (Inverse Problems, ML, CV)
- Nature, Science

**技术开发** (6 个):
- GitHub Trending
- Hacker News
- MIT Tech Review
- TechCrunch

**新闻资讯** (5 个):
- BBC (Tech/Science)
- The Guardian
- Reuters, NYT

**社交媒体** (7 个):
- Twitter (AI 研究者)
- Reddit (ML/Python)

**专业博客** (4 个):
- Google AI Blog
- OpenAI Blog
- DeepMind
- Distill.pub

### LLM 筛选逻辑

```python
# 1. 拉取所有源（取前 30 条）
all_items = fetch_rss_feeds()

# 2. 获取用户兴趣
user_interests = memory_tool.search("用户当前正在学习和关注的领域")

# 3. LLM 筛选
prompt = INTELLIGENCE_FILTER_PROMPT.format(
    feed_count=len(all_items),
    feeds_content=feeds_text,
    user_interests=user_interests
)

# 4. 返回 1-3 条最相关信息
result = call_claude_api(prompt)
```

### 推送优先级

```python
NotifyPriority.LOW  # 仅推送到 Notion，不打扰用户
```

---

## 🚀 改进建议

### 短期（立即修复）
1. ✅ 修复 Web Chat 中的 action 名称
2. ✅ 更新工具说明文档
3. ✅ 添加错误处理（RSS 源失败时的降级）

### 中期（1-2 周）
1. 🔄 改为异步执行（立即回复 + 后台收集）
2. 📊 添加进度提示（"正在收集... 20%"）
3. 🎯 支持指定领域查询（"收集 AI 相关的信息"）

### 长期（1-2 月）
1. 🤖 智能推送时间（根据用户习惯调整）
2. 📈 情报质量评分（用户反馈）
3. 🔍 深度分析模式（不只是标题，还有全文摘要）
4. 💾 情报历史归档和搜索

---

## 📝 总结

### 当前状态
- ✅ **定时推送**: 完全正常，每天 08:00 自动执行
- ❌ **手动查询**: 有 BUG，action 名称错误导致无法使用
- ✅ **响应方式**: 同步执行，立即返回结果（不需要再次询问）

### 关键发现
1. **不是异步的**: 用户询问后会等待 10-30 秒，然后直接看到结果
2. **action 名称错误**: 应该是 `briefing` 而不是 `fetch_latest`
3. **推送优先级低**: 仅推送到 Notion，不会打扰用户

### 立即行动
修复 `web_chat.py` 中的 action 名称，让手动查询功能可用。

---

**报告生成时间**: 2026-03-11  
**分析者**: AI Assistant  
**状态**: 待修复
