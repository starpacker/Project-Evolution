# Evolution AI Agent - 快速启动指南

## 🎯 5分钟快速启动

### 第一步：克隆并进入项目

```bash
cd /home/yjh/ProjectEvolution
```

### 第二步：配置环境变量

```bash
# 复制配置模板
cp .env.example .env

# 编辑配置文件（必填项）
nano .env
```

**必填配置项**：

```bash
# LLM配置（必填）
CLAUDE_API_KEY=sk-ant-your-key-here
OPENAI_API_KEY=sk-your-key-here

# 邮箱配置（推荐）
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_TO=your-personal-email@gmail.com

# 用户标识
EVOLUTION_USER_ID=yjh
```

### 第三步：启动服务

```bash
# 方式1：使用Docker（推荐）
docker-compose up -d

# 方式2：直接运行
python scripts/show_logo.py --startup
```

### 第四步：验证运行

```bash
# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f
```

---

## 📧 邮箱配置详细步骤

### Gmail配置（推荐）

#### 1. 启用两步验证
- 访问：https://myaccount.google.com/security
- 找到"两步验证"并启用

#### 2. 生成应用专用密码
- 访问：https://myaccount.google.com/apppasswords
- 选择"邮件"和"其他（自定义名称）"
- 输入"Evolution AI"
- 复制生成的16位密码（格式：abcd efgh ijkl mnop）

#### 3. 配置.env文件

```bash
SMTP_HOST=smtp.gmail.com
SMTP_PORT=465
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=abcd efgh ijkl mnop  # 刚才复制的密码
SMTP_TO=your-personal-email@gmail.com
```

#### 4. 测试邮件发送

```bash
# 发送测试邮件
python -c "
from evolution.notification.router import NotificationRouter
router = NotificationRouter()
router.send_test_email()
print('测试邮件已发送！')
"
```

### QQ邮箱配置

```bash
# 1. 登录QQ邮箱 -> 设置 -> 账户
# 2. 找到"POP3/IMAP/SMTP/Exchange/CardDAV/CalDAV服务"
# 3. 开启"IMAP/SMTP服务"
# 4. 生成授权码

SMTP_HOST=smtp.qq.com
SMTP_PORT=465
SMTP_USER=3067025832@qq.com
SMTP_PASSWORD=aczrrzllrjqfdegh  # 授权码
SMTP_TO=3067025832@qq.com
```

### 163邮箱配置

```bash
# 1. 登录163邮箱 -> 设置 -> POP3/SMTP/IMAP
# 2. 开启"IMAP/SMTP服务"
# 3. 设置授权密码

SMTP_HOST=smtp.163.com
SMTP_PORT=465
SMTP_USER=your-email@163.com
SMTP_PASSWORD=your-authorization-code
SMTP_TO=your-personal-email@163.com
```

---

## 📡 RSSHub信息源配置

### 已配置的30个信息源

Evolution默认配置了30个精选信息源，涵盖：

- **🎓 学术研究** (5个): arXiv (ML/CV/Inverse Problems), Nature, Science
- **💻 技术开发** (6个): GitHub Trending, Hacker News, MIT Tech Review, TechCrunch
- **📰 新闻资讯** (5个): BBC (Tech/Science), The Guardian, Reuters, NYT
- **🐦 社交媒体** (7个): Twitter (AI研究者/OpenAI/Google AI), Reddit (ML/Python)
- **📝 专业博客** (4个): Google AI Blog, OpenAI Blog, DeepMind, Distill.pub

### 查看完整配置

```bash
# 查看所有配置的源
cat evolution/config/settings.py | grep -A 3 '"name":'

# 查看RSSHub详细文档
cat docs/RSSHUB_GUIDE.md
```

### 测试信息源

```bash
# 测试GitHub Trending
curl http://localhost:1200/github/trending/daily/python

# 测试arXiv
curl http://localhost:1200/arxiv/search_query=machine+learning

# 测试Hacker News
curl http://localhost:1200/hackernews/best
```

---

## 🎨 Logo显示

### 显示方式

```bash
# 完整启动序列（带动画）
python scripts/show_logo.py

# 仅显示静态logo
python scripts/show_logo.py --static

# 仅显示动画
python scripts/show_logo.py --animate

# 完整启动序列
python scripts/show_logo.py --startup
```

### Logo效果预览

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

---

## 🚀 启动方式对比

### 方式1：Docker Compose（推荐）

**优点**：
- 一键启动所有服务
- 环境隔离，不污染系统
- 易于管理和维护

**启动命令**：
```bash
# 启动
docker-compose up -d

# 查看状态
docker-compose ps

# 查看日志
docker-compose logs -f

# 停止
docker-compose down

# 重启
docker-compose restart
```

### 方式2：Python直接运行

**优点**：
- 开发调试方便
- 启动速度快

**启动命令**：
```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate

# 安装依赖
pip install -e .

# 显示logo并启动
python scripts/show_logo.py --startup
python -m evolution.main
```

### 方式3：系统服务（生产环境）

**优点**：
- 开机自启
- 自动重启
- 系统级管理

**配置步骤**：
```bash
# 1. 创建服务文件
sudo nano /etc/systemd/system/evolution.service

# 2. 添加以下内容：
[Unit]
Description=Evolution AI Agent
After=network.target

[Service]
Type=simple
User=yjh
WorkingDirectory=/home/yjh/ProjectEvolution
ExecStartPre=/usr/bin/python3 /home/yjh/ProjectEvolution/scripts/show_logo.py --static
ExecStart=/home/yjh/ProjectEvolution/venv/bin/python -m evolution.main
Restart=always

[Install]
WantedBy=multi-user.target

# 3. 启动服务
sudo systemctl daemon-reload
sudo systemctl start evolution
sudo systemctl enable evolution

# 4. 管理服务
sudo systemctl status evolution
sudo systemctl restart evolution
sudo journalctl -u evolution -f
```

---

## 🔧 常用命令速查

### Docker相关

```bash
# 启动所有服务
docker-compose up -d

# 启动特定服务
docker-compose up -d postgres redis

# 查看运行状态
docker-compose ps

# 查看日志
docker-compose logs -f
docker-compose logs -f evolution  # 特定服务

# 进入容器
docker-compose exec evolution bash

# 重启服务
docker-compose restart

# 停止服务
docker-compose stop

# 停止并删除容器
docker-compose down

# 重新构建
docker-compose build --no-cache
```

### 数据库相关

```bash
# 连接PostgreSQL
docker-compose exec postgres psql -U evolution_user -d evolution_db

# 备份数据库
docker-compose exec postgres pg_dump -U evolution_user evolution_db > backup.sql

# 恢复数据库
docker-compose exec -T postgres psql -U evolution_user evolution_db < backup.sql

# 连接Redis
docker-compose exec redis redis-cli

# 查看Redis数据
docker-compose exec redis redis-cli KEYS "*"
```

### 日志相关

```bash
# 查看所有日志
tail -f logs/*.log

# 查看特定日志
tail -f logs/evolution.log
tail -f logs/notification.log
tail -f logs/error.log

# 查看最近100行
tail -n 100 logs/evolution.log

# 搜索日志
grep "ERROR" logs/evolution.log
grep "email" logs/notification.log
```

### 测试相关

```bash
# 运行所有测试
pytest tests/

# 运行特定测试
pytest tests/test_notification.py

# 显示详细输出
pytest -v tests/

# 显示打印输出
pytest -s tests/

# 测试覆盖率
pytest --cov=evolution tests/
```

---

## 🐛 常见问题排查

### 问题1：邮件发送失败

**症状**：
```
SMTPAuthenticationError: Username and Password not accepted
```

**解决方案**：
1. 确认使用的是应用专用密码，不是账户密码
2. 检查SMTP配置是否正确
3. 确认已启用两步验证（Gmail）
4. 测试SMTP连接：
```bash
python -c "
import smtplib
smtp = smtplib.SMTP('smtp.gmail.com', 587)
smtp.starttls()
smtp.login('your-email@gmail.com', 'your-app-password')
print('连接成功！')
smtp.quit()
"
```

### 问题2：Docker启动失败

**症状**：
```
Error: Port 5432 is already in use
```

**解决方案**：
```bash
# 查找占用端口的进程
sudo lsof -i :5432

# 停止进程
sudo kill -9 <PID>

# 或修改docker-compose.yml中的端口映射
ports:
  - "5433:5432"  # 使用5433端口
```

### 问题3：数据库连接失败

**症状**：
```
could not connect to server: Connection refused
```

**解决方案**：
```bash
# 检查数据库是否运行
docker-compose ps postgres

# 查看数据库日志
docker-compose logs postgres

# 重启数据库
docker-compose restart postgres

# 等待数据库就绪
sleep 10
```

### 问题4：LLM API调用失败

**症状**：
```
OpenAI API error: Invalid API key
```

**解决方案**：
1. 验证API Key格式正确
2. 检查API额度是否充足
3. 测试API连接：
```bash
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"
```

---

## 📊 健康检查

### 系统健康检查脚本

创建 `health_check.sh`：

```bash
#!/bin/bash

echo "🔍 Evolution AI Agent 健康检查"
echo "================================"

# 1. 检查Docker服务
echo -n "Docker服务: "
if docker-compose ps | grep -q "Up"; then
    echo "✅ 运行中"
else
    echo "❌ 未运行"
fi

# 2. 检查数据库
echo -n "PostgreSQL: "
if docker-compose exec -T postgres pg_isready -U evolution_user &>/dev/null; then
    echo "✅ 正常"
else
    echo "❌ 异常"
fi

# 3. 检查Redis
echo -n "Redis: "
if docker-compose exec -T redis redis-cli ping &>/dev/null; then
    echo "✅ 正常"
else
    echo "❌ 异常"
fi

# 4. 检查日志文件
echo -n "日志文件: "
if [ -d "logs" ] && [ "$(ls -A logs)" ]; then
    echo "✅ 存在"
else
    echo "⚠️  不存在"
fi

# 5. 检查配置文件
echo -n "配置文件: "
if [ -f ".env" ]; then
    echo "✅ 存在"
else
    echo "❌ 不存在"
fi

echo "================================"
```

运行健康检查：
```bash
chmod +x health_check.sh
./health_check.sh
```

---

## 🎓 下一步

配置完成后，你可以：

1. **阅读完整文档**：[配置指南](./CONFIGURATION_GUIDE.md)
2. **查看技术报告**：[技术报告](../technical_report_CN.md)
3. **运行测试**：`pytest tests/`
4. **查看API文档**：访问 http://localhost:8000/docs
5. **加入开发**：阅读 [开发指南](./DEVELOPMENT_GUIDE.md)

---

## 📞 获取帮助

- **文档**：查看 `docs/` 目录下的所有文档
- **问题**：提交 GitHub Issue
- **邮件**：your-email@example.com

---

**祝你使用愉快！🎉**
