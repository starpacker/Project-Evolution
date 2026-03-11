"""
BaseTool 兼容层
当不在 CowAgent 环境中运行时（如单元测试），提供 BaseTool 和 ToolResult 的最小实现。
在 CowAgent 内运行时，直接 import 真正的 BaseTool。
"""

from enum import Enum
from typing import Any, Optional


class ToolStage(Enum):
    PRE_PROCESS = "pre_process"
    POST_PROCESS = "post_process"


class ToolResult:
    """工具执行结果"""

    def __init__(self, status: str = None, result: Any = None, ext_data: Any = None):
        self.status = status
        self.result = result
        self.ext_data = ext_data

    @staticmethod
    def success(result, ext_data: Any = None):
        return ToolResult(status="success", result=result, ext_data=ext_data)

    @staticmethod
    def fail(result, ext_data: Any = None):
        return ToolResult(status="error", result=result, ext_data=ext_data)

    def __repr__(self):
        return f"ToolResult(status={self.status!r}, result={str(self.result)[:100]!r})"


class BaseTool:
    """
    CowAgent BaseTool 兼容实现。
    在 CowAgent 内，被真正的 BaseTool 替换。
    独立运行时使用此最小实现。
    """

    stage = ToolStage.PRE_PROCESS
    name: str = "base_tool"
    description: str = "Base tool"
    params: dict = {}
    model: Optional[Any] = None
    context: Optional[Any] = None

    @classmethod
    def get_json_schema(cls) -> dict:
        return {
            "name": cls.name,
            "description": cls.description,
            "parameters": cls.params,
        }

    def execute_tool(self, params: dict) -> ToolResult:
        try:
            return self.execute(params)
        except Exception as e:
            return ToolResult.fail(f"Tool execution error: {str(e)}")

    def execute(self, params: dict) -> ToolResult:
        raise NotImplementedError

    def close(self):
        pass


# 尝试导入 CowAgent 的真正 BaseTool
try:
    from agent.tools.base_tool import BaseTool as CowBaseTool
    from agent.tools.base_tool import ToolResult as CowToolResult
    from agent.tools.base_tool import ToolStage as CowToolStage

    # 使用 CowAgent 原版
    BaseTool = CowBaseTool  # type: ignore[misc]
    ToolResult = CowToolResult  # type: ignore[misc]
    ToolStage = CowToolStage  # type: ignore[misc]
    COWAGENT_AVAILABLE = True
except ImportError:
    COWAGENT_AVAILABLE = False
