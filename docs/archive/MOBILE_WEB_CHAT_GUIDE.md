# 📱 手机 Web Chat 使用指南

## 🎯 方案概述

**无需 Telegram！** 使用轻量级 Web 界面，手机浏览器直接访问。

### ✨ 特点
- ✅ **零依赖** - 不需要任何第三方平台账号
- ✅ **超轻量** - 单文件 Flask 服务器 + 纯 HTML/CSS/JS
- ✅ **移动优化** - 响应式设计，手机体验流畅
- ✅ **工具集成** - 支持记忆、数据库、反思、情报等所有工具
- ✅ **对话历史** - 自动保存，重启不丢失

---

## 🚀 快速开始

### 方案 A：局域网访问（最简单）

**适用场景**：手机和服务器在同一 WiFi

```bash
# 1. 安装依赖
pip install flask flask-cors

# 2. 启动服务器
./scripts/start_web_chat.sh

# 3. 手机浏览器访问
# http://你的服务器IP:5000
```

**如何找到服务器 IP？**
```bash
# Linux/Mac
hostname -I | awk '{print $1}'

# 或者
ip addr show | grep "inet " | grep -v 127.0.0.1
```

---

### 方案 B：公网访问（推荐）

**适用场景**：随时随地访问，不限网络

#### 选项 1：使用 Cloudflare Tunnel（免费，推荐）

```bash
# 1. 安装 cloudflared
# Ubuntu/Debian
wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
sudo dpkg -i cloudflared-linux-amd64.deb

# 2. 启动 Web Chat
./scripts/start_web_chat.sh &

# 3. 创建隧道（首次需要登录 Cloudflare）
cloudflared tunnel --url http://localhost:5000

# 会生成一个公网地址，例如：
# https://random-name.trycloudflare.com
```

**优点**：
- ✅ 完全免费
- ✅ 自动 HTTPS
- ✅ 无需域名
- ✅ 无需配置防火墙

#### 选项 2：使用 Ngrok（免费额度）

```bash
# 1. 注册 Ngrok 账号：https://ngrok.com
# 2. 安装 ngrok
wget https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-linux-amd64.tgz
tar xvzf ngrok-v3-stable-linux-amd64.tgz
sudo mv ngrok /usr/local/bin/

# 3. 配置 token（从 Ngrok 网站获取）
ngrok config add-authtoken YOUR_TOKEN

# 4. 启动 Web Chat
./scripts/start_web_chat.sh &

# 5. 创建隧道
ngrok http 5000

# 会生成一个公网地址，例如：
# https://abc123.ngrok-free.app
```

#### 选项 3：使用 Tailscale（最安全）

```bash
# 1. 安装 Tailscale
curl -fsSL https://tailscale.com/install.sh | sh

# 2. 登录
sudo tailscale up

# 3. 启动 Web Chat
./scripts/start_web_chat.sh

# 4. 手机安装 Tailscale App，登录同一账号
# 5. 访问服务器的 Tailscale IP:5000
```

**优点**：
- ✅ 点对点加密
- ✅ 不经过第三方服务器
- ✅ 最安全的方案

---

## 📱 手机使用

### 1. 添加到主屏幕（类似 App）

**iOS (Safari):**
1. 打开网址
2. 点击底部「分享」按钮
3. 选择「添加到主屏幕」
4. 命名为「Evolution AI」

**Android (Chrome):**
1. 打开网址
2. 点击右上角「⋮」菜单
3. 选择「添加到主屏幕」
4. 命名为「Evolution AI」

### 2. 功能说明

**基础对话：**
```
你好
今天天气怎么样？
帮我总结一下最近的工作
```

**使用工具：**
```
查询我上周的记忆
生成今天的反思
获取最新的情报订阅
查询数据库中的反思记录
```

**工具会自动调用**，无需手动指定格式。

---

## 🔧 高级配置

### 修改端口

编辑 `evolution/chat/web_chat.py`：

```python
if __name__ == "__main__":
    run_server(host="0.0.0.0", port=8080)  # 改为 8080
```

### 添加密码保护

安装依赖：
```bash
pip install flask-httpauth
```

修改 `web_chat.py`：
```python
from flask_httpauth import HTTPBasicAuth

auth = HTTPBasicAuth()

users = {
    "admin": "your_password"  # 修改密码
}

@auth.verify_password
def verify_password(username, password):
    if username in users and users[username] == password:
        return username

@app.route("/")
@auth.login_required
def index():
    return render_template("chat.html", model=LLM_MODEL)
```

### 使用 HTTPS（Nginx 反向代理）

```nginx
server {
    listen 443 ssl;
    server_name your-domain.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    location / {
        proxy_pass http://localhost:5000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
```

---

## 🐛 故障排查

### 问题 1：无法访问

**检查防火墙：**
```bash
# Ubuntu/Debian
sudo ufw allow 5000

# CentOS/RHEL
sudo firewall-cmd --add-port=5000/tcp --permanent
sudo firewall-cmd --reload
```

**检查服务器是否启动：**
```bash
curl http://localhost:5000/health
```

### 问题 2：AI 不回复

**检查 LLM 配置：**
```bash
# 查看 .env 文件
cat .env | grep LLM

# 测试 API
python3 -c "
from evolution.utils.llm import call_claude_api
print(call_claude_api('你好'))
"
```

### 问题 3：工具调用失败

**检查工具初始化：**
```bash
python3 -c "
from evolution.tools.memory_tool import MemoryTool
tool = MemoryTool()
print(tool.search('test'))
"
```

---

## 📊 性能优化

### 使用 Gunicorn（生产环境）

```bash
# 安装
pip install gunicorn

# 启动（4 个 worker）
gunicorn -w 4 -b 0.0.0.0:5000 evolution.chat.web_chat:app
```

### 使用 Redis 存储会话

```bash
# 安装
pip install redis

# 修改 web_chat.py 使用 Redis 存储历史
```

---

## 🔒 安全建议

1. **不要暴露到公网** - 除非添加了认证
2. **使用 HTTPS** - 避免明文传输
3. **定期更新依赖** - `pip install --upgrade flask`
4. **限制访问 IP** - 使用防火墙规则
5. **使用 Tailscale** - 最安全的远程访问方案

---

## 🎨 界面定制

### 修改主题颜色

编辑 `templates/chat.html`，修改 CSS：

```css
/* 渐变色 */
background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);

/* 改为其他颜色，例如绿色 */
background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
```

### 添加头像

在 `message-content` 前添加：
```html
<img src="avatar.png" class="avatar">
```

---

## 📈 监控和日志

### 查看访问日志

```bash
tail -f logs/web_chat.log
```

### 查看对话记录

```bash
cat data/conversation_logs/web_chat_$(date +%Y%m).jsonl | jq
```

---

## 🆚 方案对比

| 方案 | 优点 | 缺点 | 推荐度 |
|------|------|------|--------|
| **局域网访问** | 最简单，零配置 | 仅限同一 WiFi | ⭐⭐⭐ |
| **Cloudflare Tunnel** | 免费，自动 HTTPS | 需要注册账号 | ⭐⭐⭐⭐⭐ |
| **Ngrok** | 简单易用 | 免费版有限制 | ⭐⭐⭐⭐ |
| **Tailscale** | 最安全，点对点 | 需要安装客户端 | ⭐⭐⭐⭐⭐ |

---

## 🎯 推荐配置

**日常使用（家里/办公室）：**
```bash
局域网访问 + 添加到主屏幕
```

**随时随地访问：**
```bash
Cloudflare Tunnel 或 Tailscale
```

**最高安全性：**
```bash
Tailscale + HTTPS + 密码保护
```

---

## 📞 需要帮助？

- 查看日志：`tail -f logs/web_chat.log`
- 健康检查：`curl http://localhost:5000/health`
- 重启服务：`pkill -f web_chat && ./scripts/start_web_chat.sh`
