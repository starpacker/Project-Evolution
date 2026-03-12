#!/usr/bin/env python3
"""
早晨情报推送脚本
每天早上8点自动运行，推送技术情报摘要
"""

import sys
import os
from datetime import datetime
sys.path.insert(0, '/home/yjh/ProjectEvolution')

from evolution.notification.router import NotificationRouter, Notification, NotifyPriority
from evolution.tools.intelligence_tool import EvolutionIntelligenceTool

def main():
    today = datetime.now().strftime("%Y-%m-%d")
    router = NotificationRouter()
    
    print(f"[{datetime.now()}] 开始收集早晨情报...")
    
    # 收集情报
    intelligence_tool = EvolutionIntelligenceTool()
    result = intelligence_tool.execute({
        "action": "briefing",
        "category": "tech"
    })
    
    if result.success:
        # 发送推送
        notification = Notification(
            title=f"🌅 早安！{today} 技术情报摘要",
            body=(
                "早上好！这是今天为你准备的技术情报：\n\n"
                f"{result.data}\n\n"
                "祝你今天工作顺利！💪"
            ),
            priority=NotifyPriority.NORMAL,  # 改为NORMAL，发送邮件
            category="intelligence",
            metadata={"time": "morning", "date": today}
        )
        
        success = router.send(notification)
        if success:
            print(f"[{datetime.now()}] ✅ 早晨情报推送成功")
        else:
            print(f"[{datetime.now()}] ❌ 推送失败")
            sys.exit(1)
    else:
        print(f"[{datetime.now()}] ❌ 情报收集失败: {result.error}")
        sys.exit(1)

if __name__ == "__main__":
    main()
