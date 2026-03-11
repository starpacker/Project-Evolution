#!/usr/bin/env python3
"""
快速测试 Telegram Bot 配置
"""

import os
import sys
import httpx
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

def load_env():
    """加载 .env 文件"""
    env_file = Path(__file__).parent.parent / ".env"
    if not env_file.exists():
        print("❌ .env 文件不存在")
        return {}
    
    env_vars = {}
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                env_vars[key] = value
    return env_vars

def test_bot_token(token):
    """测试 Bot Token 是否有效"""
    try:
        resp = httpx.get(f"https://api.telegram.org/bot{token}/getMe", timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            if data.get("ok"):
                bot_info = data.get("result", {})
                print(f"✅ Bot Token 有效")
                print(f"   Bot 名称: {bot_info.get('first_name')}")
                print(f"   Bot 用户名: @{bot_info.get('username')}")
                return True
        print(f"❌ Bot Token 无效: {resp.text}")
        return False
    except Exception as e:
        print(f"❌ 连接失败: {e}")
        return False

def test_chat_id(token, chat_id):
    """测试 Chat ID 是否正确"""
    try:
        resp = httpx.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={
                "chat_id": chat_id,
                "text": "🧪 Evolution Bot 配置测试成功！\n\n如果你看到这条消息，说明配置正确。"
            },
            timeout=10
        )
        if resp.status_code == 200:
            print(f"✅ Chat ID 有效，测试消息已发送")
            return True
        else:
            print(f"❌ Chat ID 无效: {resp.text}")
            return False
    except Exception as e:
        print(f"❌ 发送消息失败: {e}")
        return False

def main():
    print("╔═══════════════════════════════════════╗")
    print("║  Evolution Telegram Bot 配置测试     ║")
    print("╚═══════════════════════════════════════╝")
    print()
    
    # 加载环境变量
    env_vars = load_env()
    
    # 检查配置
    token = env_vars.get("TG_BOT_TOKEN", "")
    chat_id = env_vars.get("TG_CHAT_ID", "")
    
    if not token or token == "123456:ABC-xxx":
        print("❌ TG_BOT_TOKEN 未配置")
        print("   请在 .env 文件中设置正确的 Bot Token")
        print()
        print("📖 获取 Token 的步骤：")
        print("   1. 在 Telegram 搜索 @BotFather")
        print("   2. 发送 /newbot 创建新 Bot")
        print("   3. 按提示设置名称和用户名")
        print("   4. 复制返回的 Token 到 .env 文件")
        return 1
    
    if not chat_id or chat_id == "123456789":
        print("❌ TG_CHAT_ID 未配置")
        print("   请在 .env 文件中设置你的 Chat ID")
        print()
        print("📖 获取 Chat ID 的步骤：")
        print("   1. 在 Telegram 搜索你的 Bot")
        print("   2. 点击 Start 或发送任意消息")
        print(f"   3. 访问: https://api.telegram.org/bot{token}/getUpdates")
        print("   4. 在返回的 JSON 中找到 chat.id")
        return 1
    
    print("🔍 开始测试...\n")
    
    # 测试 Token
    print("1️⃣ 测试 Bot Token...")
    if not test_bot_token(token):
        return 1
    print()
    
    # 测试 Chat ID
    print("2️⃣ 测试 Chat ID...")
    if not test_chat_id(token, chat_id):
        return 1
    print()
    
    print("╔═══════════════════════════════════════╗")
    print("║  ✅ 所有测试通过！                   ║")
    print("╚═══════════════════════════════════════╝")
    print()
    print("🚀 下一步：启动 Bot")
    print("   方式1: python -m evolution.chat.telegram_bot")
    print("   方式2: ./scripts/start_telegram_bot.sh")
    print()
    print("💬 然后在 Telegram 中向你的 Bot 发送消息即可开始对话！")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
