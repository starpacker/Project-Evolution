# Evolution v0.1.0

> 7×24 运行的私人 AI Agent — 秘书、导师、训练师、情感助手、情报收集者

## 🚀 快速开始

### 访问 Web Chat

**当前已部署运行**:
- **本地访问**: http://localhost:5000
- **局域网访问**: http://10.128.250.187:5000
- **健康检查**: `curl http://localhost:5000/health`

### 本地安装

```bash
# 1. 安装依赖
pip install flask flask-cors openai defusedxml httpx apscheduler markdown

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env 文件，设置 API 密钥

# 3. 启动 Web Chat
python3 -m evolution.chat.web_chat

# 4. 访问浏览器
# 打开 http://localhost:5000
```

## 📚 文档

- **完整技术报告**: [technical_report_CN.md](technical_report_CN.md)
- **快速开始指南**: [docs/QUICK_START.md](docs/QUICK_START.md)
- **验证报告**: [docs/VALIDATION_REPORT.md](docs/VALIDATION_REPORT.md)

## ✅ 已验证功能

| 功能 | 状态 | 说明 |
|------|------|------|
| SMTP 邮件 | ✅ | smtp.qq.com:465 |
| Notion API | ✅ | 数据库: Docs |
| LLM API | ✅ | cds/Claude-4.6-opus |
| Web Chat | ✅ | Flask 服务器运行中 |

## 🛠️ 核心功能

### 五大角色

1. **🗓️ 秘书** - 日程管理、提醒
2. **🧠 导师** - 每日反思、苏格拉底式提问
3. **🏋️ 训练师** - 7 种训练模态
4. **💑 情感助手** - 人物档案、关系监控
5. **📡 情报收集者** - RSS 订阅、智能筛选

### 四大工具

- **Memory Tool** - Mem0 记忆系统 (向量 + 图谱)
- **DB Tool** - SQLite 数据库 (7 张表)
- **Reflection Tool** - 每日/周度反思
- **Intelligence Tool** - RSS 情报收集

## 📊 项目统计

- **源码**: 2,872 行 (14 个文件)
- **测试**: 2,429 行 (264 个测试用例)
- **测试通过率**: 100%
- **核心依赖**: 7 个包

## 🔧 管理命令

```bash
# 查看运行状态
ps aux | grep web_chat

# 停止服务器
kill <PID>

# 查看对话日志
tail -f data/conversation_logs/web_chat_*.jsonl

# 运行测试
pytest
```

## 📝 许可

内部使用

---

**最后更新**: 2026-03-11  
**部署状态**: ✅ 运行中  
**服务器**: server3090 (10.128.250.187)
