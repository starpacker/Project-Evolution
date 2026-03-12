#!/usr/bin/env python3
"""测试embedding是否工作"""
import sys
import os
sys.path.insert(0, '/home/yjh/ProjectEvolution')
os.environ['EMBEDDING_MODEL'] = 'aliyun/text-embedding-v4'

print("1. 应用补丁...")
from evolution.utils.mem0_patch import apply_all_patches
apply_all_patches()

print("2. 测试embedding...")
from mem0.embeddings.openai import OpenAIEmbedding
from mem0.configs.embeddings.base import BaseEmbedderConfig

config = BaseEmbedderConfig(
    model='aliyun/text-embedding-v4',
    api_key='sk-Zj3a7RQDVCXr-Axg-0gtkg',
    openai_base_url='https://ai-gateway-internal.dp.tech/v1',
    embedding_dims=1024
)

embedder = OpenAIEmbedding(config)
result = embedder.embed("测试文本")

print(f"✅ Embedding成功！维度: {len(result)}")
print("SUCCESS")
