#!/bin/bash
# Evolution 一键安装脚本
# 用法: bash scripts/setup.sh

set -e

echo "╔══════════════════════════════════════╗"
echo "║   Project Evolution v0.1 - Setup     ║"
echo "╚══════════════════════════════════════╝"
echo ""

# ── 1. 创建数据目录 ──
DATA_DIR="${EVOLUTION_ROOT:-/data/evolution}/data"
echo "[1/5] Creating data directories..."
mkdir -p "$DATA_DIR"/{reflections,conversation_logs,qdrant,kuzu_db}
echo "  ✅ $DATA_DIR"

# ── 2. 安装 Python 依赖 ──
echo ""
echo "[2/5] Installing Python packages..."
pip install --quiet \
    "mem0ai[graph]>=1.0.5" \
    anthropic \
    httpx \
    apscheduler \
    markdown \
    2>/dev/null || pip install --quiet \
    anthropic \
    httpx \
    apscheduler \
    markdown

echo "  ✅ Python packages installed"

# ── 3. 初始化 SQLite ──
echo ""
echo "[3/5] Initializing SQLite database..."
python3 -c "
import sys
sys.path.insert(0, '$(dirname $(dirname $(realpath $0)))')
from evolution.db.manager import DatabaseManager
db = DatabaseManager('$DATA_DIR/evolution.db')
print('  ✅ SQLite tables initialized')
stats = db.get_stats()
for k, v in stats.items():
    print(f'    {k}: {v}')
"

# ── 4. 启动 RSSHub (Docker) ──
echo ""
echo "[4/5] Starting RSSHub..."
if command -v docker &> /dev/null; then
    if docker ps | grep -q rsshub; then
        echo "  ✅ RSSHub already running"
    else
        docker run -d --name rsshub -p 1200:1200 \
            -e NODE_ENV=production \
            -e CACHE_TYPE=memory \
            --restart always \
            diygod/rsshub:latest 2>/dev/null && echo "  ✅ RSSHub started" || echo "  ⚠️ RSSHub start failed (non-fatal)"
    fi
else
    echo "  ⚠️ Docker not found. RSSHub skipped (install Docker for RSS feeds)"
fi

# ── 5. 验证 ──
echo ""
echo "[5/5] Verification..."
python3 -c "
import sys
sys.path.insert(0, '$(dirname $(dirname $(realpath $0)))')

# Check all modules load
from evolution.config.settings import MEM0_CONFIG, USER_ID
from evolution.config.prompts import SYSTEM_PROMPT
from evolution.db.manager import DatabaseManager
from evolution.tools.memory_tool import EvolutionMemoryTool
from evolution.tools.db_tool import EvolutionDBTool
from evolution.tools.reflection_tool import EvolutionReflectionTool
from evolution.tools.intelligence_tool import EvolutionIntelligenceTool
from evolution.notification.router import NotificationRouter
from evolution.utils.bridge import get_evolution_tools

tools = get_evolution_tools()
print(f'  ✅ {len(tools)} tools loaded: {[t.name for t in tools]}')

# Test DB
db = EvolutionDBTool()
result = db.execute({'action': 'stats'})
print(f'  ✅ DB tool: {result.status}')

# Test Memory
mem = EvolutionMemoryTool()
print(f'  ✅ Memory tool: initialized')

print()
print('🎉 Evolution is ready!')
print()
print('Next steps:')
print('  1. Set environment variables (CLAUDE_API_KEY, etc.)')
print('  2. Copy system prompt to CowAgent config')
print('  3. Register tools with CowAgent')
"

echo ""
echo "╔══════════════════════════════════════╗"
echo "║         Setup Complete! 🚀           ║"
echo "╚══════════════════════════════════════╝"
