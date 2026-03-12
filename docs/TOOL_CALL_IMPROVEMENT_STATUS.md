# 工具调用改进状态报告

**日期**: 2026-03-12  
**状态**: ✅ **已完成 — 全部测试通过**

---

## 问题背景

根据 `technical_report_CN.md`，工具调用存在约 80% 的失败率。LLM 在需要调用工具（如查询日程、添加记忆）时，经常无法正确触发工具执行。

## 根因分析（6 个问题）

| # | 问题 | 影响 | 修复状态 |
|---|------|------|----------|
| 1 | 系统提示词矛盾 — `build_system_prompt()` 生成模糊工具说明，未使用 `TOOL_USAGE_GUIDE` | LLM 不知道如何调用工具 | ✅ 已修复 |
| 2 | `parse_tool_calls` 返回原始字符串而非解析后的 JSON | 参数传入工具时报错 | ✅ 已修复 |
| 3 | 工具名称不匹配 — 提示词用短名(memory/db)，验证期望长名(evolution_memory/evolution_db) | 工具匹配失败 | ✅ 已修复 |
| 4 | `TOOL_USAGE_GUIDE` 从未被注入到活跃提示词中 | LLM 没有工具调用示例 | ✅ 已修复 |
| 5 | 工具结果反馈差 — 结果作为原始文本追加，LLM 未据此生成回复 | 用户看到原始数据而非自然语言 | ✅ 已修复 |
| 6 | 未使用 OpenAI Function Calling API — 网关支持 `tools` 参数但未利用 | 依赖不可靠的文本解析 | ✅ 已修复 |

## 修改的文件

### `evolution/utils/llm.py`
- 新增 `call_llm_with_tools()` 函数，支持 OpenAI Function Calling
- 返回结构化结果：`{"content", "tool_calls", "raw_message"}`
- 自动回退：API 不支持时返回 `None`

### `evolution/chat/web_chat.py`
- 新增 `OPENAI_TOOLS` — 完整的工具 JSON Schema 定义
- 新增 `_process_with_function_calling()` — Function Calling 主模式
- 新增 `_process_with_text_parsing()` — 文本解析回退模式
- 改进 `build_system_prompt()` — 使用 `TOOL_USAGE_GUIDE`
- 改进 `process_message()` — 双模式调度器，自动检测 API 能力
- 工具结果反馈给 LLM 生成自然语言回复

### `evolution/utils/tool_handler.py`
- `TOOL_USAGE_GUIDE` 包含完整 action 列表、必需参数和 JSON 示例

## 测试结果

### 端到端测试 (2026-03-12 13:35)

| 测试 | 描述 | 结果 |
|------|------|------|
| Test 1 | 基本 LLM 连接 | ✅ 通过 |
| Test 2 | Function Calling API | ✅ 通过 — LLM 正确调用 `evolution_db` |
| Test 3 | 文本解析回退模式 | ✅ 通过 — `[TOOL:evolution_db]{"action":"list_schedule"}[/TOOL]` |
| Test 4a | 简单对话 | ✅ 通过 — 无工具场景正常 |
| Test 4b | 查询待办事项 | ✅ 通过 — 调用工具后生成自然语言回复 |
| Test 4c | 添加日程 | ✅ 通过 — "已记下。3月14日周六下午3点，组会。" |
| Test 4d | 确认日程列表 | ✅ 通过 — 列出所有 5 条日程 |

### 关键验证

- **模式**: Function Calling（主模式，自动检测成功）
- **工具执行**: `evolution_db` 的 `list_schedule`、`add_schedule` 均正确执行
- **结果反馈**: 工具结果被反馈给 LLM，生成了高质量的自然语言回复
- **示例回复**:
  > 周四下午，你手头是这些：
  > - 🟡 **和龙香君吃晚饭** — 截止下午4点
  > - 🔴 **下午3点开组会** — 高优先级
  > - 🟡 **关注麦当劳派日送派**
  > - 🟡 **去图书馆** — 上午10点前

## 架构

```
用户消息 → process_message()
  ├─ Function Calling 模式（主）
  │   ├─ call_llm_with_tools() → LLM 返回 tool_calls
  │   ├─ _execute_tool_by_name() → 执行工具
  │   ├─ 工具结果作为 tool message 追加
  │   └─ call_llm_with_tools() → LLM 生成自然语言回复
  │
  └─ 文本解析模式（回退）
      ├─ call_claude_api() → LLM 返回含 [TOOL:...] 的文本
      ├─ parse_tool_calls_json() → 解析工具调用
      ├─ _execute_tool_by_name() → 执行工具
      └─ call_claude_api() → LLM 根据工具结果生成回复
```
