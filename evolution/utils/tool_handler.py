"""
改进的工具调用处理模块
支持JSON格式、参数验证和自动重试
"""

import json
import re
import logging
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger("evolution.tool_handler")

# 工具参数要求定义
TOOL_PARAM_REQUIREMENTS = {
    "evolution_db": {
        "add_schedule": {
            "required": ["content"],
            "optional": ["due_date", "remind_at", "priority", "category"],
            "example": '{"action": "add_schedule", "content": "明天下午3点开会", "due_date": "2026-03-13", "priority": "high"}'
        },
        "add_skill": {
            "required": ["name"],
            "optional": ["category", "level", "target_level"],
            "example": '{"action": "add_skill", "name": "Python", "category": "professional", "level": 3}'
        },
        "add_training": {
            "required": ["skill_name", "modality"],
            "optional": ["topic", "rating", "notes"],
            "example": '{"action": "add_training", "skill_name": "Python", "modality": "T2", "topic": "算法练习"}'
        },
        "upsert_person": {
            "required": ["name"],
            "optional": ["relationship", "notes"],
            "example": '{"action": "upsert_person", "name": "张三", "relationship": "同事"}'
        }
    },
    "evolution_memory": {
        "add": {
            "required": ["content"],
            "optional": ["metadata"],
            "example": '{"action": "add", "content": "我喜欢Python编程"}'
        },
        "search": {
            "required": ["query"],
            "optional": [],
            "example": '{"action": "search", "query": "Python"}'
        }
    }
}

def parse_tool_calls_json(text: str) -> List[Dict]:
    """
    解析JSON格式的工具调用
    
    格式: [TOOL:tool_name]{"param": "value"}[/TOOL]
    """
    pattern = r'\[TOOL:(\w+)\](.*?)\[/TOOL\]'
    matches = re.findall(pattern, text, re.DOTALL)
    
    tool_calls = []
    for tool_name, params_str in matches:
        try:
            params = json.loads(params_str.strip())
            tool_calls.append({
                "name": tool_name,
                "params": params
            })
        except json.JSONDecodeError as e:
            logger.error(f"JSON解析失败: {params_str}, 错误: {e}")
            # 尝试修复常见JSON错误
            try:
                # 修复单引号
                fixed = params_str.replace("'", '"')
                params = json.loads(fixed)
                tool_calls.append({
                    "name": tool_name,
                    "params": params
                })
            except:
                logger.error(f"JSON修复失败")
    
    return tool_calls

def validate_tool_params(tool_name: str, params: Dict) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    验证工具参数
    
    Returns:
        (is_valid, error_message, retry_hint)
    """
    if tool_name not in TOOL_PARAM_REQUIREMENTS:
        return True, None, None
    
    action = params.get("action")
    if not action:
        return False, "缺少action参数", None
    
    if action not in TOOL_PARAM_REQUIREMENTS[tool_name]:
        return True, None, None  # 未知action，不验证
    
    requirements = TOOL_PARAM_REQUIREMENTS[tool_name][action]
    required_params = requirements["required"]
    
    # 检查必需参数
    missing = [p for p in required_params if p not in params or not params[p]]
    if missing:
        error_msg = f"缺少必需参数: {', '.join(missing)}"
        retry_hint = f"请按照以下格式重新调用:\n[TOOL:{tool_name}]\n{requirements['example']}\n[/TOOL]"
        return False, error_msg, retry_hint
    
    return True, None, None

def execute_tool_with_validation(tool_name: str, params: Dict, tool_instances: Dict) -> Dict:
    """
    执行工具调用并验证参数
    
    Args:
        tool_name: 工具名称
        params: 参数字典
        tool_instances: 工具实例字典 {"evolution_db": db_tool, ...}
    
    Returns:
        {"success": bool, "result": str, "error": str, "retry_hint": str}
    """
    # 1. 验证参数
    is_valid, error_msg, retry_hint = validate_tool_params(tool_name, params)
    if not is_valid:
        logger.warning(f"工具参数验证失败: {tool_name}, {error_msg}")
        return {
            "success": False,
            "result": "",
            "error": error_msg,
            "retry_hint": retry_hint
        }
    
    # 2. 执行工具
    try:
        tool = tool_instances.get(tool_name)
        if not tool:
            return {
                "success": False,
                "result": "",
                "error": f"未知工具: {tool_name}",
                "retry_hint": None
            }
        
        result = tool.execute(params)
        
        if result.status == "success":
            return {
                "success": True,
                "result": result.result,
                "error": None,
                "retry_hint": None
            }
        else:
            # 工具执行失败，检查是否需要重试
            error_msg = result.result
            retry_hint = None
            
            # 生成重试提示
            if "需要" in error_msg and "参数" in error_msg:
                action = params.get("action")
                if action and tool_name in TOOL_PARAM_REQUIREMENTS:
                    if action in TOOL_PARAM_REQUIREMENTS[tool_name]:
                        example = TOOL_PARAM_REQUIREMENTS[tool_name][action]["example"]
                        retry_hint = f"请按照以下格式重新调用:\n[TOOL:{tool_name}]\n{example}\n[/TOOL]"
            
            return {
                "success": False,
                "result": "",
                "error": error_msg,
                "retry_hint": retry_hint
            }
    
    except Exception as e:
        logger.error(f"工具执行异常: {tool_name}, {e}")
        return {
            "success": False,
            "result": "",
            "error": str(e),
            "retry_hint": None
        }

def format_tool_result(tool_name: str, result: Dict) -> str:
    """格式化工具执行结果"""
    if result["success"]:
        return result["result"]
    else:
        # 不直接显示错误给用户，而是记录日志
        logger.error(f"工具调用失败: {tool_name}, {result['error']}")
        
        # 返回友好的错误提示
        if result["retry_hint"]:
            return f"⚠️ 工具调用需要修正\n\n{result['retry_hint']}"
        else:
            return f"⚠️ {result['error']}"

# 添加到SYSTEM_PROMPT的工具使用说明
TOOL_USAGE_GUIDE = """

---

# 工具调用

格式: [TOOL:工具名]{"action": "操作名", ...参数}[/TOOL]

## evolution_db — 所有 action 列表（必须使用以下精确名称）

| action | 用途 | 必需参数 |
|--------|------|----------|
| add_schedule | 添加日程/提醒 | content |
| list_schedule | 查询日程/待办 | (无) |
| complete_schedule | 完成日程 | id |
| delete_schedule | 删除日程 | id |
| add_skill | 添加技能 | name |
| list_skills | 查询技能列表 | (无) |
| update_skill | 更新技能等级 | name, level |
| stale_skills | 查看久未训练技能 | (无) |
| upsert_person | 添加/更新人物 | name |
| get_person | 查询人物 | name |
| list_persons | 列出所有人物 | (无) |
| add_training | 添加训练记录 | skill_name, modality |
| list_trainings | 查询训练记录 | (无) |
| add_model | 添加心智模型 | name |
| list_models | 列出心智模型 | (无) |
| stats | 查看数据统计 | (无) |

## evolution_memory — 所有 action 列表

| action | 用途 | 必需参数 |
|--------|------|----------|
| add | 添加记忆 | content |
| search | 搜索记忆 | query |
| profile | 获取用户档案 | (无) |

## 示例

用户说"帮我记住明天下午3点开会":
[TOOL:evolution_db]{"action": "add_schedule", "content": "明天下午3点开会", "due_date": "2026-03-13", "priority": "high"}[/TOOL]

用户说"我今天有什么安排":
[TOOL:evolution_db]{"action": "list_schedule"}[/TOOL]

用户说"我掌握了哪些技能":
[TOOL:evolution_db]{"action": "list_skills"}[/TOOL]

用户说"给我看看数据统计":
[TOOL:evolution_db]{"action": "stats"}[/TOOL]

用户说"我已经完成了编号1的任务":
[TOOL:evolution_db]{"action": "complete_schedule", "id": 1}[/TOOL]

用户说"记住我喜欢Python":
[TOOL:evolution_memory]{"action": "add", "content": "我喜欢Python"}[/TOOL]

用户说"我之前说过什么研究方向":
[TOOL:evolution_memory]{"action": "search", "query": "研究方向"}[/TOOL]

⚠️ 不要编造不存在的 action 名称。必须使用上表中的精确名称。
⚠️ 不要说"已经记住了"而不调用工具。必须真正调用工具才能保存数据。
"""
