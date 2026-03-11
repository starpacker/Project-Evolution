#!/usr/bin/env python3
"""
验证所有凭证的有效性
Validate all credentials (SMTP, Notion, LLM API)
"""

import sys
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import httpx
import json

def validate_smtp(host, port, user, password, to_address):
    """验证 SMTP 邮件配置"""
    print("\n" + "="*50)
    print("📧 验证 SMTP 邮件配置...")
    print("="*50)
    
    try:
        # 连接 SMTP 服务器
        print(f"连接到 {host}:{port}...")
        server = smtplib.SMTP_SSL(host, port, timeout=10)
        
        # 登录
        print(f"使用账号 {user} 登录...")
        server.login(user, password)
        
        # 发送测试邮件
        msg = MIMEMultipart()
        msg['From'] = user
        msg['To'] = to_address
        msg['Subject'] = '🧪 Evolution 邮件配置测试'
        
        body = """
        <html>
        <body>
            <h2>✅ Evolution 邮件配置测试成功！</h2>
            <p>如果你看到这封邮件，说明 SMTP 配置正确。</p>
            <p>系统现在可以通过邮件发送通知了。</p>
        </body>
        </html>
        """
        msg.attach(MIMEText(body, 'html'))
        
        print(f"发送测试邮件到 {to_address}...")
        server.send_message(msg)
        server.quit()
        
        print("✅ SMTP 配置验证成功！")
        print(f"   服务器: {host}:{port}")
        print(f"   账号: {user}")
        print(f"   测试邮件已发送到: {to_address}")
        return True
        
    except smtplib.SMTPAuthenticationError:
        print("❌ SMTP 认证失败：用户名或密码错误")
        return False
    except smtplib.SMTPException as e:
        print(f"❌ SMTP 错误: {e}")
        return False
    except Exception as e:
        print(f"❌ 连接失败: {e}")
        return False

def validate_notion(token, database_id):
    """验证 Notion API 配置"""
    print("\n" + "="*50)
    print("📝 验证 Notion API 配置...")
    print("="*50)
    
    try:
        # 测试 Token
        print("测试 Notion Token...")
        headers = {
            "Authorization": f"Bearer {token}",
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json"
        }
        
        resp = httpx.get("https://api.notion.com/v1/users/me", headers=headers, timeout=10)
        
        if resp.status_code == 200:
            user_data = resp.json()
            print(f"✅ Notion Token 有效")
            print(f"   用户: {user_data.get('name', 'N/A')}")
        else:
            print(f"❌ Notion Token 无效: {resp.status_code} - {resp.text}")
            return False
        
        # 测试数据库访问
        print(f"\n测试数据库访问 (ID: {database_id[:8]}...)...")
        resp = httpx.get(
            f"https://api.notion.com/v1/databases/{database_id}",
            headers=headers,
            timeout=10
        )
        
        if resp.status_code == 200:
            db_data = resp.json()
            print(f"✅ 数据库访问成功")
            print(f"   数据库标题: {db_data.get('title', [{}])[0].get('plain_text', 'N/A')}")
            
            # 尝试创建测试页面
            print("\n创建测试页面...")
            test_page = {
                "parent": {"database_id": database_id},
                "properties": {
                    "Name": {
                        "title": [
                            {
                                "text": {
                                    "content": "🧪 Evolution 配置测试"
                                }
                            }
                        ]
                    }
                }
            }
            
            resp = httpx.post(
                "https://api.notion.com/v1/pages",
                headers=headers,
                json=test_page,
                timeout=10
            )
            
            if resp.status_code == 200:
                print("✅ 测试页面创建成功")
                print("   Notion 配置完全正常！")
                return True
            else:
                print(f"⚠️  无法创建页面: {resp.status_code}")
                print(f"   可能是权限问题，但读取权限正常")
                return True  # 读取权限足够
        else:
            print(f"❌ 无法访问数据库: {resp.status_code} - {resp.text}")
            return False
            
    except Exception as e:
        print(f"❌ Notion API 测试失败: {e}")
        return False

def validate_llm_api(api_key, base_url, model):
    """验证 LLM API 配置"""
    print("\n" + "="*50)
    print("🤖 验证 LLM API 配置...")
    print("="*50)
    
    try:
        print(f"测试 API: {base_url}")
        print(f"模型: {model}")
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        # 测试简单的 completion
        payload = {
            "model": model,
            "messages": [
                {"role": "user", "content": "请用一句话回复：你好"}
            ],
            "max_tokens": 50,
            "temperature": 0.3
        }
        
        print("发送测试请求...")
        resp = httpx.post(
            f"{base_url}/chat/completions",
            headers=headers,
            json=payload,
            timeout=30
        )
        
        if resp.status_code == 200:
            data = resp.json()
            response_text = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            print(f"✅ LLM API 配置有效")
            print(f"   模型响应: {response_text[:100]}")
            print(f"   使用的模型: {data.get('model', model)}")
            return True
        else:
            print(f"❌ API 请求失败: {resp.status_code}")
            print(f"   响应: {resp.text[:200]}")
            return False
            
    except Exception as e:
        print(f"❌ LLM API 测试失败: {e}")
        return False

def main():
    print("\n╔═══════════════════════════════════════════════╗")
    print("║     Evolution 凭证验证工具                   ║")
    print("║  Credential Validation Tool                  ║")
    print("╚═══════════════════════════════════════════════╝")
    
    # 从用户提供的信息中读取凭证
    credentials = {
        "smtp": {
            "host": os.environ.get("SMTP_HOST", "smtp.qq.com"),
            "port": int(os.environ.get("SMTP_PORT", "465")),
            "user": os.environ.get("SMTP_USER", ""),
            "password": os.environ.get("SMTP_PASSWORD", ""),
            "to": os.environ.get("SMTP_TO", "")
        },
        "notion": {
            "token": os.environ.get("NOTION_TOKEN", ""),
            "database_id": os.environ.get("NOTION_DATABASE_ID", "")
        },
        "llm": {
            "api_key": os.environ.get("LLM_API_KEY", ""),
            "base_url": os.environ.get("LLM_BASE_URL", "https://ai-gateway-internal.dp.tech/v1"),
            "model": os.environ.get("LLM_MODEL", "cds/Claude-4.6-opus")
        }
    }
    
    results = {}
    
    # 验证 SMTP
    results['smtp'] = validate_smtp(
        credentials['smtp']['host'],
        credentials['smtp']['port'],
        credentials['smtp']['user'],
        credentials['smtp']['password'],
        credentials['smtp']['to']
    )
    
    # 验证 Notion
    results['notion'] = validate_notion(
        credentials['notion']['token'],
        credentials['notion']['database_id']
    )
    
    # 验证 LLM API
    results['llm'] = validate_llm_api(
        credentials['llm']['api_key'],
        credentials['llm']['base_url'],
        credentials['llm']['model']
    )
    
    # 总结
    print("\n" + "="*50)
    print("📊 验证结果汇总")
    print("="*50)
    print(f"SMTP 邮件:  {'✅ 通过' if results['smtp'] else '❌ 失败'}")
    print(f"Notion API: {'✅ 通过' if results['notion'] else '❌ 失败'}")
    print(f"LLM API:    {'✅ 通过' if results['llm'] else '❌ 失败'}")
    
    all_passed = all(results.values())
    if all_passed:
        print("\n🎉 所有凭证验证通过！可以注入到项目中。")
        return 0
    else:
        print("\n⚠️  部分凭证验证失败，请检查配置。")
        return 1

if __name__ == "__main__":
    sys.exit(main())
