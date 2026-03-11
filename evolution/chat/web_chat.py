"""
超轻量 Web Chat 服务器 - 手机浏览器直接访问
使用 Flask 提供简单的聊天界面，无需任何第三方平台
"""

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict

from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_cors import CORS

from evolution.config.settings import (
    CONVERSATION_LOG_DIR,
    LLM_MODEL,
)
from evolution.config.prompts import SYSTEM_PROMPT
from evolution.utils.llm import call_claude_api
from evolution.tools.memory_tool import EvolutionMemoryTool
from evolution.tools.db_tool import EvolutionDBTool
from evolution.tools.reflection_tool import EvolutionReflectionTool
from evolution.tools.intelligence_tool import EvolutionIntelligenceTool

logger = logging.getLogger("evolution.chat.web")

app = Flask(__name__, template_folder="templates", static_folder="static")
CORS(app)  # 允许跨域访问

# 初始化工具
memory_tool = EvolutionMemoryTool()
db_tool = EvolutionDBTool()
reflection_tool = EvolutionReflectionTool()
intelligence_tool = EvolutionIntelligenceTool()

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


def build_system_prompt(role: str = "all") -> str:
    """构建系统提示词，根据选择的角色调整"""
    
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
    
    # 添加工具使用说明
    tool_instructions = """

---

# 工具调用格式

当需要使用工具时，请在回复中使用以下格式：
```
[TOOL:tool_name]
参数说明
[/TOOL]
```

**可用工具：**
- `memory` - 记忆管理：`[TOOL:memory]search: 查询内容[/TOOL]` 或 `[TOOL:memory]add: 新记忆[/TOOL]`
- `db` - 数据库查询：`[TOOL:db]query: SELECT * FROM table[/TOOL]`
- `reflection` - 反思工具：`[TOOL:reflection]generate_daily[/TOOL]`
- `intelligence` - 情报工具：`[TOOL:intelligence]fetch_latest[/TOOL]`
"""
    
    return base_prompt + tool_instructions + role_focus.get(role, "")


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
    """执行工具调用"""
    try:
        if tool_name == "memory":
            if "search:" in params:
                query = params.split("search:", 1)[1].strip()
                result = memory_tool.execute({"action": "search", "query": query})
                return f"记忆搜索结果：\n{result.result if result.status == 'success' else result.result}"
            elif "add:" in params:
                content = params.split("add:", 1)[1].strip()
                result = memory_tool.execute({"action": "add", "content": content})
                return f"已添加到记忆：{result.result if result.status == 'success' else result.result}"
            else:
                return "记忆工具参数格式：search: 查询内容 或 add: 新记忆"
        
        elif tool_name == "db":
            if "query:" in params:
                query = params.split("query:", 1)[1].strip()
                result = db_tool.execute({"action": "query", "sql": query})
                return f"查询结果：\n{result.result if result.status == 'success' else result.result}"
            else:
                return "数据库工具参数格式：query: SQL语句"
        
        elif tool_name == "reflection":
            if "generate_daily" in params:
                result = reflection_tool.execute({"action": "generate", "type": "daily"})
                return f"每日反思：\n{result.result if result.status == 'success' else result.result}"
            elif "generate_weekly" in params:
                result = reflection_tool.execute({"action": "generate", "type": "weekly"})
                return f"周反思：\n{result.result if result.status == 'success' else result.result}"
            else:
                return "反思工具参数：generate_daily 或 generate_weekly"
        
        elif tool_name == "intelligence":
            if "fetch_latest" in params:
                result = intelligence_tool.execute({"action": "fetch_latest"})
                return f"最新情报：\n{result.result if result.status == 'success' else result.result}"
            else:
                return "情报工具参数：fetch_latest"
        
        else:
            return f"未知工具：{tool_name}"
    
    except Exception as e:
        logger.error(f"工具执行失败 {tool_name}: {e}")
        return f"工具执行出错：{str(e)}"


def process_message(user_message: str) -> str:
    """处理用户消息，调用 LLM 和工具"""
    global current_role
    
    # 构建对话上下文
    messages_context = "\n".join([
        f"{'用户' if msg['role'] == 'user' else 'Evolution'}: {msg['content']}"
        for msg in conversation_history[-10:]  # 只保留最近10轮对话
    ])
    
    prompt = f"""对话历史：
{messages_context}

用户最新消息：{user_message}

请回复用户。如果需要使用工具，请使用 [TOOL:name]params[/TOOL] 格式。"""
    
    # 调用 LLM
    system_prompt = build_system_prompt(current_role)
    response = call_claude_api(prompt, system=system_prompt, max_tokens=2048)
    
    if not response:
        return "抱歉，AI 服务暂时不可用，请稍后再试。"
    
    # 解析并执行工具调用
    tool_calls = parse_tool_calls(response)
    if tool_calls:
        tool_results = []
        for tool in tool_calls:
            result = execute_tool(tool["name"], tool["params"])
            tool_results.append(f"**[{tool['name']}]** {result}")
        
        # 移除工具调用标记，添加工具结果
        import re
        response = re.sub(r'\[TOOL:.*?\[/TOOL\]', '', response, flags=re.DOTALL)
        response = response.strip() + "\n\n" + "\n\n".join(tool_results)
    
    return response


@app.route("/")
def index():
    """主页 - 聊天界面"""
    return render_template("chat.html", model=LLM_MODEL)


@app.route("/api/chat", methods=["POST"])
def chat():
    """处理聊天消息"""
    data = request.json
    user_message = data.get("message", "").strip()
    
    if not user_message:
        return jsonify({"error": "消息不能为空"}), 400
    
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
    """健康检查"""
    return jsonify({
        "status": "ok",
        "model": LLM_MODEL,
        "history_count": len(conversation_history),
        "current_role": current_role
    })


def run_server(host: str = "0.0.0.0", port: int = 5000):
    """启动 Web 服务器"""
    logger.info(f"🚀 Web Chat 服务器启动: http://{host}:{port}")
    logger.info(f"📱 手机访问: http://你的服务器IP:{port}")
    app.run(host=host, port=port, debug=False)


if __name__ == "__main__":
    run_server()
