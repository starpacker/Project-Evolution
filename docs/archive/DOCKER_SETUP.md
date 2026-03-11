# Docker 安装指南

## 📋 概述

Evolution 的情报收集功能依赖 RSSHub，而 RSSHub 需要通过 Docker 运行。本指南将帮助你在不同操作系统上安装 Docker。

---

## 🐧 Ubuntu/Debian 安装

### 方法1：使用官方脚本（推荐）

```bash
# 1. 更新包索引
sudo apt-get update

# 2. 安装依赖
sudo apt-get install -y \
    apt-transport-https \
    ca-certificates \
    curl \
    gnupg \
    lsb-release

# 3. 添加 Docker 官方 GPG 密钥
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# 4. 设置稳定版仓库
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# 5. 安装 Docker Engine
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# 6. 验证安装
sudo docker run hello-world
```

### 方法2：使用包管理器（快速但版本可能较旧）

```bash
# 安装 Docker 和 Docker Compose
sudo apt-get update
sudo apt-get install -y docker.io docker-compose

# 启动 Docker 服务
sudo systemctl start docker
sudo systemctl enable docker

# 验证安装
sudo docker --version
sudo docker-compose --version
```

### 配置用户权限（重要）

```bash
# 将当前用户添加到 docker 组（避免每次使用 sudo）
sudo usermod -aG docker $USER

# 重新登录使权限生效
# 或者运行：
newgrp docker

# 验证（不需要 sudo）
docker ps
```

---

## 🍎 macOS 安装

### 方法1：使用 Docker Desktop（推荐）

1. 访问 [Docker Desktop for Mac](https://www.docker.com/products/docker-desktop)
2. 下载并安装 Docker Desktop
3. 启动 Docker Desktop 应用
4. 等待 Docker 图标显示为绿色（运行中）

### 方法2：使用 Homebrew

```bash
# 安装 Docker
brew install --cask docker

# 或者安装命令行工具
brew install docker docker-compose

# 启动 Docker Desktop
open /Applications/Docker.app

# 验证安装
docker --version
docker-compose --version
```

---

## 🪟 Windows 安装

### 使用 Docker Desktop

1. 访问 [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop)
2. 下载并安装 Docker Desktop
3. 启动 Docker Desktop
4. 确保启用 WSL 2 后端（推荐）

### WSL 2 配置（推荐）

```powershell
# 在 PowerShell（管理员）中运行
wsl --install

# 重启计算机后，在 WSL 2 中安装 Docker
# 参考 Ubuntu 安装步骤
```

---

## ✅ 验证安装

运行以下命令验证 Docker 安装成功：

```bash
# 检查 Docker 版本
docker --version
# 输出示例: Docker version 24.0.0, build 1234567

# 检查 Docker Compose 版本
docker-compose --version
# 输出示例: Docker Compose version v2.20.0

# 检查 Docker 服务状态
docker info

# 运行测试容器
docker run hello-world
```

---

## 🚀 启动 RSSHub

安装完 Docker 后，返回项目目录启动 RSSHub：

```bash
cd /home/yjh/ProjectEvolution

# 使用启动脚本（推荐）
./scripts/start_rsshub.sh

# 或手动启动
docker-compose up -d rsshub

# 验证 RSSHub 运行
curl http://localhost:1200
```

---

## 🐛 常见问题

### 问题1: permission denied

**症状**:
```
Got permission denied while trying to connect to the Docker daemon socket
```

**解决方案**:
```bash
# 将用户添加到 docker 组
sudo usermod -aG docker $USER

# 重新登录或运行
newgrp docker
```

### 问题2: Docker daemon not running

**症状**:
```
Cannot connect to the Docker daemon
```

**解决方案**:
```bash
# Ubuntu/Debian
sudo systemctl start docker
sudo systemctl enable docker

# macOS
# 启动 Docker Desktop 应用

# 检查状态
sudo systemctl status docker
```

### 问题3: docker-compose: command not found

**症状**:
```
bash: docker-compose: command not found
```

**解决方案**:
```bash
# Ubuntu/Debian
sudo apt-get install docker-compose

# macOS
brew install docker-compose

# 或使用 Docker Compose V2（内置）
docker compose version
```

### 问题4: 网络连接问题

**症状**: 拉取镜像时超时或失败

**解决方案**:
```bash
# 配置 Docker 镜像加速（中国大陆用户）
sudo mkdir -p /etc/docker
sudo tee /etc/docker/daemon.json <<-'EOF'
{
  "registry-mirrors": [
    "https://docker.mirrors.ustc.edu.cn",
    "https://hub-mirror.c.163.com"
  ]
}
EOF

# 重启 Docker
sudo systemctl daemon-reload
sudo systemctl restart docker
```

---

## 📊 资源限制

### 限制 Docker 容器资源使用

编辑 `docker-compose.yml`：

```yaml
services:
  rsshub:
    image: diygod/rsshub:latest
    ports:
      - "1200:1200"
    environment:
      - NODE_ENV=production
      - CACHE_TYPE=memory
    restart: always
    # 资源限制
    mem_limit: 512m
    cpus: 1.0
```

---

## 🔧 Docker 常用命令

```bash
# 查看运行中的容器
docker ps

# 查看所有容器（包括停止的）
docker ps -a

# 查看容器日志
docker logs rsshub
docker logs -f rsshub  # 实时查看

# 停止容器
docker stop rsshub

# 启动容器
docker start rsshub

# 重启容器
docker restart rsshub

# 删除容器
docker rm rsshub

# 查看镜像
docker images

# 删除镜像
docker rmi diygod/rsshub

# 清理未使用的资源
docker system prune -a
```

---

## 📚 相关文档

- [Docker 官方文档](https://docs.docker.com/)
- [Docker Compose 文档](https://docs.docker.com/compose/)
- [RSSHub 文档](https://docs.rsshub.app/)
- [Evolution RSSHub 指南](./RSSHUB_GUIDE.md)

---

## 🎯 下一步

安装完 Docker 后：

1. ✅ 运行 `./scripts/start_rsshub.sh` 启动 RSSHub
2. ✅ 查看 `docs/RSSHUB_GUIDE.md` 了解信息源配置
3. ✅ 测试情报收集功能

---

**最后更新**: 2026-03-11  
**维护者**: Evolution Team
