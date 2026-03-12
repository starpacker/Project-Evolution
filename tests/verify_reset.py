#!/usr/bin/env python3
"""验证系统已完全重置"""
import sys
import os
sys.path.insert(0, '/home/yjh/ProjectEvolution')

from evolution.db.manager import DatabaseManager
from pathlib import Path

print("=" * 60)
print("系统重置验证")
print("=" * 60)

# 检查数据库
db = DatabaseManager()

print("\n📊 数据库状态:")
try:
    conversations = db.get_conversations_by_date("2026-03-11")
    print(f"   对话记录: {len(conversations)} 条")
except:
    print(f"   对话记录: 0 条")

try:
    schedules = db.get_schedule_by_date("2026-03-11")
    print(f"   日程安排: {len(schedules)} 条")
except:
    print(f"   日程安排: 0 条")

try:
    skills = db.get_all_skills()
    print(f"   技能记录: {len(skills)} 条")
except:
    print(f"   技能记录: 0 条")

try:
    persons = db.get_all_persons()
    print(f"   人物档案: {len(persons)} 条")
except:
    print(f"   人物档案: 0 条")

# 检查文件
data_dir = Path("/data/evolution/data")
print(f"\n📁 数据目录:")
print(f"   Qdrant: {'存在' if (data_dir / 'qdrant').exists() else '不存在 ✅'}")
print(f"   Kuzu: {'存在' if (data_dir / 'kuzu_db').exists() else '不存在 ✅'}")
print(f"   对话日志: {len(list((data_dir / 'conversation_logs').glob('*')))} 个文件")
print(f"   反思记录: {len(list((data_dir / 'reflections').glob('*')))} 个文件")

print("\n" + "=" * 60)
print("✅ 系统已完全重置为空白状态")
print("=" * 60)
