#!/usr/bin/env python3
"""
Evolution 真实API压力测试
通过HTTP API与系统交互，模拟真实用户场景
"""

import sys
import os
import json
import time
import random
import requests
from datetime import datetime, timedelta

# 测试配置
API_BASE = "http://10.128.250.187:5000"
TEST_DURATION_DAYS = 7
CONVERSATIONS_PER_DAY = 50  # 每天对话次数
DELAY_BETWEEN_MESSAGES = 2  # 消息间隔（秒）

# 用户对话场景库
SCENARIOS = {
    "schedule_add": [
        "帮我添加一个日程：明天下午3点开会",
        "提醒我后天早上9点联系张三",
        "我周五要去北京出差",
        "下周一有个重要会议，早上10点",
        "帮我记录：周三下午2点面试",
        "添加日程：周四晚上7点聚餐",
    ],
    "schedule_query": [
        "我今天有什么安排？",
        "查看本周的日程",
        "明天有什么事情？",
        "我最近有哪些待办事项？",
    ],
    "skill_record": [
        "我今天学习了Python编程2小时",
        "记录：完成了机器学习课程第3章",
        "我练习了算法题，做了5道",
        "今天看了深度学习的论文",
        "学习了React框架的基础知识",
    ],
    "skill_query": [
        "我的Python技能怎么样了？",
        "查看我的技能树",
        "我最近在学什么？",
        "我掌握了哪些技能？",
    ],
    "person_add": [
        "张三是我的同事，负责后端开发",
        "李四是项目经理，很严格但专业",
        "王五是我的导师，在AI领域很有经验",
        "小明今天帮我解决了一个bug",
        "记录：刘老师是我的论文指导老师",
    ],
    "person_query": [
        "张三是谁？",
        "我认识哪些人？",
        "谁是我的导师？",
        "告诉我关于李四的信息",
    ],
    "memory_add": [
        "记住，我最喜欢的编程语言是Python",
        "我的生日是3月15日",
        "我住在北京海淀区",
        "我的目标是成为AI专家",
        "我喜欢喝咖啡，不喜欢茶",
    ],
    "memory_query": [
        "我喜欢什么编程语言？",
        "我的生日是什么时候？",
        "我的目标是什么？",
        "我住在哪里？",
    ],
    "emotion": [
        "今天压力好大，项目进度落后了",
        "我感觉很焦虑，不知道该怎么办",
        "团队沟通出现了问题",
        "我遇到了一个技术难题",
        "今天心情不错，解决了一个大问题",
        "我很开心，项目终于完成了",
    ],
    "complex": [
        "明天要和张三讨论Python项目，下午3点",
        "我今天学习了深度学习2小时，感觉有点累",
        "提醒我周五联系李四讨论项目进度",
        "记住，王五教授建议我多看论文",
    ],
    "casual": [
        "你好",
        "今天天气怎么样？",
        "给我讲个笑话",
        "你能帮我做什么？",
        "谢谢",
        "再见",
    ],
}

class StressTester:
    def __init__(self):
        self.stats = {
            "total": 0,
            "success": 0,
            "error": 0,
            "tool_errors": 0,
            "api_errors": 0,
            "errors": [],
            "response_times": [],
        }
        self.start_time = datetime.now()
        
    def send_message(self, message: str) -> dict:
        """发送消息到API"""
        try:
            start = time.time()
            response = requests.post(
                f"{API_BASE}/api/chat",
                json={"message": message},
                timeout=30
            )
            elapsed = time.time() - start
            
            self.stats["response_times"].append(elapsed)
            
            if response.status_code == 200:
                return {
                    "success": True,
                    "data": response.json(),
                    "elapsed": elapsed
                }
            else:
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}",
                    "elapsed": elapsed
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "elapsed": 0
            }
    
    def check_tool_error(self, response_text: str) -> bool:
        """检查是否有工具调用错误"""
        error_keywords = [
            "需要.*参数",
            "参数格式",
            "[db]",
            "[memory]",
            "工具.*失败",
        ]
        import re
        for keyword in error_keywords:
            if re.search(keyword, response_text):
                return True
        return False
    
    def run_conversation(self, message: str, scenario: str) -> dict:
        """执行一次对话"""
        self.stats["total"] += 1
        
        print(f"\n[{self.stats['total']}] 👤 {message}")
        
        result = self.send_message(message)
        
        if not result["success"]:
            self.stats["api_errors"] += 1
            self.stats["error"] += 1
            print(f"❌ API错误: {result['error']}")
            self.stats["errors"].append({
                "type": "api_error",
                "message": message,
                "error": result["error"],
                "scenario": scenario
            })
            return result
        
        response_text = result["data"].get("response", "")
        print(f"🤖 {response_text[:100]}...")
        print(f"⏱️  响应时间: {result['elapsed']:.2f}s")
        
        # 检查工具错误
        if self.check_tool_error(response_text):
            self.stats["tool_errors"] += 1
            self.stats["error"] += 1
            print(f"⚠️  工具调用错误")
            self.stats["errors"].append({
                "type": "tool_error",
                "message": message,
                "response": response_text,
                "scenario": scenario
            })
        else:
            self.stats["success"] += 1
            print(f"✅ 成功")
        
        return result
    
    def run_day(self, day: int):
        """模拟一天的对话"""
        print(f"\n{'='*70}")
        print(f"📅 第 {day} 天")
        print(f"{'='*70}")
        
        for i in range(CONVERSATIONS_PER_DAY):
            # 随机选择场景
            scenario = random.choice(list(SCENARIOS.keys()))
            message = random.choice(SCENARIOS[scenario])
            
            # 执行对话
            self.run_conversation(message, scenario)
            
            # 延迟
            time.sleep(DELAY_BETWEEN_MESSAGES)
            
            # 每10条打印一次统计
            if (i + 1) % 10 == 0:
                self.print_stats(brief=True)
    
    def print_stats(self, brief=False):
        """打印统计信息"""
        if brief:
            success_rate = (self.stats["success"] / self.stats["total"] * 100) if self.stats["total"] > 0 else 0
            avg_time = sum(self.stats["response_times"]) / len(self.stats["response_times"]) if self.stats["response_times"] else 0
            print(f"\n📊 进度: {self.stats['total']} | 成功率: {success_rate:.1f}% | 平均响应: {avg_time:.2f}s")
        else:
            print(f"\n{'='*70}")
            print("📊 详细统计")
            print(f"{'='*70}")
            print(f"总对话数: {self.stats['total']}")
            print(f"成功: {self.stats['success']}")
            print(f"错误: {self.stats['error']}")
            print(f"  - 工具错误: {self.stats['tool_errors']}")
            print(f"  - API错误: {self.stats['api_errors']}")
            
            if self.stats["total"] > 0:
                success_rate = self.stats["success"] / self.stats["total"] * 100
                print(f"成功率: {success_rate:.1f}%")
            
            if self.stats["response_times"]:
                avg_time = sum(self.stats["response_times"]) / len(self.stats["response_times"])
                min_time = min(self.stats["response_times"])
                max_time = max(self.stats["response_times"])
                print(f"\n响应时间:")
                print(f"  平均: {avg_time:.2f}s")
                print(f"  最快: {min_time:.2f}s")
                print(f"  最慢: {max_time:.2f}s")
    
    def save_report(self):
        """保存测试报告"""
        report = {
            "start_time": self.start_time.isoformat(),
            "end_time": datetime.now().isoformat(),
            "duration": str(datetime.now() - self.start_time),
            "stats": self.stats,
        }
        
        filename = f"logs/stress_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        os.makedirs("logs", exist_ok=True)
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"\n📄 报告已保存: {filename}")
    
    def run(self):
        """运行完整测试"""
        print("🚀 Evolution 压力测试开始")
        print(f"目标: {TEST_DURATION_DAYS}天 x {CONVERSATIONS_PER_DAY}次/天 = {TEST_DURATION_DAYS * CONVERSATIONS_PER_DAY}次对话")
        print(f"API: {API_BASE}")
        
        try:
            for day in range(1, TEST_DURATION_DAYS + 1):
                self.run_day(day)
                self.print_stats()
        except KeyboardInterrupt:
            print("\n\n⚠️  测试被中断")
        finally:
            print(f"\n{'='*70}")
            print("🏁 测试结束")
            print(f"{'='*70}")
            self.print_stats()
            self.save_report()
            
            # 打印错误摘要
            if self.stats["errors"]:
                print(f"\n❌ 发现 {len(self.stats['errors'])} 个错误:")
                for i, err in enumerate(self.stats["errors"][:10], 1):
                    print(f"\n{i}. [{err['type']}] {err['scenario']}")
                    print(f"   消息: {err['message']}")
                    if 'response' in err:
                        print(f"   响应: {err['response'][:100]}...")

def main():
    tester = StressTester()
    tester.run()

if __name__ == "__main__":
    main()
