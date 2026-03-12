#!/bin/bash
# Evolution 主动推送功能安装脚本

set -e

echo "========================================"
echo "Evolution 主动推送功能安装"
echo "========================================"

# 检查脚本权限
echo ""
echo "1. 设置脚本执行权限..."
chmod +x /home/yjh/ProjectEvolution/scripts/morning_briefing.py
chmod +x /home/yjh/ProjectEvolution/scripts/evening_report.py
chmod +x /home/yjh/ProjectEvolution/scripts/weekly_report.py
echo "   ✅ 脚本权限设置完成"

# 创建日志目录
echo ""
echo "2. 创建日志目录..."
mkdir -p /home/yjh/ProjectEvolution/logs
echo "   ✅ 日志目录创建完成"

# 显示crontab配置
echo ""
echo "3. Crontab配置内容:"
echo "========================================"
cat /home/yjh/ProjectEvolution/scripts/crontab.txt
echo "========================================"

# 询问是否安装
echo ""
read -p "是否要安装这些定时任务到crontab? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]
then
    echo ""
    echo "4. 安装定时任务..."
    
    # 备份现有crontab
    crontab -l > /tmp/crontab_backup_$(date +%Y%m%d_%H%M%S).txt 2>/dev/null || true
    echo "   ✅ 已备份现有crontab"
    
    # 添加新任务
    (crontab -l 2>/dev/null || true; echo ""; echo "# Evolution 主动推送任务"; cat /home/yjh/ProjectEvolution/scripts/crontab.txt | grep -v "^#" | grep -v "^$") | crontab -
    echo "   ✅ 定时任务安装完成"
    
    echo ""
    echo "5. 验证安装..."
    crontab -l | grep -A 10 "Evolution"
    echo "   ✅ 验证完成"
else
    echo ""
    echo "跳过安装。你可以手动运行以下命令安装:"
    echo "  crontab -e"
    echo "然后将 scripts/crontab.txt 的内容添加到文件末尾"
fi

echo ""
echo "========================================"
echo "✅ 安装完成！"
echo "========================================"
echo ""
echo "📝 使用说明:"
echo "  - 早晨情报: 每天 08:00 自动推送"
echo "  - 晚间日报: 每天 21:00 自动推送"
echo "  - 周报: 每周日 20:00 自动推送"
echo ""
echo "📊 查看日志:"
echo "  tail -f logs/morning_briefing.log"
echo "  tail -f logs/evening_report.log"
echo "  tail -f logs/weekly_report.log"
echo ""
echo "🔧 管理定时任务:"
echo "  crontab -l  # 查看所有任务"
echo "  crontab -e  # 编辑任务"
echo ""
echo "🧪 手动测试:"
echo "  python3 scripts/morning_briefing.py"
echo "  python3 scripts/evening_report.py"
echo "  python3 scripts/weekly_report.py"
echo ""
