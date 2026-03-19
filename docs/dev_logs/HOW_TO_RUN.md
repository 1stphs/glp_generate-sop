# 如何运行 SOP 生成系统 V6

## 📋 前提条件

1. **API Keys**: 需要配置 Grok 和 Gemini API
2. **Python 环境**: Python 3.8+
3. **依赖包**: 需要安装 LangGraph 和其他依赖

## 🚀 快速开始

### 步骤 1: 安装依赖

```bash
cd sop_deeplang
pip install -r requirements.txt
```

### 步骤 2: 配置 API Keys

```bash
cp .env.example .env
```

编辑 `.env` 文件：

```env
# OpenAI-compatible API (用于 Grok 4.1)
OPENAI_API_KEY=your_grok_api_key_here
OPENAI_BASE_URL=https://api.openai.com/v1

# Google Gemini API
GEMINI_API_KEY=your_gemini_api_key_here
```

### 步骤 3: 运行系统

```bash
python main.py
```

## 📊 数据说明

系统使用真实的验证方案和 GLP 报告数据：

- **验证方案**: `/Users/pangshasha/Documents/github/glp_generate-sop/mockData/workflow-b/protocol_content.json`
- **GLP 报告**: `/Users/pangshasha/Documents/github/glp_generate-sop/mockData/workflow-b/report_content.json`

系统会自动：
1. 加载第一条数据（`protocol_content1` 和 `report_content1`）
2. 解析前 5 个主要章节：
   - 引言
   - 材料和方法
   - 方法学验证内容和接受标准
   - 数据处理
   - 归档

## 📁 输出文件

运行后，会在以下位置生成文件：

### SOP 模板
```
memory/sop_templates/
├── 引言_20260317_123456.md
├── 引言_20260317_123456.json
├── 材料和方法_20260317_123456.md
└── ...
```

### 审计日志
```
memory/audit_logs/
└── audit_2026-03-17.jsonl
```

### Skill 版本（如果有更新）
```
memory/skills/writing/
├── writer_skill_v1.0.md
└── writer_skill_v1.1.md  (Curator 更新后)
```

## 🔍 预期输出

控制台会显示：

```
======================================================================
🚀 SOP 生成系统 V6 - DeepLang (使用真实数据)
======================================================================

📂 加载真实数据...
   ✓ 验证方案加载完成 (10589 字符)
   ✓ GLP报告加载完成 (39426 字符)

📋 解析章节结构...
   ✓ 识别到 5 个章节:
      1. 引言
      2. 材料和方法
      3. 方法学验证内容和接受标准
      4. 数据处理
      5. 归档

======================================================================
📋 开始处理章节: 引言
======================================================================

🎯 [引言] 复杂度: standard | 路由: standard_path | 原因: 包含操作步骤
📝 [引言] Writer生成完成 (迭代1)
🔬 [引言] Simulator盲测: 可执行
🔍 [引言] Reviewer评分: 4/5 ✓通过
💾 [引言] 模板已保存 (评分: 4.0)
✅ [引言] 执行完成 (迭代1次, 最终评分: 4.0)

...

======================================================================
📊 处理汇总
======================================================================
✓ 成功: 3/5
✗ 失败: 2/5
```

## ⚙️ 配置说明

可以修改 `config.py` 来调整系统行为：

```python
# 最大迭代次数（复杂章节）
MAX_ITERATIONS = 3

# 简单章节列表
SIMPLE_SECTIONS = ["缩略词表", "缩写", "参考文献", ...]

# 复杂章节列表
COMPLEX_SECTIONS = ["方法学验证", "稳定性研究", "统计分析", ...]
```

## 🐛 故障排查

### 问题：找不到 langgraph 模块

```bash
# 重新安装依赖
pip install -r requirements.txt --upgrade
```

### 问题：API 调用失败

```bash
# 检查 .env 配置
cat .env

# 测试 API Key
python3 -c "import os; print(os.getenv('OPENAI_API_KEY'))"
```

### 问题：数据加载失败

```bash
# 检查数据文件是否存在
ls -la /Users/pangshasha/Documents/github/glp_generate-sop/mockData/workflow-b/
```

## 📝 章节处理说明

系统会对每个章节执行以下流程：

1. **复杂度评估**（Master 节点）：
   - 简单章节 → Writer → Format Verify → END
   - 标准章节 → Writer → Simulator → Reviewer → END
   - 复杂章节 → Writer → Simulator → Reviewer → （如果失败）→ Analyzer → Curator → Writer（循环）

2. **SOP 生成**（Writer 节点）：
   - 使用 Gemini 3.1 Flash Lite 生成 SOP
   - 基于 Writer Skill 的指导原则

3. **盲测**（Simulator 节点）：
   - 使用 Grok 4.1 进行盲测
   - 识别缺失或模糊的信息

4. **质量审核**（Reviewer 节点）：
   - 使用 Grok 4.1 进行严格审核
   - 评分 1-5 分，4 分及以上为通过

5. **失败分析**（Analyzer 节点，仅失败时）：
   - 使用 Grok 4.1 分析根本原因
   - 提出具体的修复策略

6. **Skill 更新**（Curator 节点，仅失败时）：
   - 使用 Grok 4.1 更新 Writer Skill
   - 生成新版本的 Skill 文件

## 📊 成本估算

单章节成本（标准路径）：
- Master（规则匹配）：$0
- Writer（Gemini）：约 $0.001
- Simulator（Grok）：约 $0.002
- Reviewer（Grok）：约 $0.002
- **总计**：约 $0.005

5 个章节总成本：约 $0.025

## 📞 支持

如有问题，请检查：
1. API Keys 是否正确配置
2. 网络连接是否正常
3. 数据文件是否存在
4. 依赖包是否正确安装
