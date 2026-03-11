"""Tests for evolution.tools.reflection_tool.EvolutionReflectionTool.

Covers _extract_json, daily reflection, weekly report, get/recent actions,
error handling, all with mocked LLM and DB.
"""

import json
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from evolution.tools.reflection_tool import EvolutionReflectionTool


# ──────────────────────────────────────────────
# _extract_json helper
# ──────────────────────────────────────────────
class TestExtractJson:
    """Validate JSON extraction from various LLM output formats."""

    def test_plain_json(self):
        """Pure JSON string should pass through."""
        raw = '{"key": "value"}'
        assert EvolutionReflectionTool._extract_json(raw) == '{"key": "value"}'

    def test_json_with_markdown_fence(self):
        """```json ... ``` wrapper should be stripped."""
        raw = '```json\n{"a": 1}\n```'
        assert EvolutionReflectionTool._extract_json(raw) == '{"a": 1}'

    def test_json_with_generic_fence(self):
        """``` ... ``` wrapper should be stripped."""
        raw = '```\n{"b": 2}\n```'
        assert EvolutionReflectionTool._extract_json(raw) == '{"b": 2}'

    def test_json_embedded_in_text(self):
        """JSON embedded in surrounding text should be extracted."""
        raw = 'Here is the output:\n{"result": true}\nThat is all.'
        extracted = EvolutionReflectionTool._extract_json(raw)
        assert json.loads(extracted) == {"result": True}

    def test_no_json(self):
        """Text without braces should return the stripped text."""
        raw = "No JSON here"
        assert EvolutionReflectionTool._extract_json(raw) == "No JSON here"

    def test_whitespace_handling(self):
        """Leading/trailing whitespace should be stripped."""
        raw = '  \n {"x": 1} \n  '
        assert json.loads(EvolutionReflectionTool._extract_json(raw)) == {"x": 1}


# ──────────────────────────────────────────────
# Daily reflection
# ──────────────────────────────────────────────
class TestDailyReflection:
    """Test _run_daily_reflection with mocked dependencies."""

    def _make_tool(self, tmp_db_path, llm_response):
        """Helper to create a reflection tool with mocked LLM."""
        tool = EvolutionReflectionTool(config={"db_path": tmp_db_path})
        # Seed a conversation so the tool doesn't skip
        tool.db.log_conversation("user", "Hello world")
        # Mock LLM
        tool._call_llm = MagicMock(return_value=llm_response)
        # Mock notifier
        tool._notifier = MagicMock()
        tool._notifier.send = MagicMock(return_value={})
        return tool

    def test_daily_with_valid_json(self, tmp_db_path):
        """Daily reflection with valid JSON from LLM should succeed."""
        report = {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "emotional_state": {"primary_emotion": "calm", "intensity": 0.3},
            "anomalies": [],
            "tomorrow_suggestion": "Read a paper",
            "evening_message": "Rest well tonight",
        }
        tool = self._make_tool(tmp_db_path, json.dumps(report))
        result = tool.execute({"action": "daily"})
        assert result.status == "success"
        assert result.result["emotion"] == "calm"
        assert result.result["conversations_analyzed"] >= 1

    def test_daily_with_markdown_json(self, tmp_db_path):
        """Daily reflection with markdown-wrapped JSON should still work."""
        report = {
            "emotional_state": {"primary_emotion": "excited", "intensity": 0.7},
            "anomalies": [],
            "tomorrow_suggestion": "Ship it",
            "evening_message": "Good job",
        }
        llm_out = f"```json\n{json.dumps(report)}\n```"
        tool = self._make_tool(tmp_db_path, llm_out)
        result = tool.execute({"action": "daily"})
        assert result.status == "success"

    def test_daily_with_malformed_json(self, tmp_db_path):
        """Daily reflection with non-JSON LLM output should use fallback."""
        tool = self._make_tool(tmp_db_path, "Sorry I can't generate JSON")
        result = tool.execute({"action": "daily"})
        assert result.status == "success"
        assert result.result["emotion"] == "unknown"

    def test_daily_no_conversations(self, tmp_db_path):
        """Daily with no conversations should skip and return success."""
        tool = EvolutionReflectionTool(config={"db_path": tmp_db_path})
        tool._notifier = MagicMock()
        result = tool.execute({"action": "daily", "date": "2099-01-01"})
        assert result.status == "success"
        assert "没有对话记录" in result.result

    def test_daily_llm_failure(self, tmp_db_path):
        """Daily with LLM returning None should fail."""
        tool = self._make_tool(tmp_db_path, None)
        tool._call_llm = MagicMock(return_value=None)
        result = tool.execute({"action": "daily"})
        assert result.status == "error"


# ──────────────────────────────────────────────
# Weekly report
# ──────────────────────────────────────────────
class TestWeeklyReport:
    """Test _run_weekly_report."""

    def test_weekly_no_reflections(self, tmp_db_path):
        """Weekly with no reflections should return a message."""
        tool = EvolutionReflectionTool(config={"db_path": tmp_db_path})
        tool._notifier = MagicMock()
        result = tool.execute({"action": "weekly"})
        assert result.status == "success"
        assert "暂无反思数据" in result.result

    def test_weekly_with_data(self, tmp_db_path):
        """Weekly with reflection data should call LLM and succeed."""
        tool = EvolutionReflectionTool(config={"db_path": tmp_db_path})
        # Seed reflections
        today = datetime.now().strftime("%Y-%m-%d")
        tool.db.save_reflection(today, '{"test": true}', "calm", 0.3, "study", "rest")
        tool._call_llm = MagicMock(return_value="Weekly summary: all good")
        tool._notifier = MagicMock()
        tool._notifier.send = MagicMock(return_value={})
        result = tool.execute({"action": "weekly"})
        assert result.status == "success"


# ──────────────────────────────────────────────
# Get / recent
# ──────────────────────────────────────────────
class TestGetRecent:
    """Test get and recent actions."""

    def test_get_existing_reflection(self, tmp_db_path):
        """get action for an existing date returns the reflection."""
        tool = EvolutionReflectionTool(config={"db_path": tmp_db_path})
        tool.db.save_reflection("2026-03-10", '{"a":1}', "happy", 0.5, "s", "m")
        result = tool.execute({"action": "get", "date": "2026-03-10"})
        assert result.status == "success"
        assert "2026-03-10" in result.result

    def test_get_missing_reflection(self, tmp_db_path):
        """get action for missing date returns a message."""
        tool = EvolutionReflectionTool(config={"db_path": tmp_db_path})
        result = tool.execute({"action": "get", "date": "1999-01-01"})
        assert result.status == "success"
        assert "没有找到" in result.result

    def test_recent_with_data(self, tmp_db_path):
        """recent action returns reflection summaries."""
        tool = EvolutionReflectionTool(config={"db_path": tmp_db_path})
        today = datetime.now().strftime("%Y-%m-%d")
        tool.db.save_reflection(today, '{}', "focused", 0.4, "code", "sleep")
        result = tool.execute({"action": "recent", "days": 7})
        assert result.status == "success"

    def test_recent_no_data(self, tmp_db_path):
        """recent action with no data returns a message."""
        tool = EvolutionReflectionTool(config={"db_path": tmp_db_path})
        result = tool.execute({"action": "recent", "days": 1})
        assert result.status == "success"
        assert "暂无" in result.result


# ──────────────────────────────────────────────
# Error handling
# ──────────────────────────────────────────────
class TestReflectionErrors:
    """Test error paths."""

    def test_invalid_action(self, reflection_tool):
        """Unknown action returns error."""
        result = reflection_tool.execute({"action": "explode"})
        assert result.status == "error"

    def test_missing_action(self, reflection_tool):
        """Missing action returns error."""
        result = reflection_tool.execute({})
        assert result.status == "error"
