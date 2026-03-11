"""
Telegram Bot 双向对话接口
轻量级实现，支持与 Evolution Agent 的完整交互
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Optional

import httpx

from evolution.config.settings import NOTIFICATION_CONFIG
from evolution.db.manager import DatabaseManager
from evolution.tools.memory_tool import EvolutionMemoryTool
from evolution.tools.db_tool import EvolutionDBTool
from evolution.tools.reflection_tool import EvolutionReflectionTool
from evolution.tools.intelligence_tool import EvolutionIntelligenceTool
from evolution.utils.llm import call_claude_api
from evolution.config.prompts import SYSTEM_PROMPT

logger = logging.getLogger("evolution.chat.telegram")


class TelegramBot:
    """轻量级 Telegram Bot - 使用 Long Polling 模式"""

    def __init__(self):
        tg_config = NOTIFICATION_CONFIG.get("telegram", {})
        self.bot_token = tg_config.get("bot_token", "")
        self.chat_id = tg_config.get("chat_id", "")
        
        if not self.bot_token:
            raise ValueError("Telegram bot_token not configured")
        
        self.api_base = f"https://api.telegram.org/bot{self.bot_token}"
        self.db = DatabaseManager()
        
        # 初始化工具
        self.tools = {
            "memory": EvolutionMemoryTool(),
            "db": EvolutionDBTool(),
            "reflection": EvolutionReflectionTool(),
            "intelligence": EvolutionIntelligenceTool(),
        }
        
        self.last_update_id = 0
        logger.info("[TelegramBot] Initialized successfully")

    async def send_message(self, text: str, chat_id: Optional[str] = None) -> bool:
        """发送消息到 Telegram"""
        target_chat = chat_id or self.chat_id
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"{self.api_base}/sendMessage",
                    json={
                        "chat_id": target_chat,
                        "text": text[:4096],
                        "parse_mode": "Markdown",
                    },
                    timeout=10,
                )
                return resp.status_code == 200
        except Exception as e:
            logger.error(f"[TelegramBot] Send failed: {e}")
            return False

    async def get_updates(self, timeout: int = 30) -> list:
        """获取新消息（Long Polling）"""
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"{self.api_base}/getUpdates",
                    json={
                        "offset": self.last_update_id + 1,
                        "timeout": timeout,
                        "allowed_updates": ["message"],
                    },
                    timeout=timeout + 5,
                )
                if resp.status_code == 200:
                    data = resp.json()
                    return data.get("result", [])
                return []
        except Exception as e:
            logger.error(f"[TelegramBot] Get updates failed: {e}")
            return []

    def _parse_tool_call(self, text: str) -> Optional[dict]:
        """
        解析用户消息中的工具调用意图
        例如：
        - "提醒我明天下午3点开会" -> schedule tool
        - "我今天做了什么" -> db tool (list_schedule)
        - "搜索我之前说过的关于论文的事" -> memory tool
        """
        text_lower = text.lower()
        
        # 日程相关
        if any(kw in text_lower for kw in ["提醒", "日程", "待办", "明天", "下周"]):
            return {"tool": "db", "action": "add_schedule", "raw_text": text}
        
        if any(kw in text_lower for kw in ["今天做什么", "今日日程", "今天有什么安排"]):
            return {"tool": "db", "action": "list_schedule"}
        
        # 记忆搜索
        if any(kw in text_lower for kw in ["搜索", "之前", "记得", "我说过"]):
            query = text.replace("搜索", "").replace("之前", "").strip()
            return {"tool": "memory", "action": "search", "query": query}
        
        # 情报
        if any(kw in text_lower for kw in ["情报", "新闻", "今日简报"]):
            return {"tool": "intelligence", "action": "briefing"}
        
        # 反思
        if any(kw in text_lower for kw in ["今日反思", "每日总结"]):
            return {"tool": "reflection", "action": "daily"}
        
        return None

    def _execute_tool(self, tool_call: dict) -> str:
        """执行工具调用"""
        tool_name = tool_call.get("tool")
        tool = self.tools.get(tool_name)
        
        if not tool:
            return f"工具 {tool_name} 不存在"
        
        try:
            params = {k: v for k, v in tool_call.items() if k != "tool"}
            result = tool.execute(params)
            
            if result.status == "success":
                return result.data
            else:
                return f"工具执行失败: {result.message}"
        except Exception as e:
            logger.error(f"[TelegramBot] Tool execution error: {e}")
            return f"工具执行出错: {str(e)}"

    async def _generate_response(self, user_message: str) -> str:
        """生成 AI 回复"""
        # 1. 检查是否需要调用工具
        tool_call = self._parse_tool_call(user_message)
        tool_context = ""
        
        if tool_call:
            logger.info(f"[TelegramBot] Detected tool call: {tool_call}")
            tool_result = self._execute_tool(tool_call)
            tool_context = f"\n\n[工具执行结果]\n{tool_result}\n"
        
        # 2. 搜索相关记忆
        memory_context = ""
        try:
            memory_result = self.tools["memory"].execute({
                "action": "search",
                "query": user_message[:100]
            })
            if memory_result.status == "success" and memory_result.data:
                memories = json.loads(memory_result.data).get("memories", [])
                if memories:
                    memory_context = "\n[相关记忆]\n" + "\n".join(
                        f"- {m.get('memory', '')}" for m in memories[:3]
                    ) + "\n"
        except Exception as e:
            logger.warning(f"[TelegramBot] Memory search failed: {e}")
        
        # 3. 构建 prompt
        prompt = f"""用户消息: {user_message}
{memory_context}{tool_context}
请以 Evolution 导师的身份回复用户。遵循你的人格设定：克制、深邃、不废话。
如果工具已经提供了信息，基于这些信息给出洞察，而不是重复数据。
"""
        
        # 4. 调用 LLM
        response = call_claude_api(prompt, max_tokens=1000, system=SYSTEM_PROMPT)
        
        if not response:
            return "抱歉，我现在无法思考。LLM 服务暂时不可用。"
        
        # 5. 记录对话
        try:
            self.db.log_conversation("user", user_message)
            self.db.log_conversation("assistant", response)
        except Exception as e:
            logger.warning(f"[TelegramBot] Failed to log conversation: {e}")
        
        return response

    async def handle_message(self, message: dict):
        """处理单条消息"""
        try:
            chat_id = str(message["chat"]["id"])
            text = message.get("text", "").strip()
            
            if not text:
                return
            
            # 只响应配置的 chat_id（安全性）
            if self.chat_id and chat_id != self.chat_id:
                logger.warning(f"[TelegramBot] Ignored message from unauthorized chat: {chat_id}")
                return
            
            logger.info(f"[TelegramBot] Received: {text[:50]}...")
            
            # 特殊命令
            if text == "/start":
                await self.send_message(
                    "👋 Evolution 已启动\n\n"
                    "我是你的 7×24 智慧导师，同时扮演：\n"
                    "🗓️ 秘书 | 🧠 导师 | 🏋️ 训练师 | 💑 情感助手 | 📡 情报收集者\n\n"
                    "直接和我对话即可。",
                    chat_id
                )
                return
            
            if text == "/help":
                await self.send_message(
                    "💡 使用提示：\n\n"
                    "• 直接对话：任何问题或想法\n"
                    "• 日程管理：「提醒我明天3点开会」\n"
                    "• 查看日程：「今天做什么」\n"
                    "• 搜索记忆：「搜索我之前说的论文」\n"
                    "• 获取情报：「今日情报」\n"
                    "• 每日反思：「今日反思」\n\n"
                    "我会记住我们的每次对话。",
                    chat_id
                )
                return
            
            # 生成回复
            response = await self._generate_response(text)
            await self.send_message(response, chat_id)
            
        except Exception as e:
            logger.error(f"[TelegramBot] Handle message error: {e}", exc_info=True)
            try:
                await self.send_message(
                    "抱歉，处理你的消息时出现了错误。请稍后再试。",
                    chat_id
                )
            except:
                pass

    async def run(self):
        """启动 Bot（Long Polling 模式）"""
        logger.info("[TelegramBot] Starting bot with Long Polling...")
        
        # 发送启动通知
        try:
            await self.send_message("🟢 Evolution Bot 已启动，随时待命。")
        except:
            pass
        
        while True:
            try:
                updates = await self.get_updates()
                
                for update in updates:
                    self.last_update_id = update["update_id"]
                    
                    if "message" in update:
                        await self.handle_message(update["message"])
                
            except KeyboardInterrupt:
                logger.info("[TelegramBot] Shutting down...")
                try:
                    await self.send_message("🔴 Evolution Bot 已停止。")
                except:
                    pass
                break
            except Exception as e:
                logger.error(f"[TelegramBot] Main loop error: {e}")
                await asyncio.sleep(5)


def main():
    """启动 Telegram Bot"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )
    
    bot = TelegramBot()
    asyncio.run(bot.run())


if __name__ == "__main__":
    main()
