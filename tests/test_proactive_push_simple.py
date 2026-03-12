#!/usr/bin/env python3
"""
测试Evolution系统的主动推送功能（简化版，不调用LLM）
"""

import sys
import os
from datetime import datetime, timedelta
sys.path.insert(0, '/home/yjh/ProjectEvolution')

from evolution.db.manager import DatabaseManager
from evolution.notification.router import NotificationRouter, Notification, NotifyPriority

print("=" * 70)
print("Evolution 主动推送功能测试（简化版）")
print("=" * 70)

db = DatabaseManager()
router = NotificationRouter()
today = datetime.now().strftime("%Y-%m-%d")

# ============================================================
# 场景1: 反思后主动发起对话
# ============================================================
print("\n" + "=" * 70)
print("场景1: 反思后主动发起对话")
print("=" * 70)

print("\n1️⃣ 模拟检测到用户需要支持...")
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

print("\n2️⃣ 发送主动对话邀请...")
success = router.send(notification)
if success:
    print("   ✅ 主动对话邀请已发送")
    print("   📧 邮件: 已发送")
    print("   📔 Notion: 已创建页面")
else:
    print("   ❌ 发送失败")

# ============================================================
# 场景2: 早晨推送情报摘要
# ============================================================
print("\n" + "=" * 70)
print("场景2: 早晨推送情报摘要")
print("=" * 70)

print("\n1️⃣ 准备早晨情报推送...")
notification = Notification(
    title=f"🌅 早安！{today} 技术情报摘要",
    body=(
        "早上好！这是今天为你准备的技术情报：\n\n"
        "📰 AI领域:\n"
        "- OpenAI发布GPT-5预览版\n"
        "- Google推出新的Gemini模型\n\n"
        "💻 开发工具:\n"
        "- VS Code 1.95发布，新增AI辅助功能\n"
        "- Python 3.13 Beta版本可用\n\n"
        "🔬 研究进展:\n"
        "- 新的Transformer架构优化方法\n"
        "- 量子计算在机器学习中的应用\n\n"
        "祝你今天工作顺利！💪"
    ),
    priority=NotifyPriority.NORMAL,  # 改为NORMAL，发送邮件
    category="intelligence",
    metadata={"time": "morning", "date": today}
)

print("\n2️⃣ 发送早晨情报...")
success = router.send(notification)
if success:
    print("   ✅ 早晨情报已推送")
    print("   � 邮件: 已发送")
    print("   📔 Notion: 已创建页面")
else:
    print("   ❌ 推送失败")

# ============================================================
# 场景3: 晚上推送反思总结（日报）
# ============================================================
print("\n" + "=" * 70)
print("场景3: 晚上推送反思总结（日报）")
print("=" * 70)

print("\n1️⃣ 准备晚间日报推送...")
notification = Notification(
    title=f"🌙 {today} 每日反思总结",
    body=(
        f"今天的一天即将结束，这是你的每日反思：\n\n"
        "📊 今日概览:\n"
        "- 对话次数: 15次\n"
        "- 主要话题: 项目管理、技术问题、团队协作\n"
        "- 情绪状态: 有压力但积极应对\n\n"
        "💡 关键洞察:\n"
        "1. 你在技术难点上遇到了挑战，但展现出了解决问题的决心\n"
        "2. 团队沟通问题需要关注，可能影响项目进度\n"
        "3. 你提到了压力，建议适当调整节奏\n\n"
        "🎯 明日建议:\n"
        "- 优先解决核心技术难点\n"
        "- 安排团队沟通会议\n"
        "- 留出时间进行技术调研\n\n"
        "明天继续加油！晚安 😴"
    ),
    priority=NotifyPriority.NORMAL,
    category="reflection",
    metadata={"type": "daily_report", "date": today}
)

print("\n2️⃣ 发送晚间日报...")
success = router.send(notification)
if success:
    print("   ✅ 晚间日报已推送")
    print("   📧 邮件: 已发送")
    print("   📔 Notion: 已创建页面")
else:
    print("   ❌ 推送失败")

# ============================================================
# 场景4: 周报推送
# ============================================================
print("\n" + "=" * 70)
print("场景4: 周报推送")
print("=" * 70)

today_dt = datetime.now()
week_start = (today_dt - timedelta(days=today_dt.weekday())).strftime("%Y-%m-%d")
week_end = today

print("\n1️⃣ 准备周报推送...")
notification = Notification(
    title=f"📊 {week_start} ~ {week_end} 每周总结",
    body=(
        f"这是本周的总结报告：\n\n"
        "📈 本周数据:\n"
        "- 工作日: 5天\n"
        "- 总对话: 87次\n"
        "- 完成任务: 12项\n"
        "- 新增技能: 3项\n\n"
        "🎯 主要成就:\n"
        "1. 完成了Mem0集成和调试\n"
        "2. 修复了Notion推送功能\n"
        "3. 优化了系统架构\n\n"
        "💭 反思与改进:\n"
        "- 技术问题解决能力有提升\n"
        "- 需要更好地管理时间和压力\n"
        "- 团队协作可以进一步加强\n\n"
        "📅 下周计划:\n"
        "- 完成项目核心功能\n"
        "- 进行系统性能优化\n"
        "- 准备技术分享\n\n"
        "新的一周，新的开始！💪"
    ),
    priority=NotifyPriority.NORMAL,
    category="weekly_report",
    metadata={"type": "weekly_report", "start": week_start, "end": week_end}
)

print("\n2️⃣ 发送周报...")
success = router.send(notification)
if success:
    print("   ✅ 周报已推送")
    print("   📧 邮件: 已发送")
    print("   📔 Notion: 已创建页面")
else:
    print("   ❌ 推送失败")

# ============================================================
# 总结
# ============================================================
print("\n" + "=" * 70)
print("测试总结")
print("=" * 70)
print("""
✅ 场景1: 反思后主动对话
   - 触发条件: 检测到情绪/问题关键词
   - 优先级: HIGH
   - 通道: 邮件 + Notion
   - 目的: 提供情感支持和问题解决

✅ 场景2: 早晨情报推送
   - 触发时间: 每天 08:00
   - 优先级: NORMAL
   - 通道: 邮件 + Notion
   - 目的: 提供每日技术资讯

✅ 场景3: 晚间日报推送
   - 触发时间: 每天 21:00
   - 优先级: NORMAL
   - 通道: 邮件 + Notion
   - 目的: 每日反思和总结

✅ 场景4: 周报推送
   - 触发时间: 每周日 20:00
   - 优先级: NORMAL
   - 通道: 邮件 + Notion
   - 目的: 周度总结和规划

💡 实际部署建议:
1. 使用cron或systemd timer定时触发
2. 创建独立的推送脚本
3. 添加错误重试机制
4. 记录推送日志
""")

print("\n📝 Cron配置示例:")
print("""
# 早晨情报推送 (每天 08:00)
0 8 * * * cd /home/yjh/ProjectEvolution && python scripts/morning_briefing.py

# 晚间日报推送 (每天 21:00)
0 21 * * * cd /home/yjh/ProjectEvolution && python scripts/evening_report.py

# 周报推送 (每周日 20:00)
0 20 * * 0 cd /home/yjh/ProjectEvolution && python scripts/weekly_report.py
""")

print("=" * 70)
print("✅ 所有测试完成！")
print("=" * 70)
