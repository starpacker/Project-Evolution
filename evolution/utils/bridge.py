"""
CowAgent 集成桥接器
将 Evolution 的 4 个自定义工具注册到 CowAgent 的 ToolManager 中。
同时设置定时任务和 POST_PROCESS hook。
"""

import logging
from typing import List

logger = logging.getLogger("evolution.bridge")


def get_evolution_tools() -> list:
    """返回所有 Evolution 工具实例"""
    from evolution.tools.memory_tool import EvolutionMemoryTool
    from evolution.tools.db_tool import EvolutionDBTool
    from evolution.tools.reflection_tool import EvolutionReflectionTool
    from evolution.tools.intelligence_tool import EvolutionIntelligenceTool

    return [
        EvolutionMemoryTool(),
        EvolutionDBTool(),
        EvolutionReflectionTool(),
        EvolutionIntelligenceTool(),
    ]


def register_with_cowagent():
    """
    在 CowAgent 的 ToolManager 中注册 Evolution 工具。

    用法 1：在 CowAgent 启动脚本中调用：
        from evolution.utils.bridge import register_with_cowagent
        register_with_cowagent()

    用法 2：在 CowAgent config.json 的 tools 配置中引用工具名称。
    """
    try:
        from agent.tools.tool_manager import ToolManager
        from evolution.tools.memory_tool import EvolutionMemoryTool
        from evolution.tools.db_tool import EvolutionDBTool
        from evolution.tools.reflection_tool import EvolutionReflectionTool
        from evolution.tools.intelligence_tool import EvolutionIntelligenceTool

        tm = ToolManager()

        # 注册工具类
        for tool_cls in [
            EvolutionMemoryTool,
            EvolutionDBTool,
            EvolutionReflectionTool,
            EvolutionIntelligenceTool,
        ]:
            tm.tool_classes[tool_cls.name] = tool_cls
            logger.info(f"[Bridge] Registered tool: {tool_cls.name}")

        logger.info("[Bridge] All Evolution tools registered with CowAgent")
        return True
    except ImportError as e:
        logger.warning(f"[Bridge] CowAgent not available: {e}")
        return False


def setup_scheduled_tasks():
    """
    使用 CowAgent 的 SchedulerTool 创建 Evolution 的定时任务。

    - 23:00 每日反思
    - 08:00 早间情报
    - 周日 20:00 周报
    """
    from evolution.config.settings import SCHEDULE_CONFIG

    try:
        from agent.tools.scheduler.scheduler_tool import SchedulerTool

        scheduler = SchedulerTool()

        tasks = [
            {
                "action": "create",
                "name": "evolution_daily_reflection",
                "ai_task": (
                    "你是Evolution导师。现在是每日反思时间。"
                    "请使用 evolution_reflection 工具（action='daily'）生成今日反思报告。"
                    "如果有严重异常（severity > 0.6），请在回复中强调。"
                ),
                "schedule_type": "cron",
                "schedule_value": SCHEDULE_CONFIG["daily_reflection"]["cron"],
            },
            {
                "action": "create",
                "name": "evolution_morning_briefing",
                "ai_task": (
                    "你是Evolution情报收集者。现在是早间情报时间。"
                    "请使用 evolution_intelligence 工具（action='briefing'）获取今日情报。"
                    "然后使用 evolution_db 工具（action='list_schedule'）获取今日日程。"
                    "将情报和日程组合，以导师口吻回复。"
                ),
                "schedule_type": "cron",
                "schedule_value": SCHEDULE_CONFIG["morning_briefing"]["cron"],
            },
            {
                "action": "create",
                "name": "evolution_weekly_report",
                "ai_task": (
                    "你是Evolution导师。现在是每周成长报告时间。"
                    "请使用 evolution_reflection 工具（action='weekly'）生成周度报告。"
                ),
                "schedule_type": "cron",
                "schedule_value": SCHEDULE_CONFIG["weekly_report"]["cron"],
            },
        ]

        for task in tasks:
            try:
                result = scheduler.execute(task)
                logger.info(f"[Bridge] Scheduled task created: {task['name']} → {result.status}")
            except Exception as e:
                logger.error(f"[Bridge] Failed to create task {task['name']}: {e}")

        logger.info("[Bridge] All scheduled tasks configured")
        return True
    except ImportError:
        logger.warning("[Bridge] CowAgent SchedulerTool not available")
        return False


def get_system_prompt() -> str:
    """获取五角色统一 System Prompt"""
    from evolution.config.prompts import SYSTEM_PROMPT
    return SYSTEM_PROMPT


def log_conversation(role: str, content: str):
    """记录对话到 SQLite（供每日反思使用）"""
    try:
        from evolution.db.manager import DatabaseManager
        db = DatabaseManager()
        db.log_conversation(role, content)
    except Exception as e:
        logger.error(f"[Bridge] Failed to log conversation: {e}")
