#!/usr/bin/env python3
"""
Evolution 分步测试脚本
逐个功能测试，便于发现问题
"""

import os
import sys
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).parent.parent))

from evolution.tools.memory_tool import EvolutionMemoryTool
from evolution.tools.db_tool import EvolutionDBTool
from evolution.db.manager import DatabaseManager


def print_section(title):
    """打印章节标题"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


def test_memory():
    """测试记忆系统"""
    print_section("🧠 测试记忆系统")
    
    memory_tool = EvolutionMemoryTool()
    
    # 1. 添加记忆
    print("1️⃣ 添加记忆...")
    memories = [
        "我正在学习深度学习，特别关注Transformer架构",
        "我的导师是李教授，他对我的论文要求很严格",
        "我计划在3月底完成论文初稿",
    ]
    
    for mem in memories:
        result = memory_tool.execute({
            "action": "add",
            "content": mem
        })
        print(f"   ✓ {mem[:40]}... -> {result.status}")
    
    # 2. 搜索记忆
    print("\n2️⃣ 搜索记忆...")
    result = memory_tool.execute({
        "action": "search",
        "query": "深度学习"
    })
    print(f"   搜索结果: {result.result[:200]}...")
    
    # 3. 获取档案
    print("\n3️⃣ 获取用户档案...")
    result = memory_tool.execute({"action": "profile"})
    print(f"   档案: {result.result[:200]}...")
    
    print("\n✅ 记忆系统测试完成")


def test_schedule():
    """测试日程管理"""
    print_section("📅 测试日程管理")
    
    db_tool = EvolutionDBTool()
    
    # 1. 添加日程
    print("1️⃣ 添加日程...")
    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    result = db_tool.execute({
        "action": "add_schedule",
        "content": "完成系统测试",
        "due_date": f"{tomorrow}T18:00:00",
        "priority": "high"
    })
    print(f"   {result.result}")
    
    # 2. 查询日程
    print("\n2️⃣ 查询日程...")
    result = db_tool.execute({"action": "list_schedule"})
    print(f"{result.result}")
    
    # 3. 统计
    print("\n3️⃣ 统计数据...")
    result = db_tool.execute({"action": "stats"})
    print(f"{result.result}")
    
    print("\n✅ 日程管理测试完成")


def test_skills():
    """测试技能管理"""
    print_section("🎯 测试技能管理")
    
    db_tool = EvolutionDBTool()
    
    # 1. 添加技能
    print("1️⃣ 添加技能...")
    skills = [
        {"name": "深度学习", "category": "professional", "level": 5, "target_level": 8},
        {"name": "批判性思维", "category": "thinking", "level": 3, "target_level": 7},
    ]
    
    for skill in skills:
        result = db_tool.execute({"action": "add_skill", **skill})
        if result.status == "success":
            print(f"   ✓ {skill['name']}")
        else:
            print(f"   ⚠️  {skill['name']} (可能已存在)")
    
    # 2. 查询技能
    print("\n2️⃣ 查询技能列表...")
    result = db_tool.execute({"action": "list_skills"})
    print(f"{result.result}")
    
    print("\n✅ 技能管理测试完成")


def test_persons():
    """测试人物档案"""
    print_section("👥 测试人物档案")
    
    db_tool = EvolutionDBTool()
    
    # 1. 添加人物
    print("1️⃣ 添加人物...")
    persons = [
        {"name": "李教授", "relationship": "导师", "interaction_frequency": "high"},
        {"name": "张同学", "relationship": "同学", "interaction_frequency": "medium"},
    ]
    
    for person in persons:
        result = db_tool.execute({"action": "upsert_person", **person})
        print(f"   ✓ {person['name']}")
    
    # 2. 查询人物
    print("\n2️⃣ 查询人物列表...")
    result = db_tool.execute({"action": "list_persons"})
    print(f"{result.result}")
    
    print("\n✅ 人物档案测试完成")


def test_training():
    """测试训练记录"""
    print_section("📚 测试训练记录")
    
    db = DatabaseManager()
    db_tool = EvolutionDBTool()
    
    # 获取技能
    skills = db.list_skills()
    if not skills:
        print("   ⚠️  没有技能，跳过训练测试")
        return
    
    skill = skills[0]
    
    # 1. 添加训练记录
    print(f"1️⃣ 为技能 '{skill['name']}' 添加训练记录...")
    result = db_tool.execute({
        "action": "add_training",
        "skill_name": skill["name"],
        "modality": "T2",
        "topic": "深度学习中的注意力机制",
        "rating": "good"
    })
    print(f"   {result.result}")
    
    # 2. 查询训练记录
    print("\n2️⃣ 查询训练记录...")
    result = db_tool.execute({
        "action": "list_trainings",
        "skill_name": skill["name"]
    })
    print(f"{result.result}")
    
    print("\n✅ 训练记录测试完成")


def test_conversation():
    """测试对话记录"""
    print_section("💬 测试对话记录")
    
    db = DatabaseManager()
    
    # 1. 添加对话
    print("1️⃣ 添加对话记录...")
    today = datetime.now().strftime("%Y-%m-%d")
    conversations = [
        ("user", "今天学习了Transformer的原理"),
        ("assistant", "很好，你能具体说说学到了什么吗？"),
        ("user", "主要是自注意力机制"),
    ]
    
    for role, content in conversations:
        db.log_conversation(today, role, content)
        print(f"   ✓ {role}: {content[:30]}...")
    
    # 2. 查询对话
    print("\n2️⃣ 查询今日对话...")
    convs = db.get_conversations_by_date(today)
    print(f"   找到 {len(convs)} 条对话记录")
    
    print("\n✅ 对话记录测试完成")


def test_notifications():
    """测试通知系统"""
    print_section("📧 测试通知系统")
    
    from evolution.config.settings import EMAIL_ENABLED, NOTION_ENABLED
    from evolution.notification.router import NotificationRouter, Notification, NotifyPriority
    
    router = NotificationRouter()
    
    # 1. 测试邮件
    if EMAIL_ENABLED:
        print("1️⃣ 测试邮件通知...")
        notification = Notification(
            title="Evolution 测试 - 邮件",
            body=f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            priority=NotifyPriority.NORMAL,
            category="test"
        )
        try:
            router.send(notification)
            print("   ✅ 邮件发送成功")
        except Exception as e:
            print(f"   ❌ 邮件发送失败: {e}")
    else:
        print("1️⃣ ⚠️  邮件通知未启用")
    
    # 2. 测试Notion
    if NOTION_ENABLED:
        print("\n2️⃣ 测试Notion通知...")
        notification = Notification(
            title="Evolution 测试 - Notion",
            body=f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            priority=NotifyPriority.LOW,
            category="intelligence",
            metadata={"date": datetime.now().strftime("%Y-%m-%d")}
        )
        try:
            router.send(notification)
            print("   ✅ Notion推送成功")
        except Exception as e:
            print(f"   ❌ Notion推送失败: {e}")
    else:
        print("\n2️⃣ ⚠️  Notion通知未启用")
    
    print("\n✅ 通知系统测试完成")


def main():
    """主测试流程"""
    print("\n" + "="*60)
    print("  🚀 Evolution 分步测试")
    print("="*60)
    
    try:
        test_memory()
        test_schedule()
        test_skills()
        test_persons()
        test_training()
        test_conversation()
        test_notifications()
        
        print("\n" + "="*60)
        print("  ✅ 所有测试完成")
        print("="*60 + "\n")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  测试被用户中断")
        return 1
    except Exception as e:
        print(f"\n\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
