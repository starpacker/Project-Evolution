"""Tests for evolution.db.manager.DatabaseManager.

Covers all CRUD operations for schedules, skills, persons, training logs,
mental models, reflections, conversation logs, stats, and thread-safety.
"""

import json
import threading
from datetime import datetime, timedelta

import pytest


# ──────────────────────────────────────────────
# Schedule CRUD
# ──────────────────────────────────────────────
class TestScheduleCRUD:
    """Validate schedule create / read / update / delete."""

    def test_add_schedule_returns_positive_id(self, db):
        """add_schedule should return a positive integer row id."""
        sid = db.add_schedule(content="Write tests", due_date="2026-03-15", priority="high")
        assert isinstance(sid, int)
        assert sid > 0

    def test_add_schedule_with_all_fields(self, db):
        """All optional fields should be stored correctly."""
        sid = db.add_schedule(
            content="Full schedule",
            due_date="2026-04-01",
            remind_at="2026-03-31 09:00:00",
            priority="low",
            category="personal",
            context="from test",
        )
        rows = db.get_pending_schedules()
        match = [r for r in rows if r["id"] == sid]
        assert len(match) == 1
        assert match[0]["priority"] == "low"
        assert match[0]["category"] == "personal"

    def test_get_schedule_by_date(self, db):
        """Only pending schedules on the specified date should be returned."""
        db.add_schedule(content="A", due_date="2026-03-10")
        db.add_schedule(content="B", due_date="2026-03-11")
        results = db.get_schedule_by_date("2026-03-10")
        assert len(results) == 1
        assert results[0]["content"] == "A"

    def test_get_schedule_by_date_empty(self, db):
        """Should return empty list when no schedules exist for the date."""
        results = db.get_schedule_by_date("2099-01-01")
        assert results == []

    def test_get_pending_schedules(self, db):
        """get_pending_schedules should return only pending items."""
        sid = db.add_schedule(content="Pending one")
        db.add_schedule(content="Pending two")
        db.complete_schedule(sid)
        pending = db.get_pending_schedules()
        assert len(pending) == 1
        assert pending[0]["content"] == "Pending two"

    def test_get_overdue_schedules(self, db):
        """Past-due pending schedules should appear in overdue list."""
        db.add_schedule(content="Old task", due_date="2020-01-01 00:00:00")
        overdue = db.get_overdue_schedules()
        assert len(overdue) >= 1
        assert overdue[0]["content"] == "Old task"

    def test_complete_schedule_success(self, db):
        """complete_schedule should return True and change status."""
        sid = db.add_schedule(content="Do it")
        assert db.complete_schedule(sid) is True
        pending = db.get_pending_schedules()
        assert all(r["id"] != sid for r in pending)

    def test_complete_schedule_nonexistent(self, db):
        """complete_schedule on a missing id should return False."""
        assert db.complete_schedule(99999) is False

    def test_cancel_schedule(self, db):
        """cancel_schedule should remove item from pending list."""
        sid = db.add_schedule(content="Cancel me")
        assert db.cancel_schedule(sid) is True
        pending = db.get_pending_schedules()
        assert all(r["id"] != sid for r in pending)

    def test_cancel_schedule_nonexistent(self, db):
        """cancel_schedule on missing id should return False."""
        assert db.cancel_schedule(99999) is False

    def test_delete_schedule(self, db):
        """delete_schedule should physically remove the row."""
        sid = db.add_schedule(content="Delete me")
        assert db.delete_schedule(sid) is True
        assert db.delete_schedule(sid) is False  # already gone

    def test_delete_schedule_nonexistent(self, db):
        """delete on missing id returns False."""
        assert db.delete_schedule(99999) is False


# ──────────────────────────────────────────────
# Skill CRUD
# ──────────────────────────────────────────────
class TestSkillCRUD:
    """Validate skill create / read / update / stale detection."""

    def test_add_skill(self, db):
        """add_skill should create a new skill and return an id."""
        sid = db.add_skill(name="Python", category="professional", level=3, target_level=8)
        assert isinstance(sid, int)
        assert sid > 0

    def test_add_duplicate_skill_ignored(self, db):
        """INSERT OR IGNORE means duplicate names are silently ignored."""
        db.add_skill(name="Python", category="professional")
        sid2 = db.add_skill(name="Python", category="professional")
        # INSERT OR IGNORE returns 0 for lastrowid on conflict
        skills = db.list_skills()
        assert len(skills) == 1

    def test_get_skill(self, db):
        """get_skill should return a dict with all fields."""
        db.add_skill(name="Rust", category="professional", level=2)
        skill = db.get_skill("Rust")
        assert skill is not None
        assert skill["name"] == "Rust"
        assert skill["level"] == 2

    def test_get_skill_not_found(self, db):
        """get_skill for missing name should return None."""
        assert db.get_skill("Nonexistent") is None

    def test_list_skills_all(self, db):
        """list_skills without category returns all."""
        db.add_skill(name="A", category="professional")
        db.add_skill(name="B", category="thinking")
        assert len(db.list_skills()) == 2

    def test_list_skills_by_category(self, db):
        """list_skills with category filter returns only matching."""
        db.add_skill(name="A", category="professional")
        db.add_skill(name="B", category="thinking")
        result = db.list_skills(category="thinking")
        assert len(result) == 1
        assert result[0]["name"] == "B"

    def test_update_skill_level(self, db):
        """update_skill_level should change level and add xp."""
        db.add_skill(name="Go", category="professional", level=1)
        ok = db.update_skill_level("Go", 5, xp_delta=100)
        assert ok is True
        skill = db.get_skill("Go")
        assert skill["level"] == 5
        assert skill["xp"] == 100

    def test_update_skill_level_nonexistent(self, db):
        """Updating a missing skill returns False."""
        assert db.update_skill_level("Ghost", 3) is False

    def test_get_stale_skills(self, db):
        """Newly added skills with no last_trained should be stale."""
        db.add_skill(name="Stale", category="professional")
        stale = db.get_stale_skills(days=0)
        assert any(s["name"] == "Stale" for s in stale)


# ──────────────────────────────────────────────
# Person CRUD
# ──────────────────────────────────────────────
class TestPersonCRUD:
    """Validate person upsert / get / list / top-mentioned."""

    def test_upsert_person_insert(self, db):
        """First upsert should create a new person."""
        pid = db.upsert_person("Alice", relationship="friend")
        assert isinstance(pid, int)
        assert pid > 0

    def test_upsert_person_update(self, db):
        """Second upsert for same name should increment mention_count."""
        db.upsert_person("Bob", relationship="colleague")
        db.upsert_person("Bob", relationship="close friend")
        person = db.get_person("Bob")
        assert person["mention_count"] == 2

    def test_get_person(self, db):
        """get_person should return full dict."""
        db.upsert_person("Charlie")
        p = db.get_person("Charlie")
        assert p is not None
        assert p["name"] == "Charlie"

    def test_get_person_not_found(self, db):
        """get_person for missing name returns None."""
        assert db.get_person("Nobody") is None

    def test_list_persons(self, db):
        """list_persons should return all persons ordered by mention_count."""
        db.upsert_person("X")
        db.upsert_person("Y")
        db.upsert_person("X")  # X mentioned twice
        persons = db.list_persons()
        assert len(persons) == 2
        assert persons[0]["name"] == "X"

    def test_get_top_mentioned_persons(self, db):
        """get_top_mentioned_persons should respect limit."""
        for name in ["A", "B", "C", "D", "E", "F"]:
            db.upsert_person(name)
        top = db.get_top_mentioned_persons(limit=3)
        assert len(top) == 3


# ──────────────────────────────────────────────
# Training Logs
# ──────────────────────────────────────────────
class TestTrainingLogs:
    """Validate training log add / query."""

    def test_add_training_log(self, db):
        """Should insert a training log even without a matching skill."""
        tid = db.add_training_log(
            skill_name="Unknown", modality="T1", topic="Test", rating="good"
        )
        assert isinstance(tid, int)

    def test_add_training_log_with_skill(self, db):
        """Training log should link to skill_id when skill exists."""
        db.add_skill(name="Logic", category="thinking")
        tid = db.add_training_log(
            skill_name="Logic", modality="T2", topic="Debate", rating="excellent", insight="Great"
        )
        logs = db.get_training_logs(skill_name="Logic")
        assert len(logs) == 1
        assert logs[0]["topic"] == "Debate"
        assert logs[0]["insight"] == "Great"

    def test_get_training_logs_all(self, db):
        """get_training_logs without skill_name returns all logs."""
        db.add_training_log("A", "T1", "t1", "ok")
        db.add_training_log("B", "T2", "t2", "ok")
        logs = db.get_training_logs()
        assert len(logs) == 2

    def test_get_training_logs_empty(self, db):
        """Empty table returns empty list."""
        assert db.get_training_logs() == []


# ──────────────────────────────────────────────
# Mental Models
# ──────────────────────────────────────────────
class TestMentalModels:
    """Validate mental model add / list."""

    def test_add_mental_model(self, db):
        """add_mental_model should store name, domain, description."""
        mid = db.add_mental_model(
            name="Sunk Cost", source_domain="Economics",
            description="Past costs should not affect future decisions",
            applications=["investment", "relationships"],
        )
        assert isinstance(mid, int)

    def test_add_duplicate_mental_model_ignored(self, db):
        """Duplicate names are silently ignored."""
        db.add_mental_model(name="First Principles", source_domain="Physics", description="D")
        db.add_mental_model(name="First Principles", source_domain="Physics", description="D2")
        models = db.list_mental_models()
        assert len(models) == 1

    def test_list_mental_models(self, db):
        """list_mental_models should deserialize applications JSON."""
        db.add_mental_model(name="M1", source_domain="S1", description="D1", applications=["a"])
        models = db.list_mental_models()
        assert len(models) == 1
        assert models[0]["applications"] == ["a"]

    def test_list_mental_models_empty(self, db):
        """Empty table returns empty list."""
        assert db.list_mental_models() == []


# ──────────────────────────────────────────────
# Reflections
# ──────────────────────────────────────────────
class TestReflections:
    """Validate reflection save / get / range."""

    def test_save_and_get_reflection(self, db):
        """save_reflection + get_reflection round-trip."""
        db.save_reflection(
            date="2026-03-10",
            report_json='{"test": true}',
            primary_emotion="calm",
            emotional_intensity=0.3,
            tomorrow_suggestion="Read more",
            evening_message="Good night",
        )
        ref = db.get_reflection("2026-03-10")
        assert ref is not None
        assert ref["primary_emotion"] == "calm"
        assert ref["tomorrow_suggestion"] == "Read more"

    def test_get_reflection_not_found(self, db):
        """Missing date returns None."""
        assert db.get_reflection("1999-01-01") is None

    def test_save_reflection_replaces_on_same_date(self, db):
        """INSERT OR REPLACE should overwrite on duplicate date."""
        db.save_reflection("2026-03-10", "{}", "happy", 0.5, "s1", "m1")
        db.save_reflection("2026-03-10", "{}", "sad", 0.9, "s2", "m2")
        ref = db.get_reflection("2026-03-10")
        assert ref["primary_emotion"] == "sad"

    def test_get_reflections_range(self, db):
        """get_reflections_range should return only dates in range."""
        db.save_reflection("2026-03-08", "{}", "a", 0.1, "", "")
        db.save_reflection("2026-03-09", "{}", "b", 0.2, "", "")
        db.save_reflection("2026-03-10", "{}", "c", 0.3, "", "")
        results = db.get_reflections_range("2026-03-08", "2026-03-09")
        assert len(results) == 2


# ──────────────────────────────────────────────
# Conversation Logs
# ──────────────────────────────────────────────
class TestConversationLogs:
    """Validate conversation logging and querying."""

    def test_log_conversation(self, db):
        """log_conversation should insert and return an id."""
        cid = db.log_conversation("user", "Hello")
        assert isinstance(cid, int)
        assert cid > 0

    def test_get_conversations_by_date(self, db):
        """Conversations logged today should be retrievable by today's date."""
        db.log_conversation("user", "Hi")
        db.log_conversation("assistant", "Hello!")
        today = datetime.now().strftime("%Y-%m-%d")
        convs = db.get_conversations_by_date(today)
        assert len(convs) == 2

    def test_get_conversations_by_date_empty(self, db):
        """No conversations on the date returns empty list."""
        assert db.get_conversations_by_date("1999-01-01") == []

    def test_get_conversation_count_by_date(self, db):
        """Count should match number of logged conversations."""
        today = datetime.now().strftime("%Y-%m-%d")
        db.log_conversation("user", "1")
        db.log_conversation("user", "2")
        db.log_conversation("assistant", "3")
        assert db.get_conversation_count_by_date(today) == 3

    def test_get_conversation_count_zero(self, db):
        """Count for empty date is 0."""
        assert db.get_conversation_count_by_date("2099-12-31") == 0


# ──────────────────────────────────────────────
# Stats
# ──────────────────────────────────────────────
class TestStats:
    """Validate aggregated statistics."""

    def test_get_stats_empty(self, db):
        """All counts should be 0 on a fresh database."""
        stats = db.get_stats()
        assert stats["total_schedules"] == 0
        assert stats["pending_schedules"] == 0
        assert stats["total_skills"] == 0
        assert stats["total_persons"] == 0

    def test_get_stats_after_inserts(self, db):
        """Stats should reflect inserted rows."""
        db.add_schedule(content="S1")
        db.add_schedule(content="S2")
        db.add_skill(name="Skill1", category="professional")
        db.upsert_person("P1")
        stats = db.get_stats()
        assert stats["total_schedules"] == 2
        assert stats["pending_schedules"] == 2
        assert stats["total_skills"] == 1
        assert stats["total_persons"] == 1


# ──────────────────────────────────────────────
# Thread Safety
# ──────────────────────────────────────────────
class TestThreadSafety:
    """Verify concurrent writes from multiple threads."""

    def test_concurrent_schedule_inserts(self, db):
        """Multiple threads inserting schedules concurrently should all succeed."""
        errors = []
        n_threads = 10
        n_per_thread = 5

        def insert_schedules(thread_id):
            try:
                for i in range(n_per_thread):
                    db.add_schedule(content=f"Thread-{thread_id}-{i}")
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=insert_schedules, args=(t,)) for t in range(n_threads)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert errors == [], f"Thread errors: {errors}"
        pending = db.get_pending_schedules()
        assert len(pending) == n_threads * n_per_thread


# ──────────────────────────────────────────────
# Edge Cases
# ──────────────────────────────────────────────
class TestEdgeCases:
    """Edge case coverage."""

    def test_schedule_with_no_due_date(self, db):
        """Schedule without due_date should be valid."""
        sid = db.add_schedule(content="No due date")
        pending = db.get_pending_schedules()
        assert any(r["id"] == sid for r in pending)

    def test_reset_singleton(self, db):
        """reset_singleton should allow a fresh instance."""
        db.reset_singleton()
        from evolution.db.manager import DatabaseManager
        assert DatabaseManager._instance is None
