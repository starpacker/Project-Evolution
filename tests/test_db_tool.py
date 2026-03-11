"""Tests for evolution.tools.db_tool.EvolutionDBTool.

Covers all 16 actions with valid params, missing params, and integration workflows.
"""

import json

import pytest


# ──────────────────────────────────────────────
# Schedule actions
# ──────────────────────────────────────────────
class TestDBToolSchedule:
    """Test schedule-related actions in EvolutionDBTool."""

    def test_add_schedule_success(self, db_tool):
        """add_schedule with content returns success."""
        r = db_tool.execute({"action": "add_schedule", "content": "Buy groceries"})
        assert r.status == "success"
        assert "日程已添加" in r.result

    def test_add_schedule_missing_content(self, db_tool):
        """add_schedule without content returns error."""
        r = db_tool.execute({"action": "add_schedule"})
        assert r.status == "error"

    def test_list_schedule_pending(self, db_tool):
        """list_schedule returns pending items."""
        db_tool.execute({"action": "add_schedule", "content": "Task A"})
        r = db_tool.execute({"action": "list_schedule"})
        assert r.status == "success"

    def test_list_schedule_by_date(self, db_tool):
        """list_schedule with date filter."""
        db_tool.execute({"action": "add_schedule", "content": "Dated", "due_date": "2026-05-01"})
        r = db_tool.execute({"action": "list_schedule", "date": "2026-05-01"})
        assert r.status == "success"

    def test_list_schedule_overdue(self, db_tool):
        """list_schedule with overdue filter."""
        db_tool.execute({"action": "add_schedule", "content": "Old", "due_date": "2020-01-01 00:00:00"})
        r = db_tool.execute({"action": "list_schedule", "filter": "overdue"})
        assert r.status == "success"

    def test_list_schedule_empty(self, db_tool):
        """list_schedule on empty db returns a success message."""
        r = db_tool.execute({"action": "list_schedule"})
        assert r.status == "success"

    def test_complete_schedule_success(self, db_tool):
        """complete_schedule with valid id."""
        db_tool.execute({"action": "add_schedule", "content": "Complete me"})
        r = db_tool.execute({"action": "complete_schedule", "id": 1})
        assert r.status == "success"

    def test_complete_schedule_missing_id(self, db_tool):
        """complete_schedule without id returns error."""
        r = db_tool.execute({"action": "complete_schedule"})
        assert r.status == "error"

    def test_complete_schedule_nonexistent(self, db_tool):
        """complete_schedule on missing id returns error."""
        r = db_tool.execute({"action": "complete_schedule", "id": 9999})
        assert r.status == "error"

    def test_delete_schedule_success(self, db_tool):
        """delete_schedule with valid id."""
        db_tool.execute({"action": "add_schedule", "content": "Del me"})
        r = db_tool.execute({"action": "delete_schedule", "id": 1})
        assert r.status == "success"

    def test_delete_schedule_missing_id(self, db_tool):
        """delete_schedule without id returns error."""
        r = db_tool.execute({"action": "delete_schedule"})
        assert r.status == "error"


# ──────────────────────────────────────────────
# Skill actions
# ──────────────────────────────────────────────
class TestDBToolSkill:
    """Test skill-related actions."""

    def test_add_skill_success(self, db_tool):
        """add_skill with name returns success."""
        r = db_tool.execute({"action": "add_skill", "name": "Python", "category": "professional"})
        assert r.status == "success"

    def test_add_skill_missing_name(self, db_tool):
        """add_skill without name returns error."""
        r = db_tool.execute({"action": "add_skill"})
        assert r.status == "error"

    def test_list_skills_empty(self, db_tool):
        """list_skills on empty db returns success."""
        r = db_tool.execute({"action": "list_skills"})
        assert r.status == "success"

    def test_list_skills_with_data(self, db_tool):
        """list_skills after adding returns formatted output."""
        db_tool.execute({"action": "add_skill", "name": "Go", "category": "professional", "level": 3})
        r = db_tool.execute({"action": "list_skills"})
        assert r.status == "success"
        assert "Go" in r.result

    def test_list_skills_by_category(self, db_tool):
        """list_skills with category filter."""
        db_tool.execute({"action": "add_skill", "name": "A", "category": "professional"})
        db_tool.execute({"action": "add_skill", "name": "B", "category": "thinking"})
        r = db_tool.execute({"action": "list_skills", "category": "thinking"})
        assert r.status == "success"
        assert "B" in r.result

    def test_update_skill_success(self, db_tool):
        """update_skill with valid name and level."""
        db_tool.execute({"action": "add_skill", "name": "Python", "category": "professional"})
        r = db_tool.execute({"action": "update_skill", "name": "Python", "level": 5, "xp_delta": 50})
        assert r.status == "success"

    def test_update_skill_missing_name(self, db_tool):
        """update_skill without name returns error."""
        r = db_tool.execute({"action": "update_skill", "level": 3})
        assert r.status == "error"

    def test_update_skill_missing_level(self, db_tool):
        """update_skill without level returns error."""
        r = db_tool.execute({"action": "update_skill", "name": "X"})
        assert r.status == "error"

    def test_stale_skills_empty(self, db_tool):
        """stale_skills when all are active."""
        r = db_tool.execute({"action": "stale_skills"})
        assert r.status == "success"


# ──────────────────────────────────────────────
# Person actions
# ──────────────────────────────────────────────
class TestDBToolPerson:
    """Test person-related actions."""

    def test_upsert_person_success(self, db_tool):
        """upsert_person with name returns success."""
        r = db_tool.execute({"action": "upsert_person", "name": "Alice"})
        assert r.status == "success"

    def test_upsert_person_missing_name(self, db_tool):
        """upsert_person without name returns error."""
        r = db_tool.execute({"action": "upsert_person"})
        assert r.status == "error"

    def test_get_person_found(self, db_tool):
        """get_person for existing person returns JSON."""
        db_tool.execute({"action": "upsert_person", "name": "Bob"})
        r = db_tool.execute({"action": "get_person", "name": "Bob"})
        assert r.status == "success"
        assert "Bob" in r.result

    def test_get_person_not_found(self, db_tool):
        """get_person for missing person returns friendly message."""
        r = db_tool.execute({"action": "get_person", "name": "Nobody"})
        assert r.status == "success"
        assert "没有找到" in r.result

    def test_get_person_missing_name(self, db_tool):
        """get_person without name returns error."""
        r = db_tool.execute({"action": "get_person"})
        assert r.status == "error"

    def test_list_persons_empty(self, db_tool):
        """list_persons on empty db returns success."""
        r = db_tool.execute({"action": "list_persons"})
        assert r.status == "success"


# ──────────────────────────────────────────────
# Training actions
# ──────────────────────────────────────────────
class TestDBToolTraining:
    """Test training-related actions."""

    def test_add_training_success(self, db_tool):
        """add_training with required params returns success."""
        r = db_tool.execute({
            "action": "add_training",
            "skill_name": "Logic",
            "modality": "T2",
            "topic": "Debate",
            "rating": "good",
        })
        assert r.status == "success"

    def test_add_training_missing_params(self, db_tool):
        """add_training without skill_name or modality returns error."""
        r = db_tool.execute({"action": "add_training", "topic": "X"})
        assert r.status == "error"

    def test_list_trainings_empty(self, db_tool):
        """list_trainings on empty db returns success."""
        r = db_tool.execute({"action": "list_trainings"})
        assert r.status == "success"


# ──────────────────────────────────────────────
# Mental Model actions
# ──────────────────────────────────────────────
class TestDBToolMentalModel:
    """Test mental-model-related actions."""

    def test_add_model_success(self, db_tool):
        """add_model with name returns success."""
        r = db_tool.execute({
            "action": "add_model",
            "name": "Occam's Razor",
            "source_domain": "Philosophy",
            "description": "Simplest explanation is likely correct",
        })
        assert r.status == "success"

    def test_add_model_missing_name(self, db_tool):
        """add_model without name returns error."""
        r = db_tool.execute({"action": "add_model"})
        assert r.status == "error"

    def test_list_models_empty(self, db_tool):
        """list_models on empty db returns success."""
        r = db_tool.execute({"action": "list_models"})
        assert r.status == "success"


# ──────────────────────────────────────────────
# Stats & misc
# ──────────────────────────────────────────────
class TestDBToolMisc:
    """Test stats and invalid actions."""

    def test_stats(self, db_tool):
        """stats action returns formatted statistics."""
        r = db_tool.execute({"action": "stats"})
        assert r.status == "success"
        assert "统计" in r.result

    def test_invalid_action(self, db_tool):
        """Unknown action returns error."""
        r = db_tool.execute({"action": "explode"})
        assert r.status == "error"

    def test_no_action(self, db_tool):
        """Missing action key returns error."""
        r = db_tool.execute({})
        assert r.status == "error"


# ──────────────────────────────────────────────
# Workflow integration
# ──────────────────────────────────────────────
class TestDBToolWorkflow:
    """End-to-end workflows through the tool interface."""

    def test_schedule_lifecycle(self, db_tool):
        """Create → list → complete → verify schedule is done."""
        db_tool.execute({"action": "add_schedule", "content": "Lifecycle task", "due_date": "2026-06-01"})
        r1 = db_tool.execute({"action": "list_schedule"})
        assert "Lifecycle task" in r1.result

        db_tool.execute({"action": "complete_schedule", "id": 1})
        r2 = db_tool.execute({"action": "list_schedule"})
        # Completed tasks should no longer appear in pending
        assert "Lifecycle task" not in r2.result or "没有待办" in r2.result

    def test_skill_training_workflow(self, db_tool):
        """Add skill → train → update level."""
        db_tool.execute({"action": "add_skill", "name": "Critical Thinking", "category": "thinking", "level": 1})
        db_tool.execute({
            "action": "add_training",
            "skill_name": "Critical Thinking",
            "modality": "T4",
            "topic": "Self-questioning",
            "rating": "excellent",
        })
        db_tool.execute({"action": "update_skill", "name": "Critical Thinking", "level": 2, "xp_delta": 30})
        r = db_tool.execute({"action": "list_skills"})
        assert "Critical Thinking" in r.result
        assert "Lv.2" in r.result
