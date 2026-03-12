"""
自定义Embedding包装器，用于解决aliyun/text-embedding-v4不支持dimensions参数的问题
"""
from mem0.embeddings.base import EmbeddingBase
from openai import OpenAI


class CustomOpenAIEmbedding(EmbeddingBase):
    """自定义OpenAI兼容的Embedding，不传递dimensions参数"""
    
    def __init__(self, config):
        super().__init__(config)
        self.client = OpenAI(
            api_key=config.get("api_key"),
            base_url=config.get("openai_base_url")
        )
        self.model = config.get("model")
    
    def embed(self, text, type="query"):
        """生成embedding，不传递dimensions参数"""
        if isinstance(text, str):
            text = [text]
        
        response = self.client.embeddings.create(
            input=text,
            model=self.model
            # 不传递dimensions参数
        )
        
        embeddings = [item.embedding for item in response.data]
        return embeddings[0] if len(embeddings) == 1 else embeddings
