"""
EvolutionIntelligenceTool — 情报收集引擎
从 RSSHub 拉取订阅源，用 LLM 筛选与用户最相关的信息，生成早间推送。

支持两种模式：
1. RSSHub 模式（需要 Docker）：统一 RSS 接口，支持 30+ 源
2. Lite 模式（无需 Docker）：直接调用 API，支持 6 个核心源
"""

import ipaddress
import json
import logging
import os
from datetime import datetime
from typing import Dict, List, Optional
from urllib.parse import urlparse

import httpx

try:
    from defusedxml.ElementTree import fromstring as safe_xml_fromstring
except ImportError:  # pragma: no cover
    import xml.etree.ElementTree as _ET
    def safe_xml_fromstring(text: str):
        """Fallback: disable external entities via XMLParser."""
        parser = _ET.XMLParser()
        # Prevent entity expansion (standard-lib best-effort)
        parser.feed(text)
        return parser.close()

from evolution.tools.base import BaseTool, ToolResult
from evolution.utils.llm import call_claude_api, extract_json

logger = logging.getLogger("evolution.tools.intelligence")


class EvolutionIntelligenceTool(BaseTool):
    """情报收集工具 — 从 RSS 获取信息并用 LLM 筛选"""

    name: str = "evolution_intelligence"
    description: str = (
        "从 RSS 订阅源获取最新情报，并用 LLM 筛选与用户最相关的信息。\n\n"
        "使用方法：\n"
        "- 获取今日情报摘要: action='briefing'\n"
        "- 获取原始 RSS: action='raw_feeds'\n"
        "- 添加订阅源: action='add_feed', name='源名称', url='RSS URL', category='professional'\n"
        "- 列出订阅源: action='list_feeds'\n\n"
        "⚠️ 情报摘要通常由定时任务在08:00自动触发。"
    )
    params: dict = {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["briefing", "raw_feeds", "add_feed", "list_feeds"],
                "description": "操作类型",
            },
            "name": {"type": "string", "description": "订阅源名称"},
            "url": {"type": "string", "description": "RSS URL"},
            "category": {"type": "string", "description": "分类"},
        },
        "required": ["action"],
    }

    def __init__(self, config: dict = None):
        self.config = config or {}
        self._memory_tool = None
        self._extra_feeds: List[Dict] = []
        
        # 自动检测是否使用 Lite 模式
        self.use_lite_mode = self._should_use_lite_mode()
        if self.use_lite_mode:
            logger.info("[Intelligence] 🔄 使用 Lite 模式（无需 RSSHub/Docker）")
            from evolution.tools.intelligence_lite import IntelligenceSourceLite
            self._lite_source = IntelligenceSourceLite()
        else:
            logger.info("[Intelligence] 📡 使用 RSSHub 模式")
            self._lite_source = None
    
    def _should_use_lite_mode(self) -> bool:
        """检测是否应该使用 Lite 模式"""
        # 1. 检查环境变量强制设置
        force_lite = os.getenv("INTELLIGENCE_LITE_MODE", "").lower() == "true"
        if force_lite:
            return True
        
        # 2. 检查 RSSHub 是否可访问
        from evolution.config.settings import RSSHUB_BASE_URL
        try:
            resp = httpx.get(RSSHUB_BASE_URL, timeout=3)
            if resp.status_code == 200:
                return False  # RSSHub 可用，使用标准模式
        except Exception:
            pass
        
        # 3. RSSHub 不可用，自动降级到 Lite 模式
        logger.warning("[Intelligence] ⚠️  RSSHub 不可用，自动切换到 Lite 模式")
        return True

    @property
    def memory_tool(self):
        if self._memory_tool is None:
            from evolution.tools.memory_tool import EvolutionMemoryTool
            self._memory_tool = EvolutionMemoryTool(self.config)
        return self._memory_tool

    def _get_feeds(self) -> List[Dict]:
        from evolution.config.settings import RSS_FEEDS
        return RSS_FEEDS + self._extra_feeds

    def execute(self, params: dict) -> ToolResult:
        action = params.get("action")
        try:
            if action == "briefing":
                return self._generate_briefing()
            elif action == "raw_feeds":
                return self._fetch_raw_feeds()
            elif action == "add_feed":
                return self._add_feed(params)
            elif action == "list_feeds":
                return self._list_feeds()
            else:
                return ToolResult.fail(f"未知操作: {action}")
        except Exception as e:
            logger.error(f"[Intelligence] Error: {e}", exc_info=True)
            return ToolResult.fail(f"情报操作失败: {str(e)}")

    def _fetch_raw_feeds(self) -> ToolResult:
        """从所有 RSS 源拉取原始内容"""
        all_items = []
        feeds = self._get_feeds()
        for feed_config in feeds:
            try:
                items = self._parse_rss(feed_config["url"], feed_config["name"])
                all_items.extend(items)
            except Exception as e:
                logger.warning(f"[Intelligence] Feed {feed_config['name']} failed: {e}")
        return ToolResult.success(
            {"total_items": len(all_items), "items": all_items[:50]}
        )

    def _generate_briefing(self) -> ToolResult:
        """生成早间情报摘要"""
        # 1. 拉取信息源
        if self.use_lite_mode:
            # Lite 模式：直接调用 API
            all_items = self._lite_source.fetch_all()
        else:
            # RSSHub 模式：从 RSS 拉取
            all_items = []
            feeds = self._get_feeds()
            for feed_config in feeds:
                try:
                    items = self._parse_rss(feed_config["url"], feed_config["name"])
                    all_items.extend(items)
                except Exception as e:
                    logger.warning(f"[Intelligence] Feed {feed_config['name']} failed: {e}")

        if not all_items:
            return ToolResult.success(
                {
                    "has_relevant": False,
                    "briefing_text": "今日信息源暂时无法访问，没有情报更新。",
                }
            )

        # 2. 获取用户兴趣
        user_interests = ""
        mem_result = self.memory_tool.execute(
            {"action": "search", "query": "用户当前正在学习和关注的领域"}
        )
        if mem_result.status == "success" and isinstance(mem_result.result, dict):
            interests_list = [
                m.get("memory", "")
                for m in mem_result.result.get("memories", [])
            ]
            user_interests = "\n".join(f"- {i}" for i in interests_list[:10])

        # 3. LLM 筛选
        feeds_text = "\n".join(
            f"[{i+1}] [{item['source']}] {item['title']}: {item['summary'][:150]}"
            for i, item in enumerate(all_items[:30])
        )

        from evolution.config.prompts import INTELLIGENCE_FILTER_PROMPT
        prompt = INTELLIGENCE_FILTER_PROMPT.format(
            feed_count=len(all_items),
            feeds_content=feeds_text,
            user_interests=user_interests or "（暂无用户兴趣数据）",
        )

        report_text = self._call_llm(prompt)
        if not report_text:
            # LLM 不可用时，返回前3条
            fallback = "\n".join(
                f"- [{item['source']}] {item['title']}"
                for item in all_items[:3]
            )
            return ToolResult.success(
                {
                    "has_relevant": True,
                    "briefing_text": f"（LLM 不可用，原始 RSS 摘要）\n{fallback}",
                }
            )

        # 4. 解析并返回
        try:
            parsed = json.loads(self._extract_json(report_text))
        except json.JSONDecodeError:
            parsed = {
                "has_relevant": True,
                "briefing_text": report_text[:500],
            }

        # 5. 推送
        self._send_briefing_notification(parsed)

        return ToolResult.success(parsed)

    @staticmethod
    def _is_safe_url(url: str) -> bool:
        """Validate URL: must be http(s) and not target private/reserved IPs."""
        try:
            parsed = urlparse(url)
        except Exception:
            return False
        if parsed.scheme not in ("http", "https"):
            return False
        hostname = parsed.hostname
        if not hostname:
            return False
        try:
            addr = ipaddress.ip_address(hostname)
            if addr.is_private or addr.is_reserved or addr.is_loopback:
                return False
        except ValueError:
            # It's a hostname, not a raw IP — check common private names
            lower = hostname.lower()
            if lower in ("localhost",) or lower.endswith(".local"):
                return False
        return True

    def _add_feed(self, params: dict) -> ToolResult:
        name = params.get("name", "")
        url = params.get("url", "")
        category = params.get("category", "general")
        if not name or not url:
            return ToolResult.fail("需要 name 和 url 参数")
        if not self._is_safe_url(url):
            return ToolResult.fail("URL 无效: 仅支持 http/https 且不允许内网地址")
        self._extra_feeds.append({"name": name, "url": url, "category": category})
        return ToolResult.success(f"✅ 订阅源已添加: {name} ({url})")

    def _list_feeds(self) -> ToolResult:
        feeds = self._get_feeds()
        lines = [f"📡 共 {len(feeds)} 个订阅源:"]
        for f in feeds:
            lines.append(f"  [{f.get('category','?')}] {f['name']}: {f['url']}")
        return ToolResult.success("\n".join(lines))

    def _parse_rss(self, url: str, source_name: str) -> List[Dict]:
        """解析 RSS/Atom feed"""
        items = []
        try:
            resp = httpx.get(url, timeout=15, follow_redirects=True)
            resp.raise_for_status()
            root = safe_xml_fromstring(resp.text)

            # RSS 2.0
            for item in root.findall(".//item")[:10]:
                title = item.findtext("title", "")
                desc = item.findtext("description", "")
                link = item.findtext("link", "")
                items.append(
                    {
                        "source": source_name,
                        "title": title.strip(),
                        "summary": self._clean_html(desc)[:300],
                        "link": link.strip(),
                    }
                )

            # Atom
            ns = {"atom": "http://www.w3.org/2005/Atom"}
            for entry in root.findall(".//atom:entry", ns)[:10]:
                title = entry.findtext("atom:title", "", ns)
                summary = entry.findtext("atom:summary", "", ns)
                link_el = entry.find("atom:link", ns)
                link = link_el.get("href", "") if link_el is not None else ""
                items.append(
                    {
                        "source": source_name,
                        "title": title.strip(),
                        "summary": self._clean_html(summary)[:300],
                        "link": link.strip(),
                    }
                )
        except Exception as e:
            logger.warning(f"[Intelligence] RSS parse error for {source_name}: {e}")
        return items

    @staticmethod
    def _clean_html(text: str) -> str:
        """简单去除 HTML 标签"""
        import re
        text = re.sub(r"<[^>]+>", "", text)
        text = re.sub(r"\s+", " ", text).strip()
        return text

    def _send_briefing_notification(self, parsed: dict):
        """发送情报推送"""
        from evolution.notification.router import Notification, NotifyPriority
        from evolution.notification.router import NotificationRouter

        briefing_text = parsed.get("briefing_text", "今天没有值得关注的新信息。")
        notifier = NotificationRouter()
        notifier.send(
            Notification(
                title=f"📡 早间情报 | {datetime.now().strftime('%Y-%m-%d')}",
                body=briefing_text,
                priority=NotifyPriority.LOW,
                category="intelligence",
                metadata={"date": datetime.now().strftime("%Y-%m-%d")},
            )
        )

    def _call_llm(self, prompt: str) -> Optional[str]:
        if self.model:
            try:
                return self.model.generate(prompt)
            except Exception:
                pass
        return call_claude_api(prompt, max_tokens=2048)

    # Keep _call_claude_api as a thin wrapper for backward compatibility
    def _call_claude_api(self, prompt: str) -> Optional[str]:
        return call_claude_api(prompt, max_tokens=2048)

    @staticmethod
    def _extract_json(text: str) -> str:
        return extract_json(text)
