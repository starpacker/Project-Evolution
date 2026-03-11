#!/bin/bash

# Evolution RSSHub 快速启动脚本

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔═══════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║${NC}  ${GREEN}🚀 Evolution RSSHub 启动脚本${NC}                          ${BLUE}║${NC}"
echo -e "${BLUE}╚═══════════════════════════════════════════════════════════╝${NC}"
echo ""

# 1. 检查 Docker
echo -n "🐳 检查 Docker: "
if command -v docker &> /dev/null; then
    echo -e "${GREEN}✅ 已安装${NC}"
else
    echo -e "${RED}❌ 未安装${NC}"
    echo -e "${YELLOW}请先安装 Docker:${NC}"
    echo "  Ubuntu/Debian: sudo apt-get install docker.io docker-compose"
    echo "  macOS: brew install docker docker-compose"
    exit 1
fi

# 2. 检查 Docker Compose
echo -n "🐳 检查 Docker Compose: "
if command -v docker-compose &> /dev/null; then
    echo -e "${GREEN}✅ 已安装${NC}"
else
    echo -e "${RED}❌ 未安装${NC}"
    exit 1
fi

# 3. 检查 Docker 服务
echo -n "🔧 检查 Docker 服务: "
if docker info &> /dev/null; then
    echo -e "${GREEN}✅ 运行中${NC}"
else
    echo -e "${RED}❌ 未运行${NC}"
    echo -e "${YELLOW}尝试启动 Docker 服务...${NC}"
    sudo systemctl start docker
    sleep 2
    if docker info &> /dev/null; then
        echo -e "${GREEN}✅ Docker 服务已启动${NC}"
    else
        echo -e "${RED}❌ 无法启动 Docker 服务${NC}"
        exit 1
    fi
fi

# 4. 检查端口 1200
echo -n "🔌 检查端口 1200: "
if lsof -i :1200 &> /dev/null; then
    echo -e "${YELLOW}⚠️  已被占用${NC}"
    echo -e "${YELLOW}正在尝试停止现有服务...${NC}"
    docker-compose stop rsshub 2>/dev/null || true
    sleep 2
fi
echo -e "${GREEN}✅ 可用${NC}"

# 5. 拉取最新镜像
echo -e "\n${YELLOW}📥 拉取 RSSHub 最新镜像...${NC}"
docker-compose pull rsshub

# 6. 启动 RSSHub
echo -e "\n${YELLOW}🚀 启动 RSSHub 服务...${NC}"
docker-compose up -d rsshub

# 7. 等待服务就绪
echo -e "\n${YELLOW}⏳ 等待服务启动...${NC}"
for i in {1..30}; do
    if curl -s http://localhost:1200 > /dev/null 2>&1; then
        echo -e "${GREEN}✅ RSSHub 服务已就绪！${NC}"
        break
    fi
    echo -n "."
    sleep 1
    if [ $i -eq 30 ]; then
        echo -e "\n${RED}❌ 服务启动超时${NC}"
        echo -e "${YELLOW}查看日志: docker-compose logs rsshub${NC}"
        exit 1
    fi
done

# 8. 测试几个源
echo -e "\n${BLUE}╔═══════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║${NC}  ${GREEN}🧪 测试信息源${NC}                                          ${BLUE}║${NC}"
echo -e "${BLUE}╚═══════════════════════════════════════════════════════════╝${NC}"
echo ""

test_feed() {
    local name=$1
    local path=$2
    echo -n "  📡 ${name}: "
    if curl -s -o /dev/null -w "%{http_code}" "http://localhost:1200${path}" | grep -q "200"; then
        echo -e "${GREEN}✅ 正常${NC}"
        return 0
    else
        echo -e "${RED}❌ 失败${NC}"
        return 1
    fi
}

# 测试几个关键源
test_feed "GitHub Trending" "/github/trending/daily/python"
test_feed "Hacker News" "/hackernews/best"
test_feed "arXiv ML" "/arxiv/search_query=machine+learning"

# 9. 显示统计信息
echo -e "\n${BLUE}╔═══════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║${NC}  ${GREEN}📊 配置统计${NC}                                            ${BLUE}║${NC}"
echo -e "${BLUE}╚═══════════════════════════════════════════════════════════╝${NC}"
echo ""

# 统计配置的源数量
FEED_COUNT=$(grep -c '"name":' evolution/config/settings.py || echo "0")
echo -e "  📡 配置的信息源: ${GREEN}${FEED_COUNT}${NC} 个"

# 按类别统计
echo -e "\n  按类别分布:"
for category in academic tech news social blog; do
    count=$(grep -c "\"category\": \"${category}\"" evolution/config/settings.py || echo "0")
    if [ "$count" -gt 0 ]; then
        echo -e "    ${category}: ${GREEN}${count}${NC} 个"
    fi
done

# 10. 显示有用的命令
echo -e "\n${BLUE}╔═══════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║${NC}  ${GREEN}💡 常用命令${NC}                                            ${BLUE}║${NC}"
echo -e "${BLUE}╚═══════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "  查看日志:     ${YELLOW}docker-compose logs -f rsshub${NC}"
echo -e "  查看状态:     ${YELLOW}docker-compose ps${NC}"
echo -e "  停止服务:     ${YELLOW}docker-compose stop rsshub${NC}"
echo -e "  重启服务:     ${YELLOW}docker-compose restart rsshub${NC}"
echo -e "  测试源:       ${YELLOW}curl http://localhost:1200/github/trending/daily/python${NC}"
echo -e "  完整文档:     ${YELLOW}cat docs/RSSHUB_GUIDE.md${NC}"
echo ""

echo -e "${GREEN}🎉 RSSHub 启动成功！${NC}"
echo -e "${YELLOW}访问: http://localhost:1200${NC}"
echo ""
