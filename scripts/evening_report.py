#!/usr/bin/env python3
"""
晚间日报推送脚本
每天晚上9点自动运行，推送每日反思总结
"""

import sys
import os
from datetime import datetime
sys.path.insert(0, '/home/yjh/ProjectEvolution')

from evolution.notification.router import NotificationRouter, Notification, NotifyPriority
from evolution.tools.reflection_tool import EvolutionReflectionTool

def main():
    today = datetime.now().strftime("%Y-%m-%d")
    router = NotificationRouter()
    
    print(f"[{datetime.now()}] 开始生成每日反思...")
    
    # 生成每日反思
    reflection_tool = EvolutionReflectionTool()
    result = reflection_tool.execute({
        "action": "daily",
        "date": today
    })
    
    if result.success:
        # 发送推送
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
            print(f"[{datetime.now()}] ✅ 晚间日报推送成功")
        else:
            print(f"[{datetime.now()}] ❌ 推送失败")
            sys.exit(1)
    else:
        print(f"[{datetime.now()}] ❌ 反思生成失败: {result.error}")
        sys.exit(1)

if __name__ == "__main__":
    main()
