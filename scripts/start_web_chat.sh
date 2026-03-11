#!/bin/bash
# 启动 Web Chat 服务器

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

# 加载环境变量
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

# 检查依赖
echo "🔍 检查依赖..."
if ! python3 -c "import flask" 2>/dev/null; then
    echo "📦 安装 Flask..."
    pip install flask flask-cors
fi

# 启动服务器
echo "🚀 启动 Web Chat 服务器..."
echo "📱 访问地址："
echo "   本地: http://localhost:5000"
echo "   局域网: http://$(hostname -I | awk '{print $1}'):5000"
echo ""
echo "💡 提示："
echo "   1. 确保防火墙允许 5000 端口"
echo "   2. 手机连接同一 WiFi 即可访问"
echo "   3. 按 Ctrl+C 停止服务器"
echo ""

python3 -m evolution.chat.web_chat
