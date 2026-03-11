# Evolution AI Agent - 配置指南

## 📋 目录

- [快速启动](#快速启动)
- [环境配置](#环境配置)
- [邮箱通知配置](#邮箱通知配置)
- [数据库配置](#数据库配置)
- [LLM配置](#llm配置)
- [启动方式](#启动方式)
- [常见问题](#常见问题)

---

## 🚀 快速启动

### 一键启动脚本

```bash
# 1. 进入项目目录
cd /home/yjh/ProjectEvolution

# 2. 运行启动脚本（自动显示Logo并启动服务）
./scripts/setup.sh

# 或者手动启动
python scripts/show_logo.py --startup
docker-compose up -d
```

### 显示Logo的不同方式

```bash
# 完整启动序列（默认）
python scripts/show_logo.py

# 仅显示静态Logo
python scripts/show_logo.py --static

# 仅显示动画
python scripts/show_logo.py --animate

# 完整启动序列
python scripts/show_logo.py --startup
```

---

## ⚙️ 环境配置

### 1. 创建环境配置文件

在项目根目录创建 `.env` 文件：

```bash
# 复制示例配置文件
cp .env.example .env

# 编辑配置文件
nano .env
```

### 2. 基础环境变量

```bash
# ==================== 基础配置 ====================
PROJECT_NAME=Evolution
ENVIRONMENT=production  # development, staging, production
DEBUG=false
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR, CRITICAL

# ==================== 服务端口 ====================
API_PORT=8000
REDIS_PORT=6379
POSTGRES_PORT=5432

# ==================== 数据库配置 ====================
# PostgreSQL
POSTGRES_USER=evolution_user
POSTGRES_PASSWORD=your_secure_password_here
POSTGRES_DB=evolution_db
POSTGRES_HOST=localhost

# Redis
REDIS_HOST=localhost
REDIS_PASSWORD=your_redis_password_here

# ==================== LLM配置 ====================
# OpenAI
OPENAI_API_KEY=sk-your-openai-api-key-here
OPENAI_MODEL=gpt-4-turbo-preview
OPENAI_BASE_URL=https://api.openai.com/v1

# Anthropic Claude (可选)
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key-here
ANTHROPIC_MODEL=claude-3-opus-20240229

# 本地LLM (可选)
LOCAL_LLM_URL=http://localhost:11434
LOCAL_LLM_MODEL=llama2

# ==================== 邮箱通知配置 ====================
# SMTP服务器配置
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USE_TLS=true
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-specific-password

# 发件人信息
EMAIL_FROM=your-email@gmail.com
EMAIL_FROM_NAME=Evolution AI Agent

# 收件人信息（多个邮箱用逗号分隔）
EMAIL_TO=your-personal-email@gmail.com,backup-email@example.com

# 通知设置
EMAIL_NOTIFICATIONS_ENABLED=true
EMAIL_DAILY_SUMMARY=true
EMAIL_DAILY_SUMMARY_TIME=09:00  # 每天9点发送日报
EMAIL_URGENT_ALERTS=true

# ==================== 安全配置 ====================
SECRET_KEY=your-secret-key-generate-with-openssl-rand-hex-32
JWT_SECRET=your-jwt-secret-key-here
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# ==================== 存储配置 ====================
DATA_DIR=/home/yjh/ProjectEvolution/data
LOGS_DIR=/home/yjh/ProjectEvolution/logs
BACKUP_DIR=/home/yjh/ProjectEvolution/backups

# ==================== 功能开关 ====================
ENABLE_MEMORY=true
ENABLE_REFLECTION=true
ENABLE_INTELLIGENCE=true
ENABLE_NOTIFICATIONS=true
ENABLE_AUTO_BACKUP=true

# ==================== 性能配置 ====================
MAX_WORKERS=4
REQUEST_TIMEOUT=300
MAX_RETRIES=3
CACHE_TTL=3600
```

---

## 📧 邮箱通知配置

### Gmail配置示例

#### 1. 启用两步验证

1. 访问 [Google账户安全设置](https://myaccount.google.com/security)
2. 启用"两步验证"

#### 2. 生成应用专用密码

1. 访问 [应用专用密码](https://myaccount.google.com/apppasswords)
2. 选择"邮件"和"其他（自定义名称）"
3. 输入"Evolution AI"
4. 复制生成的16位密码

#### 3. 配置.env文件

```bash
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USE_TLS=true
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=abcd efgh ijkl mnop  # 应用专用密码

EMAIL_FROM=your-email@gmail.com
EMAIL_FROM_NAME=Evolution AI Agent
EMAIL_TO=your-personal-email@gmail.com
```

### 其他邮箱服务商配置

#### QQ邮箱

```bash
SMTP_HOST=smtp.qq.com
SMTP_PORT=587
SMTP_USE_TLS=true
SMTP_USERNAME=your-qq-number@qq.com
SMTP_PASSWORD=your-authorization-code  # 授权码，非QQ密码
```

#### 163邮箱

```bash
SMTP_HOST=smtp.163.com
SMTP_PORT=465
SMTP_USE_TLS=true
SMTP_USERNAME=your-email@163.com
SMTP_PASSWORD=your-authorization-code
```

#### Outlook/Hotmail

```bash
SMTP_HOST=smtp-mail.outlook.com
SMTP_PORT=587
SMTP_USE_TLS=true
SMTP_USERNAME=your-email@outlook.com
SMTP_PASSWORD=your-password
```

### 测试邮箱配置

```bash
# 运行邮箱测试脚本
python -m evolution.notification.router --test

# 或者使用Python交互式测试
python << EOF
from evolution.notification.router import NotificationRouter
router = NotificationRouter()
router.send_test_email()
EOF
```

---

## 🗄️ 数据库配置

### PostgreSQL配置

#### 使用Docker（推荐）

```bash
# docker-compose.yml 已包含PostgreSQL配置
docker-compose up -d postgres

# 查看数据库日志
docker-compose logs -f postgres
```

#### 本地安装

```bash
# Ubuntu/Debian
sudo apt-get install postgresql postgresql-contrib

# macOS
brew install postgresql

# 创建数据库和用户
sudo -u postgres psql
CREATE DATABASE evolution_db;
CREATE USER evolution_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE evolution_db TO evolution_user;
\q
```

### Redis配置

```bash
# 使用Docker
docker-compose up -d redis

# 本地安装
# Ubuntu/Debian
sudo apt-get install redis-server

# macOS
brew install redis

# 启动Redis
redis-server
```

---

## 🤖 LLM配置

### OpenAI配置

```bash
# 获取API Key: https://platform.openai.com/api-keys
OPENAI_API_KEY=sk-proj-...
OPENAI_MODEL=gpt-4-turbo-preview  # 或 gpt-3.5-turbo

# 可选：使用代理
OPENAI_BASE_URL=https://your-proxy.com/v1
```

### Anthropic Claude配置

```bash
# 获取API Key: https://console.anthropic.com/
ANTHROPIC_API_KEY=sk-ant-...
ANTHROPIC_MODEL=claude-3-opus-20240229
```

### 本地LLM配置（Ollama）

```bash
# 安装Ollama
curl -fsSL https://ollama.com/install.sh | sh

# 下载模型
ollama pull llama2
ollama pull mistral

# 配置
LOCAL_LLM_URL=http://localhost:11434
LOCAL_LLM_MODEL=llama2
```

---

## 🎯 启动方式

### 方式1：Docker Compose（推荐）

```bash
# 启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down

# 重启服务
docker-compose restart
```

### 方式2：Python虚拟环境

```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
source venv/bin/activate  # Linux/macOS
# 或
.\venv\Scripts\activate  # Windows

# 安装依赖
pip install -e .

# 启动服务
python -m evolution.main
```

### 方式3：系统服务（Systemd）

创建服务文件 `/etc/systemd/system/evolution.service`：

```ini
[Unit]
Description=Evolution AI Agent
After=network.target postgresql.service redis.service

[Service]
Type=simple
User=yjh
WorkingDirectory=/home/yjh/ProjectEvolution
Environment="PATH=/home/yjh/ProjectEvolution/venv/bin"
ExecStartPre=/home/yjh/ProjectEvolution/scripts/show_logo.py --static
ExecStart=/home/yjh/ProjectEvolution/venv/bin/python -m evolution.main
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

启动服务：

```bash
# 重载systemd配置
sudo systemctl daemon-reload

# 启动服务
sudo systemctl start evolution

# 开机自启
sudo systemctl enable evolution

# 查看状态
sudo systemctl status evolution

# 查看日志
sudo journalctl -u evolution -f
```

---

## 🔧 高级配置

### 自定义启动脚本

创建 `start.sh`：

```bash
#!/bin/bash

# Evolution AI Agent 启动脚本

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting Evolution AI Agent...${NC}"

# 1. 显示Logo
python scripts/show_logo.py --startup

# 2. 检查环境变量
if [ ! -f .env ]; then
    echo -e "${RED}Error: .env file not found!${NC}"
    echo -e "${YELLOW}Please create .env file from .env.example${NC}"
    exit 1
fi

# 3. 检查依赖
echo -e "${YELLOW}Checking dependencies...${NC}"
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}docker-compose not found!${NC}"
    exit 1
fi

# 4. 启动数据库服务
echo -e "${YELLOW}Starting database services...${NC}"
docker-compose up -d postgres redis

# 5. 等待数据库就绪
echo -e "${YELLOW}Waiting for database...${NC}"
sleep 5

# 6. 运行数据库迁移
echo -e "${YELLOW}Running database migrations...${NC}"
python -m evolution.db.migrate

# 7. 启动主服务
echo -e "${YELLOW}Starting main service...${NC}"
python -m evolution.main

echo -e "${GREEN}Evolution AI Agent started successfully!${NC}"
```

赋予执行权限：

```bash
chmod +x start.sh
./start.sh
```

### 环境变量优先级

1. 命令行参数（最高优先级）
2. `.env` 文件
3. 系统环境变量
4. 默认配置（最低优先级）

### 配置文件位置

```
ProjectEvolution/
├── .env                          # 主配置文件（不提交到Git）
├── .env.example                  # 配置模板
├── evolution/config/
│   ├── settings.py              # 配置加载逻辑
│   └── prompts.py               # Prompt配置
└── docker-compose.yml           # Docker配置
```

---

## 📊 监控和日志

### 日志配置

```bash
# 日志级别
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR, CRITICAL

# 日志文件
LOGS_DIR=/home/yjh/ProjectEvolution/logs

# 日志轮转
LOG_MAX_SIZE=100MB
LOG_BACKUP_COUNT=10
```

### 查看日志

```bash
# 实时查看所有日志
tail -f logs/*.log

# 查看特定服务日志
tail -f logs/evolution.log
tail -f logs/notification.log
tail -f logs/error.log

# 使用Docker查看
docker-compose logs -f evolution
```

### 健康检查

```bash
# HTTP健康检查端点
curl http://localhost:8000/health

# 数据库连接检查
python -m evolution.db.manager --check

# Redis连接检查
redis-cli ping
```

---

## 🔒 安全建议

### 1. 保护敏感信息

```bash
# 确保.env文件不被提交
echo ".env" >> .gitignore

# 设置文件权限
chmod 600 .env

# 使用环境变量管理工具
# 推荐：direnv, dotenv, vault
```

### 2. 定期更新密钥

```bash
# 生成新的SECRET_KEY
openssl rand -hex 32

# 生成新的JWT_SECRET
openssl rand -base64 32
```

### 3. 使用HTTPS

```bash
# 在生产环境使用反向代理（Nginx/Caddy）
# 配置SSL证书（Let's Encrypt）
```

---

## 🐛 常见问题

### Q1: 邮件发送失败

**问题**: `SMTPAuthenticationError: Username and Password not accepted`

**解决方案**:
- 检查是否使用了应用专用密码（而非账户密码）
- 确认SMTP服务器地址和端口正确
- 检查是否启用了两步验证

### Q2: 数据库连接失败

**问题**: `could not connect to server: Connection refused`

**解决方案**:
```bash
# 检查PostgreSQL是否运行
docker-compose ps postgres

# 查看数据库日志
docker-compose logs postgres

# 重启数据库
docker-compose restart postgres
```

### Q3: LLM API调用失败

**问题**: `OpenAI API error: Invalid API key`

**解决方案**:
- 验证API Key是否正确
- 检查API额度是否用完
- 确认网络连接正常
- 尝试使用代理

### Q4: 端口被占用

**问题**: `Error: Port 8000 is already in use`

**解决方案**:
```bash
# 查找占用端口的进程
lsof -i :8000

# 杀死进程
kill -9 <PID>

# 或修改配置使用其他端口
API_PORT=8001
```

---

## 📚 相关文档

- [技术报告](../technical_report_CN.md)
- [验证报告](./VALIDATION_REPORT.md)
- [API文档](./API_DOCUMENTATION.md)
- [开发指南](./DEVELOPMENT_GUIDE.md)

---

## 💡 快速参考

### 常用命令

```bash
# 启动服务
docker-compose up -d

# 停止服务
docker-compose down

# 查看日志
docker-compose logs -f

# 重启服务
docker-compose restart

# 显示Logo
python scripts/show_logo.py

# 运行测试
pytest tests/

# 数据库备份
pg_dump evolution_db > backup.sql

# 数据库恢复
psql evolution_db < backup.sql
```

### 环境变量快速设置

```bash
# 一键设置基础环境变量
export OPENAI_API_KEY="your-key"
export SMTP_USERNAME="your-email@gmail.com"
export SMTP_PASSWORD="your-app-password"
export EMAIL_TO="your-personal-email@gmail.com"
```

---

## 🎉 完成配置后

配置完成后，运行以下命令验证：

```bash
# 1. 显示启动Logo
python scripts/show_logo.py --startup

# 2. 启动所有服务
docker-compose up -d

# 3. 运行健康检查
curl http://localhost:8000/health

# 4. 发送测试邮件
python -m evolution.notification.router --test

# 5. 查看服务状态
docker-compose ps
```

如果所有检查都通过，恭喜你！Evolution AI Agent已经成功配置并运行！🎊

---

**最后更新**: 2026-03-11  
**维护者**: Evolution Team  
**联系方式**: your-email@example.com
