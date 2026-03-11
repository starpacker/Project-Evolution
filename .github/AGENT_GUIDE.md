# 🤖 Multi-Agent Workflow 使用指南

> 基于 [github/awesome-copilot](https://github.com/github/awesome-copilot) 的多智能体编排系统

---

## 📦 你拥有什么

本工作区配置了 **14 个 AI 智能体**，组成两套独立的编排系统，可以根据任务复杂度选择使用。

### 系统 A：RUG（Repeat Until Good）— 轻量编排

```
你 → @RUG → 分解任务 → @SWE 实现 / @QA 验证 → 循环直到全部通过 → 完成
```

| Agent | 文件 | 角色 |
|-------|------|------|
| `RUG` | `rug_orchestrator.agent.md` | 🎯 纯编排器 — 自己不写代码，只分解、委派、验证、重试 |
| `SWE` | `swe-subagent.agent.md` | 💻 高级工程师 — 功能开发、调试、重构、测试 |
| `QA` | `qa_subagent.agent.md` | ✅ QA 测试员 — 测试计划、bug 狩猎、边界分析 |

### 系统 B：Gem Team — 全流程 DAG 编排

```
你 → @gem-orchestrator → Phase 1: Research → Phase 2: Plan → Phase 3: Execute (waves) → Phase 4: Summary
```

| Agent | 文件 | 角色 |
|-------|------|------|
| `gem-orchestrator` | `gem-orchestrator.agent.md` | 🎯 团队领导 — 4 阶段工作流编排 |
| `gem-researcher` | `gem-researcher.agent.md` | 🔍 研究员 — 多遍混合检索，输出 YAML |
| `gem-planner` | `gem-planner.agent.md` | 📋 规划师 — DAG 任务分解，预检分析 |
| `gem-implementer` | `gem-implementer.agent.md` | 💻 TDD 实现者 — Red→Green 测试驱动 |
| `gem-reviewer` | `gem-reviewer.agent.md` | 👁️ 安全审查 — OWASP Top 10, secrets 检测 |
| `gem-documentation-writer` | `gem_documentation_writer.agent.md` | 📚 文档撰写 — 技术文档、架构图 |

### 独立工具 Agent（两套系统都可调用）

| Agent | 文件 | 角色 |
|-------|------|------|
| `Context Architect` | `context_architect.agent.md` | 🗺️ 代码架构分析、依赖映射 |
| `Thinking Beast Mode` | `thinking_beast.agent.md` | 🧠 深度自主求解，联网研究 |
| `Debug Mode Instructions` | `debug.agent.md` | 🐛 系统化调试流程 |
| `Critical thinking mode instructions` | `critical_thinking.agent.md` | 🤔 质疑假设，挑战推理 |
| `Prompt Engineer` | `prompt_engineer.agent.md` | ✍️ 提示词分析和优化 |

---

## 🚀 快速开始

### 1. 简单编码任务 — 直接对话或 `@SWE`

```
@SWE 帮我写一个函数，读取 CSV 文件并计算每个模型的平均成功率
```

SWE 会：读取上下文 → 规划 → 实现 → 验证 → 交付

### 2. 中等复杂度 — 用 `@RUG`

```
@RUG 帮我重构 analyze_correlations.py，提取公共函数到 utils.py，
然后添加单元测试
```

RUG 会：
1. 调 `SWE` 分析当前代码结构
2. 调 `SWE` 执行重构
3. 调 `SWE` 编写测试
4. 每步都用 `QA` 验证
5. 失败则带着错误信息重试

### 3. 大型复杂项目 — 用 `@gem-orchestrator`

```
@gem-orchestrator 为这个 benchmark 分析项目创建一个完整的数据管线：
自动读取所有 CSV → 统一预处理 → 计算多种指标 → 生成对比图表 → 输出报告
```

gem-orchestrator 会：
1. **Phase 1 Research** — 调 `gem-researcher` 分析所有 CSV 文件的结构和模式
2. **Phase 2 Plan** — 调 `gem-planner` 生成 `plan.yaml` (DAG 任务图，分成多个 wave)
3. **Phase 3 Execute** — 按 wave 顺序调 `gem-implementer` 实现每个任务，调 `gem-reviewer` 安全审查
4. **Phase 4 Summary** — 调 `gem-documentation-writer` 生成文档

### 4. 调试 bug — 用 `@Debug Mode Instructions`

```
@Debug Mode Instructions 运行 analyze_stats.py 时报错 KeyError: 'model_name'，
帮我找到并修复
```

### 5. 质疑方案 — 用 `@Critical thinking mode instructions`

```
@Critical thinking mode instructions 我打算用 Pearson 相关系数来评估
模型排名的一致性，这个方案合理吗？
```

### 6. 安全审查 — 用 `@gem-reviewer`

```
@gem-reviewer 审查 batch_process_models.py 的安全性，特别关注文件路径处理
和数据验证
```

### 7. 代码架构分析 — 用 `@Context Architect`

```
@Context Architect 分析 analyze_*.py 这些文件之间的依赖关系，
画出架构图
```

### 8. 深度自主求解 — 用 `@Thinking Beast Mode`

```
@Thinking Beast Mode 研究如何用 Bootstrap 方法估计模型成功率的置信区间，
然后实现它
```

---

## 🏗️ 两套系统的选择指南

| 场景 | 推荐系统 | 原因 |
|------|----------|------|
| 改一个函数 | `@SWE` 直接调用 | 无需编排开销 |
| 改 2-5 个文件 | `@RUG` | 轻量编排，分步实现+验证 |
| 新建完整功能模块 | `@gem-orchestrator` | 需要研究→规划→实现→审查全流程 |
| 重构+测试+文档 | `@RUG` 或 `@gem-orchestrator` | 都可以，gem 会更系统化 |
| 调研技术方案 | `@gem-researcher` 直接调用 | 不需要完整编排 |
| Bug 修复 | `@Debug Mode Instructions` | 专用调试流程 |

---

## ⚙️ 工作原理

### RUG 的核心机制

```
                    ┌─────────────┐
                    │   @RUG      │
                    │ (编排器)     │
                    └──────┬──────┘
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
        ┌──────────┐ ┌──────────┐ ┌──────────┐
        │  @SWE    │ │   @QA    │ │  其他     │
        │ (实现)    │ │ (验证)    │ │  Agent   │
        └──────────┘ └──────────┘ └──────────┘
```

**关键规则：**
- RUG **永远不自己写代码**，只用 `runSubagent` 和 `manage_todo_list`
- 每个子 agent 获得**独立的上下文窗口** → 不会因为上下文过长而变笨
- 每次实现后都启动**单独的验证 agent** → 不信任自我评估
- 验证失败 → **带着错误信息重新启动**新的子 agent

### Gem Team 的核心机制

```
Phase 1: Research ──→ research_findings.yaml
                          │
Phase 2: Plan ────→ plan.yaml (DAG with waves)
                          │
Phase 3: Execute ──→ Wave 1 (并行) → Wave 2 (并行) → ...
                          │
Phase 4: Summary ──→ 文档 + PRD
```

**关键规则：**
- 所有 agent 通过 **JSON 格式**通信
- 任务用 **DAG**（有向无环图）组织，同一 wave 内的任务可**并行执行**
- 失败分类处理：`transient`→重试 | `needs_replan`→重新规划 | `escalate`→反馈用户
- 自动生成 **PRD**（产品需求文档）

---

## 📁 文件结构

```
~/.github/
├── copilot-instructions.md          # 全局配置 — Copilot 在所有对话中读取
└── agents/
    ├── rug_orchestrator.agent.md     # 🎯 RUG 编排器
    ├── swe-subagent.agent.md         # 💻 SWE 工程师
    ├── qa_subagent.agent.md          # ✅ QA 测试员
    ├── gem-orchestrator.agent.md     # 🎯 Gem 编排器
    ├── gem-researcher.agent.md       # 🔍 研究员
    ├── gem-planner.agent.md          # 📋 规划师
    ├── gem-implementer.agent.md      # 💻 TDD 实现者
    ├── gem-reviewer.agent.md         # 👁️ 安全审查
    ├── gem_documentation_writer.agent.md  # 📚 文档撰写
    ├── context_architect.agent.md    # 🗺️ 架构分析
    ├── thinking_beast.agent.md       # 🧠 深度求解
    ├── debug.agent.md                # 🐛 调试专家
    ├── critical_thinking.agent.md    # 🤔 质疑者
    └── prompt_engineer.agent.md      # ✍️ Prompt 优化
```

---

## 💡 高级技巧

### 1. 链式调用

你可以手动组合 agent 形成自定义流程：

```
# Step 1: 先让研究员分析
@gem-researcher 分析 analyze_*.py 文件群的代码结构和模式

# Step 2: 然后让规划师制定方案
@gem-planner 基于上面的研究结果，制定重构计划

# Step 3: 最后让实现者执行
@SWE 按照上面的计划实现重构
```

### 2. 用 Critical Thinking 质疑方案

在实施前用 Critical Thinking 挑战你的想法：

```
@Critical thinking mode instructions 我准备把所有 analyze_*.py
合并成一个统一的分析框架，这个方案有什么潜在问题？
```

### 3. 用 Prompt Engineer 优化指令

如果你觉得 agent 理解不了你的意思：

```
@Prompt Engineer 优化这个 prompt：
"帮我分析数据然后画图"
```

### 4. 跨系统调用

RUG 可以调用 Gem Team 的 agent，反过来也可以：

```
@RUG 帮我做以下工作：
1. 用 gem-researcher 分析 analyze_correlations.py 的代码结构
2. 用 SWE 根据分析结果重构代码
3. 用 QA 编写和运行测试
4. 用 gem-reviewer 做安全审查
```

---

## ⚠️ 注意事项

1. **上下文窗口有限** — 不要在一个请求中塞太多任务，让编排器帮你拆分
2. **子 agent 链可能较长** — 复杂任务可能需要 10+ 轮 subagent 调用，耐心等待
3. **验证很重要** — 始终用独立 agent 验证实现结果，不要信任自我评估
4. **具体 > 模糊** — 越具体的指令，agent 执行质量越高
5. **迭代优于一步到位** — 先让 agent 完成核心功能，再逐步完善

---

## 🔗 来源

所有 agent prompt 来自 [github/awesome-copilot](https://github.com/github/awesome-copilot) 开源仓库：

- **RUG 系统**: [`plugins/rug-agentic-workflow`](https://github.com/github/awesome-copilot/tree/main/plugins/rug-agentic-workflow)
- **Gem Team**: [`plugins/gem-team`](https://github.com/github/awesome-copilot/tree/main/plugins/gem-team)
- **其他 Agent**: [`agents/`](https://github.com/github/awesome-copilot/tree/main/agents) 目录

MIT License.
