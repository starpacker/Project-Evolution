#!/usr/bin/env python3
"""简单测试Mem0补丁"""
import sys
import os
sys.path.insert(0, '/home/yjh/ProjectEvolution')

# 设置环境变量
os.environ['EMBEDDING_MODEL'] = 'aliyun/text-embedding-v4'

print("=" * 60)
print("测试 Mem0 Embedding 补丁")
print("=" * 60)

# 1. 应用补丁
print("\n1️⃣ 应用补丁...")
from evolution.utils.mem0_patch import apply_all_patches
apply_all_patches()

# 2. 初始化
print("\n2️⃣ 初始化Mem0...")
from mem0 import Memory
from evolution.config.settings import MEM0_CONFIG

print(f"   Model: {MEM0_CONFIG['embedder']['config']['model']}")
print(f"   Dims: {MEM0_CONFIG['embedder']['config']['embedding_dims']}")

memory = Memory.from_config(MEM0_CONFIG)
print("   ✅ 初始化成功")

# 3. 测试添加
print("\n3️⃣ 测试添加...")
result = memory.add(
    [{"role": "user", "content": "我喜欢Python编程"}],
    user_id="test"
)
print(f"   ✅ 添加成功")

# 4. 测试搜索
print("\n4️⃣ 测试搜索...")
results = memory.search("Python", user_id="test", limit=3)
print(f"   ✅ 搜索成功，找到 {len(results.get('results', []))} 条")

print("\n" + "=" * 60)
print("🎉 所有测试通过！")
print("=" * 60)
