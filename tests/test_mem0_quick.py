#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, '/home/yjh/ProjectEvolution')
os.environ['EMBEDDING_MODEL'] = 'aliyun/text-embedding-v4'

try:
    from evolution.utils.mem0_patch import apply_all_patches
    apply_all_patches()
    
    from mem0 import Memory
    from evolution.config.settings import MEM0_CONFIG
    
    memory = Memory.from_config(MEM0_CONFIG)
    memory.add([{"role": "user", "content": "测试"}], user_id="test")
    results = memory.search("测试", user_id="test")
    
    print("SUCCESS")
    sys.exit(0)
except Exception as e:
    print(f"FAILED: {e}")
    sys.exit(1)
