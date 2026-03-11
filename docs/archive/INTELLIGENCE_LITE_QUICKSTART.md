# Intelligence Tool 模式切换 - 快速测试指南

## ✅ 已完成的工作

### 1. 创建 Lite 模式实现

**文件**: `evolution/tools/intelligence_lite.py`

**功能**:
- ✅ 无需 Docker/RSSHub
- ✅ 直接调用 6 个核心源的官方 API
- ✅ 支持的源：
  - arXiv ML (机器学习论文)
  - arXiv CV (计算机视觉论文)
  - GitHub Trending (Python 热门项目)
  - Hacker News (最佳技术文章)
  - Reddit ML (ML 社区讨论)
  - BBC Tech (BBC 科技新闻)

### 2. 修改主工具支持自动切换

**文件**: `evolution/tools/intelligence_tool.py`

**新增功能**:
- ✅ 自动检测 RSSHub 是否可用
- ✅ RSSHub 不可用时自动降级到 Lite 模式
- ✅ 支持环境变量强制切换模式
- ✅ 两种模式对用户透明，无需手动配置

### 3. 创建完整文档

**文件**: `docs/INTELLIGENCE_MODE_GUIDE.md`

**内容**:
- 两种模式对比
- 自动切换机制
- 使用建议
- 故障排查
- 性能对比

---

## 🚀 快速使用指南

### 当前状态：无 Docker

由于你没有 sudo 权限，系统会**自动使用 Lite 模式**。

### 测试 Lite 模式

```bash
# 方式1：直接测试 Lite 模式
cd /home/yjh/ProjectEvolution
python evolution/tools/intelligence_lite.py

# 方式2：通过主工具测试（会自动使用 Lite 模式）
python -c "
from evolution.tools.intelligence_tool import EvolutionIntelligenceTool
tool = EvolutionIntelligenceTool()
print(f'当前模式: {\"Lite\" if tool.use_lite_mode else \"RSSHub\"}')
result = tool.execute({'action': 'briefing'})
print(result.result)
"
```

### 强制使用 Lite 模式

```bash
# 在 .env 文件中添加
echo "INTELLIGENCE_LITE_MODE=true" >> .env

# 或临时设置
export INTELLIGENCE_LITE_MODE=true
```

---

## 📊 两种模式对比

| 特性 | Lite 模式 | RSSHub 模式 |
|------|----------|------------|
| **需要 Docker** | ❌ 不需要 | ✅ 需要 |
| **需要 sudo** | ❌ 不需要 | ✅ 需要 |
| **信息源数量** | 6 个核心源 | 30+ 个源 |
| **启动时间** | < 1 秒 | ~30 秒 |
| **内存占用** | ~50 MB | ~250 MB |
| **配置复杂度** | 零配置 | 需要配置 Docker |
| **适用场景** | 个人开发、无 sudo | 生产环境、需要丰富源 |

---

## 🎯 你的情况

### 当前状态
- ❌ 无 sudo 权限
- ❌ 无法安装 Docker
- ✅ 可以使用 Lite 模式

### 推荐方案

**使用 Lite 模式**（已自动启用）

**优点**:
- ✅ 无需任何额外配置
- ✅ 6 个核心源已覆盖主要需求
- ✅ 直接调用官方 API，稳定可靠
- ✅ 启动快速，资源占用少

**信息源覆盖**:
- 🎓 学术：arXiv (ML + CV)
- 💻 技术：GitHub Trending + Hacker News
- 🐦 社交：Reddit ML
- 📰 新闻：BBC Tech

---

## 🔄 自动切换逻辑

```
启动 Intelligence Tool
    ↓
检查环境变量 INTELLIGENCE_LITE_MODE
    ↓
是 → 使用 Lite 模式
    ↓
否 → 尝试连接 RSSHub (http://localhost:1200)
    ↓
成功 → 使用 RSSHub 模式
    ↓
失败 → 自动降级到 Lite 模式
```

**你无需手动配置，系统会自动选择最佳模式！**

---

## 📝 使用示例

### 示例1：获取今日情报

```python
from evolution.tools.intelligence_tool import EvolutionIntelligenceTool

# 创建工具（会自动检测模式）
tool = EvolutionIntelligenceTool()

# 获取情报摘要
result = tool.execute({"action": "briefing"})

if result.status == "success":
    print(result.result["briefing_text"])
else:
    print(f"失败: {result.result}")
```

### 示例2：查看当前模式

```python
from evolution.tools.intelligence_tool import EvolutionIntelligenceTool

tool = EvolutionIntelligenceTool()
mode = "Lite 模式（无需 Docker）" if tool.use_lite_mode else "RSSHub 模式"
print(f"当前使用: {mode}")
```

### 示例3：测试 Lite 模式所有源

```python
from evolution.tools.intelligence_lite import IntelligenceSourceLite

source = IntelligenceSourceLite()

# 测试单个源
print("测试 arXiv ML:")
items = source.fetch_arxiv_ml()
for item in items[:3]:
    print(f"  - {item['title']}")

# 测试所有源
print("\n测试所有源:")
all_items = source.fetch_all()
print(f"总计获取 {len(all_items)} 条信息")
```

---

## 🐛 故障排查

### 问题：Lite 模式某些源获取失败

**可能原因**:
- 网络连接问题
- API 限流
- 防火墙阻止

**解决方案**:
```bash
# 1. 测试网络连接
curl http://export.arxiv.org/api/query?search_query=machine+learning
curl https://api.github.com/search/repositories?q=language:python

# 2. 如果需要代理
export HTTP_PROXY=http://your-proxy:port
export HTTPS_PROXY=http://your-proxy:port

# 3. 重新测试
python evolution/tools/intelligence_lite.py
```

### 问题：想要更多信息源

**方案1**: 等待获得 sudo 权限后使用 RSSHub 模式

**方案2**: 在 Lite 模式中添加自定义源

编辑 `evolution/tools/intelligence_lite.py`，参考现有源的实现添加新源。

---

## 📚 相关文件

| 文件 | 说明 |
|------|------|
| `evolution/tools/intelligence_lite.py` | Lite 模式实现（6 个核心源） |
| `evolution/tools/intelligence_tool.py` | 主工具（含自动切换逻辑） |
| `docs/INTELLIGENCE_MODE_GUIDE.md` | 完整的模式切换指南 |
| `docs/RSSHUB_GUIDE.md` | RSSHub 模式指南（需要 Docker） |
| `docs/DOCKER_SETUP.md` | Docker 安装指南 |

---

## 🎉 总结

### 你现在可以做什么

1. ✅ **直接使用情报收集功能**（无需 Docker）
2. ✅ **获取 6 个核心源的最新信息**
3. ✅ **系统会自动使用 Lite 模式**
4. ✅ **未来有 sudo 权限时可无缝切换到 RSSHub 模式**

### 下一步

```bash
# 1. 测试 Lite 模式
python evolution/tools/intelligence_lite.py

# 2. 集成到 Evolution
# 系统会自动使用 Lite 模式，无需额外配置

# 3. 查看每日情报（08:00 自动触发）
# 或手动触发：
python -c "
from evolution.tools.intelligence_tool import EvolutionIntelligenceTool
tool = EvolutionIntelligenceTool()
result = tool.execute({'action': 'briefing'})
print(result.result)
"
```

---

**完成日期**: 2026-03-11  
**状态**: ✅ Lite 模式已实现并自动启用  
**维护者**: Evolution Team
