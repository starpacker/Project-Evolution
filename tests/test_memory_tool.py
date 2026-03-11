"""Tests for evolution.tools.memory_tool.EvolutionMemoryTool.

Covers search / add / profile actions, MockMemory fallback, validation, edge cases.
"""

import pytest

from evolution.tools.memory_tool import EvolutionMemoryTool, MockMemory


class TestMockMemory:
    """Verify the MockMemory standalone behaviour."""

    def test_add_and_search(self):
        """Added memories should be findable via keyword search."""
        mm = MockMemory()
        mm.add([{"content": "User loves Python"}], user_id="u1")
        result = mm.search("python", user_id="u1")
        assert len(result["results"]) == 1

    def test_search_no_match(self):
        """Search for non-existent keyword returns empty results."""
        mm = MockMemory()
        mm.add([{"content": "something else"}], user_id="u1")
        result = mm.search("nonexistent", user_id="u1")
        assert result["results"] == []

    def test_get_all(self):
        """get_all returns everything stored."""
        mm = MockMemory()
        mm.add([{"content": "one"}], user_id="u1")
        mm.add([{"content": "two"}], user_id="u1")
        all_mem = mm.get_all(user_id="u1")
        assert len(all_mem["results"]) == 2


class TestMemoryToolSearch:
    """Test the search action of EvolutionMemoryTool."""

    def test_search_with_results(self, memory_tool):
        """Search should return matching memories."""
        memory_tool.execute({"action": "add", "content": "User studies physics"})
        result = memory_tool.execute({"action": "search", "query": "physics"})
        assert result.status == "success"
        assert isinstance(result.result, dict)
        assert len(result.result["memories"]) >= 1

    def test_search_no_results(self, memory_tool):
        """Search with no matches returns empty memories list."""
        result = memory_tool.execute({"action": "search", "query": "xyz_nothing"})
        assert result.status == "success"
        assert result.result["memories"] == []

    def test_search_missing_query(self, memory_tool):
        """Search without query param should fail."""
        result = memory_tool.execute({"action": "search"})
        assert result.status == "error"

    def test_search_empty_query(self, memory_tool):
        """Search with empty string query should fail."""
        result = memory_tool.execute({"action": "search", "query": ""})
        assert result.status == "error"


class TestMemoryToolAdd:
    """Test the add action of EvolutionMemoryTool."""

    def test_add_success(self, memory_tool):
        """Add should succeed and return a success message."""
        result = memory_tool.execute({"action": "add", "content": "Remember this"})
        assert result.status == "success"
        assert "记忆已添加" in result.result

    def test_add_with_metadata(self, memory_tool):
        """Add with metadata should succeed."""
        result = memory_tool.execute({
            "action": "add",
            "content": "Daily reflection note",
            "metadata": {"type": "reflection", "date": "2026-03-10"},
        })
        assert result.status == "success"

    def test_add_missing_content(self, memory_tool):
        """Add without content should fail."""
        result = memory_tool.execute({"action": "add"})
        assert result.status == "error"

    def test_add_empty_content(self, memory_tool):
        """Add with empty content should fail."""
        result = memory_tool.execute({"action": "add", "content": ""})
        assert result.status == "error"

    def test_add_long_content_truncated_in_message(self, memory_tool):
        """Add with long content should show truncated confirmation."""
        long_text = "A" * 200
        result = memory_tool.execute({"action": "add", "content": long_text})
        assert result.status == "success"
        assert "..." in result.result


class TestMemoryToolProfile:
    """Test the profile action of EvolutionMemoryTool."""

    def test_profile_empty(self, memory_tool):
        """Profile with no memories should show placeholder text."""
        result = memory_tool.execute({"action": "profile"})
        assert result.status == "success"
        assert result.result["total_memories"] == 0

    def test_profile_with_data(self, memory_tool):
        """Profile should include previously added memories."""
        memory_tool.execute({"action": "add", "content": "User likes hiking"})
        memory_tool.execute({"action": "add", "content": "User is 25 years old"})
        result = memory_tool.execute({"action": "profile"})
        assert result.status == "success"
        assert result.result["total_memories"] == 2
        assert "hiking" in result.result["profile"]


class TestMemoryToolInvalidAction:
    """Test error handling for invalid actions."""

    def test_unknown_action(self, memory_tool):
        """Unknown action should return error."""
        result = memory_tool.execute({"action": "delete"})
        assert result.status == "error"

    def test_no_action(self, memory_tool):
        """Missing action key should return error."""
        result = memory_tool.execute({})
        assert result.status == "error"


class TestMemoryToolExecuteTool:
    """Test the execute_tool wrapper (from BaseTool)."""

    def test_execute_tool_catches_exception(self):
        """execute_tool should catch exceptions and return error."""
        tool = EvolutionMemoryTool()
        tool._memory = MockMemory()
        tool._user_id = "u"
        # Monkey-patch execute to raise
        original = tool.execute
        def boom(params):
            raise RuntimeError("boom")
        tool.execute = boom
        result = tool.execute_tool({"action": "search", "query": "x"})
        assert result.status == "error"
        tool.execute = original
