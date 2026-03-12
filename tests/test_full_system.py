"""
Evolution 完整系统测试
测试所有功能模块的端到端集成
"""

import os
import sys
import json
import time
from datetime import datetime, timedelta
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from evolution.tools.memory_tool import EvolutionMemoryTool
from evolution.tools.db_tool import EvolutionDBTool
from evolution.tools.reflection_tool import EvolutionReflectionTool
from evolution.tools.intelligence_tool import EvolutionIntelligenceTool
from evolution.notification.router import NotificationRouter, Notification, NotifyPriority
from evolution.db.manager import DatabaseManager


class SystemTester:
    """系统测试器"""
    
    def __init__(self):
        self.memory_tool = EvolutionMemoryTool()
        self.db_tool = EvolutionDBTool()
        self.reflection_tool = EvolutionReflectionTool()
        self.intelligence_tool = EvolutionIntelligenceTool()
        self.db = DatabaseManager()
        
        self.test_results = []
        self.current_test = None
    
    def log(self, message, level="INFO"):
        """记录测试日志"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        prefix = {
            "INFO": "ℹ️",
            "SUCCESS": "✅",
            "ERROR": "❌",
            "WARNING": "⚠️",
        }.get(level, "📝")
        print(f"[{timestamp}] {prefix} {message}")
    
    def start_test(self, test_name):
        """开始一个测试"""
        self.current_test = {
            "name": test_name,
            "start_time": time.time(),
            "status": "running",
            "errors": [],
        }
        self.log(f"\n{'='*60}", "INFO")
        self.log(f"开始测试: {test_name}", "INFO")
        self.log(f"{'='*60}", "INFO")
    
    def end_test(self, success=True, error=None):
        """结束一个测试"""
        if self.current_test:
            self.current_test["end_time"] = time.time()
            self.current_test["duration"] = self.current_test["end_time"] - self.current_test["start_time"]
            self.current_test["status"] = "success" if success else "failed"
            if error:
                self.current_test["errors"].append(error)
            
            self.test_results.append(self.current_test)
            
            if success:
                self.log(f"✅ 测试通过: {self.current_test['name']} ({self.current_test['duration']:.2f}s)", "SUCCESS")
            else:
                self.log(f"❌ 测试失败: {self.current_test['name']}: {error}", "ERROR")
            
            self.current_test = None
    
    # ==================== 记忆系统测试 ====================
    
    def test_memory_add(self):
        """测试记忆添加"""
        self.start_test("记忆系统 - 添加记忆")
        try:
            # 添加多条测试记忆
            memories = [
                "我正在学习深度学习，特别关注Transformer架构",
                "我的导师是李教授，他对我的论文要求很严格",
                "我最近在读《深度学习》这本书，觉得很有收获",
                "我计划在3月底完成论文初稿",
            ]
            
            for mem in memories:
                result = self.memory_tool.execute({
                    "action": "add",
                    "content": mem,
                    "metadata": {"type": "test", "timestamp": datetime.now().isoformat()}
                })
                
                if result.status != "success":
                    raise Exception(f"添加记忆失败: {result.result}")
                
                self.log(f"已添加记忆: {mem[:50]}...", "INFO")
            
            self.end_test(success=True)
        except Exception as e:
            self.end_test(success=False, error=str(e))
    
    def test_memory_search(self):
        """测试记忆搜索"""
        self.start_test("记忆系统 - 搜索记忆")
        try:
            # 搜索不同主题
            queries = [
                "深度学习",
                "导师",
                "论文",
                "学习计划",
            ]
            
            for query in queries:
                result = self.memory_tool.execute({
                    "action": "search",
                    "query": query
                })
                
                if result.status != "success":
                    raise Exception(f"搜索失败: {result.result}")
                
                self.log(f"搜索 '{query}': 找到相关记忆", "INFO")
                self.log(f"  结果: {result.result[:200]}...", "INFO")
            
            self.end_test(success=True)
        except Exception as e:
            self.end_test(success=False, error=str(e))
    
    def test_memory_profile(self):
        """测试用户档案获取"""
        self.start_test("记忆系统 - 获取用户档案")
        try:
            result = self.memory_tool.execute({"action": "profile"})
            
            if result.status != "success":
                raise Exception(f"获取档案失败: {result.result}")
            
            self.log("用户档案获取成功", "INFO")
            self.log(f"  档案内容: {result.result[:300]}...", "INFO")
            
            self.end_test(success=True)
        except Exception as e:
            self.end_test(success=False, error=str(e))
    
    # ==================== 数据库工具测试 ====================
    
    def test_schedule_management(self):
        """测试日程管理"""
        self.start_test("数据库工具 - 日程管理")
        try:
            # 添加日程
            tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
            result = self.db_tool.execute({
                "action": "add_schedule",
                "content": "完成系统测试报告",
                "due_date": f"{tomorrow}T18:00:00",
                "priority": "high",
                "category": "professional"
            })
            
            if result.status != "success":
                raise Exception(f"添加日程失败: {result.result}")
            
            self.log(f"已添加日程: {result.result}", "INFO")
            
            # 查询日程
            result = self.db_tool.execute({"action": "list_schedule"})
            if result.status != "success":
                raise Exception(f"查询日程失败: {result.result}")
            
            self.log(f"日程列表:\n{result.result}", "INFO")
            
            self.end_test(success=True)
        except Exception as e:
            self.end_test(success=False, error=str(e))
    
    def test_skill_management(self):
        """测试技能管理"""
        self.start_test("数据库工具 - 技能管理")
        try:
            # 添加技能
            skills = [
                {"name": "深度学习", "category": "professional", "level": 5, "target_level": 8},
                {"name": "批判性思维", "category": "thinking", "level": 3, "target_level": 7},
                {"name": "Python编程", "category": "professional", "level": 7, "target_level": 9},
            ]
            
            for skill in skills:
                result = self.db_tool.execute({
                    "action": "add_skill",
                    **skill
                })
                
                if result.status != "success":
                    self.log(f"添加技能 {skill['name']} 可能已存在，跳过", "WARNING")
                else:
                    self.log(f"已添加技能: {skill['name']}", "INFO")
            
            # 查询技能列表
            result = self.db_tool.execute({"action": "list_skills"})
            if result.status != "success":
                raise Exception(f"查询技能失败: {result.result}")
            
            self.log(f"技能列表:\n{result.result}", "INFO")
            
            self.end_test(success=True)
        except Exception as e:
            self.end_test(success=False, error=str(e))
    
    def test_person_management(self):
        """测试人物档案管理"""
        self.start_test("数据库工具 - 人物档案管理")
        try:
            # 添加人物
            persons = [
                {
                    "name": "李教授",
                    "relationship": "导师",
                    "likes": "严谨的研究态度",
                    "dislikes": "拖延",
                    "interaction_frequency": "high",
                    "emotional_impact": "positive"
                },
                {
                    "name": "张同学",
                    "relationship": "同学",
                    "likes": "讨论技术问题",
                    "interaction_frequency": "medium",
                    "emotional_impact": "neutral"
                },
            ]
            
            for person in persons:
                result = self.db_tool.execute({
                    "action": "upsert_person",
                    **person
                })
                
                if result.status != "success":
                    raise Exception(f"添加人物失败: {result.result}")
                
                self.log(f"已添加/更新人物: {person['name']}", "INFO")
            
            # 查询人物列表
            result = self.db_tool.execute({"action": "list_persons"})
            if result.status != "success":
                raise Exception(f"查询人物失败: {result.result}")
            
            self.log(f"人物列表:\n{result.result}", "INFO")
            
            self.end_test(success=True)
        except Exception as e:
            self.end_test(success=False, error=str(e))
    
    def test_training_log(self):
        """测试训练记录"""
        self.start_test("数据库工具 - 训练记录")
        try:
            # 获取技能ID
            skills = self.db.list_skills()
            if not skills:
                raise Exception("没有可用的技能，请先添加技能")
            
            skill = skills[0]
            
            # 添加训练记录
            result = self.db_tool.execute({
                "action": "add_training",
                "skill_name": skill["name"],
                "modality": "T2",
                "topic": "深度学习中的注意力机制",
                "rating": "good",
                "insight": "理解了自注意力的计算过程"
            })
            
            if result.status != "success":
                raise Exception(f"添加训练记录失败: {result.result}")
            
            self.log(f"已添加训练记录: {result.result}", "INFO")
            
            # 查询训练记录
            result = self.db_tool.execute({
                "action": "list_trainings",
                "skill_name": skill["name"]
            })
            
            if result.status != "success":
                raise Exception(f"查询训练记录失败: {result.result}")
            
            self.log(f"训练记录:\n{result.result}", "INFO")
            
            self.end_test(success=True)
        except Exception as e:
            self.end_test(success=False, error=str(e))
    
    def test_stats(self):
        """测试统计功能"""
        self.start_test("数据库工具 - 统计数据")
        try:
            result = self.db_tool.execute({"action": "stats"})
            
            if result.status != "success":
                raise Exception(f"获取统计失败: {result.result}")
            
            self.log(f"系统统计:\n{result.result}", "INFO")
            
            self.end_test(success=True)
        except Exception as e:
            self.end_test(success=False, error=str(e))
    
    # ==================== 反思系统测试 ====================
    
    def test_daily_reflection(self):
        """测试每日反思"""
        self.start_test("反思系统 - 每日反思生成")
        try:
            # 先添加一些对话记录
            today = datetime.now().strftime("%Y-%m-%d")
            conversations = [
                ("user", "今天学习了Transformer的原理，感觉很有收获"),
                ("assistant", "很好，你能具体说说学到了什么吗？"),
                ("user", "主要是自注意力机制，还有位置编码"),
                ("assistant", "不错，这些是Transformer的核心。你打算如何应用这些知识？"),
            ]
            
            for role, content in conversations:
                self.db.log_conversation(today, role, content)
            
            self.log("已添加测试对话记录", "INFO")
            
            # 生成每日反思
            self.log("正在生成每日反思（这可能需要20-30秒）...", "INFO")
            result = self.reflection_tool.execute({
                "action": "generate",
                "type": "daily"
            })
            
            if result.status != "success":
                raise Exception(f"生成反思失败: {result.result}")
            
            self.log(f"每日反思生成成功:\n{result.result[:500]}...", "SUCCESS")
            
            self.end_test(success=True)
        except Exception as e:
            self.end_test(success=False, error=str(e))
    
    # ==================== 情报系统测试 ====================
    
    def test_intelligence_briefing(self):
        """测试情报收集"""
        self.start_test("情报系统 - 情报收集与筛选")
        try:
            self.log("正在收集情报（这可能需要30-60秒）...", "INFO")
            result = self.intelligence_tool.execute({"action": "briefing"})
            
            if result.status != "success":
                raise Exception(f"情报收集失败: {result.result}")
            
            self.log(f"情报收集成功:\n{result.result[:500]}...", "SUCCESS")
            
            self.end_test(success=True)
        except Exception as e:
            self.end_test(success=False, error=str(e))
    
    def test_intelligence_feeds(self):
        """测试RSS源管理"""
        self.start_test("情报系统 - RSS源管理")
        try:
            # 列出当前订阅源
            result = self.intelligence_tool.execute({"action": "list_feeds"})
            
            if result.status != "success":
                raise Exception(f"列出订阅源失败: {result.result}")
            
            self.log(f"当前订阅源:\n{result.result[:300]}...", "INFO")
            
            # 添加自定义源（测试）
            result = self.intelligence_tool.execute({
                "action": "add_feed",
                "url": "https://arxiv.org/rss/cs.AI",
                "name": "arXiv AI (测试)"
            })
            
            if result.status == "success":
                self.log("成功添加测试订阅源", "INFO")
            
            self.end_test(success=True)
        except Exception as e:
            self.end_test(success=False, error=str(e))
    
    # ==================== 通知系统测试 ====================
    
    def test_email_notification(self):
        """测试邮件通知"""
        self.start_test("通知系统 - 邮件推送")
        try:
            from evolution.config.settings import EMAIL_ENABLED
            
            if not EMAIL_ENABLED:
                self.log("邮件通知未启用，跳过测试", "WARNING")
                self.end_test(success=True)
                return
            
            router = NotificationRouter()
            notification = Notification(
                title="Evolution 系统测试 - 邮件通知",
                body="这是一封测试邮件，用于验证邮件通知功能是否正常工作。\n\n测试时间: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                priority=NotifyPriority.NORMAL,
                category="test"
            )
            
            router.send(notification)
            self.log("邮件通知已发送", "SUCCESS")
            
            self.end_test(success=True)
        except Exception as e:
            self.end_test(success=False, error=str(e))
    
    def test_notion_notification(self):
        """测试Notion通知"""
        self.start_test("通知系统 - Notion推送")
        try:
            from evolution.config.settings import NOTION_ENABLED
            
            if not NOTION_ENABLED:
                self.log("Notion通知未启用，跳过测试", "WARNING")
                self.end_test(success=True)
                return
            
            router = NotificationRouter()
            notification = Notification(
                title="Evolution 系统测试 - Notion通知",
                body="这是一条测试记录，用于验证Notion集成功能。\n\n测试时间: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                priority=NotifyPriority.LOW,
                category="intelligence",
                metadata={"date": datetime.now().strftime("%Y-%m-%d")}
            )
            
            router.send(notification)
            self.log("Notion通知已发送", "SUCCESS")
            
            self.end_test(success=True)
        except Exception as e:
            self.end_test(success=False, error=str(e))
    
    # ==================== 生成测试报告 ====================
    
    def generate_report(self):
        """生成测试报告"""
        self.log("\n" + "="*60, "INFO")
        self.log("测试报告", "INFO")
        self.log("="*60, "INFO")
        
        total = len(self.test_results)
        success = sum(1 for t in self.test_results if t["status"] == "success")
        failed = total - success
        
        self.log(f"\n总测试数: {total}", "INFO")
        self.log(f"通过: {success} ✅", "SUCCESS")
        self.log(f"失败: {failed} ❌", "ERROR" if failed > 0 else "INFO")
        
        if failed > 0:
            self.log("\n失败的测试:", "ERROR")
            for test in self.test_results:
                if test["status"] == "failed":
                    self.log(f"  - {test['name']}: {test['errors']}", "ERROR")
        
        # 保存详细报告
        report_path = Path(__file__).parent.parent / "data" / "test_report.json"
        report_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "summary": {
                    "total": total,
                    "success": success,
                    "failed": failed,
                },
                "tests": self.test_results
            }, f, ensure_ascii=False, indent=2)
        
        self.log(f"\n详细报告已保存到: {report_path}", "INFO")
        
        return failed == 0


def main():
    """主测试流程"""
    print("\n" + "="*60)
    print("🚀 Evolution 完整系统测试")
    print("="*60 + "\n")
    
    tester = SystemTester()
    
    # 记忆系统测试
    tester.test_memory_add()
    tester.test_memory_search()
    tester.test_memory_profile()
    
    # 数据库工具测试
    tester.test_schedule_management()
    tester.test_skill_management()
    tester.test_person_management()
    tester.test_training_log()
    tester.test_stats()
    
    # 反思系统测试
    tester.test_daily_reflection()
    
    # 情报系统测试
    tester.test_intelligence_briefing()
    tester.test_intelligence_feeds()
    
    # 通知系统测试
    tester.test_email_notification()
    tester.test_notion_notification()
    
    # 生成报告
    success = tester.generate_report()
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
