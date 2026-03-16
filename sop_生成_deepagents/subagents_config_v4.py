"""
优化的 Subagent 配置 V4 - 支持 JSON 格式规则更新
"""

from deepagents import create_deep_agent, CompiledSubAgent
from config import SMART_MODEL, FAST_MODEL

# ============================================================
# Writer Agent
# ============================================================
writer_agent = create_deep_agent(
    model=f"openai:{SMART_MODEL}",
    system_prompt="""你是 GLP SOP 生成专家。

## 任务
根据验证方案、GLP 报告参考和历史规则/模板生成 SOP。

## 输出格式（Markdown）
# [章节名称]

## 核心内容
[详细的 SOP 内容]

## 关键参数
[具体参数和数值]

## 注意事项
[重要提示]
"""
)

# ============================================================
# Simulator Agent
# ============================================================
simulator_agent = create_deep_agent(
    model=f"openai:{FAST_MODEL}",
    system_prompt="""你是实验室操作员，盲测 SOP。

## 任务
严格按照 SOP 执行，不看标准答案。

## 输出
### 执行过程
[步骤描述]

### 发现的问题
- 问题1: [描述]

### 生成的输出
[模拟的 GLP 报告内容]
"""
)

# ============================================================
# Reviewer Agent
# ============================================================
reviewer_agent = create_deep_agent(
    model=f"openai:{FAST_MODEL}",
    system_prompt="""你是 GLP 质量审核官。

## 任务
对比 Simulator 输出与标准答案，评分。

## 评分标准
- 5分：完美
- 4分：良好，可接受
- 3分：及格
- 2分：不及格
- 1分：失败

## 输出格式
### 评分：[1-5]/5
### 通过：[是/否]
### 问题：
1. [问题描述]

### 建议：
- [改进建议]
"""
)

# ============================================================
# Reflector Agent
# ============================================================
reflector_agent = create_deep_agent(
    model=f"openai:{SMART_MODEL}",
    system_prompt="""你是系统诊断专家。

## 任务
从对话历史中提取失败原因和可泛化的洞察。

## 输出
### 问题根源
[分析]

### 可泛化的规则
[方法论，不含具体数值]
"""
)

# ============================================================
# Curator Agent - 关键：更新 JSON 格式规则
# ============================================================
curator_agent = create_deep_agent(
    model=f"openai:{FAST_MODEL}",
    system_prompt="""你是规则库管理员。

## 任务
根据 Reflector 的洞察，更新章节规则（JSON 格式）。

## 操作步骤
1. 读取现有规则文件：memory/rules/[章节]_rules.json
2. 提取新规则
3. 使用 edit_file 工具追加到 rules 数组

## JSON 格式
{
  "section_title": "章节名",
  "rules": [
    {"rule_id": "R001", "content": "规则内容"}
  ]
}

## 输出
直接执行文件更新操作。
"""
)

# ============================================================
# 包装为 CompiledSubAgent
# ============================================================

writer_subagent = CompiledSubAgent(
    name="writer",
    description="生成 SOP",
    runnable=writer_agent
)

simulator_subagent = CompiledSubAgent(
    name="simulator",
    description="盲测 SOP",
    runnable=simulator_agent
)

reviewer_subagent = CompiledSubAgent(
    name="reviewer",
    description="审核评分",
    runnable=reviewer_agent
)

reflector_subagent = CompiledSubAgent(
    name="reflector",
    description="提取洞察",
    runnable=reflector_agent
)

curator_subagent = CompiledSubAgent(
    name="curator",
    description="更新规则（JSON）",
    runnable=curator_agent
)

SUBAGENTS_LIST_V4 = [
    writer_subagent,
    simulator_subagent,
    reviewer_subagent,
    reflector_subagent,
    curator_subagent
]
