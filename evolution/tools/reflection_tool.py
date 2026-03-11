"""
EvolutionReflectionTool — 每日反思引擎
定时任务触发，生成每日反思报告，写入Mem0 + SQLite，推送通知。
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional

from evolution.tools.base import BaseTool, ToolResult
from evolution.utils.llm import call_claude_api, extract_json

logger = logging.getLogger("evolution.tools.reflection")


class EvolutionReflectionTool(BaseTool):
    """每日反思工具 — 生成反思报告、检测异常、推送通知"""

    name: str = "evolution_reflection"
    description: str = (
        "生成每日反思报告或周度成长报告。\n\n"
        "使用方法：\n"
        "- 每日反思: action='daily' (可选 date='2026-03-10')\n"
        "- 周度报告: action='weekly'\n"
        "- 查看历史反思: action='get', date='2026-03-10'\n"
        "- 查看最近N天反思: action='recent', days=7\n\n"
        "⚠️ 每日反思通常由定时任务在23:00自动触发，也可手动调用。"
    )
    params: dict = {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["daily", "weekly", "get", "recent"],
                "description": "操作类型",
            },
            "date": {
                "type": "string",
                "description": "日期 YYYY-MM-DD（用于 daily 或 get）",
            },
            "days": {
                "type": "integer",
                "description": "天数（用于 recent）",
            },
        },
        "required": ["action"],
    }

    def __init__(self, config: dict = None):
        self.config = config or {}
        self._db = None
        self._memory_tool = None
        self._notifier = None
        self._llm_client = None

    @property
    def db(self):
        if self._db is None:
            from evolution.db.manager import DatabaseManager
            self._db = DatabaseManager(self.config.get("db_path"))
        return self._db

    @property
    def memory_tool(self):
        if self._memory_tool is None:
            from evolution.tools.memory_tool import EvolutionMemoryTool
            self._memory_tool = EvolutionMemoryTool(self.config)
        return self._memory_tool

    @property
    def notifier(self):
        if self._notifier is None:
            from evolution.notification.router import NotificationRouter
            self._notifier = NotificationRouter()
        return self._notifier

    def execute(self, params: dict) -> ToolResult:
        action = params.get("action")
        try:
            if action == "daily":
                return self._run_daily_reflection(params.get("date"))
            elif action == "weekly":
                return self._run_weekly_report()
            elif action == "get":
                return self._get_reflection(params.get("date"))
            elif action == "recent":
                return self._get_recent(params.get("days", 7))
            else:
                return ToolResult.fail(f"未知操作: {action}")
        except Exception as e:
            logger.error(f"[EvolutionReflection] Error: {e}", exc_info=True)
            return ToolResult.fail(f"反思操作失败: {str(e)}")

    def _run_daily_reflection(self, date: Optional[str] = None) -> ToolResult:
        """执行每日反思"""
        target_date = date or datetime.now().strftime("%Y-%m-%d")

        # Step 1: 收集今日对话
        conversations = self.db.get_conversations_by_date(target_date)
        if not conversations:
            return ToolResult.success(f"📝 {target_date} 没有对话记录，跳过反思。")

        conv_text = "\n".join(
            f"[{c['timestamp']}] {c['role']}: {c['content'][:200]}"
            for c in conversations
        )

        # Step 2: 检索 Mem0 记忆 + 图谱关系
        mem_result = self.memory_tool.execute(
            {"action": "search", "query": f"用户今天的状态和关注点 {target_date}"}
        )
        memories_text = ""
        relations_text = ""
        if mem_result.status == "success" and isinstance(mem_result.result, dict):
            memories_text = "\n".join(
                f"- {m.get('memory', '')}"
                for m in mem_result.result.get("memories", [])
            )
            relations_text = "\n".join(
                f"- {r}" for r in mem_result.result.get("relations", [])
            )

        # Step 3: 生成反思报告
        from evolution.config.prompts import DAILY_REFLECTION_PROMPT
        prompt = DAILY_REFLECTION_PROMPT.format(
            today_conversations=conv_text[:6000],
            existing_memories=memories_text[:2000] or "（无历史记忆）",
            graph_relations=relations_text[:1000] or "（无图谱关系）",
            date=target_date,
        )

        report_json = self._call_llm(prompt)
        if not report_json:
            return ToolResult.fail("LLM 调用失败，无法生成反思报告")

        # Step 4: 解析并存储
        try:
            report = json.loads(self._extract_json(report_json))
        except json.JSONDecodeError:
            logger.error(f"[Reflection] Failed to parse report JSON: {report_json[:200]}")
            # 用原始文本作为报告
            report = {
                "date": target_date,
                "emotional_state": {"primary_emotion": "unknown", "intensity": 0},
                "anomalies": [],
                "tomorrow_suggestion": "继续保持",
                "evening_message": report_json[:200],
            }

        # 存入 SQLite
        self.db.save_reflection(
            date=target_date,
            report_json=json.dumps(report, ensure_ascii=False),
            primary_emotion=report.get("emotional_state", {}).get("primary_emotion", "unknown"),
            emotional_intensity=report.get("emotional_state", {}).get("intensity", 0),
            tomorrow_suggestion=report.get("tomorrow_suggestion", ""),
            evening_message=report.get("evening_message", ""),
        )

        # 存入 Mem0
        reflection_summary = (
            f"[每日反思 {target_date}] "
            f"情绪: {report.get('emotional_state', {}).get('primary_emotion', '?')} "
            f"强度: {report.get('emotional_state', {}).get('intensity', 0)} "
            f"建议: {report.get('tomorrow_suggestion', '')}"
        )
        self.memory_tool.execute(
            {
                "action": "add",
                "content": reflection_summary,
                "metadata": {"type": "daily_reflection", "date": target_date},
            }
        )

        # Step 5: 推送通知
        self._send_reflection_notification(target_date, report)

        return ToolResult.success(
            {
                "date": target_date,
                "emotion": report.get("emotional_state", {}).get("primary_emotion"),
                "tomorrow": report.get("tomorrow_suggestion"),
                "evening_message": report.get("evening_message"),
                "anomaly_count": len(report.get("anomalies", [])),
                "conversations_analyzed": len(conversations),
            }
        )

    def _run_weekly_report(self) -> ToolResult:
        """生成周度报告"""
        today = datetime.now()
        start_date = (today - timedelta(days=7)).strftime("%Y-%m-%d")
        end_date = today.strftime("%Y-%m-%d")

        reflections = self.db.get_reflections_range(start_date, end_date)
        if not reflections:
            return ToolResult.success("本周暂无反思数据，无法生成周报。")

        # 获取用户档案
        profile_result = self.memory_tool.execute({"action": "profile"})
        user_profile = ""
        if profile_result.status == "success" and isinstance(profile_result.result, dict):
            user_profile = profile_result.result.get("profile", "")

        weekly_data = "\n".join(
            f"[{r['date']}] {r.get('report_json', '')[:500]}"
            for r in reflections
        )

        from evolution.config.prompts import WEEKLY_REPORT_PROMPT
        prompt = WEEKLY_REPORT_PROMPT.format(
            weekly_reflections=weekly_data[:8000],
            user_profile=user_profile[:2000] or "（无档案数据）",
        )

        report_text = self._call_llm(prompt)
        if not report_text:
            return ToolResult.fail("LLM 调用失败，无法生成周报")

        # 推送周报
        from evolution.notification.router import Notification, NotifyPriority
        self.notifier.send(
            Notification(
                title=f"📊 周度报告 | {start_date} ~ {end_date}",
                body=report_text,
                priority=NotifyPriority.NORMAL,
                category="report",
                metadata={"week_start": start_date, "week_end": end_date},
            )
        )

        return ToolResult.success(report_text)

    def _get_reflection(self, date: Optional[str] = None) -> ToolResult:
        target_date = date or datetime.now().strftime("%Y-%m-%d")
        reflection = self.db.get_reflection(target_date)
        if not reflection:
            return ToolResult.success(f"没有找到 {target_date} 的反思报告。")
        return ToolResult.success(
            json.dumps(reflection, ensure_ascii=False, indent=2, default=str)
        )

    def _get_recent(self, days: int = 7) -> ToolResult:
        end = datetime.now()
        start = end - timedelta(days=days)
        reflections = self.db.get_reflections_range(
            start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d")
        )
        if not reflections:
            return ToolResult.success(f"最近 {days} 天暂无反思记录。")
        lines = [f"📅 最近 {days} 天的反思:"]
        for r in reflections:
            emotion = r.get("primary_emotion", "?")
            suggestion = r.get("tomorrow_suggestion", "?")
            lines.append(f"  [{r['date']}] 情绪: {emotion} | 建议: {suggestion}")
        return ToolResult.success("\n".join(lines))

    def _send_reflection_notification(self, date: str, report: dict):
        """发送反思通知"""
        from evolution.notification.router import Notification, NotifyPriority

        # 检查异常
        anomalies = report.get("anomalies", [])
        critical_anomalies = [a for a in anomalies if a.get("severity", 0) > 0.6]

        if critical_anomalies:
            for anomaly in critical_anomalies:
                self.notifier.send(
                    Notification(
                        title=f"⚠️ 异常检测 | {date}",
                        body=f"{anomaly['description']}\n建议：{anomaly.get('intervention', '')}",
                        priority=NotifyPriority.CRITICAL,
                        category="anomaly",
                        metadata={"date": date},
                    )
                )

        # 晚间寄语
        evening_msg = report.get("evening_message", report.get("tomorrow_suggestion", ""))
        self.notifier.send(
            Notification(
                title=f"🧠 每日反思 | {date}",
                body=evening_msg,
                priority=NotifyPriority.NORMAL,
                category="reflection",
                metadata={
                    "date": date,
                    "mood": report.get("emotional_state", {}).get("primary_emotion", ""),
                },
            )
        )

    def _call_llm(self, prompt: str) -> Optional[str]:
        """调用 LLM（优先用 CowAgent 的 model，否则直接调 Claude API）"""
        if self.model:
            try:
                response = self.model.generate(prompt)
                return response
            except Exception as e:
                logger.warning(f"[Reflection] CowAgent model failed: {e}")

        return call_claude_api(prompt)

    # Keep _call_claude_api as a thin wrapper for backward compatibility
    def _call_claude_api(self, prompt: str) -> Optional[str]:
        return call_claude_api(prompt)

    @staticmethod
    def _extract_json(text: str) -> str:
        return extract_json(text)
