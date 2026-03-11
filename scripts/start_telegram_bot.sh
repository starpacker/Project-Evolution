#!/bin/bash
# Evolution Telegram Bot 启动脚本

set -e

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}╔═══════════════════════════════════════╗${NC}"
echo -e "${GREEN}║   Evolution Telegram Bot Launcher    ║${NC}"
echo -e "${GREEN}╚═══════════════════════════════════════╝${NC}"
echo ""

# 检查环境变量
if [ ! -f .env ]; then
    echo -e "${RED}❌ .env 文件不存在${NC}"
    echo -e "${YELLOW}请先创建 .env 文件并配置 Telegram Bot Token${NC}"
    exit 1
fi

# 加载环境变量
source .env

# 检查必要配置
if [ -z "$TG_BOT_TOKEN" ]; then
    echo -e "${RED}❌ TG_BOT_TOKEN 未配置${NC}"
    echo -e "${YELLOW}请在 .env 中设置 TG_BOT_TOKEN${NC}"
    exit 1
fi

if [ -z "$TG_CHAT_ID" ]; then
    echo -e "${RED}❌ TG_CHAT_ID 未配置${NC}"
    echo -e "${YELLOW}请在 .env 中设置 TG_CHAT_ID${NC}"
    exit 1
fi

# 检查 Python 环境
if ! command -v python &> /dev/null; then
    echo -e "${RED}❌ Python 未安装${NC}"
    exit 1
fi

# 创建日志目录
mkdir -p logs

echo -e "${GREEN}✅ 配置检查通过${NC}"
echo ""
echo -e "${YELLOW}启动模式选择：${NC}"
echo "  1) 前台运行（测试模式，Ctrl+C 停止）"
echo "  2) 后台运行（生产模式，nohup）"
echo "  3) 查看运行状态"
echo "  4) 停止后台进程"
echo ""
read -p "请选择 [1-4]: " choice

case $choice in
    1)
        echo -e "${GREEN}🚀 前台启动 Telegram Bot...${NC}"
        python -m evolution.chat.telegram_bot
        ;;
    2)
        echo -e "${GREEN}🚀 后台启动 Telegram Bot...${NC}"
        nohup python -m evolution.chat.telegram_bot > logs/telegram_bot.log 2>&1 &
        PID=$!
        echo $PID > logs/telegram_bot.pid
        echo -e "${GREEN}✅ Bot 已启动，PID: $PID${NC}"
        echo -e "${YELLOW}查看日志: tail -f logs/telegram_bot.log${NC}"
        echo -e "${YELLOW}停止服务: kill $PID 或运行此脚本选择选项4${NC}"
        ;;
    3)
        if [ -f logs/telegram_bot.pid ]; then
            PID=$(cat logs/telegram_bot.pid)
            if ps -p $PID > /dev/null 2>&1; then
                echo -e "${GREEN}✅ Bot 正在运行，PID: $PID${NC}"
                echo ""
                echo "最近10条日志："
                tail -n 10 logs/telegram_bot.log
            else
                echo -e "${RED}❌ Bot 未运行（PID 文件存在但进程不存在）${NC}"
                rm logs/telegram_bot.pid
            fi
        else
            echo -e "${YELLOW}⚠️  未找到 PID 文件，Bot 可能未启动${NC}"
        fi
        ;;
    4)
        if [ -f logs/telegram_bot.pid ]; then
            PID=$(cat logs/telegram_bot.pid)
            if ps -p $PID > /dev/null 2>&1; then
                kill $PID
                echo -e "${GREEN}✅ Bot 已停止（PID: $PID）${NC}"
                rm logs/telegram_bot.pid
            else
                echo -e "${YELLOW}⚠️  进程不存在，清理 PID 文件${NC}"
                rm logs/telegram_bot.pid
            fi
        else
            echo -e "${YELLOW}⚠️  未找到 PID 文件${NC}"
            # 尝试查找进程
            PIDS=$(pgrep -f "evolution.chat.telegram_bot")
            if [ -n "$PIDS" ]; then
                echo -e "${YELLOW}找到相关进程: $PIDS${NC}"
                read -p "是否停止这些进程？[y/N]: " confirm
                if [ "$confirm" = "y" ] || [ "$confirm" = "Y" ]; then
                    kill $PIDS
                    echo -e "${GREEN}✅ 进程已停止${NC}"
                fi
            else
                echo -e "${YELLOW}未找到运行中的 Bot 进程${NC}"
            fi
        fi
        ;;
    *)
        echo -e "${RED}无效选择${NC}"
        exit 1
        ;;
esac
