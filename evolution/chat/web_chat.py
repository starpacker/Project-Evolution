"""
超轻量 Web Chat 服务器 - 手机浏览器直接访问
使用 Flask 提供简单的聊天界面，无需任何第三方平台

工具调用策略（双模式）：
1. 主模式：OpenAI Function Calling API（结构化、可靠）
2. 回退模式：文本解析 [TOOL:name]{json}[/TOOL]（当 API 不支持 tools 参数时）

v0.2.1: 增加输入验证、速率限制、增强健康检查、启动配置校验。
"""

import json
import logging
import re
import os
import time
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_cors import CORS

from evolution.config.settings import (
    CONVERSATION_LOG_DIR,
    LLM_MODEL,
)
from evolution.config.prompts import SYSTEM_PROMPT
from evolution.utils.llm import call_claude_api, call_llm_with_tools
from evolution.tools.memory_tool import EvolutionMemoryTool
from evolution.tools.db_tool import EvolutionDBTool
from evolution.tools.reflection_tool import EvolutionReflectionTool
from evolution.tools.intelligence_tool import EvolutionIntelligenceTool
from evolution.utils.tool_handler import parse_tool_calls_json, execute_tool_with_validation, TOOL_USAGE_GUIDE
from evolution.chat.dashboard import register_dashboard_routes

logger = logging.getLogger("evolution.chat.web")

app = Flask(__name__, template_folder="templates", static_folder="static")
CORS(app)  # 允许跨域访问

# 初始化工具
memory_tool = EvolutionMemoryTool()
db_tool = EvolutionDBTool()
reflection_tool = EvolutionReflectionTool()
intelligence_tool = EvolutionIntelligenceTool()

# 工具实例字典（供 execute_tool_with_validation 使用）
# 同时注册短名和长名，确保 LLM 输出的 [TOOL:memory] 和 [TOOL:evolution_memory] 都能匹配
tool_instances = {
    "evolution_memory": memory_tool,
    "evolution_db": db_tool,
    "evolution_reflection": reflection_tool,
    "evolution_intelligence": intelligence_tool,
    "memory": memory_tool,
    "db": db_tool,
    "reflection": reflection_tool,
    "intelligence": intelligence_tool,
}

# 会话历史（简单内存存储，重启会丢失）
conversation_history: List[Dict] = []
MAX_HISTORY = 50

# 当前激活的角色（默认为全角色模式）
current_role: str = "all"  # all, secretary, mentor, trainer, emotional, intelligence


def save_conversation(user_msg: str, assistant_msg: str):
    """保存对话到日志文件"""
    log_file = Path(CONVERSATION_LOG_DIR) / f"web_chat_{datetime.now().strftime('%Y%m')}.jsonl"
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(json.dumps({
            "timestamp": datetime.now().isoformat(),
            "user": user_msg,
            "assistant": assistant_msg
        }, ensure_ascii=False) + "\n")


def build_system_prompt(role: str = "all", include_time_context: bool = False) -> str:
    """构建系统提示词，根据选择的角色调整
    
    Args:
        role: 角色模式
        include_time_context: 是否注入时间上下文（按需注入，避免性能损耗）
    """
    
    # 角色专注提示
    role_focus = {
        "secretary": "\n\n**当前模式：秘书模式** - 专注于日程管理、提醒和任务规划。",
        "mentor": "\n\n**当前模式：导师模式** - 专注于心智引导、反思和成长建议。",
        "trainer": "\n\n**当前模式：训练师模式** - 专注于技能训练和思维锻炼。",
        "emotional": "\n\n**当前模式：情感助手模式** - 专注于人际关系分析和精力管理。",
        "intelligence": "\n\n**当前模式：情报收集者模式** - 专注于信息筛选和知识推送。",
        "all": ""
    }
    
    # 使用统一的 SYSTEM_PROMPT
    base_prompt = SYSTEM_PROMPT
    
    # 按需注入时间上下文（仅在需要时）
    context_info = ""
    if include_time_context:
        now = datetime.now()
        context_info = f"""

---

# 当前时间上下文

**当前时间**: {now.strftime('%Y-%m-%d %H:%M:%S')} ({now.strftime('%A')})
**当前日期**: {now.strftime('%Y年%m月%d日')}
**星期**: 周{'一二三四五六日'[now.weekday()]}

⚠️ 在处理日程、时间相关任务时，请基于上述时间判断。
"""
    
    base_prompt = base_prompt + context_info
    
    # 使用 TOOL_USAGE_GUIDE（包含完整的 action 列表、必需参数和 JSON 示例）
    return base_prompt + TOOL_USAGE_GUIDE + role_focus.get(role, "")


def parse_tool_calls(text: str) -> List[Dict]:
    """解析 LLM 回复中的工具调用"""
    tools = []
    import re
    pattern = r'\[TOOL:(\w+)\](.*?)\[/TOOL\]'
    matches = re.findall(pattern, text, re.DOTALL)
    
    for tool_name, params in matches:
        tools.append({
            "name": tool_name.strip(),
            "params": params.strip()
        })
    
    return tools


def execute_tool(tool_name: str, params: str) -> str:
    """执行工具调用，支持多种参数格式"""
    try:
        if isinstance(params, dict):
            params_dict = params
        elif isinstance(params, str):
            params_dict = _parse_tool_params(params)
        else:
            params_dict = {"action": str(params)}
        
        # 使用新的验证执行函数
        result = execute_tool_with_validation(tool_name, params_dict, tool_instances)
        
        # 格式化返回值为可读字符串
        if isinstance(result, dict):
            if result.get("success"):
                return result.get("result", "✅ 操作成功")
            else:
                error = result.get("error", "未知错误")
                hint = result.get("retry_hint", "")
                logger.warning(f"工具调用失败: {tool_name}, 错误: {error}")
                return f"⚠️ {error}" + (f"\n{hint}" if hint else "")
        
        return str(result)
        
    except Exception as e:
        logger.error(f"工具执行失败: {tool_name}, 错误: {e}")
        return f"工具执行失败: {str(e)}"


def _parse_tool_params(raw: str) -> dict:
    """解析工具参数字符串，支持 JSON 和 Python kwargs 格式
    
    支持的格式:
    1. JSON: {"action": "add_schedule", "content": "开会"}
    2. Python kwargs: action='add_schedule', content='开会'
    3. 纯文本: 当作 action 值
    """
    raw = raw.strip()
    
    # 1. 尝试 JSON
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, ValueError):
        pass
    
    # 2. 尝试 Python kwargs 格式: key='value', key2='value2'
    #    也支持 key="value" 和 key=value
    import re
    # 匹配 key=value 对，value 可以是引号包裹的字符串或无引号的值
    kv_pattern = r"""(\w+)\s*=\s*(?:'([^']*)'|"([^"]*)"|(\{[^}]*\})|(\[[^\]]*\])|([^,\s]+))"""
    matches = re.findall(kv_pattern, raw)
    
    if matches:
        params_dict = {}
        for match in matches:
            key = match[0]
            # 取第一个非空的捕获组作为 value
            value = match[1] or match[2] or match[3] or match[4] or match[5]
            
            # 尝试解析嵌套 JSON（如 metadata={...}）
            if value.startswith('{') or value.startswith('['):
                try:
                    value = json.loads(value.replace("'", '"'))
                except (json.JSONDecodeError, ValueError):
                    pass
            
            # 尝试转换数字
            if isinstance(value, str) and value.isdigit():
                value = int(value)
            
            params_dict[key] = value
        
        if params_dict:
            return params_dict
    
    # 3. Fallback: 纯文本当作 action
    return {"action": raw}


def needs_time_context(message: str) -> bool:
    """检测消息是否需要时间上下文
    
    仅在用户消息包含时间相关词汇时返回 True，避免不必要的上下文注入
    """
    time_keywords = [
        # 时间词
        '今天', '明天', '后天', '昨天', '前天',
        '今年', '明年', '去年',
        '本周', '下周', '上周',
        '本月', '下月', '上月',
        '现在', '当前', '最近',
        # 日程相关
        '日程', '安排', '计划', '待办', '任务',
        '截止', '过期', '到期',
        # 时间查询
        '什么时候', '几点', '哪天', '星期',
        # 英文
        'today', 'tomorrow', 'yesterday',
        'schedule', 'deadline', 'overdue',
    ]
    
    message_lower = message.lower()
    return any(keyword in message_lower for keyword in time_keywords)


# ── OpenAI Function Calling 工具定义 ─────────────────────
OPENAI_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "evolution_db",
            "description": "管理用户的结构化数据：日程、技能树、人物档案、训练记录、心智模型、统计。",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": [
                            "add_schedule", "list_schedule", "complete_schedule", "delete_schedule",
                            "add_skill", "list_skills", "update_skill", "stale_skills",
                            "upsert_person", "get_person", "list_persons",
                            "add_training", "list_trainings",
                            "add_model", "list_models", "stats",
                        ],
                        "description": "操作类型",
                    },
                    "content": {"type": "string", "description": "日程内容（add_schedule 必需）"},
                    "due_date": {"type": "string", "description": "截止日期 YYYY-MM-DD"},
                    "priority": {"type": "string", "enum": ["high", "medium", "low"]},
                    "category": {"type": "string", "description": "分类"},
                    "id": {"type": "integer", "description": "记录ID（complete/delete_schedule）"},
                    "name": {"type": "string", "description": "名称（技能/人物/模型）"},
                    "level": {"type": "integer", "description": "技能等级"},
                    "relationship": {"type": "string", "description": "关系类型"},
                    "skill_name": {"type": "string", "description": "技能名称（add_training）"},
                    "modality": {"type": "string", "enum": ["T1","T2","T3","T4","T5","T6","T7"]},
                    "topic": {"type": "string", "description": "训练主题"},
                    "rating": {"type": "string", "description": "评分"},
                    "date": {"type": "string", "description": "日期 YYYY-MM-DD（list_schedule）"},
                    "filter": {"type": "string", "description": "过滤器（pending/overdue）"},
                    "description": {"type": "string", "description": "描述"},
                    "source_domain": {"type": "string", "description": "来源领域（add_model）"},
                },
                "required": ["action"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "evolution_memory",
            "description": "搜索和管理用户的长期记忆（人物、事件、偏好等）。",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["search", "add", "profile"],
                        "description": "操作类型",
                    },
                    "query": {"type": "string", "description": "搜索关键词（search 必需）"},
                    "content": {"type": "string", "description": "要记住的内容（add 必需）"},
                },
                "required": ["action"],
            },
        },
    },
]

# 是否使用 Function Calling 模式（首次调用时自动检测）
_use_function_calling: Optional[bool] = None


def _execute_tool_by_name(tool_name: str, params: dict) -> str:
    """统一执行工具，返回结果字符串"""
    tool = tool_instances.get(tool_name)
    if not tool:
        return f"⚠️ 未知工具: {tool_name}"
    try:
        result = tool.execute(params)
        if result.status == "success":
            return result.result or "✅ 操作成功"
        else:
            return f"⚠️ {result.result}"
    except Exception as e:
        logger.error(f"工具执行异常: {tool_name}, {e}")
        return f"⚠️ 工具执行失败: {e}"


def process_message(user_message: str, max_retries: int = 2) -> str:
    """处理用户消息 — 双模式工具调用

    模式1（主）: OpenAI Function Calling API — 结构化、可靠
    模式2（回退）: 文本解析 [TOOL:name]{json}[/TOOL] — 兼容不支持 tools 的网关
    """
    global current_role, _use_function_calling

    include_time = needs_time_context(user_message)
    system_prompt = build_system_prompt(current_role, include_time_context=include_time)

    # 构建对话上下文
    recent = conversation_history[-10:]
    llm_messages: List[Dict[str, Any]] = []
    for msg in recent:
        llm_messages.append({"role": msg["role"], "content": msg["content"]})
    llm_messages.append({"role": "user", "content": user_message})

    # ── 尝试 Function Calling 模式 ──────────────────
    if _use_function_calling is not False:
        result = _process_with_function_calling(
            llm_messages, system_prompt, max_retries
        )
        if result is not None:
            _use_function_calling = True
            return result
        # Function calling 失败（网关不支持），切换到文本模式
        if _use_function_calling is None:
            logger.warning("[Chat] Function Calling 不可用，切换到文本解析模式")
            _use_function_calling = False

    # ── 回退：文本解析模式 ──────────────────────────
    return _process_with_text_parsing(llm_messages, system_prompt, max_retries)


def _process_with_function_calling(
    llm_messages: List[Dict], system_prompt: str, max_retries: int
) -> Optional[str]:
    """使用 OpenAI Function Calling API 处理消息"""

    messages = list(llm_messages)  # 浅拷贝

    for attempt in range(1 + max_retries):
        resp = call_llm_with_tools(
            messages=messages,
            tools=OPENAI_TOOLS,
            system=system_prompt,
            max_tokens=2048,
        )
        if resp is None:
            return None  # API 不支持 tools，回退

        tool_calls = resp.get("tool_calls")
        content = resp.get("content") or ""

        if not tool_calls:
            return content if content else "..."

        # 执行所有工具调用
        # 先把 assistant 消息（含 tool_calls）追加到 messages
        raw_msg = resp.get("raw_message")
        messages.append(_assistant_msg_with_tool_calls(raw_msg))

        all_ok = True
        for tc in tool_calls:
            tool_result_str = _execute_tool_by_name(tc["name"], tc["arguments"])
            if tool_result_str.startswith("⚠️"):
                all_ok = False
            # 追加 tool result 到 messages（OpenAI 协议要求）
            messages.append({
                "role": "tool",
                "tool_call_id": tc["id"],
                "content": tool_result_str,
            })

        if not all_ok and attempt < max_retries:
            logger.info(f"[FC] 工具调用有错误，第 {attempt+1} 次重试")
            continue

        # 让 LLM 根据工具结果生成最终自然语言回复
        final_resp = call_llm_with_tools(
            messages=messages,
            tools=OPENAI_TOOLS,
            system=system_prompt,
            max_tokens=2048,
        )
        if final_resp and final_resp.get("content"):
            return final_resp["content"]
        # 如果 LLM 没有额外文本，拼接工具结果
        parts = [content] if content else []
        for tc in tool_calls:
            r = _execute_tool_by_name(tc["name"], tc["arguments"])
            if not r.startswith("⚠️"):
                parts.append(r)
        return "\n\n".join(parts) if parts else "操作完成。"

    return "抱歉，工具调用多次失败，请稍后再试。"


def _assistant_msg_with_tool_calls(raw_message) -> dict:
    """将 OpenAI raw message 转为可序列化的 assistant message"""
    msg: Dict[str, Any] = {"role": "assistant", "content": raw_message.content or ""}
    if raw_message.tool_calls:
        msg["tool_calls"] = [
            {
                "id": tc.id,
                "type": "function",
                "function": {
                    "name": tc.function.name,
                    "arguments": tc.function.arguments,
                },
            }
            for tc in raw_message.tool_calls
        ]
    return msg


def _process_with_text_parsing(
    llm_messages: List[Dict], system_prompt: str, max_retries: int
) -> str:
    """回退模式：文本解析 [TOOL:name]{json}[/TOOL]"""

    messages = list(llm_messages)

    for attempt in range(1 + max_retries):
        response = call_claude_api(
            prompt="", system=system_prompt, max_tokens=2048, messages=messages
        )
        if not response:
            return "抱歉，AI 服务暂时不可用，请稍后再试。"

        # 尝试 JSON 格式解析
        tool_calls = parse_tool_calls_json(response)
        if not tool_calls:
            # 尝试旧格式
            tool_calls_old = parse_tool_calls(response)
            if tool_calls_old:
                tool_calls = []
                for tc in tool_calls_old:
                    params = tc["params"]
                    if isinstance(params, str):
                        params = _parse_tool_params(params)
                    tool_calls.append({"name": tc["name"], "params": params})

        if not tool_calls:
            return response

        # 执行工具
        results = []
        has_error = False
        for tc in tool_calls:
            r = _execute_tool_by_name(tc["name"], tc.get("params") or tc.get("arguments", {}))
            results.append({"tool": tc["name"], "result": r})
            if r.startswith("⚠️"):
                has_error = True

        if has_error and attempt < max_retries:
            error_fb = "工具调用出错，请修正后重试：\n"
            for tr in results:
                error_fb += f"- [{tr['tool']}] {tr['result']}\n"
            messages.append({"role": "assistant", "content": response})
            messages.append({"role": "user", "content": error_fb})
            logger.info(f"[Text] 工具调用失败，第 {attempt+1} 次重试")
            continue

        # 成功 → 把工具结果反馈给 LLM 生成自然语言回复
        tool_summary = "\n".join(f"[{tr['tool']}] {tr['result']}" for tr in results)
        messages.append({"role": "assistant", "content": response})
        messages.append({
            "role": "user",
            "content": f"工具执行结果如下，请根据结果用自然语言回复用户（不要再调用工具）：\n\n{tool_summary}",
        })
        final = call_claude_api(
            prompt="", system=system_prompt, max_tokens=1024, messages=messages
        )
        return final if final else tool_summary

    return "抱歉，工具调用多次失败，请稍后再试。"


@app.route("/")
def index():
    """主页 - 聊天界面"""
    return render_template("chat.html", model=LLM_MODEL)


# ── 速率限制 ─────────────────────────────────────────────
MAX_MESSAGE_LENGTH = 5000  # 单条消息最大字符数
RATE_LIMIT_WINDOW = 60     # 速率限制窗口（秒）
RATE_LIMIT_MAX = 30        # 窗口内最大请求数
_rate_limit_store: Dict[str, List[float]] = defaultdict(list)


def _check_rate_limit(client_ip: str) -> bool:
    """检查速率限制，返回 True 表示允许请求"""
    now = time.time()
    window_start = now - RATE_LIMIT_WINDOW
    # 清理过期记录
    _rate_limit_store[client_ip] = [
        t for t in _rate_limit_store[client_ip] if t > window_start
    ]
    if len(_rate_limit_store[client_ip]) >= RATE_LIMIT_MAX:
        return False
    _rate_limit_store[client_ip].append(now)
    return True


@app.route("/api/chat", methods=["POST"])
def chat():
    """处理聊天消息"""
    # 速率限制
    client_ip = request.remote_addr or "unknown"
    if not _check_rate_limit(client_ip):
        logger.warning(f"[Chat] Rate limit exceeded for {client_ip}")
        return jsonify({"error": "请求过于频繁，请稍后再试"}), 429

    data = request.json
    if not data:
        return jsonify({"error": "无效的请求格式"}), 400

    user_message = data.get("message", "").strip()
    
    if not user_message:
        return jsonify({"error": "消息不能为空"}), 400

    # 输入长度限制
    if len(user_message) > MAX_MESSAGE_LENGTH:
        return jsonify({"error": f"消息过长，最大 {MAX_MESSAGE_LENGTH} 字符"}), 400
    
    # 添加到历史
    conversation_history.append({
        "role": "user",
        "content": user_message,
        "timestamp": datetime.now().isoformat()
    })
    
    # 处理消息
    assistant_response = process_message(user_message)
    
    # 添加到历史
    conversation_history.append({
        "role": "assistant",
        "content": assistant_response,
        "timestamp": datetime.now().isoformat()
    })
    
    # 保存对话
    save_conversation(user_message, assistant_response)
    
    # 限制历史长度
    if len(conversation_history) > MAX_HISTORY:
        conversation_history[:] = conversation_history[-MAX_HISTORY:]
    
    return jsonify({
        "response": assistant_response,
        "timestamp": datetime.now().isoformat()
    })


@app.route("/api/history", methods=["GET"])
def get_history():
    """获取对话历史"""
    return jsonify({
        "history": conversation_history[-20:]  # 返回最近20条
    })


@app.route("/api/clear", methods=["POST"])
def clear_history():
    """清空对话历史"""
    conversation_history.clear()
    return jsonify({"status": "ok"})


@app.route("/api/role", methods=["GET", "POST"])
def manage_role():
    """管理当前激活的角色"""
    global current_role
    
    if request.method == "GET":
        # 返回当前角色和可用角色列表
        return jsonify({
            "current_role": current_role,
            "available_roles": {
                "all": "全角色模式",
                "secretary": "🗓️ 秘书",
                "mentor": "🧠 导师",
                "trainer": "🏋️ 训练师",
                "emotional": "💑 情感助手",
                "intelligence": "📡 情报收集者"
            }
        })
    
    elif request.method == "POST":
        # 切换角色
        data = request.json
        new_role = data.get("role", "all")
        
        valid_roles = ["all", "secretary", "mentor", "trainer", "emotional", "intelligence"]
        if new_role not in valid_roles:
            return jsonify({"error": "无效的角色"}), 400
        
        current_role = new_role
        return jsonify({
            "status": "ok",
            "current_role": current_role,
            "message": f"已切换到：{new_role}"
        })


@app.route("/health", methods=["GET"])
def health():
    """基础健康检查"""
    return jsonify({
        "status": "ok",
        "model": LLM_MODEL,
        "history_count": len(conversation_history),
        "current_role": current_role
    })


@app.route("/health/detailed", methods=["GET"])
def health_detailed():
    """详细健康检查 - 检查所有关键组件"""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "components": {},
        "version": "0.2.1",
    }
    
    # 1. 数据库检查
    try:
        from evolution.db.manager import DatabaseManager
        db = DatabaseManager()
        stats = db.get_stats()
        health_status["components"]["database"] = {
            "status": "healthy",
            "stats": stats,
        }
    except Exception as e:
        health_status["status"] = "degraded"
        health_status["components"]["database"] = {
            "status": "unhealthy",
            "error": str(e),
        }
    
    # 2. LLM API 检查
    try:
        from evolution.utils.llm import call_claude_api
        test_resp = call_claude_api(
            prompt="ping", system="Reply with 'pong'", max_tokens=10
        )
        health_status["components"]["llm_api"] = {
            "status": "healthy" if test_resp else "unhealthy",
            "model": LLM_MODEL,
        }
        if not test_resp:
            health_status["status"] = "degraded"
    except Exception as e:
        health_status["status"] = "degraded"
        health_status["components"]["llm_api"] = {
            "status": "unhealthy",
            "error": str(e),
        }
    
    # 3. Mem0 检查
    try:
        mem_status = "unknown"
        if memory_tool._memory is not None:
            mem_status = "initialized"
        else:
            mem_status = "not_initialized"
        health_status["components"]["memory"] = {
            "status": mem_status,
        }
    except Exception as e:
        health_status["components"]["memory"] = {
            "status": "error",
            "error": str(e),
        }
    
    # 4. 工具状态
    health_status["components"]["tools"] = {
        "registered": list(tool_instances.keys()),
        "count": len(tool_instances),
    }
    
    # 5. 会话状态
    health_status["components"]["session"] = {
        "history_count": len(conversation_history),
        "current_role": current_role,
    }
    
    return jsonify(health_status)


def run_server(host: str = "0.0.0.0", port: int = 5000):
    """启动 Web 服务器"""
    # 配置验证
    logger.info("=" * 60)
    logger.info("Evolution v0.2.1 Web Chat Server")
    logger.info("=" * 60)
    
    try:
        from evolution.utils.config_validator import validate_and_report
        if not validate_and_report():
            logger.error("配置验证失败，但服务器将继续启动（部分功能可能不可用）")
    except Exception as e:
        logger.warning(f"配置验证模块加载失败: {e}")
    
    # 注册 Dashboard 路由
    register_dashboard_routes(app)
    
    logger.info(f"🚀 Web Chat 服务器启动: http://{host}:{port}")
    logger.info(f"📊 Dashboard: http://{host}:{port}/dashboard")
    logger.info(f"💚 Health Check: http://{host}:{port}/health/detailed")
    logger.info(f"📱 手机访问: http://你的服务器IP:{port}")
    logger.info("=" * 60)
    
    app.run(host=host, port=port, debug=False)


if __name__ == "__main__":
    run_server()
