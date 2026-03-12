#!/usr/bin/env python3
"""测试Notion推送"""
import sys
sys.path.insert(0, '/home/yjh/ProjectEvolution')

from evolution.notification.router import NotificationRouter, Notification, NotifyPriority

print("=" * 60)
print("测试 Notion 推送")
print("=" * 60)

router = NotificationRouter()

# 测试推送
notification = Notification(
    title="测试通知 - Mem0修复完成",
    body="✅ Mem0 embedding补丁已成功应用\n✅ 使用aliyun/text-embedding-v4模型\n✅ 向量维度: 1024",
    priority=NotifyPriority.NORMAL,
    category="reflection",
    metadata={"test": True}
)

print("\n📤 发送测试通知...")
success = router.send(notification)

if success:
    print("✅ Notion推送成功！")
    sys.exit(0)
else:
    print("❌ Notion推送失败")
    sys.exit(1)
