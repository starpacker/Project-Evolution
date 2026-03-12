# 📊 Evolution 数据查看指南

## 🎯 访问方式

### 1. Web Dashboard（推荐）

**访问地址**:
- 本地: http://localhost:5000/dashboard
- 局域网: http://10.128.250.187:5000/dashboard

**功能模块**:

#### 📈 总览页面
- 待办日程统计
- 技能总数
- 人物档案数量
- 今日对话数
- 训练次数
- 反思记录

#### 🗓️ 日程管理
- 查看所有日程
- 按状态筛选（待办/逾期）
- 显示优先级和截止时间

#### 🎯 技能树
- 查看所有技能
- 按类别分组（professional/thinking/language/physical/emotional）
- 显示等级进度条
- 标记荒废技能（30天未训练）

#### 👥 人物档案
- 查看所有记录的人物
- 提及次数排名
- 关系类型
- 情感影响分析

#### 📚 训练记录
- 查看训练历史
- 按技能筛选
- 显示训练模态（T1-T7）
- 评分和洞察

#### 💭 反思历史
- 查看每日反思
- 情绪趋势分析
- 明日建议
- 异常检测记录

#### 💬 对话日志
- 查看对话历史
- 按日期筛选
- 完整对话内容

#### 🧠 记忆搜索
- 搜索 Mem0 记忆
- 向量搜索 + 图谱关系
- 实时搜索结果

---

## 📁 数据存储位置

### SQLite 数据库
```
/home/yjh/ProjectEvolution/data/evolution.db
```

**包含 7 张表**:
1. `schedule` - 日程表
2. `skills` - 技能树
3. `persons` - 人物档案
4. `training_logs` - 训练记录
5. `mental_models` - 心智模型
6. `daily_reflections` - 每日反思
7. `conversation_logs` - 对话日志

### 对话日志文件
```
/home/yjh/ProjectEvolution/data/conversation_logs/
├── web_chat_202603.jsonl    # Web Chat 对话
└── telegram_202603.jsonl    # Telegram 对话（如果启用）
```

### 反思文件
```
/home/yjh/ProjectEvolution/data/reflections/
├── 2026-03-10.json
├── 2026-03-11.json
└── weekly_2026-W10.json
```

### Mem0 记忆数据
```
/home/yjh/ProjectEvolution/data/qdrant/     # 向量数据库
/home/yjh/ProjectEvolution/data/kuzu_db/    # 知识图谱
```

---

## 🔧 命令行查看方式

### 1. 查看 SQLite 数据库

```bash
# 进入数据库
cd /home/yjh/ProjectEvolution
sqlite3 data/evolution.db

# 查看所有表
.tables

# 查看日程
SELECT * FROM schedule;

# 查看技能
SELECT * FROM skills;

# 查看人物档案
SELECT * FROM persons ORDER BY mention_count DESC;

# 查看训练记录
SELECT * FROM training_logs ORDER BY trained_at DESC LIMIT 10;

# 查看反思
SELECT date, primary_emotion, tomorrow_suggestion FROM daily_reflections ORDER BY date DESC;

# 查看对话统计
SELECT date, COUNT(*) as count FROM conversation_logs GROUP BY date;

# 退出
.quit
```

### 2. 查看对话日志

```bash
# 查看最新对话
tail -20 data/conversation_logs/web_chat_202603.jsonl

# 搜索特定内容
grep "关键词" data/conversation_logs/*.jsonl

# 统计对话数量
wc -l data/conversation_logs/*.jsonl

# 格式化查看
cat data/conversation_logs/web_chat_202603.jsonl | jq '.'
```

### 3. 查看反思文件

```bash
# 查看最新反思
cat data/reflections/$(ls -t data/reflections/ | head -1) | jq '.'

# 查看所有反思文件
ls -lh data/reflections/

# 搜索特定情绪
grep -r "anxious" data/reflections/
```

---

## 📊 API 端点

所有 Dashboard API 都可以通过 curl 访问：

### 总览数据
```bash
curl http://localhost:5000/api/dashboard/overview | jq '.'
```

### 日程列表
```bash
# 所有日程
curl http://localhost:5000/api/dashboard/schedules | jq '.'

# 仅待办
curl http://localhost:5000/api/dashboard/schedules?status=pending | jq '.'

# 仅逾期
curl http://localhost:5000/api/dashboard/schedules?status=overdue | jq '.'
```

### 技能详情
```bash
curl http://localhost:5000/api/dashboard/skills | jq '.'
```

### 人物档案
```bash
curl http://localhost:5000/api/dashboard/persons | jq '.'
```

### 训练记录
```bash
# 最近 50 条
curl http://localhost:5000/api/dashboard/trainings | jq '.'

# 指定技能
curl http://localhost:5000/api/dashboard/trainings?skill_id=1 | jq '.'
```

### 反思历史
```bash
# 最近 30 天
curl http://localhost:5000/api/dashboard/reflections | jq '.'

# 最近 7 天
curl http://localhost:5000/api/dashboard/reflections?days=7 | jq '.'
```

### 对话日志
```bash
# 今日对话
curl http://localhost:5000/api/dashboard/conversations | jq '.'

# 指定日期
curl http://localhost:5000/api/dashboard/conversations?date=2026-03-10 | jq '.'
```

### 记忆搜索
```bash
curl "http://localhost:5000/api/dashboard/memory/search?query=目标" | jq '.'
```

### 导出数据
```bash
# 导出所有数据
curl http://localhost:5000/api/dashboard/export/all > evolution_data.json

# 导出特定类型
curl http://localhost:5000/api/dashboard/export/schedules > schedules.json
curl http://localhost:5000/api/dashboard/export/skills > skills.json
curl http://localhost:5000/api/dashboard/export/persons > persons.json
```

---

## 🔍 高级查询示例

### SQLite 高级查询

```sql
-- 查看最活跃的技能
SELECT name, level, COUNT(tl.id) as training_count
FROM skills s
LEFT JOIN training_logs tl ON s.id = tl.skill_id
GROUP BY s.id
ORDER BY training_count DESC;

-- 查看情绪趋势
SELECT date, primary_emotion, emotional_intensity
FROM daily_reflections
ORDER BY date DESC
LIMIT 30;

-- 查看关系精力分配
SELECT name, mention_count, emotional_impact
FROM persons
ORDER BY mention_count DESC
LIMIT 10;

-- 查看逾期日程
SELECT content, due_date, priority
FROM schedule
WHERE status = 'pending' AND due_date < date('now')
ORDER BY due_date;
```

---

## 📱 移动端访问

在手机浏览器中访问：
```
http://10.128.250.187:5000/dashboard
```

Dashboard 采用响应式设计，自动适配手机屏幕。

---

## 🎨 数据可视化建议

### 方案 1: 使用 Notion（已集成）
- 自动同步反思到 Notion Database
- 使用 Notion 的图表功能可视化
- 支持多维度筛选和排序

### 方案 2: 导出到 Excel/Google Sheets
```bash
# 导出为 JSON
curl http://localhost:5000/api/dashboard/export/all > data.json

# 使用 Python 转换为 CSV
python3 << EOF
import json
import csv

with open('data.json') as f:
    data = json.load(f)

# 导出日程
with open('schedules.csv', 'w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=['content', 'due_date', 'priority', 'status'])
    writer.writeheader()
    writer.writerows(data['schedules'])
EOF
```

### 方案 3: 使用 Grafana（高级）
- 配置 SQLite 数据源
- 创建自定义仪表板
- 实时监控和告警

---

## 🔐 数据备份

### 自动备份脚本
```bash
#!/bin/bash
# backup.sh

BACKUP_DIR="/home/yjh/ProjectEvolution/backups"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# 备份数据库
cp data/evolution.db $BACKUP_DIR/evolution_$DATE.db

# 备份对话日志
tar -czf $BACKUP_DIR/conversations_$DATE.tar.gz data/conversation_logs/

# 备份反思
tar -czf $BACKUP_DIR/reflections_$DATE.tar.gz data/reflections/

# 备份 Mem0 数据
tar -czf $BACKUP_DIR/memory_$DATE.tar.gz data/qdrant/ data/kuzu_db/

echo "备份完成: $BACKUP_DIR"
```

### 定时备份（crontab）
```bash
# 每天凌晨 2 点备份
0 2 * * * /home/yjh/ProjectEvolution/scripts/backup.sh
```

---

## 📝 常见问题

### Q: Dashboard 显示"暂无数据"？
A: 这是正常的，数据库刚初始化是空的。开始使用 Evolution 后，数据会自动积累。

### Q: 如何清空所有数据？
A: 
```bash
cd /home/yjh/ProjectEvolution
rm data/evolution.db
rm -rf data/conversation_logs/*
rm -rf data/reflections/*
rm -rf data/qdrant/*
rm -rf data/kuzu_db/*
```

### Q: 如何导入旧数据？
A: 使用 SQLite 的 `.import` 命令或编写 Python 脚本。

### Q: Dashboard 加载很慢？
A: 
1. 检查数据库大小：`du -sh data/evolution.db`
2. 添加索引优化查询
3. 限制返回数据量

---

## 🚀 下一步

1. **开始使用**: 与 Evolution 对话，数据会自动记录
2. **定期查看**: 每周查看 Dashboard 了解自己的成长
3. **数据分析**: 使用 SQL 查询发现模式和趋势
4. **备份数据**: 设置自动备份保护数据安全

---

**更新时间**: 2026-03-11  
**版本**: v0.1.0
