# Intelligence Tool 模式切换指南

## 📋 概述

Evolution 的情报收集工具支持两种运行模式：

| 模式 | 依赖 | 信息源数量 | 适用场景 |
|------|------|-----------|---------|
| **RSSHub 模式** | Docker + RSSHub | 30+ 个源 | 有 sudo 权限，需要丰富信息源 |
| **Lite 模式** | 无需 Docker | 6 个核心源 | 无 sudo 权限，快速部署 |

---

## 🔄 自动切换机制

Intelligence Tool 会**自动检测**并选择合适的模式：

```python
# 检测逻辑（按优先级）
1. 检查环境变量 INTELLIGENCE_LITE_MODE=true → 强制 Lite 模式
2. 尝试连接 RSSHub (http://localhost:1200) → 成功则使用 RSSHub 模式
3. RSSHub 不可用 → 自动降级到 Lite 模式
```

**你不需要手动配置**，系统会自动选择最佳模式！

---

## 🚀 Lite 模式（推荐：无 sudo 权限）

### 特点

- ✅ **零依赖**：无需 Docker、RSSHub
- ✅ **快速启动**：立即可用
- ✅ **核心覆盖**：6 个最重要的信息源
- ✅ **稳定可靠**：直接调用官方 API

### 支持的信息源

| 源 | API | 说明 |
|----|-----|------|
| arXiv ML | `export.arxiv.org/api` | 机器学习最新论文 |
| arXiv CV | `export.arxiv.org/api` | 计算机视觉论文 |
| GitHub Trending | `api.github.com` | Python 热门项目 |
| Hacker News | `hacker-news.firebaseio.com` | 最佳技术文章 |
| Reddit ML | `reddit.com/r/MachineLearning` | ML 社区讨论 |
| BBC Tech | `feeds.bbci.co.uk` | BBC 科技新闻 |

### 启用方式

**方式1：自动启用（推荐）**

如果 RSSHub 不可用，系统会自动切换到 Lite 模式。

**方式2：强制启用**

```bash
# 在 .env 文件中添加
INTELLIGENCE_LITE_MODE=true
```

### 测试 Lite 模式

```bash
# 测试脚本
python evolution/tools/intelligence_lite.py
```

输出示例：
```
📡 开始拉取信息源...
  🎓 arXiv ML... ✅ 5 条
  🎓 arXiv CV... ✅ 5 条
  💻 GitHub Trending... ✅ 5 条
  💻 Hacker News... ✅ 5 条
  🐦 Reddit ML... ✅ 5 条
  📰 BBC Tech... ✅ 5 条

✅ 总计获取 30 条信息
```

---

## 📡 RSSHub 模式（完整功能）

### 特点

- ✅ **信息源丰富**：30+ 个精选源
- ✅ **统一接口**：所有源都是标准 RSS 格式
- ✅ **反爬虫**：内置处理复杂网站
- ✅ **社区维护**：网站改版时自动更新

### 支持的信息源

详见 `docs/RSSHUB_GUIDE.md`，包括：
- 🎓 学术：arXiv, Nature, Science
- 💻 技术：GitHub, Hacker News, MIT Tech Review, TechCrunch
- 📰 新闻：BBC, Guardian, Reuters, NYT
- 🐦 社交：Twitter, Reddit
- 📝 博客：Google AI, OpenAI, DeepMind

### 启用方式

```bash
# 1. 安装 Docker（需要 sudo）
sudo apt-get install docker.io docker-compose

# 2. 启动 RSSHub
./scripts/start_rsshub.sh

# 3. 验证
curl http://localhost:1200
```

详细步骤见 `docs/DOCKER_SETUP.md`

---

## 🔍 如何查看当前模式

### 方法1：查看日志

```bash
# 启动时会显示当前模式
tail -f logs/evolution.log | grep Intelligence
```

输出示例：
```
[Intelligence] 🔄 使用 Lite 模式（无需 RSSHub/Docker）
# 或
[Intelligence] 📡 使用 RSSHub 模式
```

### 方法2：运行测试

```python
from evolution.tools.intelligence_tool import EvolutionIntelligenceTool

tool = EvolutionIntelligenceTool()
print(f"当前模式: {'Lite' if tool.use_lite_mode else 'RSSHub'}")
```

---

## 🔄 模式对比

| 维度 | Lite 模式 | RSSHub 模式 |
|------|----------|------------|
| **依赖** | 无 | Docker + RSSHub |
| **信息源** | 6 个核心源 | 30+ 个源 |
| **启动时间** | 立即 | ~30 秒 |
| **内存占用** | ~50MB | ~200MB |
| **网络要求** | 直连 API | 需访问 RSSHub |
| **维护成本** | 低 | 中 |
| **扩展性** | 需手动添加 | 支持 1000+ 源 |

---

## 💡 使用建议

### 场景1：个人开发/测试

**推荐**: Lite 模式

```bash
# 在 .env 中设置
INTELLIGENCE_LITE_MODE=true
```

**理由**:
- 快速启动，无需配置 Docker
- 6 个核心源已覆盖主要需求
- 适合快速验证功能

### 场景2：生产环境（有 sudo）

**推荐**: RSSHub 模式

```bash
# 启动 RSSHub
./scripts/start_rsshub.sh
```

**理由**:
- 信息源更丰富（30+ 个）
- 支持社交媒体（Twitter, Reddit）
- 统一接口，易于扩展

### 场景3：无 sudo 权限

**推荐**: Lite 模式（自动启用）

**理由**:
- 无需 Docker，直接运行
- 核心功能完整可用
- 零配置，开箱即用

---

## 🧪 测试两种模式

### 测试 Lite 模式

```bash
# 强制使用 Lite 模式
export INTELLIGENCE_LITE_MODE=true

# 运行测试
python evolution/tools/intelligence_lite.py

# 或在 Python 中
from evolution.tools.intelligence_tool import EvolutionIntelligenceTool
tool = EvolutionIntelligenceTool()
result = tool.execute({"action": "briefing"})
print(result.result)
```

### 测试 RSSHub 模式

```bash
# 确保 RSSHub 运行
docker-compose up -d rsshub

# 取消 Lite 模式强制
unset INTELLIGENCE_LITE_MODE

# 运行测试
from evolution.tools.intelligence_tool import EvolutionIntelligenceTool
tool = EvolutionIntelligenceTool()
result = tool.execute({"action": "briefing"})
print(result.result)
```

---

## 🔧 自定义 Lite 模式

如果你想在 Lite 模式中添加更多源，编辑 `evolution/tools/intelligence_lite.py`：

```python
class IntelligenceSourceLite:
    
    # 添加你的自定义源
    def fetch_your_source(self) -> List[Dict[str, Any]]:
        """你的自定义源"""
        url = "https://your-api-endpoint.com"
        try:
            resp = httpx.get(url, timeout=self.timeout)
            data = resp.json()
            
            items = []
            for item in data["items"]:
                items.append({
                    "title": item["title"],
                    "description": item["description"],
                    "link": item["url"],
                    "source": "Your Source"
                })
            return items
        except Exception as e:
            print(f"❌ Your Source 获取失败: {e}")
            return []
    
    # 在 fetch_all() 中调用
    def fetch_all(self) -> List[Dict[str, Any]]:
        all_items = []
        # ... 现有源 ...
        
        # 添加你的源
        print("  📡 Your Source...", end=" ")
        items = self.fetch_your_source()
        print(f"✅ {len(items)} 条")
        all_items.extend(items)
        
        return all_items
```

---

## 🐛 故障排查

### 问题1: 自动切换到 Lite 模式

**症状**: 日志显示 "使用 Lite 模式"，但你想用 RSSHub

**解决方案**:
```bash
# 1. 检查 RSSHub 是否运行
curl http://localhost:1200

# 2. 如果未运行，启动 RSSHub
./scripts/start_rsshub.sh

# 3. 重启 Evolution
```

### 问题2: Lite 模式某些源失败

**症状**: 某个源显示 "❌ 获取失败"

**原因**: 
- 网络问题
- API 限流
- API 格式变更

**解决方案**:
```bash
# 查看详细错误
python evolution/tools/intelligence_lite.py

# 如果是网络问题，配置代理
export HTTP_PROXY=http://your-proxy:port
export HTTPS_PROXY=http://your-proxy:port
```

### 问题3: 强制使用某个模式

```bash
# 强制 Lite 模式
export INTELLIGENCE_LITE_MODE=true

# 强制 RSSHub 模式（确保 RSSHub 运行）
unset INTELLIGENCE_LITE_MODE
# 或
export INTELLIGENCE_LITE_MODE=false
```

---

## 📊 性能对比

### 启动时间

```
Lite 模式:   < 1 秒
RSSHub 模式: ~30 秒（首次启动 Docker）
```

### 信息获取时间

```
Lite 模式:   5-10 秒（6 个源并发）
RSSHub 模式: 10-20 秒（30 个源并发）
```

### 内存占用

```
Lite 模式:   ~50 MB（仅 Python 进程）
RSSHub 模式: ~250 MB（Python + Docker + RSSHub）
```

---

## 🎯 总结

| 你的情况 | 推荐模式 | 操作 |
|---------|---------|------|
| 无 sudo 权限 | Lite 模式 | 无需操作，自动启用 |
| 有 sudo，快速测试 | Lite 模式 | `export INTELLIGENCE_LITE_MODE=true` |
| 有 sudo，生产环境 | RSSHub 模式 | `./scripts/start_rsshub.sh` |
| 需要社交媒体源 | RSSHub 模式 | 必须使用 RSSHub |
| 只需核心源 | Lite 模式 | 推荐，更轻量 |

**默认行为**: 系统会自动选择最佳模式，你无需手动配置！

---

## 📚 相关文档

- `evolution/tools/intelligence_lite.py` - Lite 模式实现
- `evolution/tools/intelligence_tool.py` - 主工具（含自动切换）
- `docs/RSSHUB_GUIDE.md` - RSSHub 完整指南
- `docs/DOCKER_SETUP.md` - Docker 安装指南

---

**最后更新**: 2026-03-11  
**维护者**: Evolution Team
