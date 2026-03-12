"""
EvolutionMemoryTool — Mem0 记忆系统封装
CowAgent 工具接口，提供 search / add / get_profile 操作。
"""

import json
import logging
from typing import Any, Dict, Optional

from evolution.tools.base import BaseTool, ToolResult

# Apply Mem0 compatibility patches before importing Mem0
try:
    from evolution.utils.mem0_patch import apply_all_patches
    apply_all_patches()
except Exception as e:
    logging.warning(f"Could not apply Mem0 patches: {e}")

logger = logging.getLogger("evolution.tools.memory")


class EvolutionMemoryTool(BaseTool):
    """Mem0 记忆系统工具 — 搜索和管理用户的长期记忆"""

    name: str = "evolution_memory"
    description: str = (
        "搜索和管理用户的长期记忆（人物、事件、技能、目标、偏好等）。\n\n"
        "使用方法：\n"
        "- 搜索记忆：action='search', query='搜索关键词'\n"
        "- 添加记忆：action='add', content='要记住的内容', metadata={可选元数据}\n"
        "- 获取用户档案：action='profile' (返回所有记忆的概要)\n\n"
        "⚠️ 搜索记忆时会同时返回向量搜索结果和知识图谱中的关系。\n"
        "添加记忆时，Mem0 会自动从内容中提取实体和关系，写入向量库和图谱。"
    )
    params: dict = {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["search", "add", "profile"],
                "description": "操作类型: search(搜索), add(添加), profile(获取用户档案)",
            },
            "query": {
                "type": "string",
                "description": "搜索查询（用于 search 操作）",
            },
            "content": {
                "type": "string",
                "description": "要记住的内容（用于 add 操作）",
            },
            "metadata": {
                "type": "object",
                "description": "附加元数据，如 {'type': 'daily_reflection', 'date': '2026-03-10'}",
            },
        },
        "required": ["action"],
    }

    def __init__(self, config: dict = None):
        self.config = config or {}
        self._memory = None
        self._user_id = None

    @property
    def memory(self):
        if self._memory is None:
            self._init_memory()
        return self._memory

    @property
    def user_id(self):
        if self._user_id is None:
            from evolution.config.settings import USER_ID
            self._user_id = USER_ID
        return self._user_id

    def _init_memory(self):
        """延迟初始化 Mem0 客户端"""
        try:
            from mem0 import Memory
            from evolution.config.settings import MEM0_CONFIG
            self._memory = Memory.from_config(MEM0_CONFIG)
            logger.info("[EvolutionMemory] Mem0 initialized successfully")
        except ImportError:
            logger.warning("[EvolutionMemory] mem0 not installed, using mock")
            self._memory = MockMemory()
        except Exception as e:
            logger.error(f"[EvolutionMemory] Mem0 init failed: {e}, using mock")
            self._memory = MockMemory()

    def execute(self, params: dict) -> ToolResult:
        action = params.get("action")

        try:
            if action == "search":
                return self._search(params)
            elif action == "add":
                return self._add(params)
            elif action == "profile":
                return self._get_profile()
            else:
                return ToolResult.fail(f"未知操作: {action}")
        except Exception as e:
            logger.error(f"[EvolutionMemory] Error: {e}")
            return ToolResult.fail(f"记忆操作失败: {str(e)}")

    def _search(self, params: dict) -> ToolResult:
        query = params.get("query", "")
        if not query:
            return ToolResult.fail("搜索需要 query 参数")

        results = self.memory.search(query, user_id=self.user_id, limit=10)

        # 格式化结果
        output = {"query": query, "results": [], "relations": []}

        if isinstance(results, dict):
            for mem in results.get("results", []):
                output["results"].append(
                    {
                        "memory": mem.get("memory", ""),
                        "score": mem.get("score", 0),
                    }
                )
            for rel in results.get("relations", []):
                output["relations"].append(str(rel))
        elif isinstance(results, list):
            for mem in results:
                output["results"].append(
                    {
                        "memory": mem.get("memory", str(mem)),
                    }
                )

        summary = f"找到 {len(output['results'])} 条相关记忆"
        if output["relations"]:
            summary += f"，{len(output['relations'])} 条关系"
        
        # 格式化为字符串输出（便于显示）
        result_text = summary + "\n\n"
        for i, mem in enumerate(output["results"][:5], 1):  # 只显示前5条
            result_text += f"{i}. {mem['memory']}\n"
        
        if len(output["results"]) > 5:
            result_text += f"\n... 还有 {len(output['results']) - 5} 条记忆"

        return ToolResult.success(result_text)

    def _add(self, params: dict) -> ToolResult:
        content = params.get("content", "")
        if not content:
            return ToolResult.fail("添加记忆需要 content 参数")

        metadata = params.get("metadata", {})
        messages = [{"role": "system", "content": content}]

        result = self.memory.add(
            messages, user_id=self.user_id, metadata=metadata
        )

        return ToolResult.success(
            f"✅ 记忆已添加（向量+图谱同时更新）: {content[:80]}..."
            if len(content) > 80
            else f"✅ 记忆已添加: {content}"
        )

    def _get_profile(self) -> ToolResult:
        all_memories = self.memory.get_all(user_id=self.user_id)

        if isinstance(all_memories, dict):
            memories_list = all_memories.get("results", [])
        elif isinstance(all_memories, list):
            memories_list = all_memories
        else:
            memories_list = []

        profile_lines = []
        for mem in memories_list[:30]:  # 最多返回30条
            text = mem.get("memory", str(mem)) if isinstance(mem, dict) else str(mem)
            profile_lines.append(f"- {text}")

        profile = "\n".join(profile_lines) if profile_lines else "（暂无记忆档案）"
        
        result_text = f"📊 用户档案（共 {len(memories_list)} 条记忆）\n\n{profile}"
        
        return ToolResult.success(result_text)


class MockMemory:
    """Mem0 不可用时的 Mock 实现"""

    def __init__(self):
        self._store: list = []

    def add(self, messages, user_id=None, metadata=None):
        for msg in messages:
            self._store.append(
                {
                    "memory": msg.get("content", ""),
                    "user_id": user_id,
                    "metadata": metadata or {},
                }
            )
        return {"results": messages}

    def search(self, query, user_id=None, limit=10):
        # 简单关键词匹配
        results = []
        for mem in self._store:
            if query.lower() in mem["memory"].lower():
                results.append({"memory": mem["memory"], "score": 0.8})
        return {"results": results[:limit], "relations": []}

    def get_all(self, user_id=None):
        return {"results": self._store}
