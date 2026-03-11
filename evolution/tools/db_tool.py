"""
EvolutionDBTool — SQLite 结构化数据操作
CowAgent 工具接口，管理日程、技能树、人物档案、训练记录。
"""

import json
import logging
from typing import Any, Dict

from evolution.db.manager import DatabaseManager
from evolution.tools.base import BaseTool, ToolResult

logger = logging.getLogger("evolution.tools.db")


class EvolutionDBTool(BaseTool):
    """Evolution 结构化数据工具 — 管理日程、技能、人物、训练"""

    name: str = "evolution_db"
    description: str = (
        "管理用户的结构化数据：日程、技能树、人物档案、训练记录。\n\n"
        "使用方法：\n"
        "日程管理:\n"
        "  - action='add_schedule', content='任务', due_date='2026-03-15', priority='high', category='professional'\n"
        "  - action='list_schedule' (可选 date='2026-03-10' 或 filter='pending'|'overdue')\n"
        "  - action='complete_schedule', id=1\n"
        "  - action='delete_schedule', id=1\n\n"
        "技能管理:\n"
        "  - action='add_skill', name='Python', category='professional', level=3, target_level=8\n"
        "  - action='list_skills' (可选 category='thinking')\n"
        "  - action='update_skill', name='Python', level=4, xp_delta=10\n"
        "  - action='stale_skills' (超过14天未训练的技能)\n\n"
        "人物管理:\n"
        "  - action='upsert_person', name='小李', relationship='同事'\n"
        "  - action='get_person', name='小李'\n"
        "  - action='list_persons'\n\n"
        "训练记录:\n"
        "  - action='add_training', skill_name='批判性思维', modality='T2', topic='内卷辩论', rating='good'\n"
        "  - action='list_trainings' (可选 skill_name='批判性思维')\n\n"
        "心智模型:\n"
        "  - action='add_model', name='沉没成本', source_domain='经济学', description='...'\n"
        "  - action='list_models'\n\n"
        "统计:\n"
        "  - action='stats'\n"
    )

    params: dict = {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": [
                    "add_schedule", "list_schedule", "complete_schedule", "delete_schedule",
                    "add_skill", "list_skills", "update_skill", "stale_skills",
                    "upsert_person", "get_person", "list_persons",
                    "add_training", "list_trainings",
                    "add_model", "list_models",
                    "stats",
                ],
                "description": "操作类型",
            },
            "content": {"type": "string", "description": "日程内容"},
            "due_date": {"type": "string", "description": "截止日期 YYYY-MM-DD 或 YYYY-MM-DDTHH:MM:SS"},
            "remind_at": {"type": "string", "description": "提醒时间"},
            "priority": {"type": "string", "enum": ["high", "medium", "low"]},
            "category": {"type": "string"},
            "context": {"type": "string", "description": "日程来源上下文"},
            "id": {"type": "integer", "description": "记录ID"},
            "date": {"type": "string", "description": "日期 YYYY-MM-DD"},
            "filter": {"type": "string", "description": "过滤器"},
            "name": {"type": "string", "description": "名称（技能/人物/模型）"},
            "level": {"type": "integer", "description": "技能等级"},
            "target_level": {"type": "integer", "description": "目标等级"},
            "xp_delta": {"type": "integer", "description": "经验值增量"},
            "weakness": {"type": "string", "description": "薄弱点描述"},
            "relationship": {"type": "string", "description": "关系类型"},
            "skill_name": {"type": "string", "description": "技能名称"},
            "modality": {"type": "string", "enum": ["T1","T2","T3","T4","T5","T6","T7"]},
            "topic": {"type": "string", "description": "训练主题"},
            "rating": {"type": "string", "description": "评分"},
            "insight": {"type": "string", "description": "训练收获"},
            "source_domain": {"type": "string", "description": "来源领域"},
            "description": {"type": "string", "description": "描述"},
        },
        "required": ["action"],
    }

    def __init__(self, config: dict = None):
        self.config = config or {}
        self._db = None

    @property
    def db(self) -> DatabaseManager:
        if self._db is None:
            db_path = self.config.get("db_path")
            self._db = DatabaseManager(db_path)
        return self._db

    def execute(self, params: dict) -> ToolResult:
        action = params.get("action")
        try:
            handler = getattr(self, f"_handle_{action}", None)
            if handler:
                return handler(params)
            else:
                return ToolResult.fail(f"未知操作: {action}")
        except Exception as e:
            logger.error(f"[EvolutionDB] Error in {action}: {e}")
            return ToolResult.fail(f"数据库操作失败: {str(e)}")

    # ── 日程 ──────────────────────────────────
    def _handle_add_schedule(self, p: dict) -> ToolResult:
        content = p.get("content")
        if not content:
            return ToolResult.fail("日程需要 content 参数")
        sid = self.db.add_schedule(
            content=content,
            due_date=p.get("due_date"),
            remind_at=p.get("remind_at"),
            priority=p.get("priority", "medium"),
            category=p.get("category"),
            context=p.get("context"),
        )
        return ToolResult.success(f"✅ 日程已添加 (ID={sid}): {content}")

    def _handle_list_schedule(self, p: dict) -> ToolResult:
        date = p.get("date")
        filt = p.get("filter", "pending")
        if date:
            items = self.db.get_schedule_by_date(date)
        elif filt == "overdue":
            items = self.db.get_overdue_schedules()
        else:
            items = self.db.get_pending_schedules()

        if not items:
            return ToolResult.success("📋 当前没有待办日程。")

        lines = [f"📋 共 {len(items)} 条日程:"]
        for i, item in enumerate(items, 1):
            priority_icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(
                item.get("priority", "medium"), "⚪"
            )
            due = item.get("due_date", "无截止时间")
            lines.append(f"  {i}. {priority_icon} [{item['id']}] {item['content']} (截止: {due})")
        return ToolResult.success("\n".join(lines))

    def _handle_complete_schedule(self, p: dict) -> ToolResult:
        sid = p.get("id")
        if not sid:
            return ToolResult.fail("需要 id 参数")
        ok = self.db.complete_schedule(sid)
        return ToolResult.success(f"✅ 日程 #{sid} 已完成") if ok else ToolResult.fail(f"日程 #{sid} 不存在")

    def _handle_delete_schedule(self, p: dict) -> ToolResult:
        sid = p.get("id")
        if not sid:
            return ToolResult.fail("需要 id 参数")
        ok = self.db.delete_schedule(sid)
        return ToolResult.success(f"✅ 日程 #{sid} 已删除") if ok else ToolResult.fail(f"日程 #{sid} 不存在")

    # ── 技能 ──────────────────────────────────
    def _handle_add_skill(self, p: dict) -> ToolResult:
        name = p.get("name")
        category = p.get("category", "professional")
        if not name:
            return ToolResult.fail("技能需要 name 参数")
        sid = self.db.add_skill(
            name=name, category=category,
            level=p.get("level", 1),
            target_level=p.get("target_level", 5),
            weakness=p.get("weakness"),
        )
        return ToolResult.success(f"✅ 技能已添加: {name} (Lv.{p.get('level', 1)})")

    def _handle_list_skills(self, p: dict) -> ToolResult:
        items = self.db.list_skills(category=p.get("category"))
        if not items:
            return ToolResult.success("🏋️ 暂无技能记录。")
        lines = [f"🏋️ 共 {len(items)} 项技能:"]
        for s in items:
            bar = "█" * s["level"] + "░" * (10 - s["level"])
            last = s.get("last_trained", "从未训练")
            lines.append(f"  [{s['category']}] {s['name']}: {bar} Lv.{s['level']}/{s['target_level']} (上次: {last})")
        return ToolResult.success("\n".join(lines))

    def _handle_update_skill(self, p: dict) -> ToolResult:
        name = p.get("name")
        if not name:
            return ToolResult.fail("需要 name 参数")
        level = p.get("level")
        if level is None:
            return ToolResult.fail("需要 level 参数")
        ok = self.db.update_skill_level(name, level, p.get("xp_delta", 0))
        return ToolResult.success(f"✅ 技能 {name} 已更新到 Lv.{level}") if ok else ToolResult.fail(f"技能 {name} 不存在")

    def _handle_stale_skills(self, p: dict) -> ToolResult:
        items = self.db.get_stale_skills(days=14)
        if not items:
            return ToolResult.success("所有技能都在活跃训练中 💪")
        lines = [f"⚠️ {len(items)} 项技能超过14天未训练:"]
        for s in items:
            lines.append(f"  - {s['name']} (Lv.{s['level']}, 上次: {s.get('last_trained', '从未')})")
        return ToolResult.success("\n".join(lines))

    # ── 人物 ──────────────────────────────────
    def _handle_upsert_person(self, p: dict) -> ToolResult:
        name = p.get("name")
        if not name:
            return ToolResult.fail("需要 name 参数")
        pid = self.db.upsert_person(
            name=name,
            relationship=p.get("relationship"),
        )
        return ToolResult.success(f"✅ 人物档案已更新: {name}")

    def _handle_get_person(self, p: dict) -> ToolResult:
        name = p.get("name")
        if not name:
            return ToolResult.fail("需要 name 参数")
        person = self.db.get_person(name)
        if not person:
            return ToolResult.success(f"没有找到关于 {name} 的档案。")
        return ToolResult.success(json.dumps(person, ensure_ascii=False, indent=2, default=str))

    def _handle_list_persons(self, p: dict) -> ToolResult:
        items = self.db.list_persons()
        if not items:
            return ToolResult.success("💑 暂无人物档案。")
        lines = [f"💑 共 {len(items)} 位人物:"]
        for per in items:
            rel = per.get("relationship", "unknown")
            cnt = per.get("mention_count", 0)
            lines.append(f"  - {per['name']} ({rel}) — 提及 {cnt} 次")
        return ToolResult.success("\n".join(lines))

    # ── 训练记录 ──────────────────────────────
    def _handle_add_training(self, p: dict) -> ToolResult:
        skill_name = p.get("skill_name")
        modality = p.get("modality")
        topic = p.get("topic", "")
        rating = p.get("rating", "")
        if not skill_name or not modality:
            return ToolResult.fail("训练记录需要 skill_name 和 modality 参数")
        tid = self.db.add_training_log(
            skill_name=skill_name, modality=modality,
            topic=topic, rating=rating,
            insight=p.get("insight"),
        )
        return ToolResult.success(f"✅ 训练记录已添加: {skill_name} ({modality}) — {topic}")

    def _handle_list_trainings(self, p: dict) -> ToolResult:
        items = self.db.get_training_logs(skill_name=p.get("skill_name"), limit=20)
        if not items:
            return ToolResult.success("📝 暂无训练记录。")
        lines = [f"📝 共 {len(items)} 条训练记录:"]
        for t in items:
            lines.append(
                f"  [{t.get('trained_at','?')}] {t.get('skill_name','?')} "
                f"({t['modality']}) {t['topic']} — {t['rating']}"
            )
        return ToolResult.success("\n".join(lines))

    # ── 心智模型 ──────────────────────────────
    def _handle_add_model(self, p: dict) -> ToolResult:
        name = p.get("name")
        if not name:
            return ToolResult.fail("心智模型需要 name 参数")
        mid = self.db.add_mental_model(
            name=name,
            source_domain=p.get("source_domain", ""),
            description=p.get("description", ""),
            applications=p.get("applications"),
        )
        return ToolResult.success(f"✅ 心智模型已记录: {name}")

    def _handle_list_models(self, p: dict) -> ToolResult:
        items = self.db.list_mental_models()
        if not items:
            return ToolResult.success("🧩 暂无心智模型。")
        lines = [f"🧩 共 {len(items)} 个心智模型:"]
        for m in items:
            lines.append(f"  - {m['name']} ({m.get('source_domain','?')}): {m.get('description','')[:60]}")
        return ToolResult.success("\n".join(lines))

    # ── 统计 ──────────────────────────────────
    def _handle_stats(self, p: dict) -> ToolResult:
        stats = self.db.get_stats()
        lines = [
            "📊 Evolution 数据统计:",
            f"  日程: {stats['total_schedules']} (待办: {stats['pending_schedules']})",
            f"  技能: {stats['total_skills']}",
            f"  人物: {stats['total_persons']}",
            f"  训练: {stats['total_trainings']}",
            f"  反思: {stats['total_reflections']}",
            f"  对话: {stats['total_conversations']}",
            f"  模型: {stats['total_mental_models']}",
        ]
        return ToolResult.success("\n".join(lines))
