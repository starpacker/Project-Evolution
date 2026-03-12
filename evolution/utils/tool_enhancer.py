"""
工具调用增强器 - 自动检测和修复工具调用错误
"""

import json
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("evolution.tool_enhancer")

class ToolCallEnhancer:
    """工具调用增强器 - 提供自动重试和错误修复"""
    
    # 工具参数要求
    TOOL_REQUIREMENTS = {
        "evolution_db": {
            "add_schedule": {
                "required": ["content"],
                "optional": ["due_date", "remind_at", "priority", "category"],
                "example": {
                    "action": "add_schedule",
                    "content": "明天下午3点开会",
                    "due_date": "2026-03-13",
                    "priority": "high"
                }
            },
            "add_skill": {
                "required": ["name"],
                "optional": ["category", "level", "target_level"],
                "example": {
                    "action": "add_skill",
                    "name": "Python",
                    "category": "professional",
                    "level": 3
                }
            },
            "add_training": {
                "required": ["skill_name", "modality"],
                "optional": ["topic", "rating", "notes"],
                "example": {
                    "action": "add_training",
                    "skill_name": "Python",
                    "modality": "T2",
                    "topic": "算法练习"
                }
            },
            "upsert_person": {
                "required": ["name"],
                "optional": ["relationship", "notes"],
                "example": {
                    "action": "upsert_person",
                    "name": "张三",
                    "relationship": "同事"
                }
            }
        },
        "evolution_memory": {
            "add": {
                "required": ["content"],
                "optional": ["metadata"],
                "example": {
                    "action": "add",
                    "content": "我喜欢Python编程"
                }
            },
            "search": {
                "required": ["query"],
                "optional": [],
                "example": {
                    "action": "search",
                    "query": "Python"
                }
            }
        }
    }
    
    @classmethod
    def validate_tool_call(cls, tool_name: str, params: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """
        验证工具调用参数
        
        Returns:
            (is_valid, error_message)
        """
        if tool_name not in cls.TOOL_REQUIREMENTS:
            return True, None  # 未知工具，不验证
        
        action = params.get("action")
        if not action:
            return False, f"缺少action参数"
        
        if action not in cls.TOOL_REQUIREMENTS[tool_name]:
            return True, None  # 未知action，不验证
        
        requirements = cls.TOOL_REQUIREMENTS[tool_name][action]
        required_params = requirements["required"]
        
        # 检查必需参数
        missing = [p for p in required_params if p not in params]
        if missing:
            example = requirements["example"]
            return False, (
                f"缺少必需参数: {', '.join(missing)}\n"
                f"正确示例: {json.dumps(example, ensure_ascii=False)}"
            )
        
        return True, None
    
    @classmethod
    def generate_retry_prompt(cls, tool_name: str, action: str, error: str) -> str:
        """生成重试提示"""
        if tool_name in cls.TOOL_REQUIREMENTS and action in cls.TOOL_REQUIREMENTS[tool_name]:
            requirements = cls.TOOL_REQUIREMENTS[tool_name][action]
            example = requirements["example"]
            
            return (
                f"工具调用失败: {error}\n\n"
                f"请按照以下格式重新调用:\n"
                f"```json\n{json.dumps(example, ensure_ascii=False, indent=2)}\n```\n\n"
                f"必需参数: {', '.join(requirements['required'])}\n"
                f"可选参数: {', '.join(requirements['optional'])}"
            )
        else:
            return f"工具调用失败: {error}\n请检查参数格式。"
    
    @classmethod
    def should_auto_retry(cls, error_message: str) -> bool:
        """判断是否应该自动重试"""
        retry_keywords = [
            "需要.*参数",
            "缺少.*参数",
            "参数格式",
            "参数错误",
        ]
        import re
        for keyword in retry_keywords:
            if re.search(keyword, error_message):
                return True
        return False


def enhance_tool_description(tool):
    """增强工具描述，添加更清晰的参数说明"""
    original_desc = tool.description
    
    # 添加醒目的参数要求
    enhanced_desc = original_desc + "\n\n" + """
⚠️ 重要提示：
1. 添加日程时，content参数是必需的（描述日程内容）
2. 添加技能时，name参数是必需的（技能名称）
3. 添加训练记录时，skill_name和modality参数都是必需的
4. 添加人物时，name参数是必需的（人物姓名）
5. 添加记忆时，content参数是必需的（记忆内容）
6. 搜索记忆时，query参数是必需的（搜索关键词）

如果参数不完整，工具调用会失败。请确保提供所有必需参数。
"""
    
    tool.description = enhanced_desc
    return tool
