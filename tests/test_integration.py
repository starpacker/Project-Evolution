"""Integration tests — end-to-end workflows across multiple modules.

Tests full lifecycle of schedule, skill, person, and conversation/reflection flow.
"""

import json
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from evolution.db.manager import DatabaseManager
from evolution.tools.db_tool import EvolutionDBTool
from evolution.tools.memory_tool import EvolutionMemoryTool, MockMemory
from evolution.tools.reflection_tool import EvolutionReflectionTool


class TestScheduleLifecycle:
    """Full schedule lifecycle: create → list → complete → verify."""

    def test_full_lifecycle(self, tmp_db_path):
        """Schedule should progress through all states correctly."""
        tool = EvolutionDBTool(config={"db_path": tmp_db_path})
        # Create
        r1 = tool.execute({"action": "add_schedule", "content": "Integration test task", "due_date": "2026-12-31", "priority": "high"})
        assert r1.status == "success"
        # List
        r2 = tool.execute({"action": "list_schedule"})
        assert "Integration test task" in r2.result
        # Complete
        r3 = tool.execute({"action": "complete_schedule", "id": 1})
        assert r3.status == "success"
        # Verify it's gone from pending
        r4 = tool.execute({"action": "list_schedule"})
        assert "Integration test task" not in r4.result or "没有待办" in r4.result
        # Stats should reflect 1 total, 0 pending
        r5 = tool.execute({"action": "stats"})
        assert "待办: 0" in r5.result


class TestSkillTrackingLifecycle:
    """Skill tracking: add → train → update → stale check."""

    def test_skill_full_workflow(self, tmp_db_path):
        """Skill should be trackable through full training workflow."""
        tool = EvolutionDBTool(config={"db_path": tmp_db_path})
        # Add skill
        tool.execute({"action": "add_skill", "name": "Machine Learning", "category": "professional", "level": 2, "target_level": 7})
        # Log training
        tool.execute({
            "action": "add_training",
            "skill_name": "Machine Learning",
            "modality": "T1",
            "topic": "Gradient descent",
            "rating": "good",
            "insight": "Chain rule is key",
        })
        # Update level
        tool.execute({"action": "update_skill", "name": "Machine Learning", "level": 3, "xp_delta": 50})
        # Verify
        r = tool.execute({"action": "list_skills"})
        assert "Machine Learning" in r.result
        assert "Lv.3" in r.result
        # Training log
        r2 = tool.execute({"action": "list_trainings", "skill_name": "Machine Learning"})
        assert "Gradient descent" in r2.result


class TestPersonManagement:
    """Person management: upsert → memory → search by name."""

    def test_person_with_memory(self, tmp_db_path):
        """Person upsert + memory add should be retrievable."""
        db_tool = EvolutionDBTool(config={"db_path": tmp_db_path})
        mem_tool = EvolutionMemoryTool()
        mem_tool._memory = MockMemory()
        mem_tool._user_id = "test"

        # Upsert person
        db_tool.execute({"action": "upsert_person", "name": "Alice", "relationship": "mentor"})
        # Add memory about person
        mem_tool.execute({"action": "add", "content": "Alice is a professor of physics"})
        # Search memory
        r = mem_tool.execute({"action": "search", "query": "Alice"})
        assert r.status == "success"
        assert len(r.result["memories"]) >= 1
        # Get person from DB
        r2 = db_tool.execute({"action": "get_person", "name": "Alice"})
        assert "Alice" in r2.result


class TestConversationReflectionFlow:
    """Conversation logging → reflection trigger → report check."""

    def test_conversation_to_reflection(self, tmp_db_path):
        """Logged conversations should feed into daily reflection."""
        db = DatabaseManager(tmp_db_path)
        today = datetime.now().strftime("%Y-%m-%d")

        # Log conversations
        db.log_conversation("user", "I'm feeling great today")
        db.log_conversation("assistant", "That's wonderful to hear")
        db.log_conversation("user", "I want to study more math")

        # Verify count
        assert db.get_conversation_count_by_date(today) == 3

        # Create reflection tool and run daily
        ref_tool = EvolutionReflectionTool(config={"db_path": tmp_db_path})
        report = {
            "emotional_state": {"primary_emotion": "happy", "intensity": 0.7},
            "anomalies": [],
            "tomorrow_suggestion": "Study linear algebra",
            "evening_message": "Great day!",
        }
        ref_tool._call_llm = MagicMock(return_value=json.dumps(report))
        ref_tool._notifier = MagicMock()
        ref_tool._notifier.send = MagicMock(return_value={})

        result = ref_tool.execute({"action": "daily"})
        assert result.status == "success"
        assert result.result["emotion"] == "happy"
        assert result.result["conversations_analyzed"] == 3

        # Verify reflection was saved
        saved = db.get_reflection(today)
        assert saved is not None
        assert saved["primary_emotion"] == "happy"


class TestMultipleSchedulesAndPersons:
    """Complex scenario with multiple schedules and persons."""

    def test_multi_entity_stats(self, tmp_db_path):
        """Stats should accurately reflect multiple entities."""
        tool = EvolutionDBTool(config={"db_path": tmp_db_path})
        # Add 3 schedules
        for i in range(3):
            tool.execute({"action": "add_schedule", "content": f"Task {i}"})
        # Complete 1
        tool.execute({"action": "complete_schedule", "id": 1})
        # Add 2 skills
        tool.execute({"action": "add_skill", "name": "Coding", "category": "professional"})
        tool.execute({"action": "add_skill", "name": "Writing", "category": "professional"})
        # Add 2 persons
        tool.execute({"action": "upsert_person", "name": "X"})
        tool.execute({"action": "upsert_person", "name": "Y"})
        # Add mental model
        tool.execute({"action": "add_model", "name": "Inversion", "source_domain": "Math", "description": "Think backwards"})

        r = tool.execute({"action": "stats"})
        assert "日程: 3" in r.result
        assert "待办: 2" in r.result
        assert "技能: 2" in r.result
        assert "人物: 2" in r.result
        assert "模型: 1" in r.result
