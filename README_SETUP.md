# Evolution AI Agent - 项目启动与配置完整指南

## 🎨 项目Logo

本项目现在拥有一个精美的ASCII艺术Logo，展示了DNA螺旋和"Evolution"主题！

### Logo展示

```
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║        ●━━●                                            ║
║       ╱    ╲        ███████╗██╗   ██╗ ██████╗        ║
║      ●      ●       ██╔════╝██║   ██║██╔═══██╗       ║
║       ╲    ╱        █████╗  ██║   ██║██║   ██║       ║
║        ●━━●         ██╔══╝  ╚██╗ ██╔╝██║   ██║       ║
║       ╱    ╲        ███████╗ ╚████╔╝ ╚██████╔╝       ║
║      ●      ●       ╚══════╝  ╚═══╝   ╚═════╝        ║
║       ╲    ╱                                           ║
║        ●━━●                                            ║
║                                                           ║
║            🧬 Your 7×24 AI Companion 🧠              ║
║                                                           ║
║  Roles: Secretary │ Mentor │ Trainer │ Emotional │ Intel ║
║  Version: 0.1.0                    Status: ● Ready     ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
```

### 使用Logo

```bash
# 完整启动序列（带动画 + 启动信息）
python scripts/show_logo.py --startup

# 仅显示静态Logo
python scripts/show_logo.py --static

# 仅显示动画
python scripts/show_logo.py --animate

# 默认（完整启动序列）
python scripts/show_logo.py
```

---

## 📚 文档导航

我已经为你创建了完整的配置和启动文档：

### 1. 快速启动指南
📄 **文件**: `docs/QUICK_START.md`

**包含内容**:
- ⚡ 5分钟快速启动
- 📧 邮箱配置详细步骤（Gmail、QQ、163、Outlook）
- 🎨 Logo显示方式
- 🚀 三种启动方式对比
- 🔧 常用命令速查
- 🐛 常见问题排查
- 📊 健康检查脚本

### 2. 完整配置指南
📄 **文件**: `docs/CONFIGURATION_GUIDE.md`

**包含内容**:
- ⚙️ 环境配置详解
- 📧 邮箱通知配置（多种邮箱服务商）
- 🗄️ 数据库配置（PostgreSQL + Redis）
- 🤖 LLM配置（OpenAI、Claude、本地LLM）
- 🎯 启动方式（Docker、Python、Systemd）
- 🔧 高级配置
- 📊 监控和日志
- 🔒 安全建议

### 3. 📱 手机交互指南（新功能！）
📄 **文件**: `docs/MOBILE_QUICKSTART.md` | `docs/MOBILE_WEB_CHAT_GUIDE.md`

**通过 Web 浏览器随时随地与 Evolution 对话**:
- 💬 双向对话：发送消息，即时回复
- 🔍 记忆搜索：「查询我上周的记忆」
- 🤔 生成反思：「生成今天的反思」
- 📡 情报获取：「获取最新情报」
- ✅ 无需 Telegram，完全适合中国用户
- ✅ 极致轻量（730 行代码）
- ✅ 5 分钟配置完成

**快速开始**:
```bash
# 1. 安装依赖
pip install flask flask-cors

# 2. 启动 Web Chat
./scripts/start_web_chat.sh

# 3. 手机浏览器访问
# http://你的服务器IP:5000
```

**公网访问（可选）**:
```bash
# 使用 Cloudflare Tunnel（免费）
cloudflared tunnel --url http://localhost:5000
```

---

## 🚀 快速开始

### 第一步：显示Logo

```bash
cd /home/yjh/ProjectEvolution
python scripts/show_logo.py --startup
```

### 第二步：运行健康检查

```bash
./scripts/health_check.sh
```

这会检查：
- ✅ 配置文件是否存在
- ✅ Docker是否安装
- ✅ 数据库服务状态
- ✅ Python环境
- ✅ API密钥配置
- ✅ 邮箱配置
- ✅ 端口占用情况

### 第三步：配置环境

```bash
# 1. 复制配置模板
cp .env.example .env

# 2. 编辑配置文件
nano .env
```

**必填配置项**：

```bash
# LLM API密钥
CLAUDE_API_KEY=sk-ant-your-key-here
OPENAI_API_KEY=sk-your-key-here

# 邮箱配置（用于通知）
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_TO=your-personal-email@gmail.com

# 用户标识
EVOLUTION_USER_ID=yjh
```

### 第四步：启动服务

```bash
# 使用Docker（推荐）
docker-compose up -d

# 或直接运行
python -m evolution.main
```

---

## 📧 邮箱配置快速指南

### Gmail配置（最常用）

1. **启用两步验证**
   - 访问：https://myaccount.google.com/security
   - 启用"两步验证"

2. **生成应用专用密码**
   - 访问：https://myaccount.google.com/apppasswords
   - 选择"邮件" → "其他（自定义名称）"
   - 输入"Evolution AI"
   - 复制生成的16位密码

3. **配置.env文件**
   ```bash
   SMTP_HOST=smtp.gmail.com
   SMTP_PORT=465
   SMTP_USER=your-email@gmail.com
   SMTP_PASSWORD=abcd efgh ijkl mnop  # 应用专用密码
   SMTP_TO=your-personal-email@gmail.com
   ```

4. **测试邮件**
   ```bash
   python -c "
   from evolution.notification.router import NotificationRouter
   router = NotificationRouter()
   router.send_test_email()
   "
   ```

### 其他邮箱服务商

详见 `docs/QUICK_START.md` 中的邮箱配置章节，包含：
- QQ邮箱
- 163邮箱
- Outlook/Hotmail

---

## 🛠️ 可用脚本

### 1. Logo展示脚本
```bash
# 位置：scripts/show_logo.py
python scripts/show_logo.py --startup   # 完整启动序列
python scripts/show_logo.py --static    # 静态Logo
python scripts/show_logo.py --animate   # 动画效果
```

### 2. 健康检查脚本
```bash
# 位置：scripts/health_check.sh
./scripts/health_check.sh
```

检查项目：
- 配置文件
- Docker环境
- 数据库服务
- Python环境
- API密钥
- 邮箱配置
- 端口状态

### 3. 启动脚本
```bash
# 位置：scripts/setup.sh
./scripts/setup.sh
```

---

## 📊 项目结构

```
ProjectEvolution/
├── scripts/
│   ├── show_logo.py          # Logo展示脚本 ✨ 新增
│   ├── health_check.sh       # 健康检查脚本 ✨ 新增
│   └── setup.sh              # 启动脚本
├── docs/
│   ├── QUICK_START.md        # 快速启动指南 ✨ 新增
│   ├── CONFIGURATION_GUIDE.md # 完整配置指南 ✨ 新增
│   ├── VALIDATION_REPORT.md  # 验证报告
│   └── plan/                 # 计划文档
├── evolution/                # 主代码目录
│   ├── config/              # 配置模块
│   ├── db/                  # 数据库模块
│   ├── notification/        # 通知模块
│   ├── tools/               # 工具模块
│   └── utils/               # 工具函数
├── tests/                   # 测试目录
├── data/                    # 数据目录
├── logs/                    # 日志目录 ✨ 新增
├── .env.example             # 配置模板
├── docker-compose.yml       # Docker配置
├── pyproject.toml          # Python项目配置
└── technical_report_CN.md  # 技术报告
```

---

## 🎯 使用场景

### 场景1：首次启动

```bash
# 1. 显示Logo
python scripts/show_logo.py --startup

# 2. 健康检查
./scripts/health_check.sh

# 3. 配置环境
cp .env.example .env
nano .env

# 4. 启动服务
docker-compose up -d
```

### 场景2：日常启动

```bash
# 显示Logo并启动
python scripts/show_logo.py --startup
docker-compose up -d
```

### 场景3：调试模式

```bash
# 1. 健康检查
./scripts/health_check.sh

# 2. 查看日志
docker-compose logs -f

# 3. 测试邮件
python -m evolution.notification.router --test
```

---

## 🔧 常用命令

### Docker管理
```bash
docker-compose up -d        # 启动服务
docker-compose ps           # 查看状态
docker-compose logs -f      # 查看日志
docker-compose restart      # 重启服务
docker-compose down         # 停止服务
```

### 日志查看
```bash
tail -f logs/evolution.log      # 主日志
tail -f logs/notification.log   # 通知日志
tail -f logs/error.log          # 错误日志
```

### 测试
```bash
pytest tests/                   # 运行所有测试
pytest tests/test_notification.py  # 测试通知功能
pytest -v tests/                # 详细输出
```

---

## 🐛 故障排查

### 问题：邮件发送失败
```bash
# 检查SMTP配置
grep SMTP .env

# 测试SMTP连接
python -c "
import smtplib
smtp = smtplib.SMTP('smtp.gmail.com', 587)
smtp.starttls()
smtp.login('your-email', 'your-password')
print('连接成功！')
"
```

### 问题：数据库连接失败
```bash
# 检查数据库状态
docker-compose ps postgres

# 查看数据库日志
docker-compose logs postgres

# 重启数据库
docker-compose restart postgres
```

### 问题：端口被占用
```bash
# 查找占用进程
lsof -i :8000

# 杀死进程
kill -9 <PID>
```

---

## 📖 详细文档

- 📘 [快速启动指南](docs/QUICK_START.md) - 5分钟快速上手
- 📗 [完整配置指南](docs/CONFIGURATION_GUIDE.md) - 详细配置说明
- 📕 [技术报告](technical_report_CN.md) - 技术架构文档
- 📙 [验证报告](docs/VALIDATION_REPORT.md) - 功能验证报告

---

## 🎉 特性亮点

✨ **新增功能**：
- 🎨 精美的ASCII艺术Logo（带动画效果）
- 📊 完整的健康检查脚本
- 📚 详细的配置和启动文档
- 📧 多种邮箱服务商配置指南
- 🔧 三种启动方式（Docker、Python、Systemd）
- 🐛 常见问题排查指南

---

## 💡 下一步

1. ✅ 运行健康检查：`./scripts/health_check.sh`
2. ✅ 配置环境变量：编辑 `.env` 文件
3. ✅ 配置邮箱通知：参考 `docs/QUICK_START.md`
4. ✅ 启动服务：`docker-compose up -d`
5. ✅ 查看文档：阅读 `docs/` 目录下的所有文档

---

## 📞 获取帮助

- 📚 **文档**：查看 `docs/` 目录
- 🐛 **问题**：提交 GitHub Issue
- 📧 **邮件**：your-email@example.com

---

**祝你使用愉快！🎊**

*Evolution AI Agent - Your 7×24 AI Companion* 🧬🧠
