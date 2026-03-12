#!/usr/bin/env python3
"""
端到端测试：验证 LLM 工具调用是否正常工作
测试 Function Calling 模式和文本解析回退模式
"""
import sys
import os
import json
import logging

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("test_e2e")

# 确保项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # .env will be loaded by settings.py if available

def test_1_basic_llm_connection():
    """测试1: 基本 LLM 连接"""
    print("\n" + "="*60)
    print("测试1: 基本 LLM 连接（无工具）")
    print("="*60)
    
    from evolution.utils.llm import call_claude_api
    
    result = call_claude_api(prompt="请用一句话回答：1+1等于几？", max_tokens=100)
    
    if result:
        print(f"✅ LLM 连接成功")
        print(f"   回复: {result[:100]}")
        return True
    else:
        print(f"❌ LLM 连接失败")
        return False


def test_2_function_calling_api():
    """测试2: Function Calling API 支持"""
    print("\n" + "="*60)
    print("测试2: Function Calling API（tools 参数）")
    print("="*60)
    
    from evolution.utils.llm import call_llm_with_tools
    from evolution.chat.web_chat import OPENAI_TOOLS
    
    messages = [{"role": "user", "content": "我今天有什么待办事项？"}]
    
    result = call_llm_with_tools(
        messages=messages,
        tools=OPENAI_TOOLS,
        system="你是一个助手，需要使用工具查询用户的待办事项。",
        max_tokens=1024,
    )
    
    if result is None:
        print(f"⚠️ Function Calling 不被支持（API 返回 None）")
        print(f"   将使用文本解析回退模式")
        return False
    
    print(f"✅ Function Calling API 调用成功")
    print(f"   content: {(result.get('content') or '')[:100]}")
    print(f"   tool_calls: {result.get('tool_calls')}")
    
    if result.get('tool_calls'):
        for tc in result['tool_calls']:
            print(f"   -> 工具: {tc['name']}, 参数: {json.dumps(tc['arguments'], ensure_ascii=False)}")
        return True
    else:
        print(f"   （LLM 未调用工具，但 API 支持 tools 参数）")
        return True


def test_3_text_parsing_fallback():
    """测试3: 文本解析回退模式"""
    print("\n" + "="*60)
    print("测试3: 文本解析回退模式")
    print("="*60)
    
    from evolution.utils.llm import call_claude_api
    from evolution.utils.tool_handler import TOOL_USAGE_GUIDE
    from evolution.chat.web_chat import parse_tool_calls
    from evolution.utils.tool_handler import parse_tool_calls_json
    
    system = f"""你是一个助手。当用户需要查询待办事项时，必须调用工具。
{TOOL_USAGE_GUIDE}

现在请调用工具来回答用户的问题。"""
    
    messages = [{"role": "user", "content": "我今天有什么待办事项？请调用工具查询。"}]
    
    result = call_claude_api(prompt="", system=system, max_tokens=1024, messages=messages)
    
    if not result:
        print(f"❌ LLM 调用失败")
        return False
    
    print(f"   LLM 原始回复:\n   {result[:300]}")
    
    # 尝试解析工具调用
    tool_calls_json = parse_tool_calls_json(result)
    tool_calls_old = parse_tool_calls(result)
    
    if tool_calls_json:
        print(f"\n✅ JSON 格式工具调用解析成功: {len(tool_calls_json)} 个")
        for tc in tool_calls_json:
            print(f"   -> 工具: {tc['name']}, 参数: {json.dumps(tc['params'], ensure_ascii=False)}")
        return True
    elif tool_calls_old:
        print(f"\n✅ 旧格式工具调用解析成功: {len(tool_calls_old)} 个")
        for tc in tool_calls_old:
            print(f"   -> 工具: {tc['name']}, 参数: {tc['params'][:100]}")
        return True
    else:
        print(f"\n⚠️ LLM 回复中未找到工具调用标记")
        return False


def test_4_full_process_message():
    """测试4: 完整的 process_message 流程"""
    print("\n" + "="*60)
    print("测试4: 完整 process_message 流程")
    print("="*60)
    
    from evolution.chat.web_chat import process_message, conversation_history, _use_function_calling
    
    # 清空历史
    conversation_history.clear()
    
    # 4a: 简单对话（不需要工具）
    print("\n--- 4a: 简单对话 ---")
    r1 = process_message("你好，你是谁？")
    print(f"   回复: {r1[:200]}")
    
    from evolution.chat import web_chat
    print(f"   模式: {'Function Calling' if web_chat._use_function_calling else '文本解析'}")
    
    # 4b: 需要工具的对话（查询待办）
    print("\n--- 4b: 查询待办事项 ---")
    r2 = process_message("我有什么待办事项？")
    print(f"   回复: {r2[:300]}")
    
    # 4c: 需要工具的对话（添加日程）
    print("\n--- 4c: 添加日程 ---")
    r3 = process_message("帮我记住后天下午3点要开组会")
    print(f"   回复: {r3[:300]}")
    
    # 4d: 查询确认
    print("\n--- 4d: 确认日程已添加 ---")
    r4 = process_message("帮我看看我现在所有的日程安排")
    print(f"   回复: {r4[:300]}")
    
    # 检查结果
    success = True
    if "不可用" in r1 or "失败" in r1:
        print("\n❌ 简单对话失败")
        success = False
    if "不可用" in r2:
        print("\n❌ 查询待办失败")
        success = False
    
    if success:
        print(f"\n✅ 完整流程测试通过")
    
    return success


if __name__ == "__main__":
    print("="*60)
    print("ProjectEvolution 工具调用端到端测试")
    print("="*60)
    
    results = {}
    
    # 测试1: 基本连接
    results["basic_connection"] = test_1_basic_llm_connection()
    
    if not results["basic_connection"]:
        print("\n❌ 基本连接失败，跳过后续测试")
        sys.exit(1)
    
    # 测试2: Function Calling
    results["function_calling"] = test_2_function_calling_api()
    
    # 测试3: 文本解析
    results["text_parsing"] = test_3_text_parsing_fallback()
    
    # 测试4: 完整流程
    results["full_process"] = test_4_full_process_message()
    
    # 汇总
    print("\n" + "="*60)
    print("测试汇总")
    print("="*60)
    for name, passed in results.items():
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"  {status} - {name}")
    
    all_passed = all(results.values())
    print(f"\n{'✅ 所有测试通过!' if all_passed else '⚠️ 部分测试失败'}")
    sys.exit(0 if all_passed else 1)
