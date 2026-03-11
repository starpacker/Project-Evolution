---
applyTo: "**"
---

# Skill: Python 环境快速配置 (Bulletproof Environment Setup)

> **目标**: 为任务创建独立 Python 环境，确保一次成功，绝不浪费时间在失败重试上。

## 🚨 核心问题与根因

Agent 常见失败模式：
1. **conda create 被中断** → `/data/yjh/<TASK>_env/bin/pip` 不存在（NFS 慢 + conda-forge 超时）
2. **没有配置国内镜像** → conda-forge 元数据下载 5s 超时，而清华源仅需 1.4s
3. **没有验证步骤** → 盲目假设环境就绪，直到运行时才发现 pip/python 不存在
4. **磁盘空间不足** → `/data` NFS 97% 满，写入可能失败

## Step 0: 一次性配置清华镜像源（如果没配过）

**检查是否已配置**：
```bash
grep -q "tsinghua" ~/.condarc 2>/dev/null && echo "✅ 已配置清华源" || echo "❌ 未配置，需要配置"
grep -q "tsinghua" ~/.pip/pip.conf 2>/dev/null && echo "✅ pip 已配置清华源" || echo "❌ pip 未配置"
```

**配置 conda 清华源**（覆盖写入 `~/.condarc`）：
```bash
cat > ~/.condarc << 'EOF'
channels:
  - defaults
show_channel_urls: true
default_channels:
  - https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/main
  - https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/r
  - https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/msys2
custom_channels:
  conda-forge: https://mirrors.tuna.tsinghua.edu.cn/anaconda/cloud
  pytorch: https://mirrors.tuna.tsinghua.edu.cn/anaconda/cloud
envs_dirs:
  - /data/yjh/conda_envs
pkgs_dirs:
  - /data/yjh/pkgs
EOF
echo "✅ conda 清华源配置完成"
```

**配置 pip 清华源**：
```bash
mkdir -p ~/.pip
cat > ~/.pip/pip.conf << 'EOF'
[global]
index-url = https://pypi.tuna.tsinghua.edu.cn/simple
trusted-host = pypi.tuna.tsinghua.edu.cn
timeout = 120
retries = 5
EOF
echo "✅ pip 清华源配置完成"
```

> ⚠️ Step 0 只需执行一次。后续任务跳过此步。
> 执行前先检查，已有则跳过。

## Step 1: 检查磁盘空间

```bash
df -h /data/yjh/ | awk 'NR==2 {print "可用空间:", $4, "使用率:", $5}'
# 如果使用率 > 98%，先清理旧环境：
# conda env remove --prefix /data/yjh/<OLD_TASK>_env
# rm -rf /data/yjh/<OLD_TASK>_env
```

## Step 2: 创建独立 Python 环境（带验证）

**关键原则**：
- ✅ 必须使用 `--prefix /data/yjh/<TASK_NAME>_env`
- ✅ 必须显式指定 `python=3.10`（否则不装 pip!）
- ✅ 必须同时安装 `pip`（双保险）
- ✅ 创建后立即验证
- ❌ 绝不跳过验证直接使用

```bash
# ━━━ 创建环境 ━━━
conda create --prefix /data/yjh/<TASK_NAME>_env python=3.10 pip -y

# ━━━ 关键验证（必须全部通过才能继续）━━━
echo "=== 环境验证 ==="
test -f /data/yjh/<TASK_NAME>_env/bin/python && echo "✅ python 存在" || echo "❌ python 不存在 → 环境创建失败！"
test -f /data/yjh/<TASK_NAME>_env/bin/pip && echo "✅ pip 存在" || echo "❌ pip 不存在 → 环境创建不完整！"
/data/yjh/<TASK_NAME>_env/bin/python --version
/data/yjh/<TASK_NAME>_env/bin/pip --version
```

### 如果验证失败的修复方案

```bash
# 方案A: 删除重建（推荐）
rm -rf /data/yjh/<TASK_NAME>_env
conda create --prefix /data/yjh/<TASK_NAME>_env python=3.10 pip -y

# 方案B: 手动安装 pip（如果 python 存在但 pip 缺失）
/data/yjh/<TASK_NAME>_env/bin/python -m ensurepip --upgrade
# 再验证
/data/yjh/<TASK_NAME>_env/bin/pip --version
```

## Step 3: 安装依赖

**始终使用完整路径的 pip**，不要依赖 `conda activate`：

```bash
cd /data/yjh/<TASK_NAME>_sandbox/repo

# 根据 repo 实际情况选择安装方式：

# 情况1: 有 requirements.txt
/data/yjh/<TASK_NAME>_env/bin/pip install -r requirements.txt

# 情况2: 有 setup.py 或 pyproject.toml（可编辑安装）
/data/yjh/<TASK_NAME>_env/bin/pip install -e .

# 情况3: 有 setup.cfg + setup.py
/data/yjh/<TASK_NAME>_env/bin/pip install -e ".[dev]"

# 情况4: README 中列出依赖
/data/yjh/<TASK_NAME>_env/bin/pip install <dep1> <dep2> ...

# 情况5: 无依赖说明 → 运行时缺什么装什么
```

**必装的通用依赖**：
```bash
/data/yjh/<TASK_NAME>_env/bin/pip install numpy matplotlib
```

### pip 安装慢或超时？

```bash
# 临时指定清华源（如果全局没配）
/data/yjh/<TASK_NAME>_env/bin/pip install -r requirements.txt \
  -i https://pypi.tuna.tsinghua.edu.cn/simple \
  --trusted-host pypi.tuna.tsinghua.edu.cn \
  --timeout 120

# 如果某个包编译很慢，尝试安装预编译版本
/data/yjh/<TASK_NAME>_env/bin/pip install --prefer-binary <package>
```

## Step 4: 最终验证

```bash
echo "=== 环境最终验证 ==="
/data/yjh/<TASK_NAME>_env/bin/python -c "
import sys
print(f'Python: {sys.version}')
print(f'Executable: {sys.executable}')
print(f'Prefix: {sys.prefix}')

# 测试关键包
try:
    import numpy; print(f'numpy: {numpy.__version__}')
except ImportError: print('❌ numpy 未安装')
try:
    import matplotlib; print(f'matplotlib: {matplotlib.__version__}')
except ImportError: print('❌ matplotlib 未安装')
"
echo "✅ 环境就绪"
```

## 完整一键脚本（复制即用）

```bash
TASK_NAME="<TASK_NAME>"  # ← 替换为实际任务名

# 0. 确保镜像源已配置
grep -q "tsinghua" ~/.condarc 2>/dev/null || {
  cat > ~/.condarc << 'CONDARC'
channels:
  - defaults
show_channel_urls: true
default_channels:
  - https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/main
  - https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/r
  - https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/msys2
custom_channels:
  conda-forge: https://mirrors.tuna.tsinghua.edu.cn/anaconda/cloud
  pytorch: https://mirrors.tuna.tsinghua.edu.cn/anaconda/cloud
envs_dirs:
  - /data/yjh/conda_envs
pkgs_dirs:
  - /data/yjh/pkgs
CONDARC
  echo "✅ conda 镜像已配置"
}

grep -q "tsinghua" ~/.pip/pip.conf 2>/dev/null || {
  mkdir -p ~/.pip
  cat > ~/.pip/pip.conf << 'PIPCONF'
[global]
index-url = https://pypi.tuna.tsinghua.edu.cn/simple
trusted-host = pypi.tuna.tsinghua.edu.cn
timeout = 120
retries = 5
PIPCONF
  echo "✅ pip 镜像已配置"
}

# 1. 检查空间
echo "=== 磁盘空间 ==="
df -h /data/yjh/ | awk 'NR==2 {print "可用:", $4, "使用率:", $5}'

# 2. 创建环境
echo "=== 创建 conda 环境 ==="
conda create --prefix /data/yjh/${TASK_NAME}_env python=3.10 pip -y

# 3. 验证环境
echo "=== 验证环境 ==="
if [[ -f /data/yjh/${TASK_NAME}_env/bin/python ]] && [[ -f /data/yjh/${TASK_NAME}_env/bin/pip ]]; then
  /data/yjh/${TASK_NAME}_env/bin/python --version
  /data/yjh/${TASK_NAME}_env/bin/pip --version
  echo "✅ 环境创建成功"
else
  echo "❌ 环境创建失败，尝试重建..."
  rm -rf /data/yjh/${TASK_NAME}_env
  conda create --prefix /data/yjh/${TASK_NAME}_env python=3.10 pip -y
  # 二次验证
  if [[ -f /data/yjh/${TASK_NAME}_env/bin/pip ]]; then
    echo "✅ 重建成功"
  else
    echo "💀 环境创建彻底失败，请检查网络和磁盘"
    return 1
  fi
fi

# 4. 安装依赖
echo "=== 安装依赖 ==="
cd /data/yjh/${TASK_NAME}_sandbox/repo
if [[ -f requirements.txt ]]; then
  /data/yjh/${TASK_NAME}_env/bin/pip install -r requirements.txt
elif [[ -f setup.py ]] || [[ -f pyproject.toml ]]; then
  /data/yjh/${TASK_NAME}_env/bin/pip install -e .
else
  echo "⚠️ 未找到依赖文件，需手动安装"
fi

# 5. 安装通用依赖
/data/yjh/${TASK_NAME}_env/bin/pip install numpy matplotlib

echo "🎉 环境 ${TASK_NAME} 配置完成！"
```

## 🔑 Agent 必须遵守的规则

1. **永远先验证再使用** — 调用 `pip` 或 `python` 前必须 `test -f` 检查存在
2. **永远用完整路径** — `/data/yjh/<TASK>_env/bin/pip`，不依赖 `conda activate`
3. **conda create 必须带 `python=X.Y pip`** — 缺少则不会装 pip
4. **失败就删除重建** — 不要试图修复半成品环境，直接 `rm -rf` 重来
5. **使用清华源** — 大幅减少超时概率（5s → 1.4s）
6. **检查磁盘空间** — `/data` 已 97% 满，满了就先清理旧环境

## 🚫 绝对不要做的事

- ❌ 不要 `conda activate` 然后用裸 `pip` — 在脚本/subshell 中 activate 经常失效
- ❌ 不要省略 `python=3.10` 参数 — 否则只装 base 包，没有 python 也没有 pip
- ❌ 不要在验证失败后继续执行后续步骤
- ❌ 不要用 `conda install` 装 pip 包 — 用 `/path/to/pip install`
- ❌ 不要假设上次的环境还在 — 每次任务都要检查

## 📋 清理旧环境（释放空间）

```bash
# 查看所有环境及大小
du -sh /data/yjh/*_env 2>/dev/null | sort -rh | head -20

# 删除指定环境
rm -rf /data/yjh/<OLD_TASK>_env

# 清理 conda 缓存
conda clean --all -y
```
