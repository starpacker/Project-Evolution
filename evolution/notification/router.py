"""
统一通知路由器 — 所有推送的唯一出口
根据优先级自动路由到邮件 / Telegram / Notion
"""

import json
import logging
import smtplib
from dataclasses import dataclass, field
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from enum import Enum
from typing import Any, Dict, List, Optional

import httpx

logger = logging.getLogger("evolution.notification")


class NotifyPriority(Enum):
    LOW = "low"  # 情报摘要 → 仅 Notion
    NORMAL = "normal"  # 每日反思、周报 → 邮件 + Notion
    HIGH = "high"  # 日程提醒 → 邮件 + Telegram
    CRITICAL = "critical"  # 异常检测 → 全通道


@dataclass
class Notification:
    title: str
    body: str
    priority: NotifyPriority
    category: str  # reflection | schedule | intelligence | report | training | anomaly
    metadata: Dict[str, Any] = field(default_factory=dict)


# ──────────────────────────────────────────────
# 通道基类
# ──────────────────────────────────────────────
class BaseChannel:
    name: str = "base"

    PRIORITY_MAP: Dict[NotifyPriority, bool] = {}

    def should_handle(self, priority: NotifyPriority) -> bool:
        return self.PRIORITY_MAP.get(priority, False)

    def send(self, notification: Notification) -> bool:
        raise NotImplementedError


# ──────────────────────────────────────────────
# 邮件通道
# ──────────────────────────────────────────────
class EmailChannel(BaseChannel):
    name = "email"
    PRIORITY_MAP = {
        NotifyPriority.LOW: False,
        NotifyPriority.NORMAL: True,
        NotifyPriority.HIGH: True,
        NotifyPriority.CRITICAL: True,
    }

    def __init__(self, config: dict):
        self.server = config["smtp_server"]
        self.port = config["smtp_port"]
        self.username = config["username"]
        self.password = config["password"]
        self.to_addr = config["to_address"]
        self.prefix = config.get("subject_prefix", "[Evolution]")

    def send(self, notification: Notification) -> bool:
        try:
            html_body = self._markdown_to_html(notification.body)
            msg = MIMEMultipart("alternative")
            msg["Subject"] = f"{self.prefix} {notification.title}"
            msg["From"] = self.username
            msg["To"] = self.to_addr
            msg.attach(MIMEText(notification.body, "plain", "utf-8"))
            msg.attach(MIMEText(html_body, "html", "utf-8"))
            with smtplib.SMTP_SSL(self.server, self.port, timeout=15) as srv:
                srv.login(self.username, self.password)
                srv.send_message(msg)
            logger.info(f"[Email] Sent: {notification.title}")
            return True
        except Exception as e:
            logger.error(f"[Email] Failed: {e}")
            return False

    @staticmethod
    def _markdown_to_html(md_text: str) -> str:
        try:
            import markdown
            return markdown.markdown(md_text, extensions=["tables", "fenced_code"])
        except ImportError:
            return f"<pre>{md_text}</pre>"


# ──────────────────────────────────────────────
# Telegram 通道
# ──────────────────────────────────────────────
class TelegramChannel(BaseChannel):
    name = "telegram"
    PRIORITY_MAP = {
        NotifyPriority.LOW: False,
        NotifyPriority.NORMAL: False,
        NotifyPriority.HIGH: True,
        NotifyPriority.CRITICAL: True,
    }

    def __init__(self, config: dict):
        self.bot_token = config["bot_token"]
        self.chat_id = config["chat_id"]
        self.api_url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"

    def send(self, notification: Notification) -> bool:
        try:
            text = f"*{notification.title}*\n\n{notification.body}"
            resp = httpx.post(
                self.api_url,
                json={
                    "chat_id": self.chat_id,
                    "text": text[:4096],
                    "parse_mode": "Markdown",
                },
                timeout=10,
            )
            if resp.status_code == 200:
                logger.info(f"[Telegram] Sent: {notification.title}")
                return True
            else:
                logger.error(f"[Telegram] Failed: {resp.text}")
                return False
        except Exception as e:
            logger.error(f"[Telegram] Failed: {e}")
            return False


# ──────────────────────────────────────────────
# Notion 通道
# ──────────────────────────────────────────────
class NotionChannel(BaseChannel):
    name = "notion"
    PRIORITY_MAP = {
        NotifyPriority.LOW: True,
        NotifyPriority.NORMAL: True,
        NotifyPriority.HIGH: False,
        NotifyPriority.CRITICAL: True,
    }

    def __init__(self, config: dict):
        self.token = config["token"]
        self.databases = config.get("databases", {})
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28",
        }

    def send(self, notification: Notification) -> bool:
        db_id = self.databases.get(notification.category)
        if not db_id:
            logger.warning(
                f"[Notion] No database configured for category: {notification.category}"
            )
            return False
        try:
            payload = {
                "parent": {"database_id": db_id},
                "properties": {
                    "Name": {
                        "title": [{"text": {"content": notification.title[:100]}}]
                    },
                },
                "children": [
                    {
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": [
                                {"text": {"content": notification.body[:2000]}}
                            ]
                        },
                    }
                ],
            }
            # Add date property if available
            date_val = notification.metadata.get("date")
            if date_val:
                payload["properties"]["Date"] = {"date": {"start": date_val}}

            resp = httpx.post(
                "https://api.notion.com/v1/pages",
                headers=self.headers,
                json=payload,
                timeout=15,
            )
            if resp.status_code == 200:
                logger.info(f"[Notion] Created page: {notification.title}")
                return True
            else:
                logger.error(f"[Notion] Failed: {resp.text[:200]}")
                return False
        except Exception as e:
            logger.error(f"[Notion] Failed: {e}")
            return False


# ──────────────────────────────────────────────
# 统一路由器
# ──────────────────────────────────────────────
class NotificationRouter:
    """统一通知路由器"""

    def __init__(self, config: Optional[dict] = None):
        if config is None:
            from evolution.config.settings import NOTIFICATION_CONFIG
            config = NOTIFICATION_CONFIG

        self.channels: List[BaseChannel] = []

        if config.get("email", {}).get("enabled"):
            self.channels.append(EmailChannel(config["email"]))
            logger.info("[NotificationRouter] Email channel enabled")

        if config.get("telegram", {}).get("enabled"):
            self.channels.append(TelegramChannel(config["telegram"]))
            logger.info("[NotificationRouter] Telegram channel enabled")

        if config.get("notion", {}).get("enabled"):
            self.channels.append(NotionChannel(config["notion"]))
            logger.info("[NotificationRouter] Notion channel enabled")

        if not self.channels:
            logger.warning("[NotificationRouter] No notification channels enabled")

    def send(self, notification: Notification) -> Dict[str, bool]:
        """根据优先级路由到对应通道"""
        results = {}
        for channel in self.channels:
            if channel.should_handle(notification.priority):
                try:
                    ok = channel.send(notification)
                    results[channel.name] = ok
                except Exception as e:
                    logger.error(f"[NotificationRouter] {channel.name} error: {e}")
                    results[channel.name] = False
        return results

    def send_all(self, notification: Notification) -> Dict[str, bool]:
        """强制发送到所有通道（忽略优先级过滤）"""
        results = {}
        for channel in self.channels:
            try:
                ok = channel.send(notification)
                results[channel.name] = ok
            except Exception as e:
                logger.error(f"[NotificationRouter] {channel.name} error: {e}")
                results[channel.name] = False
        return results
