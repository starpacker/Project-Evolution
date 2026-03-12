#!/usr/bin/env python3
"""
测试Mem0补丁是否成功修复embedding问题
"""

import sys
import os

# 添加项目路径
sys.path.insert(0, '/home/yjh/ProjectEvolution')

def test_mem0_patch():
    """测试Mem0补丁"""
    print("=" * 60)
    print("测试 Mem0 Embedding 补丁")
    print("=" * 60)
    
    # 1. 应用补丁
    print("\n1️⃣ 应用Mem0补丁...")
    try:
        from evolution.utils.mem0_patch import apply_all_patches
        success = apply_all_patches()
        if success:
            print("✅ 补丁应用成功")
        else:
            print("⚠️ 补丁应用失败")
            return False
    except Exception as e:
        print(f"❌ 补丁应用异常: {e}")
        return False
    
    # 2. 初始化Mem0
    print("\n2️⃣ 初始化Mem0...")
    try:
        from mem0 import Memory
        from evolution.config.settings import MEM0_CONFIG
        
        print(f"   配置: {MEM0_CONFIG['embedder']}")
        memory = Memory.from_config(MEM0_CONFIG)
        print("✅ Mem0初始化成功")
    except Exception as e:
        print(f"❌ Mem0初始化失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 3. 测试添加记忆
    print("\n3️⃣ 测试添加记忆...")
    try:
        test_content = "我最喜欢的编程语言是Python，因为它简洁优雅。"
        messages = [{"role": "user", "content": test_content}]
        result = memory.add(messages, user_id="test_user")
        print(f"✅ 添加成功: {result}")
    except Exception as e:
        print(f"❌ 添加失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 4. 测试搜索记忆
    print("\n4️⃣ 测试搜索记忆...")
    try:
        results = memory.search("Python", user_id="test_user", limit=5)
        print(f"✅ 搜索成功，找到 {len(results.get('results', []))} 条记忆")
        for i, mem in enumerate(results.get('results', [])[:3], 1):
            print(f"   {i}. {mem.get('memory', '')[:60]}...")
    except Exception as e:
        print(f"❌ 搜索失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 5. 测试获取所有记忆
    print("\n5️⃣ 测试获取所有记忆...")
    try:
        all_memories = memory.get_all(user_id="test_user")
        count = len(all_memories.get('results', []))
        print(f"✅ 获取成功，共 {count} 条记忆")
    except Exception as e:
        print(f"❌ 获取失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n" + "=" * 60)
    print("🎉 所有测试通过！Mem0补丁工作正常！")
    print("=" * 60)
    return True


if __name__ == "__main__":
    success = test_mem0_patch()
    sys.exit(0 if success else 1)
