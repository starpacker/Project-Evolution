#!/usr/bin/env python3
"""
周报推送脚本
每周日晚上8点自动运行，推送每周总结
"""

import sys
import os
from datetime import datetime, timedelta
sys.path.insert(0, '/home/yjh/ProjectEvolution')

from evolution.notification.router import NotificationRouter, Notification, NotifyPriority
from evolution.tools.reflection_tool import EvolutionReflectionTool

def main():
    today = datetime.now()
    today_str = today.strftime("%Y-%m-%d")
    
    # 计算本周的开始和结束日期
    week_start = (today - timedelta(days=today.weekday())).strftime("%Y-%m-%d")
    week_end = today_str
    
    router = NotificationRouter()
    
    print(f"[{datetime.now()}] 开始生成周报 ({week_start} ~ {week_end})...")
    
    # 生成周报
    reflection_tool = EvolutionReflectionTool()
    result = reflection_tool.execute({
        "action": "weekly",
        "start_date": week_start,
        "end_date": week_end
    })
    
    if result.success:
        # 发送推送
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
            print(f"[{datetime.now()}] ✅ 周报推送成功")
        else:
            print(f"[{datetime.now()}] ❌ 推送失败")
            sys.exit(1)
    else:
        print(f"[{datetime.now()}] ❌ 周报生成失败: {result.error}")
        sys.exit(1)

if __name__ == "__main__":
    main()
