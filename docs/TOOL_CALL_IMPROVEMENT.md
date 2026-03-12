# Evolution 工具调用改进方案

## 问题分析

测试结果显示：**80%的工具调用失败率**

### 主要问题

1. **参数解析过于简单** - 当前使用字符串解析，容易出错
2. **缺少参数验证** - LLM传递不完整参数时没有提示
3. **没有自动重试** - 失败后不会尝试修正
4. **错误信息不清晰** - 用户看到的是原始错误

### 失败案例

```
用户: 帮我添加一个日程：明天下午3点开会
LLM: 记下了...
实际: [db] [数据库] 日程需要 content 参数
```

LLM虽然"说"记下了，但实际没有正确调用工具。

## 解决方案

### 方案A: 改用JSON格式工具调用（推荐）

**优点**:
- 参数结构清晰
- 易于验证
- 标准化

**实施**:
1. 修改SYSTEM_PROMPT，要求LLM使用JSON格式
2. 添加JSON解析和验证
3. 失败时自动生成修正提示

### 方案B: 增强当前字符串解析

**优点**:
- 改动较小
- 向后兼容

**缺点**:
- 仍然容易出错
- 难以处理复杂参数

### 方案C: 使用Function Calling API

**优点**:
- 最标准的方式
- API自动处理

**缺点**:
- 需要API支持
- 可能增加成本

## 推荐实施步骤

### 第1步: 改进工具调用格式

修改SYSTEM_PROMPT，要求使用JSON格式：

```
当需要调用工具时，使用以下格式：

[TOOL:tool_name]
{
  "action": "操作名称",
  "param1": "值1",
  "param2": "值2"
}
[/TOOL]
```

### 第2步: 添加参数验证

在execute_tool中添加验证逻辑：

```python
def validate_and_execute_tool(tool_name, params_dict):
    # 验证必需参数
    if tool_name == "db" and params_dict.get("action") == "add_schedule":
        if "content" not in params_dict:
            return {
                "success": False,
                "error": "缺少content参数",
                "retry_hint": "请提供日程内容，例如: {\"action\": \"add_schedule\", \"content\": \"明天下午3点开会\"}"
            }
    
    # 执行工具
    result = tool.execute(params_dict)
    return {"success": True, "result": result}
```

### 第3步: 实现自动重试

```python
def chat_with_retry(user_message, max_retries=2):
    for attempt in range(max_retries):
        response = call_llm(user_message)
        
        # 解析工具调用
        tool_calls = parse_tool_calls(response)
        
        # 验证并执行
        all_success = True
        for tool_call in tool_calls:
            result = validate_and_execute_tool(tool_call)
            if not result["success"]:
                all_success = False
                # 生成修正提示
                retry_prompt = f"工具调用失败: {result['error']}\n{result['retry_hint']}\n请重新调用。"
                # 继续对话，让LLM修正
                user_message = retry_prompt
                break
        
        if all_success:
            return response
    
    return "多次尝试后仍然失败，请检查参数。"
```

### 第4步: 改进错误提示

不要直接显示原始错误，而是：

```python
if tool_error:
    # 不显示给用户
    logger.error(f"Tool error: {tool_error}")
    
    # 自动重试或给出友好提示
    if should_retry:
        # 自动重试
        pass
    else:
        # 给用户友好提示
        return "我在处理你的请求时遇到了问题，让我重新尝试..."
```

## 测试计划

1. 修改后运行小规模测试（10次对话）
2. 检查成功率是否提升到90%以上
3. 运行大规模测试（100次对话）
4. 分析剩余失败案例
5. 继续优化

## 预期效果

- 成功率从20%提升到90%+
- 用户体验更流畅
- 错误信息更友好
- 系统更可靠
