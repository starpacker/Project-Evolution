"""
Evolution 全局配置
所有路径、API Key、通道配置均在此集中管理。
"""

import os
from pathlib import Path

# ──────────────────────────────────────────────
# 路径配置
# ──────────────────────────────────────────────
PROJECT_ROOT = Path(os.environ.get("EVOLUTION_ROOT", "/data/evolution"))
DATA_DIR = PROJECT_ROOT / "data"
DB_PATH = DATA_DIR / "evolution.db"
CONVERSATION_LOG_DIR = DATA_DIR / "conversation_logs"
REFLECTION_DIR = DATA_DIR / "reflections"
QDRANT_PATH = str(DATA_DIR / "qdrant")
KUZU_DB_PATH = str(DATA_DIR / "kuzu_db")

# 确保关键目录存在
for d in [DATA_DIR, CONVERSATION_LOG_DIR, REFLECTION_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# ──────────────────────────────────────────────
# LLM 配置 (OpenAI-compatible gateway)
# ──────────────────────────────────────────────
LLM_API_KEY = os.environ.get("LLM_API_KEY", "sk-Zj3a7RQDVCXr-Axg-0gtkg")
LLM_BASE_URL = os.environ.get("LLM_BASE_URL", "https://ai-gateway-internal.dp.tech/v1")
LLM_MODEL = os.environ.get("LLM_MODEL", "cds/Claude-4.6-opus")
LLM_MAX_TOKENS = int(os.environ.get("LLM_MAX_TOKENS", "8192"))
LLM_TEMPERATURE = float(os.environ.get("LLM_TEMPERATURE", "0.3"))

# Backward-compat aliases
CLAUDE_API_KEY = LLM_API_KEY
CLAUDE_MODEL = LLM_MODEL
CLAUDE_MAX_TOKENS = LLM_MAX_TOKENS

# ──────────────────────────────────────────────
# Mem0 配置
# ──────────────────────────────────────────────
EMBEDDING_PROVIDER = os.environ.get("EMBEDDING_PROVIDER", "openai")
EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL", "text-embedding-3-small")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")

MEM0_CONFIG = {
    "llm": {
        "provider": "openai",
        "config": {
            "model": LLM_MODEL,
            "temperature": 0.1,
            "max_tokens": 2000,
            "api_key": LLM_API_KEY,
            "openai_base_url": LLM_BASE_URL,
        },
    },
    "embedder": {
        "provider": EMBEDDING_PROVIDER,
        "config": {
            "model": EMBEDDING_MODEL,
            "api_key": OPENAI_API_KEY or LLM_API_KEY,
            "openai_base_url": os.environ.get("EMBEDDING_BASE_URL", LLM_BASE_URL),
        },
    },
    "vector_store": {
        "provider": "qdrant",
        "config": {
            "collection_name": "evolution_memories",
            "path": QDRANT_PATH,
        },
    },
    "graph_store": {
        "provider": "kuzu",
        "config": {
            "db_path": KUZU_DB_PATH,
        },
    },
}

# ──────────────────────────────────────────────
# 用户身份（Mem0 user_id）
# ──────────────────────────────────────────────
USER_ID = os.environ.get("EVOLUTION_USER_ID", "master")

# ──────────────────────────────────────────────
# RSSHub 配置
# ──────────────────────────────────────────────
RSSHUB_BASE_URL = os.environ.get("RSSHUB_URL", "http://localhost:1200")

# ──────────────────────────────────────────────
# 通知通道配置
# ──────────────────────────────────────────────
NOTIFICATION_CONFIG = {
    "email": {
        "enabled": os.environ.get("EMAIL_ENABLED", "false").lower() == "true",
        "smtp_server": os.environ.get("EMAIL_SMTP_SERVER", "smtp.qq.com"),
        "smtp_port": int(os.environ.get("EMAIL_SMTP_PORT", "465")),
        "username": os.environ.get("EMAIL_USERNAME", ""),
        "password": os.environ.get("EMAIL_PASSWORD", ""),
        "to_address": os.environ.get("EMAIL_TO", ""),
        "subject_prefix": os.environ.get("EMAIL_PREFIX", "[Evolution]"),
    },
    "telegram": {
        "enabled": os.environ.get("TG_ENABLED", "false").lower() == "true",
        "bot_token": os.environ.get("TG_BOT_TOKEN", ""),
        "chat_id": os.environ.get("TG_CHAT_ID", ""),
    },
    "notion": {
        "enabled": os.environ.get("NOTION_ENABLED", "false").lower() == "true",
        "token": os.environ.get("NOTION_TOKEN", ""),
        "databases": {
            "schedule": os.environ.get("NOTION_DB_SCHEDULE", ""),
            "reflection": os.environ.get("NOTION_DB_REFLECTION", ""),
            "skills": os.environ.get("NOTION_DB_SKILLS", ""),
            "weekly_report": os.environ.get("NOTION_DB_REPORT", ""),
            "intelligence": os.environ.get("NOTION_DB_INTEL", ""),
        },
    },
}

# ──────────────────────────────────────────────
# RSS 订阅源
# ──────────────────────────────────────────────
RSS_FEEDS = [
    # ========== 学术研究 (Academic) ==========
    {
        "name": "arXiv - Inverse Problems",
        "url": f"{RSSHUB_BASE_URL}/arxiv/search_query=inverse+problem",
        "category": "academic",
    },
    {
        "name": "arXiv - Machine Learning",
        "url": f"{RSSHUB_BASE_URL}/arxiv/search_query=machine+learning&sortBy=submittedDate",
        "category": "academic",
    },
    {
        "name": "arXiv - Computer Vision",
        "url": f"{RSSHUB_BASE_URL}/arxiv/search_query=computer+vision&sortBy=submittedDate",
        "category": "academic",
    },
    {
        "name": "Nature - Latest Research",
        "url": f"{RSSHUB_BASE_URL}/nature/research",
        "category": "academic",
    },
    {
        "name": "Science Magazine - Latest",
        "url": f"{RSSHUB_BASE_URL}/sciencemag/current",
        "category": "academic",
    },
    
    # ========== 技术开发 (Tech/Dev) ==========
    {
        "name": "GitHub Trending - Python",
        "url": f"{RSSHUB_BASE_URL}/github/trending/daily/python",
        "category": "tech",
    },
    {
        "name": "GitHub Trending - AI/ML",
        "url": f"{RSSHUB_BASE_URL}/github/trending/daily/jupyter-notebook",
        "category": "tech",
    },
    {
        "name": "Hacker News - Best",
        "url": f"{RSSHUB_BASE_URL}/hackernews/best",
        "category": "tech",
    },
    {
        "name": "Hacker News - Show HN",
        "url": f"{RSSHUB_BASE_URL}/hackernews/show",
        "category": "tech",
    },
    {
        "name": "MIT Technology Review",
        "url": f"{RSSHUB_BASE_URL}/technologyreview/latest",
        "category": "tech",
    },
    {
        "name": "TechCrunch - Latest",
        "url": f"{RSSHUB_BASE_URL}/techcrunch",
        "category": "tech",
    },
    
    # ========== 新闻资讯 (News) ==========
    {
        "name": "BBC News - Technology",
        "url": f"{RSSHUB_BASE_URL}/bbc/technology",
        "category": "news",
    },
    {
        "name": "BBC News - Science",
        "url": f"{RSSHUB_BASE_URL}/bbc/science_and_environment",
        "category": "news",
    },
    {
        "name": "The Guardian - Technology",
        "url": f"{RSSHUB_BASE_URL}/guardian/technology",
        "category": "news",
    },
    {
        "name": "Reuters - Technology",
        "url": f"{RSSHUB_BASE_URL}/reuters/technology",
        "category": "news",
    },
    {
        "name": "New York Times - Technology",
        "url": f"{RSSHUB_BASE_URL}/nytimes/technology",
        "category": "news",
    },
    
    # ========== 社交媒体 (Social) ==========
    {
        "name": "Twitter - AI Researchers (例: @ylecun)",
        "url": f"{RSSHUB_BASE_URL}/twitter/user/ylecun",
        "category": "social",
    },
    {
        "name": "Twitter - OpenAI",
        "url": f"{RSSHUB_BASE_URL}/twitter/user/OpenAI",
        "category": "social",
    },
    {
        "name": "Twitter - Google AI",
        "url": f"{RSSHUB_BASE_URL}/twitter/user/GoogleAI",
        "category": "social",
    },
    {
        "name": "Reddit - r/MachineLearning",
        "url": f"{RSSHUB_BASE_URL}/reddit/subreddit/MachineLearning",
        "category": "social",
    },
    {
        "name": "Reddit - r/Python",
        "url": f"{RSSHUB_BASE_URL}/reddit/subreddit/Python",
        "category": "social",
    },
    
    # ========== 专业博客 (Blogs) ==========
    {
        "name": "Google AI Blog",
        "url": f"{RSSHUB_BASE_URL}/blogs/googleblog/products/ai",
        "category": "blog",
    },
    {
        "name": "OpenAI Blog",
        "url": f"{RSSHUB_BASE_URL}/openai/blog",
        "category": "blog",
    },
    {
        "name": "DeepMind Blog",
        "url": f"{RSSHUB_BASE_URL}/deepmind/blog",
        "category": "blog",
    },
    {
        "name": "Distill.pub - Research",
        "url": f"{RSSHUB_BASE_URL}/distill",
        "category": "blog",
    },
]

# ──────────────────────────────────────────────
# 定时任务配置
# ──────────────────────────────────────────────
SCHEDULE_CONFIG = {
    "daily_reflection": {
        "name": "daily_reflection",
        "cron": "0 23 * * *",
        "description": "每日23:00反思",
    },
    "morning_briefing": {
        "name": "morning_briefing",
        "cron": "0 8 * * *",
        "description": "每日08:00早间推送",
    },
    "weekly_report": {
        "name": "weekly_report",
        "cron": "0 20 * * 0",
        "description": "每周日20:00周报",
    },
}
