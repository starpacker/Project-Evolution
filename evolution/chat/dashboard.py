"""
Evolution Dashboard - 数据查看和管理界面
提供统一的数据查看入口
"""

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path

from flask import Flask, render_template, request, jsonify
from flask_cors import CORS

from evolution.config.settings import (
    CONVERSATION_LOG_DIR,
    REFLECTION_DIR,
    DB_PATH,
)
from evolution.db.manager import DatabaseManager
from evolution.tools.memory_tool import EvolutionMemoryTool

logger = logging.getLogger("evolution.dashboard")

# 初始化
db = DatabaseManager()
memory_tool = EvolutionMemoryTool()


def get_dashboard_data():
    """获取 Dashboard 所有数据"""
    
    # 1. 日程统计
    schedules = {
        "pending": db.get_pending_schedules(),
        "overdue": db.get_overdue_schedules(),
        "total": len(db.get_pending_schedules()) + len(db.get_overdue_schedules())
    }
    
    # 2. 技能统计
    skills = db.list_skills()
    skills_by_category = {}
    for skill in skills:
        category = skill.get('category', 'unknown')
        if category not in skills_by_category:
            skills_by_category[category] = []
        skills_by_category[category].append(skill)
    
    # 3. 人物档案统计
    persons = db.list_persons()
    top_mentioned = db.get_top_mentioned_persons(limit=10)
    
    # 4. 训练记录统计
    recent_trainings = db.get_training_logs(limit=10)
    
    # 5. 反思记录
    today = datetime.now().strftime('%Y-%m-%d')
    week_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
    recent_reflections = db.get_reflections_range(week_ago, today)
    
    # 6. 对话日志统计
    conversation_count = db.get_conversation_count_by_date(today)
    
    # 7. 记忆统计（Mem0）
    try:
        memory_result = memory_tool.execute({"action": "profile"})
        memory_stats = {
            "status": "available",
            "data": memory_result.result if memory_result.status == 'success' else "无数据"
        }
    except Exception as e:
        memory_stats = {
            "status": "unavailable",
            "error": str(e)
        }
    
    # 8. 数据库统计
    db_stats = db.get_stats()
    
    return {
        "schedules": schedules,
        "skills": {
            "total": len(skills),
            "by_category": skills_by_category
        },
        "persons": {
            "total": len(persons),
            "top_mentioned": top_mentioned
        },
        "trainings": {
            "recent": recent_trainings,
            "total": len(recent_trainings)
        },
        "reflections": {
            "recent": recent_reflections,
            "count": len(recent_reflections)
        },
        "conversations": {
            "today": conversation_count
        },
        "memory": memory_stats,
        "database": db_stats,
        "timestamp": datetime.now().isoformat()
    }


def get_schedule_list(status=None):
    """获取日程列表"""
    if status == "pending":
        return db.get_pending_schedules()
    elif status == "overdue":
        return db.get_overdue_schedules()
    else:
        # 返回所有日程
        pending = db.get_pending_schedules()
        overdue = db.get_overdue_schedules()
        return pending + overdue


def get_skill_details():
    """获取技能详情"""
    skills = db.list_skills()
    
    # 按类别分组
    by_category = {}
    for skill in skills:
        category = skill.get('category', 'unknown')
        if category not in by_category:
            by_category[category] = []
        by_category[category].append(skill)
    
    # 找出荒废的技能
    stale_skills = db.get_stale_skills(days=30)
    
    return {
        "all": skills,
        "by_category": by_category,
        "stale": stale_skills,
        "total": len(skills)
    }


def get_person_details():
    """获取人物档案详情"""
    persons = db.list_persons()
    top_mentioned = db.get_top_mentioned_persons(limit=20)
    
    return {
        "all": persons,
        "top_mentioned": top_mentioned,
        "total": len(persons)
    }


def get_training_history(skill_id=None, limit=50):
    """获取训练历史"""
    return db.get_training_logs(skill_id=skill_id, limit=limit)


def get_reflection_history(days=30):
    """获取反思历史"""
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
    return db.get_reflections_range(start_date, end_date)


def get_conversation_logs(date=None, limit=100):
    """获取对话日志"""
    if date is None:
        date = datetime.now().strftime('%Y-%m-%d')
    
    conversations = db.get_conversations_by_date(date)
    return conversations[:limit]


def get_memory_search(query):
    """搜索记忆"""
    result = memory_tool.execute({"action": "search", "query": query})
    if result.status == 'success':
        return result.result
    else:
        return {"error": result.result}


def export_data(data_type):
    """导出数据为 JSON"""
    if data_type == "schedules":
        data = get_schedule_list()
    elif data_type == "skills":
        data = get_skill_details()
    elif data_type == "persons":
        data = get_person_details()
    elif data_type == "trainings":
        data = get_training_history()
    elif data_type == "reflections":
        data = get_reflection_history()
    elif data_type == "conversations":
        data = get_conversation_logs()
    elif data_type == "all":
        data = get_dashboard_data()
    else:
        return {"error": "未知的数据类型"}
    
    return data


# API 端点（可以集成到 web_chat.py 中）
def register_dashboard_routes(app):
    """注册 Dashboard 路由"""
    
    @app.route("/dashboard")
    def dashboard():
        """Dashboard 主页"""
        return render_template("dashboard.html")
    
    @app.route("/api/dashboard/overview")
    def dashboard_overview():
        """获取 Dashboard 概览数据"""
        return jsonify(get_dashboard_data())
    
    @app.route("/api/dashboard/schedules")
    def dashboard_schedules():
        """获取日程列表"""
        status = request.args.get('status')
        return jsonify(get_schedule_list(status))
    
    @app.route("/api/dashboard/skills")
    def dashboard_skills():
        """获取技能详情"""
        return jsonify(get_skill_details())
    
    @app.route("/api/dashboard/persons")
    def dashboard_persons():
        """获取人物档案"""
        return jsonify(get_person_details())
    
    @app.route("/api/dashboard/trainings")
    def dashboard_trainings():
        """获取训练历史"""
        skill_id = request.args.get('skill_id', type=int)
        limit = request.args.get('limit', 50, type=int)
        return jsonify(get_training_history(skill_id, limit))
    
    @app.route("/api/dashboard/reflections")
    def dashboard_reflections():
        """获取反思历史"""
        days = request.args.get('days', 30, type=int)
        return jsonify(get_reflection_history(days))
    
    @app.route("/api/dashboard/conversations")
    def dashboard_conversations():
        """获取对话日志"""
        date = request.args.get('date')
        limit = request.args.get('limit', 100, type=int)
        return jsonify(get_conversation_logs(date, limit))
    
    @app.route("/api/dashboard/memory/search")
    def dashboard_memory_search():
        """搜索记忆"""
        query = request.args.get('query', '')
        if not query:
            return jsonify({"error": "查询不能为空"}), 400
        return jsonify(get_memory_search(query))
    
    @app.route("/api/dashboard/export/<data_type>")
    def dashboard_export(data_type):
        """导出数据"""
        data = export_data(data_type)
        return jsonify(data)
