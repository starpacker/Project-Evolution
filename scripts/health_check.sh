#!/bin/bash

# Evolution AI Agent 健康检查脚本

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔═══════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║${NC}  ${GREEN}🔍 Evolution AI Agent 健康检查${NC}                        ${BLUE}║${NC}"
echo -e "${BLUE}╚═══════════════════════════════════════════════════════════╝${NC}"
echo ""

# 检查计数
PASS=0
FAIL=0
WARN=0

# 1. 检查配置文件
echo -n "📄 配置文件 (.env): "
if [ -f ".env" ]; then
    echo -e "${GREEN}✅ 存在${NC}"
    ((PASS++))
else
    echo -e "${RED}❌ 不存在${NC}"
    echo -e "   ${YELLOW}提示: 运行 'cp .env.example .env' 创建配置文件${NC}"
    ((FAIL++))
fi

# 2. 检查Docker
echo -n "🐳 Docker: "
if command -v docker &> /dev/null; then
    echo -e "${GREEN}✅ 已安装${NC}"
    ((PASS++))
else
    echo -e "${RED}❌ 未安装${NC}"
    ((FAIL++))
fi

# 3. 检查Docker Compose
echo -n "🐳 Docker Compose: "
if command -v docker-compose &> /dev/null; then
    echo -e "${GREEN}✅ 已安装${NC}"
    ((PASS++))
else
    echo -e "${RED}❌ 未安装${NC}"
    ((FAIL++))
fi

# 4. 检查Docker服务状态
echo -n "🔧 Docker服务: "
if docker-compose ps 2>/dev/null | grep -q "Up"; then
    echo -e "${GREEN}✅ 运行中${NC}"
    ((PASS++))
else
    echo -e "${YELLOW}⚠️  未运行${NC}"
    echo -e "   ${YELLOW}提示: 运行 'docker-compose up -d' 启动服务${NC}"
    ((WARN++))
fi

# 5. 检查PostgreSQL
echo -n "🗄️  PostgreSQL: "
if docker-compose ps postgres 2>/dev/null | grep -q "Up"; then
    if docker-compose exec -T postgres pg_isready -U evolution_user &>/dev/null; then
        echo -e "${GREEN}✅ 正常${NC}"
        ((PASS++))
    else
        echo -e "${YELLOW}⚠️  运行中但未就绪${NC}"
        ((WARN++))
    fi
else
    echo -e "${YELLOW}⚠️  未运行${NC}"
    ((WARN++))
fi

# 6. 检查Redis
echo -n "💾 Redis: "
if docker-compose ps redis 2>/dev/null | grep -q "Up"; then
    if docker-compose exec -T redis redis-cli ping &>/dev/null | grep -q "PONG"; then
        echo -e "${GREEN}✅ 正常${NC}"
        ((PASS++))
    else
        echo -e "${YELLOW}⚠️  运行中但未响应${NC}"
        ((WARN++))
    fi
else
    echo -e "${YELLOW}⚠️  未运行${NC}"
    ((WARN++))
fi

# 7. 检查Python环境
echo -n "🐍 Python: "
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    echo -e "${GREEN}✅ $PYTHON_VERSION${NC}"
    ((PASS++))
else
    echo -e "${RED}❌ 未安装${NC}"
    ((FAIL++))
fi

# 8. 检查虚拟环境
echo -n "📦 虚拟环境: "
if [ -d "venv" ]; then
    echo -e "${GREEN}✅ 存在${NC}"
    ((PASS++))
else
    echo -e "${YELLOW}⚠️  不存在${NC}"
    echo -e "   ${YELLOW}提示: 运行 'python -m venv venv' 创建虚拟环境${NC}"
    ((WARN++))
fi

# 9. 检查数据目录
echo -n "📁 数据目录: "
if [ -d "data" ]; then
    echo -e "${GREEN}✅ 存在${NC}"
    ((PASS++))
else
    echo -e "${YELLOW}⚠️  不存在${NC}"
    mkdir -p data
    echo -e "   ${GREEN}已自动创建${NC}"
    ((PASS++))
fi

# 10. 检查日志目录
echo -n "📋 日志目录: "
if [ -d "logs" ]; then
    echo -e "${GREEN}✅ 存在${NC}"
    ((PASS++))
else
    echo -e "${YELLOW}⚠️  不存在${NC}"
    mkdir -p logs
    echo -e "   ${GREEN}已自动创建${NC}"
    ((PASS++))
fi

# 11. 检查环境变量
if [ -f ".env" ]; then
    echo -n "🔑 API密钥配置: "
    if grep -q "CLAUDE_API_KEY=sk-ant-" .env && grep -q "OPENAI_API_KEY=sk-" .env; then
        echo -e "${GREEN}✅ 已配置${NC}"
        ((PASS++))
    else
        echo -e "${YELLOW}⚠️  未完全配置${NC}"
        echo -e "   ${YELLOW}提示: 请在 .env 文件中配置 API 密钥${NC}"
        ((WARN++))
    fi
    
    echo -n "📧 邮箱配置: "
    if grep -q "SMTP_USER=.*@" .env && grep -q "SMTP_PASSWORD=..*" .env; then
        echo -e "${GREEN}✅ 已配置${NC}"
        ((PASS++))
    else
        echo -e "${YELLOW}⚠️  未配置${NC}"
        echo -e "   ${YELLOW}提示: 邮箱通知功能将不可用${NC}"
        ((WARN++))
    fi
fi

# 12. 检查端口占用
echo -n "🔌 端口检查 (8000): "
if lsof -i :8000 &>/dev/null; then
    echo -e "${YELLOW}⚠️  已被占用${NC}"
    ((WARN++))
else
    echo -e "${GREEN}✅ 可用${NC}"
    ((PASS++))
fi

echo ""
echo -e "${BLUE}╔═══════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║${NC}  ${GREEN}检查结果汇总${NC}                                          ${BLUE}║${NC}"
echo -e "${BLUE}╠═══════════════════════════════════════════════════════════╣${NC}"
echo -e "${BLUE}║${NC}  ${GREEN}✅ 通过: $PASS${NC}                                              ${BLUE}║${NC}"
echo -e "${BLUE}║${NC}  ${YELLOW}⚠️  警告: $WARN${NC}                                              ${BLUE}║${NC}"
echo -e "${BLUE}║${NC}  ${RED}❌ 失败: $FAIL${NC}                                              ${BLUE}║${NC}"
echo -e "${BLUE}╚═══════════════════════════════════════════════════════════╝${NC}"
echo ""

# 总体状态
if [ $FAIL -eq 0 ] && [ $WARN -eq 0 ]; then
    echo -e "${GREEN}🎉 所有检查通过！系统状态良好。${NC}"
    exit 0
elif [ $FAIL -eq 0 ]; then
    echo -e "${YELLOW}⚠️  存在警告项，但系统可以运行。${NC}"
    exit 0
else
    echo -e "${RED}❌ 存在严重问题，请先解决失败项。${NC}"
    exit 1
fi
