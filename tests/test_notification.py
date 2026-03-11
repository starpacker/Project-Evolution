"""Tests for evolution.notification.router.

Covers NotificationRouter priority routing, EmailChannel, TelegramChannel,
NotionChannel, and channel failure handling.
"""

from unittest.mock import MagicMock, patch

import pytest

from evolution.notification.router import (
    BaseChannel,
    EmailChannel,
    Notification,
    NotificationRouter,
    NotifyPriority,
    NotionChannel,
    TelegramChannel,
)


# ──────────────────────────────────────────────
# Notification / Priority dataclasses
# ──────────────────────────────────────────────
class TestNotificationModel:
    """Basic Notification model tests."""

    def test_create_notification(self):
        """Notification should store all fields."""
        n = Notification(
            title="Test",
            body="Body text",
            priority=NotifyPriority.HIGH,
            category="schedule",
        )
        assert n.title == "Test"
        assert n.priority == NotifyPriority.HIGH
        assert n.metadata == {}

    def test_priority_values(self):
        """All priority levels should have correct string values."""
        assert NotifyPriority.LOW.value == "low"
        assert NotifyPriority.NORMAL.value == "normal"
        assert NotifyPriority.HIGH.value == "high"
        assert NotifyPriority.CRITICAL.value == "critical"


# ──────────────────────────────────────────────
# EmailChannel
# ──────────────────────────────────────────────
class TestEmailChannel:
    """Test EmailChannel with mocked SMTP."""

    def _make_channel(self):
        return EmailChannel({
            "smtp_server": "smtp.test.com",
            "smtp_port": 465,
            "username": "user@test.com",
            "password": "pass",
            "to_address": "dest@test.com",
        })

    def test_should_handle_priorities(self):
        """Email handles NORMAL, HIGH, CRITICAL but not LOW."""
        ch = self._make_channel()
        assert ch.should_handle(NotifyPriority.LOW) is False
        assert ch.should_handle(NotifyPriority.NORMAL) is True
        assert ch.should_handle(NotifyPriority.HIGH) is True
        assert ch.should_handle(NotifyPriority.CRITICAL) is True

    @patch("smtplib.SMTP_SSL")
    def test_send_success(self, mock_smtp_cls):
        """Successful email send returns True."""
        mock_srv = MagicMock()
        mock_smtp_cls.return_value.__enter__ = MagicMock(return_value=mock_srv)
        mock_smtp_cls.return_value.__exit__ = MagicMock(return_value=False)
        ch = self._make_channel()
        n = Notification("Title", "Body", NotifyPriority.HIGH, "schedule")
        assert ch.send(n) is True

    @patch("smtplib.SMTP_SSL", side_effect=Exception("Connection refused"))
    def test_send_failure(self, mock_smtp_cls):
        """SMTP failure returns False, not exception."""
        ch = self._make_channel()
        n = Notification("Title", "Body", NotifyPriority.HIGH, "schedule")
        assert ch.send(n) is False


# ──────────────────────────────────────────────
# TelegramChannel
# ──────────────────────────────────────────────
class TestTelegramChannel:
    """Test TelegramChannel with mocked httpx."""

    def _make_channel(self):
        return TelegramChannel({"bot_token": "fake", "chat_id": "123"})

    def test_should_handle_priorities(self):
        """Telegram handles HIGH and CRITICAL only."""
        ch = self._make_channel()
        assert ch.should_handle(NotifyPriority.LOW) is False
        assert ch.should_handle(NotifyPriority.NORMAL) is False
        assert ch.should_handle(NotifyPriority.HIGH) is True
        assert ch.should_handle(NotifyPriority.CRITICAL) is True

    @patch("httpx.post")
    def test_send_success(self, mock_post):
        """Successful Telegram send returns True."""
        mock_post.return_value = MagicMock(status_code=200)
        ch = self._make_channel()
        n = Notification("Alert", "Urgent", NotifyPriority.HIGH, "schedule")
        assert ch.send(n) is True
        mock_post.assert_called_once()

    @patch("httpx.post")
    def test_send_api_error(self, mock_post):
        """Non-200 status returns False."""
        mock_post.return_value = MagicMock(status_code=400, text="Bad request")
        ch = self._make_channel()
        n = Notification("Alert", "Body", NotifyPriority.HIGH, "schedule")
        assert ch.send(n) is False

    @patch("httpx.post", side_effect=Exception("Network error"))
    def test_send_network_error(self, mock_post):
        """Exception during send returns False."""
        ch = self._make_channel()
        n = Notification("Alert", "Body", NotifyPriority.HIGH, "schedule")
        assert ch.send(n) is False


# ──────────────────────────────────────────────
# NotionChannel
# ──────────────────────────────────────────────
class TestNotionChannel:
    """Test NotionChannel with mocked httpx."""

    def _make_channel(self):
        return NotionChannel({
            "token": "fake-token",
            "databases": {
                "reflection": "db-ref-id",
                "schedule": "db-sched-id",
            },
        })

    def test_should_handle_priorities(self):
        """Notion handles LOW, NORMAL, CRITICAL but not HIGH."""
        ch = self._make_channel()
        assert ch.should_handle(NotifyPriority.LOW) is True
        assert ch.should_handle(NotifyPriority.NORMAL) is True
        assert ch.should_handle(NotifyPriority.HIGH) is False
        assert ch.should_handle(NotifyPriority.CRITICAL) is True

    @patch("httpx.post")
    def test_send_success(self, mock_post):
        """Successful Notion page creation returns True."""
        mock_post.return_value = MagicMock(status_code=200)
        ch = self._make_channel()
        n = Notification("Reflect", "Content", NotifyPriority.NORMAL, "reflection", {"date": "2026-03-10"})
        assert ch.send(n) is True

    @patch("httpx.post")
    def test_send_no_database_for_category(self, mock_post):
        """Category without configured database returns False."""
        ch = self._make_channel()
        n = Notification("Title", "Body", NotifyPriority.LOW, "unknown_category")
        assert ch.send(n) is False
        mock_post.assert_not_called()

    @patch("httpx.post", side_effect=Exception("timeout"))
    def test_send_network_error(self, mock_post):
        """Exception during send returns False."""
        ch = self._make_channel()
        n = Notification("Title", "Body", NotifyPriority.LOW, "reflection")
        assert ch.send(n) is False


# ──────────────────────────────────────────────
# NotificationRouter
# ──────────────────────────────────────────────
class TestNotificationRouter:
    """Test NotificationRouter priority-based routing."""

    def test_no_channels_enabled(self):
        """Router with no channels enabled sends nothing."""
        router = NotificationRouter(config={})
        assert router.channels == []
        result = router.send(Notification("T", "B", NotifyPriority.HIGH, "schedule"))
        assert result == {}

    def test_all_channels_enabled(self, notification_config):
        """Router with all channels should instantiate 3 channels."""
        with patch("smtplib.SMTP_SSL"):
            router = NotificationRouter(config=notification_config)
        assert len(router.channels) == 3

    def test_priority_routing_high(self, notification_config):
        """HIGH priority routes to email + telegram, not notion."""
        router = NotificationRouter(config=notification_config)
        n = Notification("Alert", "Body", NotifyPriority.HIGH, "schedule")
        # Mock all channel sends
        for ch in router.channels:
            ch.send = MagicMock(return_value=True)
        result = router.send(n)
        for ch in router.channels:
            if ch.name in ("email", "telegram"):
                ch.send.assert_called_once()
            elif ch.name == "notion":
                ch.send.assert_not_called()

    def test_priority_routing_low(self, notification_config):
        """LOW priority routes only to notion."""
        router = NotificationRouter(config=notification_config)
        n = Notification("Intel", "Body", NotifyPriority.LOW, "intelligence")
        for ch in router.channels:
            ch.send = MagicMock(return_value=True)
        result = router.send(n)
        for ch in router.channels:
            if ch.name == "notion":
                ch.send.assert_called_once()
            else:
                ch.send.assert_not_called()

    def test_channel_failure_does_not_block_others(self, notification_config):
        """If one channel fails, other channels should still be tried."""
        router = NotificationRouter(config=notification_config)
        n = Notification("Crit", "Body", NotifyPriority.CRITICAL, "anomaly")
        call_log = []
        for ch in router.channels:
            if ch.name == "email":
                ch.send = MagicMock(side_effect=Exception("SMTP down"))
            else:
                ch.send = MagicMock(return_value=True)
        result = router.send(n)
        assert result.get("email") is False
        # At least one other channel should have succeeded
        non_email = {k: v for k, v in result.items() if k != "email"}
        assert any(v is True for v in non_email.values())

    def test_send_all_ignores_priority(self, notification_config):
        """send_all sends to every channel regardless of priority."""
        router = NotificationRouter(config=notification_config)
        n = Notification("Forced", "Body", NotifyPriority.LOW, "reflection")
        for ch in router.channels:
            ch.send = MagicMock(return_value=True)
        result = router.send_all(n)
        assert len(result) == 3
        for ch in router.channels:
            ch.send.assert_called_once()
