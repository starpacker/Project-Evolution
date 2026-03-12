#!/usr/bin/env python3
"""查询Notion数据库schema"""
import sys
import os
sys.path.insert(0, '/home/yjh/ProjectEvolution')

import httpx
from evolution.config.settings import NOTIFICATION_CONFIG

notion_config = NOTIFICATION_CONFIG.get('notion', {})
token = notion_config.get('token')
databases = notion_config.get('databases', {})

if not token:
    print("❌ Notion token未配置")
    sys.exit(1)

headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28",
}

print("=" * 60)
print("Notion数据库Schema查询")
print("=" * 60)

for category, db_id in databases.items():
    print(f"\n📊 类别: {category}")
    print(f"   数据库ID: {db_id}")
    
    try:
        resp = httpx.get(
            f"https://api.notion.com/v1/databases/{db_id}",
            headers=headers,
            timeout=15
        )
        
        if resp.status_code == 200:
            data = resp.json()
            properties = data.get('properties', {})
            
            print(f"   ✅ 查询成功")
            print(f"\n   属性列表:")
            for prop_name, prop_info in properties.items():
                prop_type = prop_info.get('type', 'unknown')
                print(f"     - {prop_name}: {prop_type}")
        else:
            print(f"   ❌ 查询失败: {resp.status_code}")
            print(f"   错误: {resp.text[:200]}")
    except Exception as e:
        print(f"   ❌ 异常: {e}")

print("\n" + "=" * 60)
