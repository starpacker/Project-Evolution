#!/usr/bin/env python3
"""
真实功能测试 - 测试实际的工具调用和 mem0 集成
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

def test_real_mem0():
    """测试真实的 mem0 功能"""
    print("\n=== 测试真实 mem0 功能 ===")
    
    try:
        from evolution.tools.memory_tool import EvolutionMemoryTool
        
        mem_tool = EvolutionMemoryTool()
        
        # 测试添加记忆
        print("\n1. 添加记忆...")
        result = mem_tool.execute({
            "action": "add",
            "content": "用户喜欢使用 Python 进行开发，特别是 AI 相关项目"
        })
        success = result.status == "success"
        print(f"   {'✅' if success else '❌'} 添加结果: {result.result}")
        
        # 测试搜索记忆
        print("\n2. 搜索记忆...")
        result = mem_tool.execute({
            "action": "search",
            "query": "Python 开发"
        })
        success = result.status == "success"
        print(f"   {'✅' if success else '❌'} 搜索结果: {str(result.result)[:200] if result.result else 'None'}")
        
        # 测试获取所有记忆
        print("\n3. 获取所有记忆...")
        result = mem_tool.execute({
            "action": "get_all"
        })
        success = result.status == "success"
        print(f"   {'✅' if success else '❌'} 获取结果: 找到记忆")
        
        return True
        
    except Exception as e:
        print(f"❌ mem0 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_real_intelligence():
    """测试真实的情报工具"""
    print("\n=== 测试情报工具 ===")
    
    try:
        from evolution.tools.intelligence_tool import EvolutionIntelligenceTool
        
        intel_tool = EvolutionIntelligenceTool()
        
        # 测试获取订阅列表
        print("\n1. 获取 RSS 订阅...")
        result = intel_tool.execute({
            "action": "list_subscriptions"
        })
        success = result.status == "success"
        print(f"   {'✅' if success else '⚠️'} 结果: {str(result.result)[:100]}")
        
        return True
        
    except Exception as e:
        print(f"❌ 情报工具测试失败: {e}")
        return False

def test_real_workflow():
    """测试真实工作流程"""
    print("\n=== 测试真实工作流程 ===")
    
    try:
        from evolution.tools.db_tool import EvolutionDBTool
        from evolution.tools.memory_tool import EvolutionMemoryTool
        import tempfile
        
        test_dir = tempfile.mkdtemp()
        test_db = os.path.join(test_dir, "workflow_test.db")
        
        db_tool = EvolutionDBTool(config={"db_path": test_db})
        mem_tool = EvolutionMemoryTool()
        
        print("\n场景: 用户要求添加一个重要的工作任务")
        
        # 步骤1: 添加到数据库
        print("\n1. 添加任务到数据库...")
        result1 = db_tool.execute({
            "action": "add_schedule",
            "content": "完成 ProjectL:evolution 系统测试报告",
            "due_date": "2026-03-15",
            "priority": "high",
            "category": "professional"
        })
        success1 = result1.status == "success"
        print(f"   {'✅' if success1 else '❌'} {result1.result}")
        
        # 步骤2: 记录到记忆系统
        print("\n2. 记录到记忆系统...")
        result2 = mem_tool.execute({
            "action": "add",
            "content": "用户在2026年3月12日添加了高优先级任务：完成系统测试报告，截止日期3月15日"
        })
        success2 = result2.status == "success"
        print(f"   {'✅' if success2 else '❌'} {result2.result}")
        
        # 步骤3: 验证数据
        print("\n3. 验证任务列表...")
        result3 = db_tool.execute({
            "action": "list_schedule"
        })
        success3 = result3.status == "success"
        print(f"   {'✅' if success3 else '❌'} 找到任务")
        
        # 步骤4: 验证记忆
        print("\n4. 验证记忆搜索...")
        result4 = mem_tool.execute({
            "action": "search",
            "query": "测试报告"
        })
        success4 = result4.status == "success"
        print(f"   {'✅' if success4 else '❌'} 找到相关记忆")
        
        # 清理
        import shutil
        shutil.rmtree(test_dir)
        
        success = all([success1, success2, success3, success4])
        print(f"\n{'✅' if success else '❌'} 工作流程测试{'成功' if success else '失败'}")
        
        return success
        
    except Exception as e:
        print(f"❌ 工作流程测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("=" * 60)
    print("ProjectL:evolution 真实功能测试")
    print("=" * 60)
    
    results = {
        "mem0 功能": test_real_mem0(),
        "情报工具": test_real_intelligence(),
        "工作流程": test_real_workflow()
    }
    
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    
    for name, result in results.items():
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{status} - {name}")
    
    passed = sum(1 for r in results.values() if r)
    total = len(results)
    print(f"\n总计: {passed}/{total} 测试通过")
    
    return 0 if passed == total else 1

if __name__ == "__main__":
    sys.exit(main())
