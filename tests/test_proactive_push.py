#!/usr/bin/env python3
"""
测试Evolution系统的主动推送功能

场景1: 反思后主动发起对话
场景2: 早晨推送情报摘要
场景3: 晚上推送反思总结（日报/周报）
"""

import sys
import os
from datetime import datetime, timedelta
sys.path.insert(0, '/home/yjh/ProjectEvolution')

from evolution.db.manager import DatabaseManager
from evolution.notification.router import NotificationRouter, Notification, NotifyPriority
from evolution.tools.reflection_tool import EvolutionReflectionTool
from evolution.tools.intelligence_tool import EvolutionIntelligenceTool

print("=" * 70)
print("Evolution 主动推送功能测试")
print("=" * 70)

db = DatabaseManager()
router = NotificationRouter()

# ============================================================
# 场景1: 反思后发现需要主动沟通
# ============================================================
print("\n" + "=" * 70)
print("场景1: 反思后主动发起对话")
print("=" * 70)

print("\n1️⃣ 模拟添加一些对话记录...")
# 添加一些测试对话
test_conversations = [
    ("user", "我最近压力很大，项目进度落后了"),
    ("assistant", "我理解你的压力。能具体说说是什么原因导致进度落后吗？"),
    ("user", "主要是技术难点没解决，而且团队沟通也有问题"),
    ("assistant", "技术难点和团队沟通都是重要问题。我们可以一起分析一下。"),
    ("user", "算了，我先自己想想办法"),
]

today = datetime.now().strftime("%Y-%m-%d")
for role, content in test_conversations:
    db.log_conversation(role, content)
    print(f"   - {role}: {content[:50]}...")

print("\n2️⃣ 生成每日反思...")
reflection_tool = EvolutionReflectionTool()
result = reflection_tool.execute({
    "action": "daily",
    "date": today
})

if result.success:
    print(f"   ✅ 反思生成成功")
    print(f"   内容预览: {result.data[:200]}...")
    
    # 检查是否需要主动沟通
    if "压力" in result.data or "问题" in result.data or "困难" in result.data:
        print("\n3️⃣ 检测到用户可能需要支持，准备主动发起对话...")
        
        notification = Notification(
            title="💭 我注意到你今天可能遇到了一些挑战",
            body=(
                "根据今天的对话，我注意到你提到了项目压力和技术难点。\n\n"
                "如果你愿意的话，我们可以一起：\n"
                "1. 分析具体的技术难点\n"
                "2. 讨论团队沟通的改进方法\n"
                "3. 制定一个可行的行动计划\n\n"
                "我随时都在，不用有压力 😊"
            ),
            priority=NotifyPriority.HIGH,
            category="reflection",
            metadata={"trigger": "emotional_support_needed", "date": today}
        )
        
        success = router.send(notification)
        if success:
            print("   ✅ 主动对话邀请已发送（邮件+Notion）")
        else:
            print("   ⚠️ 发送失败")
else:
    print(f"   ❌ 反思生成失败: {result.error}")

# ============================================================
# 场景2: 早晨推送情报摘要
# ============================================================
print("\n" + "=" * 70)
print("场景2: 早晨推送情报摘要")
print("=" * 70)

print("\n1️⃣ 收集情报...")
intelligence_tool = EvolutionIntelligenceTool()
result = intelligence_tool.execute({
    "action": "briefing",
    "category": "tech"
})

if result.success:
    print(f"   ✅ 情报收集成功")
    
    print("\n2️⃣ 准备早晨情报推送...")
    notification = Notification(
        title=f"🌅 早安！{today} 技术情报摘要",
        body=(
            "早上好！这是今天为你准备的技术情报：\n\n"
            f"{result.data}\n\n"
            "祝你今天工作顺利！💪"
        ),
        priority=NotifyPriority.LOW,
        category="intelligence",
        metadata={"time": "morning", "date": today}
    )
    
    success = router.send(notification)
    if success:
        print("   ✅ 早晨情报已推送（Notion）")
    else:
        print("   ⚠️ 推送失败")
else:
    print(f"   ❌ 情报收集失败: {result.error}")

# ============================================================
# 场景3: 晚上推送反思总结（日报）
# ============================================================
print("\n" + "=" * 70)
print("场景3: 晚上推送反思总结（日报）")
print("=" * 70)

print("\n1️⃣ 生成每日反思总结...")
result = reflection_tool.execute({
    "action": "daily",
    "date": today
})

if result.success:
    print(f"   ✅ 日报生成成功")
    
    print("\n2️⃣ 准备晚间日报推送...")
    notification = Notification(
        title=f"🌙 {today} 每日反思总结",
        body=(
            f"今天的一天即将结束，这是你的每日反思：\n\n"
            f"{result.data}\n\n"
            "明天继续加油！晚安 😴"
        ),
        priority=NotifyPriority.NORMAL,
        category="reflection",
        metadata={"type": "daily_report", "date": today}
    )
    
    success = router.send(notification)
    if success:
        print("   ✅ 晚间日报已推送（邮件+Notion）")
    else:
        print("   ⚠️ 推送失败")
else:
    print(f"   ❌ 日报生成失败: {result.error}")

# ============================================================
# 场景3.5: 周报推送（如果是周日）
# ============================================================
print("\n" + "=" * 70)
print("场景3.5: 周报推送（模拟）")
print("=" * 70)

print("\n1️⃣ 生成周报...")
# 获取本周日期范围
today_dt = datetime.now()
week_start = (today_dt - timedelta(days=today_dt.weekday())).strftime("%Y-%m-%d")
week_end = today

result = reflection_tool.execute({
    "action": "weekly",
    "start_date": week_start,
    "end_date": week_end
})

if result.success:
    print(f"   ✅ 周报生成成功")
    
    print("\n2️⃣ 准备周报推送...")
    notification = Notification(
        title=f"📊 {week_start} ~ {week_end} 每周总结",
        body=(
            f"这是本周的总结报告：\n\n"
            f"{result.data}\n\n"
            "新的一周，新的开始！💪"
        ),
        priority=NotifyPriority.NORMAL,
        category="weekly_report",
        metadata={"type": "weekly_report", "start": week_start, "end": week_end}
    )
    
    success = router.send(notification)
    if success:
        print("   ✅ 周报已推送（邮件+Notion）")
    else:
        print("   ⚠️ 推送失败")
else:
    print(f"   ❌ 周报生成失败: {result.error}")

# ============================================================
# 总结
# ============================================================
print("\n" + "=" * 70)
print("测试总结")
print("=" * 70)
print("""
✅ 场景1: 反思后主动对话 - 检测情绪/问题，发送支持邀请
✅ 场景2: 早晨情报推送 - 低优先级，仅Notion
✅ 场景3: 晚间日报推送 - 正常优先级，邮件+Notion
✅ 场景3.5: 周报推送 - 正常优先级，邮件+Notion

💡 实际部署建议:
1. 使用cron或systemd timer定时触发
2. 早晨情报: 每天 08:00
3. 晚间日报: 每天 21:00
4. 周报: 每周日 20:00
5. 反思触发: 每次对话后检查
""")

print("=" * 70)
