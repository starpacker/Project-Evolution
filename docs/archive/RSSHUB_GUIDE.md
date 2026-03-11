# RSSHub 配置与使用指南

## 📋 概述

Evolution 使用 RSSHub 作为统一的信息聚合层，支持 30+ 个精选信息源，涵盖学术、技术、新闻、社交媒体和专业博客。

---

## 🚀 快速启动

### 1. 启动 RSSHub 服务

```bash
# 进入项目目录
cd /home/yjh/ProjectEvolution

# 启动 RSSHub Docker 容器
docker-compose up -d rsshub

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f rsshub
```

### 2. 验证服务运行

```bash
# 测试 RSSHub 是否正常运行
curl http://localhost:1200

# 测试一个具体的源（GitHub Trending）
curl http://localhost:1200/github/trending/daily/python

# 测试 arXiv 源
curl http://localhost:1200/arxiv/search_query=machine+learning
```

### 3. 停止服务

```bash
# 停止 RSSHub
docker-compose stop rsshub

# 停止并删除容器
docker-compose down rsshub
```

---

## 📡 信息源配置

### 当前配置的 30 个信息源

#### 🎓 学术研究 (Academic) - 5个源

| 源名称 | RSSHub路径 | 说明 |
|--------|-----------|------|
| arXiv - Inverse Problems | `/arxiv/search_query=inverse+problem` | 反问题相关论文 |
| arXiv - Machine Learning | `/arxiv/search_query=machine+learning&sortBy=submittedDate` | 机器学习最新论文 |
| arXiv - Computer Vision | `/arxiv/search_query=computer+vision&sortBy=submittedDate` | 计算机视觉论文 |
| Nature - Latest Research | `/nature/research` | Nature 最新研究 |
| Science Magazine | `/sciencemag/current` | Science 最新文章 |

#### 💻 技术开发 (Tech/Dev) - 6个源

| 源名称 | RSSHub路径 | 说明 |
|--------|-----------|------|
| GitHub Trending - Python | `/github/trending/daily/python` | Python 热门项目 |
| GitHub Trending - AI/ML | `/github/trending/daily/jupyter-notebook` | Jupyter Notebook 项目 |
| Hacker News - Best | `/hackernews/best` | HN 最佳文章 |
| Hacker News - Show HN | `/hackernews/show` | Show HN 项目展示 |
| MIT Technology Review | `/technologyreview/latest` | MIT 科技评论 |
| TechCrunch | `/techcrunch` | TechCrunch 科技新闻 |

#### 📰 新闻资讯 (News) - 5个源

| 源名称 | RSSHub路径 | 说明 |
|--------|-----------|------|
| BBC News - Technology | `/bbc/technology` | BBC 科技新闻 |
| BBC News - Science | `/bbc/science_and_environment` | BBC 科学与环境 |
| The Guardian - Technology | `/guardian/technology` | 卫报科技版 |
| Reuters - Technology | `/reuters/technology` | 路透社科技新闻 |
| New York Times - Technology | `/nytimes/technology` | 纽约时报科技版 |

#### 🐦 社交媒体 (Social) - 7个源

| 源名称 | RSSHub路径 | 说明 |
|--------|-----------|------|
| Twitter - Yann LeCun | `/twitter/user/ylecun` | AI 大牛推文 |
| Twitter - OpenAI | `/twitter/user/OpenAI` | OpenAI 官方 |
| Twitter - Google AI | `/twitter/user/GoogleAI` | Google AI 官方 |
| Reddit - r/MachineLearning | `/reddit/subreddit/MachineLearning` | ML 社区讨论 |
| Reddit - r/Python | `/reddit/subreddit/Python` | Python 社区 |

#### 📝 专业博客 (Blogs) - 4个源

| 源名称 | RSSHub路径 | 说明 |
|--------|-----------|------|
| Google AI Blog | `/blogs/googleblog/products/ai` | Google AI 博客 |
| OpenAI Blog | `/openai/blog` | OpenAI 官方博客 |
| DeepMind Blog | `/deepmind/blog` | DeepMind 研究博客 |
| Distill.pub | `/distill` | 可视化研究论文 |

---

## 🔧 自定义配置

### 添加新的信息源

编辑 `evolution/config/settings.py`：

```python
RSS_FEEDS = [
    # ... 现有源 ...
    
    # 添加你的自定义源
    {
        "name": "你的源名称",
        "url": f"{RSSHUB_BASE_URL}/路径",
        "category": "academic|tech|news|social|blog",
    },
]
```

### 常用 RSSHub 路径

```bash
# Twitter 用户
/twitter/user/{username}

# Reddit 子版块
/reddit/subreddit/{subreddit}

# GitHub 用户仓库
/github/repos/{user}

# Medium 用户
/medium/{username}

# YouTube 频道
/youtube/user/{username}

# 知乎用户
/zhihu/people/activities/{id}

# 微博用户
/weibo/user/{uid}

# B站UP主
/bilibili/user/video/{uid}
```

完整路径列表：https://docs.rsshub.app/

---

## 🧪 测试情报收集功能

### 方法1：手动触发

```python
# 在 Python 环境中测试
from evolution.tools.intelligence_tool import EvolutionIntelligenceTool

tool = EvolutionIntelligenceTool()
result = tool.execute({"action": "briefing"})
print(result.result)
```

### 方法2：等待定时任务

Evolution 会在每天早上 08:00 自动运行情报收集任务。

### 方法3：使用测试脚本

```bash
# 创建测试脚本
cat > test_intelligence.py << 'EOF'
from evolution.tools.intelligence_tool import EvolutionIntelligenceTool
from evolution.config.settings import RSS_FEEDS

tool = EvolutionIntelligenceTool()

print(f"📡 配置的信息源数量: {len(RSS_FEEDS)}")
print("\n按类别统计:")
categories = {}
for feed in RSS_FEEDS:
    cat = feed['category']
    categories[cat] = categories.get(cat, 0) + 1

for cat, count in sorted(categories.items()):
    print(f"  {cat}: {count} 个源")

print("\n🔍 开始拉取情报...")
result = tool.execute({"action": "briefing"})

if result.success:
    print("\n✅ 情报收集成功!")
    print(result.result)
else:
    print("\n❌ 情报收集失败:")
    print(result.result)
EOF

# 运行测试
python test_intelligence.py
```

---

## 🐛 故障排查

### 问题1: Docker 未安装

**症状**: `docker-compose: command not found`

**解决方案**:

```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install docker.io docker-compose

# 启动 Docker 服务
sudo systemctl start docker
sudo systemctl enable docker

# 添加当前用户到 docker 组（避免每次 sudo）
sudo usermod -aG docker $USER
# 重新登录使生效
```

### 问题2: 端口 1200 被占用

**症状**: `Error: Port 1200 is already in use`

**解决方案**:

```bash
# 查找占用端口的进程
sudo lsof -i :1200

# 杀死进程
sudo kill -9 <PID>

# 或修改 docker-compose.yml 使用其他端口
ports:
  - "1201:1200"  # 使用 1201 端口

# 同时更新 .env 文件
RSSHUB_URL=http://localhost:1201
```

### 问题3: RSSHub 无法访问某些源

**症状**: 某些源返回 403 或超时

**原因**: 
- 部分网站有反爬虫机制
- 需要代理访问（如 Twitter）
- 源路径已更新

**解决方案**:

```bash
# 1. 配置代理（如果需要）
# 编辑 docker-compose.yml
services:
  rsshub:
    environment:
      - PROXY_URI=http://your-proxy:port

# 2. 查看 RSSHub 日志
docker-compose logs -f rsshub

# 3. 访问 RSSHub 文档确认路径
# https://docs.rsshub.app/
```

### 问题4: 内存不足

**症状**: RSSHub 容器频繁重启

**解决方案**:

```bash
# 限制 RSSHub 内存使用
# 编辑 docker-compose.yml
services:
  rsshub:
    mem_limit: 512m
    memswap_limit: 512m
```

---

## 📊 性能优化

### 1. 启用 Redis 缓存

```yaml
# docker-compose.yml
services:
  rsshub:
    environment:
      - CACHE_TYPE=redis
      - REDIS_URL=redis://redis:6379/
    depends_on:
      - redis
  
  redis:
    image: redis:alpine
    restart: always
```

### 2. 调整缓存时间

```yaml
services:
  rsshub:
    environment:
      - CACHE_EXPIRE=3600  # 缓存1小时
```

### 3. 限制并发请求

在 `intelligence_tool.py` 中已实现并发控制，默认最多同时拉取 10 个源。

---

## 🔐 安全建议

### 1. 不要暴露 RSSHub 到公网

RSSHub 默认监听 `0.0.0.0:1200`，仅在本地使用：

```yaml
services:
  rsshub:
    ports:
      - "127.0.0.1:1200:1200"  # 仅本地访问
```

### 2. 定期更新 RSSHub 镜像

```bash
# 拉取最新镜像
docker-compose pull rsshub

# 重启服务
docker-compose up -d rsshub
```

### 3. 监控资源使用

```bash
# 查看容器资源使用
docker stats rsshub
```

---

## 📈 监控与日志

### 查看实时日志

```bash
# 实时查看 RSSHub 日志
docker-compose logs -f rsshub

# 查看最近 100 行
docker-compose logs --tail=100 rsshub

# 查看错误日志
docker-compose logs rsshub | grep ERROR
```

### 健康检查

```bash
# 添加到 docker-compose.yml
services:
  rsshub:
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:1200"]
      interval: 30s
      timeout: 10s
      retries: 3
```

---

## 🎯 使用建议

### 1. 分阶段启用源

不要一次性启用所有 30 个源，建议：

**第一周**: 启用 5-10 个核心源
```python
# 在 settings.py 中注释掉不需要的源
RSS_FEEDS = [
    # 只保留最重要的源
    {"name": "arXiv - ML", ...},
    {"name": "GitHub Trending", ...},
    {"name": "Hacker News", ...},
    # ... 其他源暂时注释
]
```

**第二周**: 根据反馈逐步添加

### 2. 调整 LLM 筛选策略

在 `evolution/config/prompts.py` 中的 `INTELLIGENCE_FILTER_PROMPT` 可以调整筛选标准：

```python
# 更严格的筛选（只推送1条最相关）
"从以上 {feed_count} 条信息中，筛选出 **1 条** 最值得关注的..."

# 更宽松的筛选（推送3-5条）
"从以上 {feed_count} 条信息中，筛选出 **3-5 条** 值得关注的..."
```

### 3. 按时间段分类推送

可以配置不同时间推送不同类别：

```python
# 早上 08:00 - 学术和技术
# 中午 12:00 - 新闻资讯
# 晚上 20:00 - 社交媒体和博客
```

---

## 📚 相关文档

- [RSSHub 官方文档](https://docs.rsshub.app/)
- [RSSHub GitHub](https://github.com/DIYgod/RSSHub)
- [Evolution 技术报告](./technical_report_CN.md)
- [Evolution 配置指南](./CONFIGURATION_GUIDE.md)

---

## ✅ 检查清单

启动 RSSHub 前的检查：

- [ ] Docker 已安装并运行
- [ ] 端口 1200 未被占用
- [ ] `docker-compose.yml` 配置正确
- [ ] `.env` 中 `RSSHUB_URL=http://localhost:1200`
- [ ] 网络连接正常（部分源需要访问国外网站）

启动后的验证：

- [ ] `docker-compose ps` 显示 rsshub 为 Up 状态
- [ ] `curl http://localhost:1200` 返回 RSSHub 首页
- [ ] 测试至少一个源能正常返回数据
- [ ] Evolution 情报工具能成功拉取信息

---

**最后更新**: 2026-03-11  
**维护者**: Evolution Team
