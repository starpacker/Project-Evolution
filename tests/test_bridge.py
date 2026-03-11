"""Tests for evolution.utils.bridge.

Covers get_evolution_tools, get_system_prompt, log_conversation, register_with_cowagent.
"""

from unittest.mock import MagicMock, patch

import pytest


class TestGetEvolutionTools:
    """Test get_evolution_tools returns the correct tool instances."""

    def test_returns_four_tools(self):
        """Should return exactly 4 tool instances."""
        from evolution.utils.bridge import get_evolution_tools
        tools = get_evolution_tools()
        assert len(tools) == 4

    def test_tool_types(self):
        """Each returned tool should be an instance of the correct class."""
        from evolution.utils.bridge import get_evolution_tools
        from evolution.tools.memory_tool import EvolutionMemoryTool
        from evolution.tools.db_tool import EvolutionDBTool
        from evolution.tools.reflection_tool import EvolutionReflectionTool
        from evolution.tools.intelligence_tool import EvolutionIntelligenceTool
        tools = get_evolution_tools()
        types = [type(t) for t in tools]
        assert EvolutionMemoryTool in types
        assert EvolutionDBTool in types
        assert EvolutionReflectionTool in types
        assert EvolutionIntelligenceTool in types

    def test_tools_have_names(self):
        """Every tool should have a non-empty name attribute."""
        from evolution.utils.bridge import get_evolution_tools
        for tool in get_evolution_tools():
            assert hasattr(tool, "name")
            assert tool.name


class TestGetSystemPrompt:
    """Test get_system_prompt returns the system prompt."""

    def test_returns_non_empty_string(self):
        """System prompt should be a non-empty string."""
        from evolution.utils.bridge import get_system_prompt
        prompt = get_system_prompt()
        assert isinstance(prompt, str)
        assert len(prompt) > 100

    def test_contains_role_markers(self):
        """System prompt should mention the five roles."""
        from evolution.utils.bridge import get_system_prompt
        prompt = get_system_prompt()
        assert "秘书" in prompt
        assert "导师" in prompt
        assert "训练师" in prompt


class TestLogConversation:
    """Test log_conversation writes to the database."""

    def test_log_conversation_writes(self, tmp_db_path):
        """log_conversation should insert a conversation row."""
        from evolution.db.manager import DatabaseManager
        from datetime import datetime
        db = DatabaseManager(tmp_db_path)
        from evolution.utils.bridge import log_conversation
        log_conversation("user", "Hello bridge")
        today = datetime.now().strftime("%Y-%m-%d")
        convs = db.get_conversations_by_date(today)
        assert any("Hello bridge" in c["content"] for c in convs)

    def test_log_conversation_handles_error_gracefully(self):
        """log_conversation should not raise on DB errors."""
        from evolution.utils.bridge import log_conversation
        with patch("evolution.db.manager.DatabaseManager.__new__", side_effect=Exception("DB error")):
            # Should not raise
            log_conversation("user", "This will fail silently")


class TestRegisterWithCowagent:
    """Test register_with_cowagent handles missing CowAgent gracefully."""

    def test_returns_false_when_cowagent_missing(self):
        """Without CowAgent installed, should return False."""
        from evolution.utils.bridge import register_with_cowagent
        result = register_with_cowagent()
        assert result is False

    def test_returns_true_with_mock_cowagent(self):
        """With mocked CowAgent ToolManager, should register and return True."""
        mock_tm_instance = MagicMock()
        mock_tm_instance.tool_classes = {}
        mock_tm_cls = MagicMock(return_value=mock_tm_instance)

        with patch.dict("sys.modules", {
            "agent": MagicMock(),
            "agent.tools": MagicMock(),
            "agent.tools.tool_manager": MagicMock(ToolManager=mock_tm_cls),
        }):
            from evolution.utils.bridge import register_with_cowagent
            result = register_with_cowagent()
            assert result is True
            assert len(mock_tm_instance.tool_classes) == 4
