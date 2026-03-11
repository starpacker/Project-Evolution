"""Tests for evolution.tools.intelligence_tool.EvolutionIntelligenceTool.

Covers RSS parsing, HTML cleaning, feed management, briefing, error handling.
"""

import json
from unittest.mock import MagicMock, patch

import pytest

from evolution.tools.intelligence_tool import EvolutionIntelligenceTool


# ──────────────────────────────────────────────
# HTML cleaning
# ──────────────────────────────────────────────
class TestCleanHtml:
    """Validate _clean_html static method."""

    def test_strip_tags(self):
        """HTML tags should be removed."""
        assert EvolutionIntelligenceTool._clean_html("<p>Hello</p>") == "Hello"

    def test_strip_nested_tags(self):
        """Nested HTML should be flattened."""
        html = "<div><b>Bold</b> and <i>italic</i></div>"
        result = EvolutionIntelligenceTool._clean_html(html)
        assert "Bold" in result and "italic" in result
        assert "<" not in result

    def test_collapse_whitespace(self):
        """Multiple spaces / newlines should become a single space."""
        assert EvolutionIntelligenceTool._clean_html("a   \n\n  b") == "a b"

    def test_empty_string(self):
        """Empty input returns empty output."""
        assert EvolutionIntelligenceTool._clean_html("") == ""


# ──────────────────────────────────────────────
# _extract_json
# ──────────────────────────────────────────────
class TestExtractJsonIntelligence:
    """Verify JSON extraction helper."""

    def test_plain_json(self):
        """Pure JSON should pass through."""
        raw = '{"key": 1}'
        assert EvolutionIntelligenceTool._extract_json(raw) == '{"key": 1}'

    def test_fenced_json(self):
        """Markdown-fenced JSON should be unwrapped."""
        raw = '```json\n{"a": 2}\n```'
        assert json.loads(EvolutionIntelligenceTool._extract_json(raw)) == {"a": 2}


# ──────────────────────────────────────────────
# RSS parsing
# ──────────────────────────────────────────────
RSS_20_XML = """<?xml version="1.0"?>
<rss version="2.0">
  <channel>
    <item>
      <title>Article One</title>
      <description>&lt;p&gt;Summary of article one&lt;/p&gt;</description>
      <link>https://example.com/1</link>
    </item>
    <item>
      <title>Article Two</title>
      <description>Plain text summary</description>
      <link>https://example.com/2</link>
    </item>
  </channel>
</rss>
"""

ATOM_XML = """<?xml version="1.0"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <entry>
    <title>Atom Entry</title>
    <summary>Atom summary text</summary>
    <link href="https://example.com/atom/1"/>
  </entry>
</feed>
"""


class TestRSSParsing:
    """Test _parse_rss with mocked HTTP responses."""

    def test_parse_rss_20(self, intelligence_tool):
        """RSS 2.0 XML should be parsed into item dicts."""
        mock_resp = MagicMock()
        mock_resp.text = RSS_20_XML
        mock_resp.raise_for_status = MagicMock()
        with patch("httpx.get", return_value=mock_resp):
            items = intelligence_tool._parse_rss("http://fake", "TestSource")
        assert len(items) == 2
        assert items[0]["title"] == "Article One"
        assert items[0]["source"] == "TestSource"
        assert "https://example.com/1" in items[0]["link"]

    def test_parse_atom(self, intelligence_tool):
        """Atom feed should be parsed correctly."""
        mock_resp = MagicMock()
        mock_resp.text = ATOM_XML
        mock_resp.raise_for_status = MagicMock()
        with patch("httpx.get", return_value=mock_resp):
            items = intelligence_tool._parse_rss("http://fake-atom", "AtomSource")
        assert len(items) == 1
        assert items[0]["title"] == "Atom Entry"
        assert items[0]["link"] == "https://example.com/atom/1"

    def test_parse_rss_network_error(self, intelligence_tool):
        """Network error should return empty list, not raise."""
        with patch("httpx.get", side_effect=Exception("timeout")):
            items = intelligence_tool._parse_rss("http://down", "Dead")
        assert items == []


# ──────────────────────────────────────────────
# Feed management
# ──────────────────────────────────────────────
class TestFeedManagement:
    """Test add_feed and list_feeds actions."""

    def test_add_feed_success(self, intelligence_tool):
        """add_feed with name and url should succeed."""
        r = intelligence_tool.execute({
            "action": "add_feed",
            "name": "Test Feed",
            "url": "http://example.com/rss",
            "category": "tech",
        })
        assert r.status == "success"
        assert "Test Feed" in r.result

    def test_add_feed_missing_params(self, intelligence_tool):
        """add_feed without name or url should fail."""
        r = intelligence_tool.execute({"action": "add_feed", "name": "No URL"})
        assert r.status == "error"

    def test_list_feeds(self, intelligence_tool):
        """list_feeds should include default and extra feeds."""
        intelligence_tool._extra_feeds.append({"name": "Extra", "url": "http://x", "category": "x"})
        r = intelligence_tool.execute({"action": "list_feeds"})
        assert r.status == "success"
        assert "Extra" in r.result

    def test_add_then_list(self, intelligence_tool):
        """Dynamically added feed should appear in list."""
        intelligence_tool.execute({
            "action": "add_feed",
            "name": "Dynamic",
            "url": "http://d",
            "category": "misc",
        })
        r = intelligence_tool.execute({"action": "list_feeds"})
        assert "Dynamic" in r.result


# ──────────────────────────────────────────────
# Briefing
# ──────────────────────────────────────────────
class TestBriefing:
    """Test briefing generation with mocked HTTP and LLM."""

    def test_briefing_no_feeds_accessible(self, intelligence_tool):
        """If all RSS feeds fail, briefing should return a fallback message."""
        with patch("httpx.get", side_effect=Exception("network error")):
            intelligence_tool._extra_feeds = []
            # Override _get_feeds to use only one feed
            intelligence_tool._get_feeds = MagicMock(
                return_value=[{"name": "F", "url": "http://f", "category": "x"}]
            )
            r = intelligence_tool.execute({"action": "briefing"})
        assert r.status == "success"
        assert "暂时无法访问" in r.result.get("briefing_text", r.result)

    def test_briefing_with_llm(self, intelligence_tool):
        """Briefing with working RSS and LLM should return parsed result."""
        mock_resp = MagicMock()
        mock_resp.text = RSS_20_XML
        mock_resp.raise_for_status = MagicMock()
        intelligence_tool._get_feeds = MagicMock(
            return_value=[{"name": "Test", "url": "http://test", "category": "tech"}]
        )
        llm_result = json.dumps({
            "has_relevant": True,
            "briefing_text": "Today's top story: Article One",
        })
        with patch("httpx.get", return_value=mock_resp):
            intelligence_tool._call_llm = MagicMock(return_value=llm_result)
            # Mock the notification sending
            with patch.object(intelligence_tool, "_send_briefing_notification"):
                r = intelligence_tool.execute({"action": "briefing"})
        assert r.status == "success"


# ──────────────────────────────────────────────
# Error handling
# ──────────────────────────────────────────────
class TestIntelligenceErrors:
    """Test error paths."""

    def test_invalid_action(self, intelligence_tool):
        """Unknown action should fail."""
        r = intelligence_tool.execute({"action": "destroy"})
        assert r.status == "error"

    def test_missing_action(self, intelligence_tool):
        """Missing action should fail."""
        r = intelligence_tool.execute({})
        assert r.status == "error"
