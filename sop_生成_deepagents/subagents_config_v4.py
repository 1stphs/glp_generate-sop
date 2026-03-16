"""
优化的 Subagent 配置 V4 - 支持 JSON 格式规则更新
"""

from deepagents import create_deep_agent, CompiledSubAgent
from config import SMART_MODEL, FAST_MODEL

# ============================================================
# 系统提示词定义
# ============================================================

WRITER_SYSTEM_PROMPT = """你是 GLP SOP 生成专家。

## 任务
根据验证方案、GLP 报告参考和历史规则/模板生成 SOP。

## 输出格式（Markdown）
# [章节名称]

## 核心内容
[详细的 SOP 内容]

## 关键参数
[具体参数和数值]

## 核心原则
[提取 3-5 条关键的操作原则或注意事项]

## 示例
[提供一个具体的 GLP 记录或操作示例]
"""

SIMULATOR_SYSTEM_PROMPT = """你是实验室操作员，盲测 SOP。

## 任务
严格按照 SOP 执行，不看标准答案。

## 输出
### 执行过程
[步骤描述]

### 发现的问题
- 问题1: [描述]

### 生成s的输出
[模拟的 GLP 报告内容]
"""

REVIEWER_SYSTEM_PROMPT = """你是 GLP 质量审核官。

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

REFLECTOR_SYSTEM_PROMPT = """你是系统诊断专家。

## 任务
从对话历史中提取失败原因和可泛化的洞察。

## 输出
### 问题根源
[分析]

### 可泛化的规则
[方法论，不含具体数值]
"""

CURATOR_SYSTEM_PROMPT = """你是规则库管理员。

## 任务
根据 Reflector 的洞察，更新或创建章节规则文件（JSON 格式）。

## 规则库路径
所有规则文件必须存储在: memory/rules/[章节名]_rules.json

## 操作逻辑
1. **检查与读取**：首先尝试使用 `read_file` 读取 `memory/rules/[章节名]_rules.json`。
2. **处理不存在的情况**：如果文件不存在，初始化一个新的 JSON 结构：
   {
     "section_title": "[内容中的章节名]",
     "rules": []
   }
3. **追加规则**：将 Reflector 提供的新规则提取出来，为每条规则生成一个新的 `rule_id`（如 R001, R002...），并追加到 `rules` 数组中。
4. **保存文件**：使用 `write_file` 将更新后的完整 JSON 内容覆盖写入原路径。

## JSON 结构示例
{
  "section_title": "主要仪器",
  "rules": [
    {"rule_id": "R001", "content": "必须记录仪器的唯一性标识（SN 号）。"},
    {"rule_id": "R002", "content": "天平使用前必须进行水平检查和校准。"}
  ]
}

## 限制
- 严禁输出空文件。
- 确保 JSON 格式严格有效。
- 必须使用 `write_file` 而不是 `edit_file` 来确保文件结构的完整性。
"""

# ============================================================
# Writer Agent
# ============================================================

writer_agent = create_deep_agent(
    model=f"openai:{SMART_MODEL}",
    system_prompt=WRITER_SYSTEM_PROMPT
)

# ============================================================
# Simulator Agent
# ============================================================
simulator_agent = create_deep_agent(
    model=f"openai:{FAST_MODEL}",
    system_prompt=SIMULATOR_SYSTEM_PROMPT
)

# ============================================================
# Reviewer Agent
# ============================================================
reviewer_agent = create_deep_agent(
    model=f"openai:{FAST_MODEL}",
    system_prompt=REVIEWER_SYSTEM_PROMPT
)

# ============================================================
# Reflector Agent
# ============================================================
reflector_agent = create_deep_agent(
    model=f"openai:{SMART_MODEL}",
    system_prompt=REFLECTOR_SYSTEM_PROMPT
)

# ============================================================
# Curator Agent
# ============================================================
curator_agent = create_deep_agent(
    model=f"openai:{FAST_MODEL}",
    system_prompt=CURATOR_SYSTEM_PROMPT
)

# ============================================================
# 包装为 SubAgent 配置字典 (不再使用 CompiledSubAgent 以便继承 Backend)
# ============================================================

writer_subagent = {
    "name": "writer",
    "description": "生成 SOP",
    "system_prompt": WRITER_SYSTEM_PROMPT,
    "model": f"openai:{SMART_MODEL}"
}

simulator_subagent = {
    "name": "simulator",
    "description": "盲测 SOP",
    "system_prompt": SIMULATOR_SYSTEM_PROMPT,
    "model": f"openai:{FAST_MODEL}"
}

reviewer_subagent = {
    "name": "reviewer",
    "description": "审核评分",
    "system_prompt": REVIEWER_SYSTEM_PROMPT,
    "model": f"openai:{FAST_MODEL}"
}

reflector_subagent = {
    "name": "reflector",
    "description": "提取洞察",
    "system_prompt": REFLECTOR_SYSTEM_PROMPT,
    "model": f"openai:{SMART_MODEL}"
}

curator_subagent = {
    "name": "curator",
    "description": "更新章节规则（JSON）",
    "system_prompt": CURATOR_SYSTEM_PROMPT,
    "model": f"openai:{FAST_MODEL}"
}
SUBAGENTS_LIST_V4 = [
    writer_subagent,
    simulator_subagent,
    reviewer_subagent,
    reflector_subagent,
    curator_subagent
]
