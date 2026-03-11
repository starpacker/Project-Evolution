# Evolution v0.1.0 — 技术报告

> **版本**: 0.1.0  
> **最后更新**: 2026-03-11  
> **作者**: Evolution Team  
> **LLM 后端**: `cds/Claude-4.6-opus` via OpenAI-compatible Gateway  
> **部署状态**: ✅ 已部署运行  
> **Web Chat**: http://10.128.250.187:5000  
> **许可**: 内部使用  

---

## 目录

1. [项目概述](#1-项目概述)
2. [系统架构](#2-系统架构)
3. [五大角色详解](#3-五大角色详解)
4. [核心模块实现详解](#4-核心模块实现详解)
5. [数据库 Schema](#5-数据库-schema)
6. [数据流图](#6-数据流图)
7. [安全设计](#7-安全设计)
8. [通知路由系统](#8-通知路由系统)
9. [测试体系](#9-测试体系)
10. [代码统计与项目结构](#10-代码统计与项目结构)
11. [部署指南](#11-部署指南)
12. [未来演进](#12-未来演进)
13. [附录](#13-附录)

---

## 1. 项目概述

### 1.1 一句话定义

**Evolution 是一个 7×24 运行的私人 AI Agent，同时扮演用户的秘书、导师、训练师、情感助手和情报收集者——一个真正"认识你"的数字伙伴。**

### 1.2 它解决什么问题？

现代知识工作者面临一组系统性困境：

| 困境 | 描述 |
|------|------|
| **目标遗忘** | 定下的目标在两周后就被日常琐事淹没 |
| **情绪失控** | 深夜陷入情绪漩涡，做出不理性的决定 |
| **精力泄漏** | 大量精力浪费在不值得的事情上，事后才意识到 |
| **缺乏诤友** | 没有一个足够了解你、又足够诚实的人，在关键时刻拉你一把 |
| **知识碎片化** | 读了很多书、学了很多东西，但没有系统地内化成思维工具 |

Evolution 就是来填这个空缺的。它不是一个聊天机器人，它是一个**有记忆、有判断、会主动行动**的系统。

### 1.3 与普通 ChatGPT 的区别

| 维度 | 普通 ChatGPT | Evolution |
|------|-------------|-----------|
| **记忆** | 每次对话从零开始（或有限的记忆） | 记住你说过的每一句话、每一个人、每一个承诺 |
| **主动性** | 你问它才答 | 主动找你：提醒日程、推送情报、发现异常时干预 |
| **人格** | 通用助手，讨好型 | 克制、诚实、不给虚假安慰，像一个真正的导师 |
| **连续性** | 无法追踪成长轨迹 | 每天反思、每周报告，形成可回溯的个人成长档案 |
| **多通道** | 只在网页里 | Web + 邮件推送 + Notion 归档 + Telegram 即时通知 |

### 1.4 技术栈一览

| 组件 | 技术选型 | 说明 |
|------|---------|------|
| Agent 框架 | CowAgent | 开源框架，负责通道接入、插件管理、定时任务 |
| LLM 大脑 | Claude (cds/Claude-4.6-opus) | 所有对话和分析的唯一大脑，通过 OpenAI-compatible Gateway 调用 |
| 记忆层 | Mem0 (向量 + 图谱) | 每轮对话自动提取事实存入向量数据库(Qdrant) + 知识图谱(Kuzu) |
| 结构化存储 | SQLite (WAL 模式) | 日程、技能树、人物档案、训练记录、反思报告等 7 张表 |
| 情报源 | RSSHub (Docker) | 聚合 arXiv、GitHub Trending、Hacker News 等信息源 |
| 通知通道 | Email / Telegram / Notion | 基于优先级的智能路由 |
| Python SDK | openai >= 1.30 | 通过 OpenAI-compatible 接口调用 LLM (非原生 anthropic SDK) |

### 1.5 系统运行环境

- **服务器**: server3090 (10.128.250.187)
- **Docker 容器**: 仅 RSSHub 需要 Docker，其余全部本地运行
- **Python**: 3.9+ (当前使用 Anaconda base 环境)
- **外部依赖**: 最小化 —— 核心依赖仅 5 个包 (`openai`, `defusedxml`, `httpx`, `apscheduler`, `markdown`)
- **Web Chat**: Flask + Flask-CORS，运行在 0.0.0.0:5000

### 1.6 已验证的服务

| 服务 | 状态 | 配置信息 |
|------|------|---------|
| **SMTP 邮件** | ✅ 已验证 | smtp.qq.com:465, 测试邮件已发送 |
| **Notion API** | ✅ 已验证 | 用户: starspin, 数据库: Docs |
| **LLM API** | ✅ 已验证 | cds/Claude-4.6-opus, 响应正常 |
| **Web Chat** | ✅ 运行中 | http://10.128.250.187:5000 |

---

## 2. 系统架构

### 2.1 整体架构图

```
用户 ←→ Web/Telegram ←→ CowAgent(底座) ←→ Claude(大脑)
                              │
                    ┌─────────┼─────────┐
                    │         │         │
                  Mem0      SQLite    RSSHub
               (记忆层)   (结构化)   (情报源)
              向量+图谱    7张表

                    │         │         │
                    └─────────┼─────────┘
                              │
                      通知路由器 (NotificationRouter)
                              │
                    ┌─────────┼─────────┐
                    │         │         │
                  Email    Telegram   Notion
```

### 2.2 模块分层

Evolution 采用清晰的分层架构：

```
┌────────────────────────────────────────────────────┐
│                CowAgent 接入层                       │
│   (ToolManager / SchedulerTool / Web/Telegram)      │
├────────────────────────────────────────────────────┤
│              Bridge 集成层 (bridge.py)               │
│   工具注册 / 定时任务 / System Prompt / 对话日志      │
├────────────────────────────────────────────────────┤
│              4 个自定义工具 (Tool Layer)              │
│  ┌──────────┬──────────┬───────────┬─────────────┐ │
│  │ Memory   │ DB Tool  │Reflection │Intelligence │ │
│  │ Tool     │          │ Tool      │ Tool        │ │
│  └──────────┴──────────┴───────────┴─────────────┘ │
├────────────────────────────────────────────────────┤
│              基础设施层                              │
│  ┌──────────┬──────────┬───────────┬─────────────┐ │
│  │ Mem0     │ SQLite   │ LLM API  │ Notification│ │
│  │ (向量+   │ (WAL,    │ (OpenAI  │ Router      │ │
│  │  图谱)   │  线程安全)│  兼容)   │ (3通道)     │ │
│  └──────────┴──────────┴───────────┴─────────────┘ │
└────────────────────────────────────────────────────┘
```

### 2.3 核心设计决策

#### 决策 1: 统一人格，4 工具（而非 5 角色工具）

**问题**: 5 个角色是否应该实现为 5 个独立的工具？

**答案**: 不。5 个角色是**人格层面**的，不是**工具层面**的。

- 5 个角色通过**统一的 System Prompt** 注入 LLM，LLM 根据上下文自然切换角色
- 4 个工具是**原子操作**：记忆(Mem0)、数据库(SQLite)、反思(LLM+规则)、情报(RSS+LLM)
- 角色不需要工具来"表演"，工具也不需要角色来"使用"

这个设计让系统更简洁：LLM 自主决定当前应该扮演哪个角色，同时调用所需的工具。

#### 决策 2: Mem0 单系统（砍掉 Graphiti）

**问题**: 是否需要 Mem0 + Graphiti 双记忆系统？

**答案**: Mem0 v1.0.5 原生内置了 Graph Memory，一个组件就够了。

- **向量记忆**: 语义搜索，返回相关记忆片段
- **图谱记忆**: 自动提取实体和关系，支持关系查询
- `memory.search()` 同时返回 `results`（向量命中）和 `relations`（图谱关联）
- 图后端选用 **Kuzu**（嵌入式，零配置，无需额外 Docker）

#### 决策 3: OpenAI-compatible Gateway（而非原生 Anthropic SDK）

**问题**: 为什么不用 `anthropic` Python SDK 直接调用 Claude？

**答案**: 用户的 API 通过 OpenAI-compatible 网关（`https://ai-gateway-internal.dp.tech/v1`）暴露。

- 使用 `openai` Python SDK，`base_url` 指向网关
- 模型名称 `cds/Claude-4.6-opus` 由网关映射到实际的 Claude 模型
- 这意味着未来可以无缝切换到其他 LLM，只需修改 `LLM_MODEL` 配置

#### 决策 4: CowAgent BaseTool 兼容层

**问题**: 如何在不安装 CowAgent 的情况下开发和测试？

**答案**: `evolution/tools/base.py` 提供了最小兼容实现。

```python
# 尝试导入 CowAgent 的真正 BaseTool
try:
    from agent.tools.base_tool import BaseTool as CowBaseTool
    BaseTool = CowBaseTool  # 使用 CowAgent 原版
except ImportError:
    COWAGENT_AVAILABLE = False  # 使用本地最小实现
```

- 在 CowAgent 环境中，自动使用真正的 `BaseTool`
- 独立运行/测试时，使用本地兼容实现
- 两种模式下工具的接口完全一致

---

## 3. 五大角色详解

### 3.1 角色总览

五个角色**共享同一个人格和同一套记忆**，通过统一的 System Prompt 注入 LLM。LLM 根据对话上下文自然选择当前应该扮演的角色。

| 角色 | 触发条件 | 核心工具 | 输出目标 |
|------|---------|---------|---------|
| 🗓️ 秘书 | 用户说"提醒我"、"记住"、"X天后" | `evolution_db` | 日程创建、查询、提醒 |
| 🧠 导师 | 用户迷茫、自欺、请求反馈 | `evolution_memory` + `evolution_reflection` | 苏格拉底式提问、规律总结、每日反思 |
| 🏋️ 训练师 | 用户请求训练 | `evolution_db` | 7 种训练模态、技能评估、进度追踪 |
| 💑 情感助手 | 用户谈及感情或提到人物 | `evolution_memory` + `evolution_db` | 人物档案、精力监控、关系预警 |
| 📡 情报收集者 | 定时任务(08:00) | `evolution_intelligence` | 情报筛选、导师口吻推送 |

### 3.2 R1: 🗓️ 秘书

**职责**: 记住用户的所有待办、截止日期、重要日子，到时间主动提醒。

**工作流程**:
1. 用户提到日程意图 → LLM 通过 `SCHEDULE_DETECTION_PROMPT` 提取日程信息
2. 调用 `evolution_db` 的 `add_schedule` action 创建日程
3. 日程到期时由定时任务触发提醒
4. 提醒语气克制："论文初稿还有3天截止，你昨天说今天要写第三章。"

**日程数据模型**:
- `content`: 任务描述
- `due_date`: 截止时间
- `remind_at`: 提醒时间
- `priority`: high / medium / low
- `category`: professional / physical / personal / relationship
- `status`: pending / done / overdue / cancelled

### 3.3 R2: 🧠 导师

**职责**: 在用户迷茫时给方向，在用户自欺时戳破，在用户崩溃时兜底。每天 23:00 自动回顾用户的一天，生成反思报告。

**人格特征**:
- 克制、诚实、不给虚假安慰。只提供基于事实的规律总结
- 面对软弱，使用苏格拉底式提问让用户自己看到逻辑的荒谬
- 真正的强大包容脆弱。在用户真正崩溃时给予温度，但不给退路
- 如果发现用户的话与过去的承诺矛盾，直接指出

**每日反思流程** (23:00 定时触发):

```
收集今日对话 → 检索 Mem0 记忆 → LLM 生成反思 → 解析 JSON → 存储 + 推送
     ↓              ↓                ↓              ↓          ↓
  SQLite        向量+图谱      DAILY_REFLECTION   情绪检测    Email/TG
conversation_logs  search()       PROMPT         异常检测    Notion
```

**反思报告输出结构** (JSON):
- `emotional_state`: 主要情绪、强度(0-1)、触发事件、趋势
- `core_goal_progress`: 专业/身体/心智三维度进展评估
- `relationship_monitor`: 关系精力占比、提及人物、健康度
- `profile_updates`: 需要更新的用户档案字段
- `anomalies`: 异常检测（精力泄漏 / 情绪异常 / 目标偏离 / 行为模式异常），含严重度和干预建议
- `tomorrow_suggestion`: 明天最应该做的一件事
- `evening_message`: 晚间寄语

### 3.4 R3: 🏋️ 训练师

**职责**: 通过多种训练模态系统性地锻炼用户的思维能力。

**7 种训练模态**:

| 模态 | 名称 | 说明 | 示例 |
|------|------|------|------|
| T1 | 概念辨析 | 区分容易混淆的概念 | "自信和自负的本质区别是什么？" |
| T2 | 立场辩论 | 对某一观点正反辩论 | "内卷是不是一个伪命题？" |
| T3 | 世界模型分析 | 分析某个现象的底层模型 | "为什么优秀的人容易拖延？" |
| T4 | 苏格拉底式自我审问 | 通过提问暴露盲点 | "你说你想变强，但你的行动说了什么？" |
| T5 | 思维实验 | 跨领域类比思考 | "热力学第二定律在人际关系中的对应物是什么？" |
| T6 | 快速测试 | 知识点快速问答 | "什么是锚定效应？举个你生活中的例子。" |
| T7 | 跨域迁移 | 将一个领域的模型应用到另一个领域 | "用博弈论分析你和导师的关系。" |

**训练流程**:
1. 用户请求训练 → LLM 查询技能树 (`evolution_db` → `list_skills`)
2. 基于当前等级和薄弱点选择合适的训练模态和难度
3. 训练完成后 → 记录训练日志 (`add_training`) + 更新技能等级 (`update_skill`)
4. 循序渐进，从用户的薄弱点切入

**技能分类**: `professional` / `thinking` / `language` / `physical` / `emotional`

### 3.5 R4: 💑 情感助手

**职责**: 自动追踪用户提到的每个人，分析精力分配，在用户过度投入某段关系时发出预警。

**核心原则**:
- **不做恋爱顾问，做心智教练**
- 关注关系中的权力动态、精力分配、自我成长
- 如果检测到用户 >40% 精力消耗在某段关系上，主动预警

**工作流程**:
1. 用户提到人物 → LLM 通过 `PERSON_EXTRACTION_PROMPT` 提取人物信息
2. 调用 `evolution_memory` 搜索该人物的历史记忆
3. 调用 `evolution_db` 的 `upsert_person` 更新人物档案
4. 每日反思中分析 `relationship_monitor`，计算精力占比

**人物档案数据模型**:
- `name`: 人名 (UNIQUE)
- `relationship`: 关系类型
- `likes` / `dislikes`: 喜好/厌恶
- `important_dates`: 重要日期
- `mention_count`: 提及次数 (自动递增)
- `last_mentioned`: 最后提及时间
- `interaction_frequency`: 互动频率 (low/medium/high)
- `emotional_impact`: 情感影响 (positive/neutral/negative)

### 3.6 R5: 📡 情报收集者

**职责**: 每天早上扫描用户关注领域的最新动态，筛选出真正值得看的 1-3 条，用导师口吻推送。

**默认订阅源** (30个精选源):

| 分类 | 源数量 | 示例 |
|------|--------|------|
| 学术研究 (academic) | 5 | arXiv (ML/CV/Inverse Problems), Nature, Science |
| 技术开发 (tech) | 6 | GitHub Trending, Hacker News, MIT Tech Review, TechCrunch |
| 新闻资讯 (news) | 5 | BBC (Tech/Science), The Guardian, Reuters, NYT |
| 社交媒体 (social) | 7 | Twitter (AI研究者/OpenAI/Google AI), Reddit (ML/Python) |
| 专业博客 (blog) | 4 | Google AI Blog, OpenAI Blog, DeepMind, Distill.pub |

**完整列表**: 见 `evolution/config/settings.py` 中的 `RSS_FEEDS` 配置

**情报推送流程** (08:00 定时触发):

```
拉取 RSS → 检索用户兴趣(Mem0) → LLM 筛选 + 提炼 → 推送通知
                                        ↓
                          INTELLIGENCE_FILTER_PROMPT
                          筛选 1-3 条最相关信息
                          用导师口吻撰写摘要
```

### 3.7 语言规则

所有角色共享统一的语言规则：

**禁用词汇**: 「作为AI」「首先其次最后」「祝你好运」「做自己就好」「加油」「我理解你的感受」

**推荐风格**: 短句、隐喻、反问、偶尔的沉默（...）、黑色幽默

**引用来源**: 只引用经过时间验证的智慧——哲学、历史、物理定律、人性规律

**长度控制**:
| 场景 | 长度限制 |
|------|---------|
| 日常闲聊 | 2-4 句话，≤100 字 |
| 心智引导 | 5-8 句话，≤200 字 |
| 深度复盘 | 结构化分析，≤400 字 |
| 紧急干预 | 先一句承认感受，再给行动指令 |

---

## 4. 核心模块实现详解

本章逐一拆解 Evolution 的每个源码模块，解释其实现逻辑、关键设计和注意事项。

### 4.1 配置中心 (`evolution/config/settings.py` — 160 行)

所有配置集中在一个文件中，通过环境变量覆盖，支持零配置启动（所有值都有默认值）。

**配置分区**:

| 分区 | 环境变量前缀 | 说明 |
|------|------------|------|
| 路径配置 | `EVOLUTION_ROOT` | 项目根目录、数据目录、数据库文件路径 |
| LLM 配置 | `LLM_API_KEY`, `LLM_BASE_URL`, `LLM_MODEL` | OpenAI-compatible Gateway 连接参数 |
| Mem0 配置 | `EMBEDDING_*`, `OPENAI_API_KEY` | 向量存储(Qdrant) + 图谱存储(Kuzu) |
| 通知配置 | `EMAIL_*`, `TG_*`, `NOTION_*` | 三通道推送参数 |
| RSS 配置 | `RSSHUB_URL` | RSSHub 服务地址 |
| 定时任务 | — | Cron 表达式：23:00 反思、08:00 情报、周日 20:00 周报 |

**关键实现细节**:

```python
# Mem0 配置结构 — 同时启用向量搜索和图谱搜索
MEM0_CONFIG = {
    "llm": {"provider": "openai", "config": {"model": LLM_MODEL, "openai_base_url": LLM_BASE_URL}},
    "embedder": {"provider": EMBEDDING_PROVIDER, "config": {"model": EMBEDDING_MODEL}},
    "vector_store": {"provider": "qdrant", "config": {"path": QDRANT_PATH}},
    "graph_store": {"provider": "kuzu", "config": {"db_path": KUZU_DB_PATH}},
}
```

- Mem0 的 LLM provider 设为 `"openai"`，通过 `openai_base_url` 指向网关，实现 Claude 调用
- 向量存储使用 Qdrant 本地模式（文件存储），无需启动独立服务
- 图谱存储使用 Kuzu 嵌入式数据库，零配置

### 4.2 Prompt 模板库 (`evolution/config/prompts.py` — 244 行)

所有 Prompt 集中管理，便于迭代优化。

**6 个核心 Prompt**:

| Prompt 名称 | 用途 | 输入变量 | 输出格式 |
|-------------|------|---------|---------|
| `SYSTEM_PROMPT` | 五角色统一人格注入 | — | 自然语言 |
| `DAILY_REFLECTION_PROMPT` | 每日 23:00 反思生成 | `today_conversations`, `existing_memories`, `graph_relations`, `date` | JSON |
| `INTELLIGENCE_FILTER_PROMPT` | 情报筛选与提炼 | `feed_count`, `feeds_content`, `user_interests` | JSON |
| `WEEKLY_REPORT_PROMPT` | 周度成长报告 | `weekly_reflections`, `user_profile` | Markdown 表格 |
| `SCHEDULE_DETECTION_PROMPT` | 日程意图检测 | `message`, `current_time` | JSON |
| `PERSON_EXTRACTION_PROMPT` | 人物信息提取 | `user_message`, `assistant_message` | JSON |

**设计原则**:
- 所有需要结构化输出的 Prompt 都要求严格 JSON 格式
- 每个 Prompt 都包含详细的输出字段说明和示例
- `SYSTEM_PROMPT` 中明确禁用了"讨好型"话术，强制导师风格

### 4.3 数据库管理器 (`evolution/db/manager.py` — 516 行)

数据库层是整个系统的结构化数据骨架，管理 7 张表。

**核心设计**: 线程安全的单例模式

```python
class DatabaseManager:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, db_path=None):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance
```

**线程安全策略**:
- **单例锁**: `threading.Lock()` 保证全局唯一实例
- **线程局部连接**: `threading.local()` 为每个线程维护独立的 SQLite 连接
- **WAL 模式**: `PRAGMA journal_mode=WAL` — 允许并发读写
- **自动清理**: `atexit.register(self.close)` 确保进程退出时关闭连接
- **测试支持**: `reset_singleton()` 方法允许测试间重置状态

**连接管理** — Context Manager 模式:

```python
@contextmanager
def _get_conn(self):
    if not hasattr(self._local, "conn") or self._local.conn is None:
        self._local.conn = sqlite3.connect(self.db_path)
        self._local.conn.row_factory = sqlite3.Row  # 字典式访问
        self._local.conn.execute("PRAGMA journal_mode=WAL")
        self._local.conn.execute("PRAGMA foreign_keys=ON")
    try:
        yield self._local.conn
        self._local.conn.commit()
    except Exception:
        self._local.conn.rollback()
        raise
```

**SQL 注入防护** — 列名白名单:

```python
_PERSON_COLUMNS = frozenset({
    "relationship", "likes", "dislikes", "important_dates",
    "interaction_frequency", "emotional_impact", "notes",
})

def upsert_person(self, name, **kwargs):
    for k, v in kwargs.items():
        if v is not None and k in self._PERSON_COLUMNS:  # 仅允许白名单列名
            set_clauses.append(f"{k} = ?")  # 值用参数化查询
```

**提供的 CRUD 方法** (按表分组):

| 表 | 方法 |
|----|------|
| `schedule` | `add_schedule`, `get_schedule_by_date`, `get_pending_schedules`, `get_overdue_schedules`, `complete_schedule`, `cancel_schedule`, `delete_schedule` |
| `skills` | `add_skill`, `get_skill`, `list_skills`, `update_skill_level`, `get_stale_skills` |
| `persons` | `upsert_person`, `get_person`, `list_persons`, `get_top_mentioned_persons` |
| `training_logs` | `add_training_log`, `get_training_logs` |
| `mental_models` | `add_mental_model`, `list_mental_models` |
| `daily_reflections` | `save_reflection`, `get_reflection`, `get_reflections_range` |
| `conversation_logs` | `log_conversation`, `get_conversations_by_date`, `get_conversation_count_by_date` |
| (跨表) | `get_stats` |

### 4.4 BaseTool 兼容层 (`evolution/tools/base.py` — 83 行)

这是一个精巧的适配器模式实现：

```python
# 本地最小实现 (在文件顶部定义)
class BaseTool:
    name: str = "base_tool"
    params: dict = {}
    def execute(self, params: dict) -> ToolResult: raise NotImplementedError

# 文件末尾：尝试替换为 CowAgent 原版
try:
    from agent.tools.base_tool import BaseTool as CowBaseTool
    BaseTool = CowBaseTool  # 覆盖本地实现
    COWAGENT_AVAILABLE = True
except ImportError:
    COWAGENT_AVAILABLE = False  # 保持本地实现
```

**CowAgent BaseTool 接口契约**:
- `name`: 工具名称（字符串）
- `description`: 工具描述（供 LLM 理解）
- `params`: JSON Schema 格式的参数定义
- `execute(params) → ToolResult`: 执行入口
- `ToolResult.success(result)` / `ToolResult.fail(error)`: 结果封装
- `ToolStage.PRE_PROCESS` / `POST_PROCESS`: 执行阶段标记

### 4.5 记忆工具 (`evolution/tools/memory_tool.py` — 208 行)

封装 Mem0，提供 3 个 action: `search` / `add` / `profile`。

**Mem0 延迟初始化与优雅降级**:

```python
def _init_memory(self):
    try:
        from mem0 import Memory
        self._memory = Memory.from_config(MEM0_CONFIG)  # 正式初始化
    except ImportError:
        self._memory = MockMemory()  # Mem0 未安装 → 降级到 Mock
    except Exception:
        self._memory = MockMemory()  # Mem0 初始化失败 → 降级到 Mock
```

**MockMemory 实现**: 当 Mem0 不可用时（如测试环境），自动降级为基于关键词的内存搜索：

```python
class MockMemory:
    def __init__(self):
        self._store: list = []

    def search(self, query, user_id=None, limit=10):
        results = [mem for mem in self._store if query.lower() in mem["memory"].lower()]
        return {"results": results[:limit], "relations": []}
```

**搜索结果格式**: 统一处理 Mem0 的两种返回格式（`dict` 带 `results`+`relations` 和纯 `list`），向上层屏蔽差异。

### 4.6 数据库工具 (`evolution/tools/db_tool.py` — 299 行)

封装 `DatabaseManager`，暴露 16 个 action 给 LLM 调用。

**路由机制** — 基于 action 名称的动态分发:

```python
def execute(self, params):
    action = params.get("action")
    handler = getattr(self, f"_handle_{action}", None)
    if handler:
        return handler(params)
    else:
        return ToolResult.fail(f"未知操作: {action}")
```

**16 个 Action**:

| 分组 | Action | 说明 |
|------|--------|------|
| 日程 | `add_schedule`, `list_schedule`, `complete_schedule`, `delete_schedule` | 完整 CRUD |
| 技能 | `add_skill`, `list_skills`, `update_skill`, `stale_skills` | 技能树管理 + 荒废检测 |
| 人物 | `upsert_person`, `get_person`, `list_persons` | 人物档案 |
| 训练 | `add_training`, `list_trainings` | 训练记录 |
| 模型 | `add_model`, `list_models` | 心智模型库 |
| 统计 | `stats` | 跨表汇总 |

**Rich 格式化输出**: 所有返回都使用 emoji 增强可读性：

```
📋 共 3 条日程:
  1. 🔴 [1] 提交论文 (截止: 2026-03-15)
  2. 🟡 [2] 买牛奶 (截止: 2026-03-11)
  3. 🟢 [3] 看书 (截止: 无截止时间)

🏋️ 共 2 项技能:
  [professional] Python: ██████░░░░ Lv.6/10 (上次: 2026-03-09)
  [thinking] 批判性思维: ███░░░░░░░ Lv.3/8 (上次: 从未训练)
```

### 4.7 反思工具 (`evolution/tools/reflection_tool.py` — 311 行)

每日反思引擎，是整个系统中最复杂的工具。

**每日反思 5 步流程**:

```
Step 1: self.db.get_conversations_by_date(target_date)
        → 收集今日所有对话记录

Step 2: self.memory_tool.execute({"action": "search", "query": "..."})
        → 从 Mem0 检索用户历史记忆和图谱关系

Step 3: call_claude_api(DAILY_REFLECTION_PROMPT.format(...))
        → LLM 生成结构化反思报告 (JSON)

Step 4: self.db.save_reflection(...)
        → 存入 SQLite; self.memory_tool.execute({"action": "add", ...})
        → 同时存入 Mem0 (向量+图谱)

Step 5: self._send_reflection_notification(...)
        → 通过 NotificationRouter 推送
        → 严重异常 (severity > 0.6) → CRITICAL 全通道推送
        → 普通反思 → NORMAL 推送
```

**JSON 解析容错**:

```python
try:
    report = json.loads(self._extract_json(report_json))
except json.JSONDecodeError:
    # LLM 输出非标准 JSON 时的兜底
    report = {
        "date": target_date,
        "emotional_state": {"primary_emotion": "unknown", "intensity": 0},
        "anomalies": [],
        "tomorrow_suggestion": "继续保持",
        "evening_message": report_json[:200],  # 用原始文本作为晚间寄语
    }
```

**LLM 调用双通道**:
1. 优先使用 CowAgent 注入的 `self.model`（Agent 环境）
2. 降级到直接调用 `call_claude_api()`（独立运行）

**周度报告**: 聚合 7 天反思数据 + 用户档案，通过 `WEEKLY_REPORT_PROMPT` 生成 Markdown 表格式周报。

### 4.8 情报工具 (`evolution/tools/intelligence_tool.py` — 301 行)

从 RSSHub 拉取订阅源，用 LLM 筛选与用户最相关的信息。

**RSS 解析** — 同时支持 RSS 2.0 和 Atom 格式:

```python
def _parse_rss(self, url, source_name):
    root = safe_xml_fromstring(resp.text)  # defusedxml (XXE 防护)

    # RSS 2.0
    for item in root.findall(".//item")[:10]:
        title = item.findtext("title", "")
        ...

    # Atom
    ns = {"atom": "http://www.w3.org/2005/Atom"}
    for entry in root.findall(".//atom:entry", ns)[:10]:
        title = entry.findtext("atom:title", "", ns)
        ...
```

**SSRF 防护** — URL 安全检查:

```python
@staticmethod
def _is_safe_url(url: str) -> bool:
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        return False  # 仅允许 http/https
    hostname = parsed.hostname
    try:
        addr = ipaddress.ip_address(hostname)
        if addr.is_private or addr.is_reserved or addr.is_loopback:
            return False  # 阻止内网地址
    except ValueError:
        if hostname.lower() in ("localhost",) or hostname.endswith(".local"):
            return False  # 阻止常见内网域名
    return True
```

**情报推送流程**:
1. 并行拉取所有 RSS 源（最多取每源 10 条）
2. 从 Mem0 检索用户当前兴趣和关注领域
3. LLM 筛选 1-3 条最相关信息，用导师口吻撰写摘要
4. 通过 NotificationRouter 以 `LOW` 优先级推送（仅 Notion）

### 4.9 通知路由器 (`evolution/notification/router.py` — 259 行)

详见 [第 8 章](#8-通知路由系统)。

### 4.10 LLM 工具函数 (`evolution/utils/llm.py` — 80 行)

所有 LLM 调用的唯一出口，避免代码重复。

**模块级客户端缓存**:

```python
_client = None  # 模块级缓存

def _get_client():
    global _client
    if _client is None:
        from openai import OpenAI
        _client = OpenAI(api_key=LLM_API_KEY, base_url=LLM_BASE_URL)
    return _client
```

**提供的函数**:
- `call_claude_api(prompt, max_tokens, system)`: 调用 LLM，返回文本或 `None`
- `extract_json(text)`: 从 LLM 输出中提取 JSON（去除 markdown 围栏和前后缀）
- `reset_client()`: 重置缓存客户端（测试用）

### 4.11 Web Chat 服务器 (`evolution/chat/web_chat.py` — 260 行)

轻量级 Web 聊天界面，基于 Flask 提供浏览器访问。

**架构设计**:
```
浏览器 ←→ Flask API ←→ LLM (Claude) ←→ 4 个工具
   │         │                            │
   │         └─→ 对话历史 (内存)          └─→ Mem0 / SQLite
   │         └─→ 对话日志 (SQLite)
   └─→ HTML/CSS/JS (响应式设计)
```

**核心端点**:

| 端点 | 方法 | 功能 |
|------|------|------|
| `/` | GET | 返回聊天界面 HTML |
| `/api/chat` | POST | 处理用户消息，返回 AI 回复 |
| `/api/history` | GET | 获取最近 20 条对话历史 |
| `/api/clear` | POST | 清空对话历史 |
| `/health` | GET | 健康检查 |

**工具调用格式**: LLM 可以在回复中使用特殊标记调用工具：
```
[TOOL:memory]search: 上周的计划[/TOOL]
[TOOL:db]query: SELECT * FROM schedule[/TOOL]
[TOOL:reflection]generate_daily[/TOOL]
[TOOL:intelligence]fetch_latest[/TOOL]
```

**对话流程**:
1. 用户发送消息 → 添加到 `conversation_history` (内存)
2. 构建上下文 (最近 10 轮对话) → 调用 `call_claude_api()`
3. 解析 LLM 回复中的工具调用标记 → 执行工具 → 合并结果
4. 返回最终回复 → 保存到 `conversation_logs` 表 (SQLite)
5. 限制历史长度 (最多 50 条)

**前端特性**:
- 响应式设计 (适配手机和电脑)
- 渐变色主题 (紫色系)
- 消息动画效果
- 自动滚动到最新消息
- 支持 Markdown 渲染 (未来可扩展)

**部署配置**:
- 监听地址: `0.0.0.0:5000` (允许局域网访问)
- CORS 启用 (允许跨域请求)
- 生产环境建议使用 Gunicorn + Nginx

### 4.12 CowAgent 桥接器 (`evolution/utils/bridge.py` — 142 行)

将 Evolution 的 4 个工具注册到 CowAgent 的 ToolManager 中。

**提供的函数**:

| 函数 | 说明 |
|------|------|
| `get_evolution_tools()` | 返回 4 个工具实例列表 |
| `register_with_cowagent()` | 在 CowAgent 的 ToolManager 中注册工具类 |
| `setup_scheduled_tasks()` | 创建 3 个定时任务 (反思/情报/周报) |
| `get_system_prompt()` | 返回五角色统一 System Prompt |
| `log_conversation(role, content)` | 记录对话到 SQLite |

**定时任务创建** — 使用 CowAgent 的 `SchedulerTool`:

```python
tasks = [
    {
        "action": "create",
        "name": "evolution_daily_reflection",
        "ai_task": "你是Evolution导师。请使用 evolution_reflection 工具（action='daily'）生成今日反思报告。",
        "schedule_type": "cron",
        "schedule_value": "0 23 * * *",  # 每天 23:00
    },
    {
        "name": "evolution_morning_briefing",
        "ai_task": "你是Evolution情报收集者。请使用 evolution_intelligence 工具（action='briefing'）获取今日情报。",
        "schedule_value": "0 8 * * *",  # 每天 08:00
    },
    {
        "name": "evolution_weekly_report",
        "ai_task": "你是Evolution导师。请使用 evolution_reflection 工具（action='weekly'）生成周度报告。",
        "schedule_value": "0 20 * * 0",  # 每周日 20:00
    },
]
```

注意：定时任务的 `ai_task` 是自然语言指令，由 CowAgent 的 LLM 执行——这意味着定时任务本身也是 LLM 驱动的，可以灵活组合多个工具。

---

## 5. 数据库 Schema

### 5.1 ER 图概览

```
┌──────────────┐     ┌───────────────┐
│   schedule   │     │    skills     │
│──────────────│     │───────────────│
│ id (PK)      │     │ id (PK)       │
│ content      │     │ name (UNIQUE) │
│ due_date     │     │ category      │
│ remind_at    │     │ level (1-10)  │
│ priority     │     │ xp            │
│ status       │     │ target_level  │
│ category     │     │ weakness      │
│ context      │     │ preferred_    │
│ created_at   │     │   modality    │
│ updated_at   │     │ last_trained  │
└──────────────┘     └───────┬───────┘
                             │ 1:N
                     ┌───────┴───────┐
                     │ training_logs │
                     │───────────────│
                     │ id (PK)       │
                     │ skill_id (FK) │
                     │ modality      │
                     │ topic         │
                     │ rating        │
                     │ insight       │
                     │ trained_at    │
                     └───────────────┘

┌──────────────┐     ┌─────────────────┐     ┌──────────────────┐
│   persons    │     │ mental_models   │     │ daily_reflections │
│──────────────│     │─────────────────│     │──────────────────│
│ id (PK)      │     │ id (PK)         │     │ id (PK)          │
│ name (UNIQ)  │     │ name (UNIQUE)   │     │ date (UNIQUE)    │
│ relationship │     │ source_domain   │     │ report_json      │
│ likes        │     │ description     │     │ primary_emotion  │
│ dislikes     │     │ applications    │     │ emotional_       │
│ important_   │     │ learned_date    │     │   intensity      │
│   dates      │     └─────────────────┘     │ tomorrow_        │
│ mention_count│                              │   suggestion     │
│ last_        │     ┌──────────────────┐     │ evening_message  │
│   mentioned  │     │conversation_logs │     │ created_at       │
│ interaction_ │     │──────────────────│     └──────────────────┘
│   frequency  │     │ id (PK)          │
│ emotional_   │     │ date             │
│   impact     │     │ timestamp        │
│ notes        │     │ role             │
└──────────────┘     │ content          │
                     └──────────────────┘
```

### 5.2 各表 DDL 与约束

#### `schedule` — 日程表

```sql
CREATE TABLE schedule (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    content TEXT NOT NULL,
    due_date TEXT,
    remind_at TEXT,
    priority TEXT DEFAULT 'medium' CHECK(priority IN ('high','medium','low')),
    status TEXT DEFAULT 'pending' CHECK(status IN ('pending','done','overdue','cancelled')),
    category TEXT CHECK(category IN ('professional','physical','personal','relationship')),
    context TEXT,
    created_at TEXT DEFAULT (datetime('now','localtime')),
    updated_at TEXT DEFAULT (datetime('now','localtime'))
);
CREATE INDEX idx_schedule_status ON schedule(status);
CREATE INDEX idx_schedule_due ON schedule(due_date);
```

#### `skills` — 技能树

```sql
CREATE TABLE skills (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    category TEXT NOT NULL CHECK(category IN ('professional','thinking','language','physical','emotional')),
    level INTEGER DEFAULT 1 CHECK(level BETWEEN 1 AND 10),
    xp INTEGER DEFAULT 0,
    last_trained TEXT,
    weakness TEXT,
    target_level INTEGER DEFAULT 5,
    preferred_modality TEXT,
    created_at TEXT DEFAULT (datetime('now','localtime'))
);
```

#### `persons` — 人物档案

```sql
CREATE TABLE persons (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    relationship TEXT,
    likes TEXT,
    dislikes TEXT,
    important_dates TEXT,
    last_mentioned TEXT,
    mention_count INTEGER DEFAULT 0,
    interaction_frequency TEXT DEFAULT 'low',
    emotional_impact TEXT DEFAULT 'neutral',
    notes TEXT,
    created_at TEXT DEFAULT (datetime('now','localtime')),
    updated_at TEXT DEFAULT (datetime('now','localtime'))
);
CREATE INDEX idx_persons_name ON persons(name);
```

#### `training_logs` — 训练记录

```sql
CREATE TABLE training_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    skill_id INTEGER,
    modality TEXT CHECK(modality IN ('T1','T2','T3','T4','T5','T6','T7')),
    topic TEXT,
    rating TEXT,
    insight TEXT,
    trained_at TEXT DEFAULT (datetime('now','localtime')),
    FOREIGN KEY (skill_id) REFERENCES skills(id)
);
```

#### `mental_models` — 心智模型

```sql
CREATE TABLE mental_models (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    source_domain TEXT,
    description TEXT,
    applications TEXT,  -- JSON 数组
    learned_date TEXT DEFAULT (datetime('now','localtime'))
);
```

#### `daily_reflections` — 每日反思

```sql
CREATE TABLE daily_reflections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL UNIQUE,
    report_json TEXT NOT NULL,  -- 完整反思报告 JSON
    primary_emotion TEXT,
    emotional_intensity REAL,
    tomorrow_suggestion TEXT,
    evening_message TEXT,
    created_at TEXT DEFAULT (datetime('now','localtime'))
);
CREATE INDEX idx_reflections_date ON daily_reflections(date);
```

#### `conversation_logs` — 对话日志

```sql
CREATE TABLE conversation_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('user','assistant','system')),
    content TEXT NOT NULL
);
CREATE INDEX idx_conv_date ON conversation_logs(date);
```

### 5.3 PRAGMA 设置

```sql
PRAGMA journal_mode=WAL;   -- Write-Ahead Logging: 允许并发读写
PRAGMA foreign_keys=ON;    -- 启用外键约束 (training_logs → skills)
```

---

## 6. 数据流图

本章用 4 个典型场景展示数据在各模块间的流转。

### 6.1 场景 A: 日常对话

```
用户消息 "提醒我明天交论文"
        │
        ▼
┌─────────────────┐
│ CowAgent 接入层  │
│ (Web/Telegram)   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  bridge.py      │  ← log_conversation("user", message)
│  log_conversation│     写入 conversation_logs 表
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Claude LLM     │  ← System Prompt (5角色人格)
│  (cds/Claude-   │     LLM 判断: 这是秘书场景
│   4.6-opus)     │
└────────┬────────┘
         │
    ┌────┴────┐
    ▼         ▼
┌────────┐ ┌────────────┐
│MemTool │ │ DB Tool    │
│search  │ │add_schedule│
│"论文"  │ │"交论文"    │
│相关记忆│ │due=明天    │
└────────┘ └────────────┘
    │         │
    ▼         ▼
┌────────┐ ┌────────┐
│ Mem0   │ │SQLite  │
│向量搜索│ │schedule│
│图谱查询│ │表插入  │
└────────┘ └────────┘
         │
         ▼
┌─────────────────┐
│  LLM 生成回复    │  "好的，已帮你设置明天交论文的提醒。
│                  │   论文初稿还有1天截止。"
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  bridge.py      │  ← log_conversation("assistant", response)
│  log_conversation│
└─────────────────┘
```

### 6.2 场景 B: 每日反思 (23:00 定时触发)

```
CowAgent SchedulerTool
│ cron: "0 23 * * *"
│ ai_task: "使用 evolution_reflection(action='daily')"
│
▼
┌──────────────────────────────────────────────┐
│           ReflectionTool._run_daily_reflection│
│                                               │
│  Step 1: db.get_conversations_by_date(today) │
│          → 收集今日对话记录                     │
│                                               │
│  Step 2: memory_tool.search("用户今天的状态")  │
│          → Mem0 向量搜索 + 图谱关系            │
│                                               │
│  Step 3: call_claude_api(                     │
│            DAILY_REFLECTION_PROMPT.format(     │
│              today_conversations=...,          │
│              existing_memories=...,            │
│              graph_relations=...,              │
│              date=today                        │
│            )                                   │
│          )                                     │
│          → LLM 生成 JSON 格式反思报告          │
│                                               │
│  Step 4: db.save_reflection(...)              │
│          → 存入 daily_reflections 表           │
│          memory_tool.add(反思摘要)             │
│          → 同时存入 Mem0 (向量+图谱)           │
│                                               │
│  Step 5: NotificationRouter.send(...)         │
│          → 普通反思: NORMAL → Email + Notion   │
│          → 异常(>0.6): CRITICAL → 全通道       │
└──────────────────────────────────────────────┘
```

### 6.3 场景 C: 早间情报 (08:00 定时触发)

```
CowAgent SchedulerTool
│ cron: "0 8 * * *"
│
▼
┌──────────────────────────────────────────────┐
│       IntelligenceTool._generate_briefing     │
│                                               │
│  1. 并行拉取所有 RSS 源                        │
│     ┌──────────────────────────────┐          │
│     │ arXiv (Inverse Problems)     │          │
│     │ GitHub Trending (Python)     │          │
│     │ Hacker News (Best)           │          │
│     │ + 用户自定义源               │          │
│     └────────────┬─────────────────┘          │
│                  ▼                             │
│     defusedxml 安全解析 (RSS 2.0 + Atom)       │
│     _clean_html() 去除标签                     │
│                  │                             │
│  2. memory_tool.search("用户关注领域")         │
│     → 获取用户兴趣标签                         │
│                  │                             │
│  3. call_claude_api(                           │
│       INTELLIGENCE_FILTER_PROMPT.format(        │
│         feed_count=N,                           │
│         feeds_content=...,                      │
│         user_interests=...                      │
│       )                                        │
│     )                                          │
│     → LLM 筛选 1-3 条最相关信息                │
│                  │                             │
│  4. NotificationRouter.send(                   │
│       priority=LOW → 仅 Notion                 │
│     )                                          │
└──────────────────────────────────────────────┘
```

### 6.4 场景 D: 周度报告 (周日 20:00)

```
CowAgent SchedulerTool
│ cron: "0 20 * * 0"
│
▼
┌──────────────────────────────────────────────┐
│        ReflectionTool._run_weekly_report      │
│                                               │
│  1. db.get_reflections_range(7天前, 今天)     │
│     → 获取本周所有每日反思                     │
│                                               │
│  2. memory_tool.profile()                     │
│     → 获取用户完整档案                         │
│                                               │
│  3. call_claude_api(                           │
│       WEEKLY_REPORT_PROMPT.format(             │
│         weekly_reflections=...,                │
│         user_profile=...                       │
│       )                                        │
│     )                                          │
│     → 生成 Markdown 格式周报                   │
│     → 包含成绩单表格 + 关键事件 + 模式分析     │
│                                               │
│  4. NotificationRouter.send(                   │
│       priority=NORMAL → Email + Notion         │
│     )                                          │
└──────────────────────────────────────────────┘
```

---

## 7. 安全设计

### 7.1 安全威胁模型

| 威胁 | 攻击面 | 严重性 | 防护措施 |
|------|--------|--------|---------|
| SQL 注入 | `upsert_person()` 动态列名 | 🔴 HIGH | 列名白名单 (`_PERSON_COLUMNS` frozenset) |
| XXE 攻击 | RSS XML 解析 | 🔴 HIGH | `defusedxml` 库 (禁用外部实体) |
| SSRF | 用户添加自定义 RSS 源 | 🟡 MEDIUM | URL 协议限制 + 私有 IP 检测 |
| 线程竞态 | DatabaseManager 单例创建 | 🟡 MEDIUM | `threading.Lock` + `threading.local()` |
| 资源泄漏 | SQLite 连接未关闭 | 🟢 LOW | `atexit.register(self.close)` |
| LLM 提示注入 | 用户消息中嵌入恶意指令 | 🟡 MEDIUM | System Prompt 中的角色约束 (缓解) |

### 7.2 SQL 注入防护

**问题**: `upsert_person()` 接受 `**kwargs`，如果直接拼接列名到 SQL 语句，攻击者可以注入恶意列名。

**解决方案**: 定义列名白名单，仅允许已知安全的列名：

```python
_PERSON_COLUMNS = frozenset({
    "relationship", "likes", "dislikes", "important_dates",
    "interaction_frequency", "emotional_impact", "notes",
})

# 在 upsert_person 中:
for k, v in kwargs.items():
    if v is not None and k in self._PERSON_COLUMNS:  # 白名单过滤
        set_clauses.append(f"{k} = ?")  # 列名来自白名单
        values.append(v)                 # 值使用参数化查询
```

### 7.3 XXE (XML External Entity) 防护

**问题**: RSS 解析使用 XML，恶意 RSS 源可能包含 XXE 攻击载荷。

**解决方案**: 使用 `defusedxml` 库替代标准库的 `xml.etree.ElementTree`:

```python
try:
    from defusedxml.ElementTree import fromstring as safe_xml_fromstring
except ImportError:
    # 回退: 使用标准库但禁用实体扩展
    import xml.etree.ElementTree as _ET
    def safe_xml_fromstring(text):
        parser = _ET.XMLParser()
        parser.feed(text)
        return parser.close()
```

### 7.4 SSRF (Server-Side Request Forgery) 防护

**问题**: 用户可以通过 `add_feed` action 添加任意 URL，可能导致系统请求内网资源。

**解决方案**: 多层 URL 验证:

```python
@staticmethod
def _is_safe_url(url: str) -> bool:
    parsed = urlparse(url)
    # Layer 1: 协议限制
    if parsed.scheme not in ("http", "https"):
        return False
    # Layer 2: IP 地址检查
    try:
        addr = ipaddress.ip_address(hostname)
        if addr.is_private or addr.is_reserved or addr.is_loopback:
            return False  # 阻止 10.x, 172.16.x, 192.168.x, 127.x
    except ValueError:
        pass
    # Layer 3: 常见内网域名
    if hostname.lower() in ("localhost",) or hostname.endswith(".local"):
        return False
    return True
```

### 7.5 线程安全

**DatabaseManager 单例**:
- `threading.Lock()` 保护单例创建
- `threading.local()` 为每个线程维护独立 SQLite 连接
- `reset_singleton()` 在测试间安全重置（先关闭连接再清空实例）

**LLM 客户端**:
- `reset_client()` 允许测试间重置模块级缓存

### 7.6 资源清理

```python
def __init__(self, db_path=None):
    ...
    atexit.register(self.close)  # 进程退出时自动关闭

def close(self):
    conn = getattr(self._local, "conn", None)
    if conn is not None:
        try:
            conn.close()
        except Exception:
            pass  # 优雅处理已关闭的连接
        self._local.conn = None
```

---

## 8. 通知路由系统

### 8.1 架构设计

通知路由器 (`NotificationRouter`) 是所有推送的**唯一出口**，根据消息优先级自动路由到合适的通道。

```
NotificationRouter.send(notification)
         │
         │  遍历所有已启用通道
         │  channel.should_handle(priority) ?
         │
    ┌────┼────────────────────┐
    ▼    ▼                    ▼
 Email  Telegram            Notion
 SMTP_SSL Bot API          Pages API
 port 465 /sendMessage     v2022-06-28
```

### 8.2 优先级路由矩阵

| 优先级 | 使用场景 | Email | Telegram | Notion |
|--------|---------|-------|----------|--------|
| `LOW` | 情报摘要 | ❌ | ❌ | ✅ |
| `NORMAL` | 每日反思、周报 | ✅ | ❌ | ✅ |
| `HIGH` | 日程提醒 | ✅ | ✅ | ❌ |
| `CRITICAL` | 异常检测 (severity > 0.6) | ✅ | ✅ | ✅ |

**设计理念**:
- **LOW**: 信息归档性质，不打扰用户 → 仅写入 Notion
- **NORMAL**: 日常推送，邮件 + 归档 → Email + Notion
- **HIGH**: 需要即时行动 → Email + Telegram 即时通知
- **CRITICAL**: 异常告警，全通道轰炸 → 确保用户一定看到

### 8.3 通道实现细节

#### Email 通道

```python
class EmailChannel(BaseChannel):
    def send(self, notification):
        html_body = self._markdown_to_html(notification.body)  # 支持 Markdown
        msg = MIMEMultipart("alternative")
        msg.attach(MIMEText(notification.body, "plain", "utf-8"))  # 纯文本备份
        msg.attach(MIMEText(html_body, "html", "utf-8"))           # HTML 主体
        with smtplib.SMTP_SSL(self.server, self.port, timeout=15) as srv:
            srv.login(self.username, self.password)
            srv.send_message(msg)
```

- 同时发送纯文本和 HTML 版本（`multipart/alternative`）
- HTML 渲染使用 `markdown` 库（支持 tables + fenced_code 扩展）
- 连接超时 15 秒

#### Telegram 通道

```python
class TelegramChannel(BaseChannel):
    def send(self, notification):
        text = f"*{notification.title}*\n\n{notification.body}"
        resp = httpx.post(self.api_url, json={
            "chat_id": self.chat_id,
            "text": text[:4096],          # Telegram 消息长度限制
            "parse_mode": "Markdown",
        }, timeout=10)
```

- 使用 Telegram Bot API 的 `/sendMessage` 端点
- 自动截断至 4096 字符（Telegram 限制）
- Markdown 格式化标题

#### Notion 通道

```python
class NotionChannel(BaseChannel):
    def send(self, notification):
        db_id = self.databases.get(notification.category)  # 按类别路由到不同数据库
        payload = {
            "parent": {"database_id": db_id},
            "properties": {
                "Name": {"title": [{"text": {"content": notification.title[:100]}}]},
                "Date": {"date": {"start": date_val}},  # 如果有日期
            },
            "children": [
                {"type": "paragraph", "paragraph": {
                    "rich_text": [{"text": {"content": notification.body[:2000]}}]
                }}
            ],
        }
        httpx.post("https://api.notion.com/v1/pages", headers=self.headers, json=payload)
```

- 使用 Notion API v2022-06-28
- 按 `notification.category` 路由到不同的 Notion Database
- 支持 5 个 Database: `schedule`, `reflection`, `skills`, `weekly_report`, `intelligence`
- 自动添加 `Date` 属性（如果 metadata 中有日期）

### 8.4 `Notification` 数据模型

```python
@dataclass
class Notification:
    title: str                          # 通知标题
    body: str                           # 通知正文
    priority: NotifyPriority            # LOW / NORMAL / HIGH / CRITICAL
    category: str                       # reflection | schedule | intelligence | report | training | anomaly
    metadata: Dict[str, Any] = field(default_factory=dict)  # 附加数据
```

### 8.5 降级策略

- 任何通道发送失败不影响其他通道
- 通道未启用（`enabled=false`）时自动跳过
- 所有通道都未启用时，`NotificationRouter` 只记录 warning 日志，不报错
- `send_all()` 方法可绕过优先级过滤，强制发送到所有通道

---

## 9. 测试体系

### 9.1 测试概览

| 类别 | 测试数 | 通过 | 失败 | 耗时 | 运行方式 |
|------|--------|------|------|------|---------|
| 单元测试 (mock 依赖) | 172 | 172 | 0 | 1.14s | `pytest` |
| 实时集成测试 (真实 API) | 92 | 92 | 0 | ~30s | `python tests/test_live_integration.py` |
| **合计** | **264** | **264** | **0** | — | — |

**测试代码量**: ~2,429 行 (10 个测试文件)  
**代码测试比**: 源码 2,612 行 / 测试 2,429 行 ≈ **93%**

### 9.2 单元测试矩阵

| 测试文件 | 用例数 | 行数 | 覆盖模块 | 关键测试点 |
|----------|--------|------|---------|-----------|
| `test_db_manager.py` | 49 | 438 | `DatabaseManager` | 7 张表完整 CRUD、WAL 模式、线程安全单例、`atexit` 清理、统计查询 |
| `test_db_tool.py` | 37 | 285 | `EvolutionDBTool` | 全部 16 个 action、错误处理、emoji 格式化输出 |
| `test_reflection_tool.py` | 19 | 201 | `EvolutionReflectionTool` | 日反思 5 步流程、JSON 解析容错、情绪检测、周报生成 |
| `test_notification.py` | 19 | 249 | `NotificationRouter` | 优先级路由矩阵、通道降级、无通道时优雅处理 |
| `test_memory_tool.py` | 17 | 149 | `EvolutionMemoryTool` | MockMemory 降级、搜索/添加/档案、返回格式统一 |
| `test_intelligence_tool.py` | 17 | 214 | `EvolutionIntelligenceTool` | URL 安全校验、SSRF 防护、HTML 清洗、RSS 解析(RSS 2.0 + Atom) |
| `test_bridge.py` | 9 | 106 | `bridge.py` | 工具注册、System Prompt、对话日志 |
| `test_integration.py` | 5 | 156 | 跨模块集成 | 日程→反思→数据库联动、工具间数据一致性 |
| `conftest.py` | — | 103 | (fixtures) | 8 个共享 fixture: 临时数据库、mock LLM、工具实例等 |
| **合计** | **172** | **1,901** | — | — |

### 9.3 实时集成测试 (92 项)

`test_live_integration.py` (528 行) — 独立脚本，使用真实 API 和真实数据库（临时目录）。

通过 `pyproject.toml` 的 `collect_ignore` 从 `pytest` 中排除（避免 CI 中产生 API 费用）。

**覆盖区域**:

| 区域 | 检查项数 | 说明 |
|------|---------|------|
| LLM API 连通性 | 6 | 真实调用 `cds/Claude-4.6-opus`，验证响应、延迟 |
| 数据库生命周期 | 20 | 全部 7 张表增删改查，WAL、线程安全、`atexit` |
| DB Tool 接口 | 18 | 全部 16 个 action + 边界错误处理 |
| Memory Tool | 7 | MockMemory 降级、搜索、添加、档案 |
| Intelligence Tool | 12 | URL 安全、SSRF、HTML 清洗、RSS 解析 |
| Reflection + 真实 LLM | 8 | 端到端反思生成（含真实 LLM 调用，~26s） |
| 通知路由 | 8 | 优先级路由、降级、格式化 |
| Bridge | 6 | 工具列表、System Prompt、对话日志 |
| LLM 工具函数 | 7 | `call_claude_api`、`extract_json`、客户端缓存 |

### 9.4 测试设计原则

1. **Mock 优先**: 单元测试中所有外部依赖 (LLM API、Mem0、网络) 均通过 `unittest.mock` 注入
2. **临时数据库**: 每个测试使用 `tempfile.mkdtemp()` 创建独立数据库，测试后清理
3. **单例重置**: 每个测试通过 `db.reset_singleton()` 重置 DatabaseManager 状态
4. **分层验证**: 先测底层 (DatabaseManager) → 再测工具层 (DBTool) → 最后测集成

---

## 10. 代码统计与项目结构

### 10.1 项目目录树

```
ProjectEvolution/
├── evolution/                          # 源码包
│   ├── __init__.py                     (9 行)
│   ├── chat/
│   │   ├── web_chat.py                 (260 行) — Web Chat 服务器
│   │   └── templates/
│   │       └── chat.html               (200+ 行) — 聊天界面
│   ├── config/
│   │   ├── settings.py                 (160 行) — 全局配置
│   │   └── prompts.py                  (244 行) — Prompt 模板库
│   ├── db/
│   │   └── manager.py                  (516 行) — SQLite 数据库管理器
│   ├── tools/
│   │   ├── base.py                     (83 行)  — BaseTool 兼容层
│   │   ├── memory_tool.py              (208 行) — Mem0 记忆工具
│   │   ├── db_tool.py                  (299 行) — 数据库操作工具
│   │   ├── reflection_tool.py          (311 行) — 反思引擎
│   │   └── intelligence_tool.py        (301 行) — 情报收集
│   ├── notification/
│   │   └── router.py                   (259 行) — 通知路由器
│   └── utils/
│       ├── llm.py                      (80 行)  — LLM 调用封装
│       └── bridge.py                   (142 行) — CowAgent 桥接器
├── tests/                              # 测试
│   ├── conftest.py                     (103 行) — 共享 fixtures
│   ├── test_db_manager.py              (438 行) — 49 tests
│   ├── test_db_tool.py                 (285 行) — 37 tests
│   ├── test_reflection_tool.py         (201 行) — 19 tests
│   ├── test_notification.py            (249 行) — 19 tests
│   ├── test_memory_tool.py             (149 行) — 17 tests
│   ├── test_intelligence_tool.py       (214 行) — 17 tests
│   ├── test_bridge.py                  (106 行) — 9 tests
│   ├── test_integration.py             (156 行) — 5 tests
│   └── test_live_integration.py        (528 行) — 92 tests (独立运行)
├── docs/
│   ├── VALIDATION_REPORT.md            — 验证报告
│   └── technical_report_CN.md          — 本文档
├── scripts/
│   └── setup.sh                        — 一键安装脚本
├── pyproject.toml                      — 项目配置与依赖
├── docker-compose.yml                  — Docker 配置 (RSSHub)
├── .env.example                        — 环境变量模板
└── PLAN_v2.md                          — 项目计划文档
```

### 10.2 代码统计4 | 2,872 | 54% |
| 测试 (tests/) | 10 | 2,429 | 46% |
| **合计** | **24** | **5,301** | 100% |

**源码按模块分布**:

| 模块 | 行数 | 占比 | 说明 |
|------|------|------|------|
| 数据库层 (db/) | 516 | 18% | DatabaseManager，7 张表 CRUD |
| 工具层 (tools/) | 1,202 | 42% | 4 个核心工具 + BaseTool 兼容层 |
| Web Chat (chat/) | 260 | 9% | Flask 服务器 + 聊天界面 |
| 配置层 (config/) | 404 | 14% | 设置 + Prompt 模板 |
| 通知层 (notification/) | 259 | 9% | 3 通道路由器 |
| 工具函数 (utils/) | 222 | 8| DatabaseManager，7 张表 CRUD |
| 工具层 (tools/) | 1,202 | 46% | 4 个核心工具 + BaseTool 兼容层 |
| 配置层 (config/) | 404 | 15% | 设置 + Prompt 模板 |
| 通知层 (notification/) | 259 | 10% | 3 通道路由器 |
| 工具函数 (utils/) | 222 | 9% | LLM 封装 + CowAgent 桥接 |
| 其他 (__init__) | 9 | <1% | — |

### 10.3 依赖关系
7 个):

| 包 | 版本 | 用途 |
|----|------|------|
| `openai` | ≥ 1.30 | LLM API 调用 (OpenAI-compatible) |
| `defusedxml` | ≥ 0.7.1 | 安全 XML 解析 (XXE 防护) |
| `httpx` | ≥ 0.27 | HTTP 客户端 (RSS 拉取、Telegram/Notion API) |
| `apscheduler` | ≥ 3.10 | 定时任务 |
| `markdown` | ≥ 3.5 | 邮件 HTML 渲染 |
| `flask` | ≥ 3.0 | Web 服务器框架 |
| `flask-cors` | ≥ 4.0 | CORS 支持
| `markdown` | ≥ 3.5 | 邮件 HTML 渲染 |

**可选依赖**:

| 包 | 用途 |
|----|------|
| `mem0ai[graph]` ≥ 1.0.5 | 完整 Mem0 (向量 + 图谱)。不安装则降级为 MockMemory |
| `notion-client` ≥ 2.2 | Notion API。不安装则 Notion 通道不可用 |

**开发依赖**:

| 包 | 用途 |
|----|------|
| `pytest` ≥ 8.0 | 测试框架 |
| `pytest-asyncio` ≥ 0.23 | 异步测试支持 |
| `pytest-cov` ≥ 5.0 | 覆盖率统计 |

---

## 11. 部署指南

### 11.1 当前部署状态 (2026-03-11)

**✅ 系统已成功部署并运行**

- **服务器**: server3090 (10.128.250.187)
- **Web Chat 地址**: 
  - 本地: http://localhost:5000
  - 局域网: http://10.128.250.187:5000
- **健康检查**: `curl http://localhost:5000/health`
- **环境配置**: `/home/yjh/ProjectEvolution/.env`

**已验证的功能**:
- ✅ SMTP 邮件推送 (smtp.qq.com:465)
- ✅ Notion API 集成 (数据库: Docs)
- ✅ LLM API 调用 (cds/Claude-4.6-opus)
- ✅ Web Chat 界面 (Flask 服务器)
- ✅ 对话功能测试通过

### 11.2 快速开始 (5 分钟)

```bash
# 1. 克隆项目
git clone <repo> && cd ProjectEvolution

# 2. 安装3 完整安装 (含 Mem0 和通知)

```bash
# 安装完整依赖
pip install -e ".[full,dev]"

# 启动 RSSHub (情报收集需要)
docker compose up -d rsshub

# 当前已配置的通知通道 (在 .env 中)
EMAIL_ENABLED=true
EMAIL_SMTP_SERVER=smtp.qq.com
EMAIL_SMTP_PORT=465
EMAIL_USERNAME=<your_email>
EMAIL_PASSWORD=<your_smtp_password>
EMAIL_TO=<recipient_email>

NOTION_ENABLED=true
NOTION_TOKEN=<your_notion_token>
NOTION_DATABASE_ID=<your_database_id>

# Telegram (可选，暂未配置)
TG_ENABLED=false
TG_BOT_TOKEN=
TG_CHAT_ID=
# 启动 RSSHub (情报收集需要)
docker compose up -d rsshub

# 配置通知通道 (在 .env 中)
EMAIL_ENABLED=true
EMAIL_SMTP_SERVER=smtp.qq.com
EMAIL_SMTP_PORT=465
EMAIL_USERNAME=your@qq.com
EMAIL_PASSWORD=your_smtp_password
EMAIL_TO=your@email.com

TG_ENABLED=true
TG_BOT_TOKEN=your_bot_token
TG_CHAT_ID=your_chat_id

NOTION_ENABLED=true
NOTION_TOKEN=your_integration_token
NOTION_DB_SCHEDULE=database_id
NOTION_DB_REFLECTION=database_id
```

### 11.4 Web Chat 使用指南

**访问方式**:
1. **电脑浏览器**: 打开 http://localhost:5000 或 http://10.128.250.187:5000
2. **手机浏览器**: 连接同一 WiFi，访问 http://10.128.250.187:5000
3. **健康检查**: `curl http://localhost:5000/health`

**可用功能**:
- 实时对话交互
- 工具调用支持 (记忆、数据库、反思、情报)
- 对话历史保存 (自动存储到 `data/conversation_logs/`)
- 响应式设计 (适配手机和电脑)

**管理命令**:
```bash
# 查看运行状态
ps aux 6 grep web_chat

# 停止服务器
kill <PID>

# 重启服务器
cd /home/yjh/ProjectEvolution
python3 -m evolution.chat.web_chat

# 查看对话日志
tail -f data/conversation_logs/web_chat_*.jsonl
```

### 11.5 集成到 CowAgent

```python
# 在 CowAgent 启动脚本中:
from ev7lution.utils.bridge import register_with_cowagent, setup_scheduled_tasks, get_system_prompt

# 1. 注册工具
register_with_cowagent()

# 2. 设置定时任务
setup_scheduled_tasks()

# 3. 获取 System Prompt (注入到 CowAgent 的 LLM 配置中)
system_prompt = get_system_prompt()
```

### 11.4 Docker Compose 配置

```yaml
# docker-compose.yml — 仅 RSSHub
services:
  rsshub:
    image: diygod/rsshub:latest
    restart: always
    ports:
      - "1200:1200"
    environment:
      - NODE_ENV=production
      - CACHE_TYPE=memory
```

Evolution 本身不需要 Docker，直接在宿主机或虚拟环境中运行。

### 11.5 环境变量完整清单

| 变量 | 当前配置 | 说明 |
|------|---------|------|
| `EVOLUTION_ROOT` | `/home/yjh/ProjectEvolution` | 数据存储根目录 |
| `LLM_API_KEY` | `sk-Zj3a7RQDVCXr-Axg-0gtkg` | LLM API 密钥 |
| `LLM_BASE_URL` | `https://ai-gateway-internal.dp.tech/v1` | API 网关地址 |
| `LLM_MODEL` | `cds/Claude-4.6-opus` | 模型名称 |
| `LLM_MAX_TOKENS` | `8192` | 最大生成 token 数 |
| `LLM_TEMPERATURE` | `0.3` | 温度参数 |
| `EVOLUTION_USER_ID` | `master` | Mem0 用户标识 |
| `EMBEDDING_PROVIDER` | `openai` | 向量化提供商 |
| `EMBEDDING_MODEL` | `text-embedding-3-small` | 向量化模型 |
| `RSSHUB_URL` | `http://localhost:1200` | RSSHub 地址 |
| `EMAIL_ENABLED` | `false` | 启用邮件通知 |
| `TG_ENABLED` | `false` | 启用 Telegram 通知 |
| `NOTION_ENABLED` | `false` | 启用 Notion 通知 |

---

## 12. 未来演进

### 12.1 短期优化 (1-2 周)

| 优先级 | 任务 | 说明 |
|--------|------|------|
| P0 | 部署到云服务器 | 2核4G 即可，配置 systemd 服务自动重启 |
| P0 | 接入真实 Mem0 | 安装 `mem0ai[graph]`，配置 Qdrant + Kuzu |
| P1 | Telegram Bot 接入 | 作为另一个对话入口，支持随时随地交互 |
| P1 | 日程提醒主动推送 | 基于 `remind_at` 字段的 cron 任务 |

### 12.2 中期增强 (1-2 月)

| 优先级 | 任务 | 说明 |
|--------|------|------|
| P1 | 技能训练内容库 | 为每个训练模态 (T1-T7) 预设高质量题目 |
| P1 | 人物关系图可视化 | 基于 Mem0 Graph Memory 生成关系网络图 |
| P2 | 多用户支持 | `USER_ID` 隔离，支持家庭/团队模式 |
| P2 | 情绪趋势分析 | 基于 `daily_reflections` 的情绪时序分析 + 可视化 |
| P2 | 自定义 RSS 持久化 | 将用户添加的 RSS 源存入 SQLite（当前仅在内存） |

### 12.3 长期愿景

- **多模态**: 语音输入 + 语音回复（通过 CowAgent 的 TTS/STT 插件）
- **移动端**: iOS/Android Shortcut 集成
- **知识库**: 将用户的阅读笔记、论文标注整合进记忆系统
- **导师网络**: 多个 Evolution 实例之间共享匿名化的成长模式数据
- **自我进化**: 根据用户反馈自动优化 Prompt 模板

---

## 13. 附录

### 附录 A: 完整 Prompt 模板

所有 Prompt 模板定义在 `evolution/config/prompts.py`，共 244 行，包含：

1. **SYSTEM_PROMPT** (~75 行): 五角色统一人格，包含每个角色的详细行为指南、语言规则和记忆使用规范
2. **DAILY_REFLECTION_PROMPT** (~60 行): 每日反思模板，输出 11 个字段的结构化 JSON
3. **INTELLIGENCE_FILTER_PROMPT** (~25 行): 情报筛选，输出 `has_relevant` + `items` + `briefing_text`
4. **WEEKLY_REPORT_PROMPT** (~30 行): 周报模板，输出 Markdown 表格
5. **SCHEDULE_DETECTION_PROMPT** (~15 行): 日程意图检测
6. **PERSON_EXTRACTION_PROMPT** (~15 行): 人物信息提取

### 附录 B: CowAgent BaseTool 接口规范

```python
class BaseTool:
    stage: ToolStage = ToolStage.PRE_PROCESS    # 执行阶段
    name: str = "tool_name"                      # 工具名称 (LLM 用此名称调用)
    description: str = "Tool description"         # 工具描述 (LLM 用此理解工具能力)
    params: dict = {                              # JSON Schema 格式的参数定义
        "type": "object",
        "properties": {
            "param1": {"type": "string", "description": "..."},
        },
        "required": ["param1"],
    }
    model: Optional[Any] = None                   # CowAgent 注入的 LLM model
    context: Optional[Any] = None                 # CowAgent 注入的上下文

    def execute(self, params: dict) -> ToolResult:
        """工具执行入口，由 CowAgent 调用"""
        raise NotImplementedError

class ToolResult:
    @staticmethod
    def success(result, ext_data=None) -> ToolResult:
        """成功结果"""

    @staticmethod
    def fail(result, ext_data=None) -> ToolResult:
        """失败结果"""
```

### 附录 C: 训练模态详解

| 模态 | 名称 | 认知层次 | 适合阶段 | 产出 |
|------|------|---------|---------|------|
| T1 | 概念辨析 | 理解 | 入门 | 概念边界图 |
| T2 | 立场辩论 | 分析 | 中级 | 双方论点清单 |
| T3 | 世界模型分析 | 综合 | 中级 | 因果链条图 |
| T4 | 苏格拉底式自我审问 | 评价 | 中高级 | 盲点清单 |
| T5 | 思维实验 | 创造 | 高级 | 类比映射 |
| T6 | 快速测试 | 记忆 | 全阶段 | 正确率统计 |
| T7 | 跨域迁移 | 创造 | 高级 | 迁移分析报告 |

### 附录 D: 安全审计清单

| # | 检查项 | 状态 | 实现位置 |
|---|--------|------|---------|
| 1 | SQL 注入防护 | ✅ 已修复 | `manager.py` → `_PERSON_COLUMNS` frozenset |
| 2 | XXE 攻击防护 | ✅ 已修复 | `intelligence_tool.py` → `defusedxml` |
| 3 | SSRF 防护 | ✅ 已修复 | `intelligence_tool.py` → `_is_safe_url()` |
| 4 | 线程安全 | ✅ 已修复 | `manager.py` → `Lock` + `local()` + `reset_singleton()` |
| 5 | 资源泄漏 | ✅ 已修复 | `manager.py` → `atexit.register(self.close)` |
| 6 | LLM 客户端缓存重置 | ✅ 已修复 | `llm.py` → `reset_client()` |

### 附录 E: 常用命令速查

```bash
# 运行全部单元测试
pytest

# 运行单个测试文件
pytest tests/test_db_manager.py

# 运行测试并显示覆盖率
pytest --cov=evolution --cov-report=html

# 运行实时集成测试 (需要真实 API Key)
python tests/test_live_integration.py

# 启动 RSSHub
docker compose up -d rsshub

# 查看 RSSHub 日志
docker compose logs -f rsshub

# 重置数据库 (删除数据目录)
rm -rf /data/evolution/data/

# 检查 Python 依赖
pip list | grep -E "openai|defusedxml|httpx|apscheduler|markdown"
```

---

> **文档结束**  
> 本报告涵盖 Evolution v0.1.0 的完整架构、实现细节、安全设计和部署指南。  
> 如有疑问，请查阅源码或联系项目维护者。
