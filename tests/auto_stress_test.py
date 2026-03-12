#!/usr/bin/env python3
"""
Evolution 自动化压力测试系统
模拟真实用户进行大量对话，发现并修复系统问题
"""

import sys
import os
import json
import time
import random
from datetime import datetime, timedelta
sys.path.insert(0, '/home/yjh/ProjectEvolution')

from evolution.utils.llm import call_llm
from evolution.db.manager import DatabaseManager

# 模拟用户的对话场景
USER_SCENARIOS = [
    # 日程管理场景
    {
        "category": "schedule",
        "prompts": [
            "帮我添加一个日程：明天下午3点开会",
            "提醒我后天早上9点联系张三",
            "我周五要去北京出差，帮我记录一下",
            "下周一有个重要会议，早上10点",
            "帮我查看本周的日程安排",
            "我今天有什么安排？",
            "把明天的会议改到下午4点",
            "取消后天的日程",
        ]
    },
    # 技能学习场景
    {
        "category": "skill",
        "prompts": [
            "我今天学习了Python编程2小时",
            "记录一下，我完成了机器学习课程第3章",
            "我在深度学习方面有了新的理解",
            "今天练习了算法题，做了5道",
            "我的Python技能怎么样了？",
            "查看我的技能树",
            "我最近在学什么？",
        ]
    },
    # 人物关系场景
    {
        "category": "person",
        "prompts": [
            "张三是我的同事，负责后端开发",
            "李四是项目经理，很严格但专业",
            "王五是我的导师，在AI领域很有经验",
            "记录一下，小明今天帮我解决了一个bug",
            "张三最近怎么样？",
            "我认识哪些人？",
            "谁是我的导师？",
        ]
    },
    # 记忆存储场景
    {
        "category": "memory",
        "prompts": [
            "记住，我最喜欢的编程语言是Python",
            "我的生日是3月15日",
            "我住在北京海淀区",
            "我的目标是成为AI专家",
            "我喜欢什么编程语言？",
            "我的生日是什么时候？",
            "我的目标是什么？",
        ]
    },
    # 情绪压力场景
    {
        "category": "emotion",
        "prompts": [
            "今天压力好大，项目进度落后了",
            "我感觉很焦虑，不知道该怎么办",
            "团队沟通出现了问题，很头疼",
            "我遇到了一个技术难题，卡住了",
            "感觉有点累，需要休息",
            "今天心情不错，解决了一个大问题",
            "我很开心，项目终于完成了",
        ]
    },
    # 复杂混合场景
    {
        "category": "complex",
        "prompts": [
            "明天要和张三讨论Python项目，下午3点，帮我记录一下",
            "我今天学习了深度学习2小时，感觉有点累但很充实",
            "提醒我周五联系李四，讨论项目进度，这个很重要",
            "记住，王五教授建议我多看论文，我要把这个加入学习计划",
            "我的同事小明今天教了我一个新算法，我要记录下来并安排时间练习",
        ]
    },
]

# 错误模式检测
ERROR_PATTERNS = [
    "需要.*参数",
    "参数格式",
    "工具.*失败",
    "Error",
    "错误",
    "失败",
]

class AutoTester:
    def __init__(self):
        self.db = DatabaseManager()
        self.conversation_count = 0
        self.error_count = 0
        self.success_count = 0
        self.errors = []
        self.start_time = datetime.now()
        
    def simulate_conversation(self, user_message: str) -> dict:
        """模拟一次对话"""
        self.conversation_count += 1
        
        print(f"\n{'='*70}")
        print(f"对话 #{self.conversation_count}")
        print(f"{'='*70}")
        print(f"👤 用户: {user_message}")
        
        try:
            # 调用LLM
            response = call_llm(
                messages=[{"role": "user", "content": user_message}],
                tools=self.get_tools(),
                temperature=0.7
            )
            
            assistant_message = response.get("content", "")
            tool_calls = response.get("tool_calls", [])
            
            print(f"🤖 助手: {assistant_message}")
            
            # 检查是否有工具调用
            if tool_calls:
                print(f"🔧 工具调用: {len(tool_calls)}个")
                for tc in tool_calls:
                    print(f"   - {tc.get('function', {}).get('name')}")
            
            # 检查错误
            has_error = self.check_errors(assistant_message)
            
            if has_error:
                self.error_count += 1
                self.errors.append({
                    "conversation": self.conversation_count,
                    "user_message": user_message,
                    "assistant_message": assistant_message,
                    "tool_calls": tool_calls,
                    "timestamp": datetime.now().isoformat()
                })
                print("❌ 检测到错误")
            else:
                self.success_count += 1
                print("✅ 对话成功")
            
            # 记录到数据库
            self.db.log_conversation("user", user_message)
            self.db.log_conversation("assistant", assistant_message)
            
            return {
                "success": not has_error,
                "response": assistant_message,
                "tool_calls": tool_calls
            }
            
        except Exception as e:
            print(f"❌ 异常: {e}")
            self.error_count += 1
            self.errors.append({
                "conversation": self.conversation_count,
                "user_message": user_message,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })
            return {"success": False, "error": str(e)}
    
    def check_errors(self, message: str) -> bool:
        """检查消息中是否包含错误"""
        import re
        for pattern in ERROR_PATTERNS:
            if re.search(pattern, message):
                return True
        return False
    
    def get_tools(self) -> list:
        """获取工具定义"""
        # 这里返回简化的工具定义，实际应该从系统中获取
        return []
    
    def run_test_week(self):
        """模拟一周的对话"""
        print("🚀 开始模拟一周的对话...")
        print(f"开始时间: {self.start_time}")
        
        # 模拟7天
        for day in range(7):
            print(f"\n{'#'*70}")
            print(f"第 {day+1} 天")
            print(f"{'#'*70}")
            
            # 每天随机进行10-20次对话
            daily_conversations = random.randint(10, 20)
            
            for _ in range(daily_conversations):
                # 随机选择场景
                scenario = random.choice(USER_SCENARIOS)
                prompt = random.choice(scenario["prompts"])
                
                # 模拟对话
                result = self.simulate_conversation(prompt)
                
                # 短暂延迟，避免API限流
                time.sleep(0.5)
            
            # 每天结束后生成统计
            self.print_daily_stats(day + 1)
            
            # 模拟一天的时间间隔
            time.sleep(1)
        
        # 最终报告
        self.generate_final_report()
    
    def print_daily_stats(self, day: int):
        """打印每日统计"""
        print(f"\n📊 第{day}天统计:")
        print(f"   总对话: {self.conversation_count}")
        print(f"   成功: {self.success_count}")
        print(f"   错误: {self.error_count}")
        if self.conversation_count > 0:
            success_rate = (self.success_count / self.conversation_count) * 100
            print(f"   成功率: {success_rate:.1f}%")
    
    def generate_final_report(self):
        """生成最终报告"""
        end_time = datetime.now()
        duration = end_time - self.start_time
        
        print(f"\n{'='*70}")
        print("📊 最终测试报告")
        print(f"{'='*70}")
        print(f"测试时长: {duration}")
        print(f"总对话数: {self.conversation_count}")
        print(f"成功: {self.success_count}")
        print(f"错误: {self.error_count}")
        
        if self.conversation_count > 0:
            success_rate = (self.success_count / self.conversation_count) * 100
            print(f"成功率: {success_rate:.1f}%")
        
        # 保存错误日志
        if self.errors:
            error_file = f"logs/test_errors_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(error_file, 'w', encoding='utf-8') as f:
                json.dump(self.errors, f, ensure_ascii=False, indent=2)
            print(f"\n错误日志已保存: {error_file}")
        
        print(f"\n{'='*70}")

def main():
    tester = AutoTester()
    tester.run_test_week()

if __name__ == "__main__":
    main()
