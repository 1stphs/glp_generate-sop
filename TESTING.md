# 快速测试指南

## 第 0 步：验证模块导入（不需要 API Key）

先运行导入测试，确保所有模块可以正确导入：

```bash
cd /Users/pangshasha/Documents/github/glp_generate-sop
python test_imports.py
```

**期望输出**：
```
✓ Config module imported
✓ Base Agent imported
✓ Writer Agent imported
✓ Simulator Agent imported
✓ Reviewer Agent imported
✓ Reflector Agent imported
✓ Curator Agent imported
✓ Main Agent imported

✓ All imports successful!
```

## 第 1 步：配置 API Key

你需要在项目根目录创建 `.env` 文件：

```bash
cd /Users/pangshasha/Documents/github/glp_generate-sop
cp .env.example .env
```

然后编辑 `.env` 文件，填入你的 API key：

```bash
OPENVIKING_LLM_API_KEY=你的API密钥
OPENVIKING_LLM_MODEL=gpt-4o
OPENVIKING_LLM_API_BASE=https://aihubmix.com/v1
```

## 第 2 步：运行功能测试

### 测试 1: Writer Agent 单元测试（推荐先运行这个）

这个测试只测试 Writer Agent，比较简单快速：

```bash
python deepagent_sop/tests/test_writer_agent.py
```

**测试内容**：
- 从 `data/workflow-b/` 加载第一份数据
- 使用 Writer Agent 为"验证试验名称"章节生成 SOP
- 测试基本的 SOP 生成流程

**期望输出**：
```
✓ API key found (provider: openai)
✓ Test data loaded from workflow-b
Section: 验证试验名称
Protocol: 3000 chars
Report: 3000 chars
✓ Writer Agent initialized

Generating SOP...
--------------------------------------------------------------------------------
SUCCESS!
SOP Type: rule_template
Core Rules:
  1. [提取的规则]
  2. ...
Template (first 200 chars):
  [模板内容]
```

### 测试 2: 完整集成测试（测试 Main Agent）

这个测试运行完整的 Main Agent 流程：

```bash
python deepagent_sop/tests/test_integration.py
```

**测试内容**：
- 从 `data/workflow-b/` 加载测试数据
- 使用 Main Agent 自主规划和执行
- 测试完整的智能体协作流程

**期望输出**：
- 任务理解
- 执行计划
- 最终结果
- Trajectory 记录

## 常见问题

### "API key not found"
确保你已经创建了 `.env` 文件并填入了 API key。

### "Import error"
确保在项目根目录下运行：
```bash
cd /Users/pangshasha/Documents/github/glp_generate-sop
python test_imports.py
```

### 超时错误
如果 LLM 调用超时，可以在 `.env` 中增加超时时间：
```bash
DEEPAGENT_LLM_TIMEOUT=120.0
```

## 测试数据说明

测试数据位于 `data/workflow-b/`：
- `protocol_content.json`: 两份验证方案
- `report_content.json`: 两份验证报告
- `structure.json`: 报告章节结构

当前测试使用第一份数据（`protocol_content1`、`report_content1`），测试章节为"验证试验名称"。

## 测试命令汇总

```bash
# 1. 导入测试（快速，无 API Key 需要）
python test_imports.py

# 2. 设置检查
python check_setup.py

# 3. Writer Agent 测试（需要 API Key）
python deepagent_sop/tests/test_writer_agent.py

# 4. 集成测试（需要 API Key）
python deepagent_sop/tests/test_integration.py
```
