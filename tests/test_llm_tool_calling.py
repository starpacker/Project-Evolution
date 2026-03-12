#!/usr/bin/env python3
"""
LLM 工具调用准确性测试
模拟真实对话场景，测试 LLM 是否能正确生成 [TOOL:name]{json}[/TOOL] 格式
"""

import os
import sys
import json
import re
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from evolution.utils.llm import call_claude_api
from evolution.config.prompts import SYSTEM_PROMPT
from evolution.utils.tool_handler import TOOL_USAGE_GUIDE, parse_tool_calls_json


def get_system_prompt():
    """构建包含工具说明的系统提示词"""
    return SYSTEM_PROMPT + TOOL_USAGE_GUIDE


# 测试用例定义
TEST_CASES = [
    {
        "id": 1,
        "description": "添加日程 - 明确的时间任务",
        "user_input": "帮我记住：明天下午3点要开会讨论项目进度",
        "expect_tool": "evolution_db",
        "expect_action": "add_schedule",
        "expect_has_tool_call": True,
        "required_params": ["content"],
    },
    {
        "id": 2,
        "description": "查询日程 - 询问待办",
        "user_input": "我今天有什么安排？",
        "expect_tool": "evolution_db",
        "expect_action": "list_schedule",
        "expect_has_tool_call": True,
        "required_params": [],
    },
    {
        "id": 3,
        "description": "添加记忆 - 个人偏好",
        "user_input": "记住：我最近在研究强化学习，特别是RLHF方向",
        "expect_tool": "evolution_memory",
        "expect_action": "add",
        "expect_has_tool_call": True,
        "required_params": ["content"],
    },
    {
        "id": 4,
        "description": "搜索记忆 - 回忆过去",
        "user_input": "我之前跟你说过关于我的研究方向吗？",
        "expect_tool": "evolution_memory",
        "expect_action": "search",
        "expect_has_tool_call": True,
        "required_params": ["query"],
    },
    {
        "id": 5,
        "description": "添加技能",
        "user_input": "帮我记录一个新技能：深度学习，目前等级3",
        "expect_tool": "evolution_db",
        "expect_action": "add_skill",
        "expect_has_tool_call": True,
        "required_params": ["name"],
    },
    {
        "id": 6,
        "description": "查询技能列表",
        "user_input": "我目前掌握了哪些技能？",
        "expect_tool": "evolution_db",
        "expect_action": "list_skills",
        "expect_has_tool_call": True,
        "required_params": [],
    },
    {
        "id": 7,
        "description": "添加人物档案",
        "user_input": "我今天和导师李教授讨论了论文方向",
        "expect_tool": "evolution_db",
        "expect_action": "upsert_person",
        "expect_has_tool_call": True,
        "required_params": ["name"],
    },
    {
        "id": 8,
        "description": "纯聊天 - 不应调用工具",
        "user_input": "你好，今天天气不错",
        "expect_tool": None,
        "expect_action": None,
        "expect_has_tool_call": False,
        "required_params": [],
    },
    {
        "id": 9,
        "description": "完成日程",
        "user_input": "我已经完成了编号1的任务",
        "expect_tool": "evolution_db",
        "expect_action": "complete_schedule",
        "expect_has_tool_call": True,
        "required_params": ["id"],
    },
    {
        "id": 10,
        "description": "查看统计",
        "user_input": "给我看看我的数据统计",
        "expect_tool": "evolution_db",
        "expect_action": "stats",
        "expect_has_tool_call": True,
        "required_params": [],
    },
]


def analyze_response(response, case):
    """分析 LLM 响应"""
    result = {
        "has_tool_call": False,
        "tool_name": None,
        "action": None,
        "params": {},
        "is_valid_json": False,
        "has_required_params": False,
        "raw_response": response[:500],
    }

    # 用 tool_handler 的解析器
    tool_calls = parse_tool_calls_json(response)

    # 也用正则兜底（旧格式兼容）
    if not tool_calls:
        pattern = r'\[TOOL:(\w+)\](.*?)\[/TOOL\]'
        matches = re.findall(pattern, response, re.DOTALL)
        for tool_name, params_str in matches:
            params_str = params_str.strip()
            try:
                params = json.loads(params_str)
                tool_calls.append({"name": tool_name, "params": params})
            except json.JSONDecodeError:
                tool_calls.append({"name": tool_name, "params": {"_raw": params_str}})

    if tool_calls:
        tc = tool_calls[0]
        result["has_tool_call"] = True
        result["tool_name"] = tc["name"]
        result["params"] = tc.get("params", {})
        result["action"] = result["params"].get("action")
        result["is_valid_json"] = isinstance(tc.get("params"), dict) and "_raw" not in tc.get("params", {})

        # 检查必需参数
        if case["required_params"]:
            result["has_required_params"] = all(
                p in result["params"] for p in case["required_params"]
            )
        else:
            result["has_required_params"] = True

    return result


def evaluate_case(case, analysis):
    """评估单个测试用例"""
    scores = {
        "tool_call_presence": False,
        "correct_tool": False,
        "correct_action": False,
        "valid_json": False,
        "has_required_params": False,
    }

    # 1. 是否正确判断需要/不需要调用工具
    if case["expect_has_tool_call"]:
        scores["tool_call_presence"] = analysis["has_tool_call"]
    else:
        scores["tool_call_presence"] = not analysis["has_tool_call"]

    if not case["expect_has_tool_call"]:
        # 不需要工具调用的场景，只检查是否正确不调用
        scores["correct_tool"] = True
        scores["correct_action"] = True
        scores["valid_json"] = True
        scores["has_required_params"] = True
        return scores

    # 2. 工具名称是否正确
    scores["correct_tool"] = analysis["tool_name"] == case["expect_tool"]

    # 3. action 是否正确
    scores["correct_action"] = analysis["action"] == case["expect_action"]

    # 4. JSON 格式是否正确
    scores["valid_json"] = analysis["is_valid_json"]

    # 5. 必需参数是否齐全
    scores["has_required_params"] = analysis["has_required_params"]

    return scores


def run_test(case):
    """运行单个测试"""
    print(f"\n{'='*60}")
    print(f"测试 #{case['id']}: {case['description']}")
    print(f"用户输入: \"{case['user_input']}\"")
    print(f"期望: tool={case['expect_tool']}, action={case['expect_action']}")

    system_prompt = get_system_prompt()
    prompt = f"用户最新消息：{case['user_input']}\n\n请回复用户。如果需要使用工具，请使用 [TOOL:name]{{json}}[/TOOL] 格式。"

    response = call_claude_api(prompt=prompt, system=system_prompt, max_tokens=1024)

    if not response:
        print("❌ LLM 无响应")
        return None

    print(f"\nLLM 响应 (前300字):\n{response[:300]}")

    analysis = analyze_response(response, case)
    scores = evaluate_case(case, analysis)

    print(f"\n--- 分析结果 ---")
    print(f"检测到工具调用: {'是' if analysis['has_tool_call'] else '否'}")
    if analysis["has_tool_call"]:
        print(f"工具名称: {analysis['tool_name']}")
        print(f"Action: {analysis['action']}")
        print(f"JSON有效: {'是' if analysis['is_valid_json'] else '否'}")
        print(f"参数: {json.dumps(analysis['params'], ensure_ascii=False)[:200]}")

    print(f"\n--- 评分 ---")
    for k, v in scores.items():
        print(f"  {'✅' if v else '❌'} {k}")

    all_pass = all(scores.values())
    print(f"\n{'✅ 通过' if all_pass else '❌ 失败'}")

    return scores


def main():
    print("=" * 60)
    print("LLM 工具调用准确性测试")
    print("模拟真实对话，测试 [TOOL:name]{json}[/TOOL] 格式")
    print("=" * 60)
    print(f"测试用例数: {len(TEST_CASES)}")

    all_scores = []
    start = time.time()

    for case in TEST_CASES:
        scores = run_test(case)
        if scores:
            all_scores.append({"id": case["id"], "desc": case["description"], "scores": scores})
        else:
            all_scores.append({"id": case["id"], "desc": case["description"], "scores": None})
        time.sleep(0.5)  # 避免 API 限流

    elapsed = time.time() - start

    # 汇总
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)

    total = len(all_scores)
    metrics = {
        "tool_call_presence": 0,
        "correct_tool": 0,
        "correct_action": 0,
        "valid_json": 0,
        "has_required_params": 0,
    }
    full_pass = 0

    for item in all_scores:
        s = item["scores"]
        if s is None:
            status = "⚠️ 无响应"
        elif all(s.values()):
            status = "✅ 通过"
            full_pass += 1
            for k in metrics:
                metrics[k] += 1
        else:
            status = "❌ 失败"
            for k in metrics:
                if s.get(k):
                    metrics[k] += 1
        print(f"{status} #{item['id']}: {item['desc']}")

    responded = sum(1 for x in all_scores if x["scores"] is not None)

    print(f"\n--- 详细指标 ---")
    for k, v in metrics.items():
        pct = (v / responded * 100) if responded > 0 else 0
        print(f"  {k}: {v}/{responded} ({pct:.0f}%)")

    overall = (full_pass / total * 100) if total > 0 else 0
    print(f"\n完全通过率: {full_pass}/{total} ({overall:.0f}%)")
    print(f"耗时: {elapsed:.1f}s")

    if overall >= 80:
        print("\n🎉 工具调用准确率良好")
    elif overall >= 60:
        print("\n⚠️  工具调用存在一定幻觉问题，需要优化 prompt")
    else:
        print("\n❌ 工具调用准确率较低，存在严重幻觉问题，需要重点优化")

    return 0 if overall >= 80 else 1


if __name__ == "__main__":
    sys.exit(main())
