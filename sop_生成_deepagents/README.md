# SOP 生成系统 2.0

基于 DeepAgents 框架的 GLP SOP 自动化生成系统，支持自动迭代改进和记忆学习。

## 🚀 快速启动

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
cp .env.example .env
```

编辑 `.env` 文件，填入你的 API 配置：

```env
OPENAI_API_KEY=your_api_key_here
OPENAI_BASE_URL=https://aihubmix.com/v1
```

### 3. 运行系统

```bash
python main_v2.py
```

## 📥 输入说明

系统需要两个输入（在 `main_v2.py` 中修改）：

### 1. 验证方案
```python
validation_plan = """
## 验证方案
### 目标
验证小分子模板的分析方法

### 范围
- 样品制备
- 仪器分析
- 数据处理

### 验证参数
- 准确度: ±5%
- 精密度: RSD < 3%
"""
```

### 2. GLP 报告（标准答案）
```python
glp_report = """
## GLP 合规报告
### 16.2 声明
本报告按照 GLP 规范编制

#### 样品信息
- 样品编号: SMP-001
- 样品名称: 标准品

#### 分析结果
- 含量: 98.5%
- 纯度: 99.2%
"""
```

## 📤 输出说明

### 1. 控制台输出
- 实时显示 Agent 执行过程
- 显示生成的 SOP 内容
- 显示系统统计信息

### 2. 文件输出

```
memory/
├── AGENTS.md                          # 主记忆文件（自动更新）
├── rules/                             # 规则库
│   └── 小分子模板.md                  # 自动积累的规则
├── templates/                         # 模板库
│   └── 小分子模板_GLP报告.md          # 高质量 SOP 模板（评分>=4）
└── audit_log/                         # 审计日志
    └── audit_2024-03.jsonl            # 执行历史记录
```

### 输出文件说明

| 文件 | 内容 | 何时生成 |
|------|------|----------|
| `templates/*.md` | 通过审核的完整 SOP | 评分 >= 4 分 |
| `rules/*.md` | 提取的通用规则 | Curator 更新时 |
| `audit_log/*.jsonl` | 执行日志（JSON Lines） | 每次运行 |

## 🔄 工作流程

```
1. 加载记忆（AGENTS.md + rules/ + templates/）
   ↓
2. Writer 生成 SOP（复用历史知识）
   ↓
3. Simulator 盲测（不看标准答案）
   ↓
4. Reviewer 审核（对比标准答案，评分）
   ↓
5. 如果评分 < 3：
   - Reflector 诊断问题
   - Curator 更新规则库
   - 返回步骤 2（最多 5 次迭代）
   ↓
6. 保存结果到 memory/
```

## 📊 查看结果

### 查看生成的 SOP 模板
```bash
cat memory/templates/小分子模板_GLP报告.md
```

### 查看学习到的规则
```bash
cat memory/rules/小分子模板.md
```

### 查看执行历史
```bash
cat memory/audit_log/audit_2024-03.jsonl
```

## ⚙️ 配置说明

编辑 `config.py` 修改系统配置：

```python
SMART_MODEL = "claude-opus-4-6"      # 主模型（Writer/Reflector）
FAST_MODEL = "claude-3-5-haiku"      # 快速模型（Simulator/Reviewer）
MAX_ITERATIONS = 5                    # 最大迭代次数
```

## 🎯 核心特性

- ✅ 5 个专门化 Subagent（Writer/Simulator/Reviewer/Reflector/Curator）
- ✅ 三层记忆系统（Rules/Templates/AuditLog）
- ✅ 自动迭代改进（最多 5 次）
- ✅ 动态规则学习（Curator 自动更新规则）
- ✅ 质量追踪（审计日志记录所有执行）

## 📚 更多文档

- `OPTIMIZATION_SUMMARY.md` - 优化方案详解
- `MIGRATION_GUIDE.py` - 版本迁移对比
- `memory/AGENTS.md` - 系统记忆说明

## 🐛 故障排查

### 问题：API 调用失败
```bash
# 检查 .env 配置
cat .env

# 确认 API Key 有效
```

### 问题：找不到 deepagents 模块
```bash
# 重新安装依赖
pip install -r requirements.txt --upgrade
```

### 问题：输出文件未生成
- 检查 `memory/` 目录权限
- 确认评分 >= 4（只有高分 SOP 才保存到 templates/）
