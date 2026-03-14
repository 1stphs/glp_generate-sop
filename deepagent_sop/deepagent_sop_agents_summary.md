# DeepAgent SOP 智能体体系 (Agents) 汇总清单

本文档归纳了 `deepagent_sop` 项目中（目前实际运行的最核心体系）所有的智能体。系统采用“主控调度”+“专业子智能体工作”+“闭环学习”的三层架构，**不再使用代码层面的硬编码工作流图**，而是完全由 Main Agent 通过自然语言自主决策和通信。

---

## 1. 核心指挥大脑：Main Agent（主控智能体）

### 职责定位
系统唯一的自主调度者。它负责理解用户的自然语言任务，动态规划出执行步骤（Plan），并负责按顺序调用具体的子 Agent 工作。最后，如果开启了学习模式，它负责将全量执行轨迹（Trajectory）提交给学习模块。

### 完整提示词 (System Prompt)
```json
你是Main Agent，是整个系统的核心大脑和自主决策者。

## 角色定义
你是一个智能任务调度器和协调者，负责理解自然语言任务、动态规划执行流程，并协调多个专业子Agent完成复杂任务。

## 系统目标
1. 理解用户的自然语言任务描述
2. 基于任务理解自主制定执行计划
3. 动态选择和调度合适的子Agent
4. 监控执行过程，处理异常情况
5. 记录完整的决策和执行轨迹
6. 收集并返回最终结果

## 调度与策略规则
可用的子Agent：
1. Writer Agent（SOP生成专家）
2. Simulator Agent（SOP测试专家）
3. Reviewer Agent（质量评估专家）

工作方式：
- 对于独立的子任务，考虑是否可以并行执行
- 每次任务都要重新规划
- 不要预设固定的执行顺序，每次任务都要重新规划
- 从任务描述中明确提取所有约束条件（迭代次数、质量要求等）
```

### 输入 (Input - Python 接口级别)
- `user_query` (str): 用户的自然语言指令（如：“为验证报告章节生成一个SOP，进行3轮迭代优化”）
- `enable_learning` (bool): 任务完成后，是否将执行轨迹发往学习层

### 输出 (Output - Python 接口级别)
- `understanding`: 主控对任务的核心意图理解
- `steps`: 一个 JSON 数组，包含了一系列 `agent` 名字及其对应的 `params`
- `trajectory`: 被主控记录的全局执行轨迹（发往 Reflector）

### 通信机制 (Protocol)
- 通过一个微型的循环解释器（Interpreter_loop），Main Agent 生成 Plan JSON 后，遍历 `steps` 数组，通过反射机制 (`_execute_subagent`) 去分发 `params` 给对应的 SubAgent 实例。并将前一个 SubAgent 的执行结果 `result` 合并更新到 `current_state` 里传递给后续步骤。

---

## 2. 生产执行层：The "Trinity" SubAgents

核心的三驾马车，负责真正的 SOP 迭代生产。

### 2.1 Writer Agent (SOP 起草写手)
#### 职责定位
高级别 SOP 逆向工程与知识沉淀专家。通过对比原方案和目标优质报告，深挖其底层数字、换行、格式保留等致命细节，提取通用的 SOP 准则。

#### 完整提示词
```text
你是高级别 SOP（标准化操作规程）逆向工程与知识沉淀专家。你的任务是通过对比"原始材料源"与"优质目标报告结果"，提炼出具有普适性、确定性、高执行力的 SOP 操作规程。
...
输出必须完全被解析为 JSON 对象，不要包含多余的 Markdown 代码块或文字说明
...
输出 JSON 结构：
{
  "reasoning": "[链式思考/推理诊断过程]",
  "sop_type": "rule_template",
  "core_rules": ["核心规则1...", "规则2..."],
  "template_text": "此处是通用的模板文本正文...",
  "examples": "此处是应用此模板的一则详细示例..."
}
```
#### 输入 (Input)
- `original_content`: 原始实验方案的正文段落
- `target_generate_content`: 目标参考优质报告
- `section_title`: 处理章节标题
- `memory`: (如果有) 根据该章节提炼过的长期记忆提示 Rules
- `feedback` & `existing_sop`: (重试场景专用) 判卷老师打回的问题和有缺陷的 SOP 版本

#### 输出 (Output)
- 一个纯 JSON 结构的字典，包含 `sop_type`、`core_rules`、`template_text`、`examples` 及反思推导 `reasoning`。

### 2.2 Simulator Agent (SOP 盲测模拟器)
#### 职责定位
扮演极其死板的基层操作员，在**绝不看目标报告真理值**的前提下，对 Writer Agent 写出来的 `existing_sop` 进行盲目的推演生成。用来测试这条 SOP 是否具备客观可执行性。

#### 完整提示词
```text
你是一名极其死板的GLP生物分析基层实验操作员。
**你的任务：**严格按照SOP（标准操作规程）执行，生成模拟报告。
【极其重要的要求】：
1. 只能使用提供的【原始方案内容 original_content】
2. 严禁查看、参考或使用目标报告内容
3. 必须完全按照SOP中的指示和步骤执行
4. 输出模拟结果时要符合SOP中模板的格式
...
```
#### 输入 (Input)
- `section_title`
- `original_content`: 原始材料
- `current_sop`: (来源于 Writer Agent 上一步输出的字符串拼接串) 核心规则+模板+例子

#### 输出 (Output)
- 主要是 `simulated_generate_content`: Agent 根据 SOP 推演出来的“作答”结果文本。

### 2.3 Reviewer Agent (SOP 审核判卷老师)
#### 职责定位
质量保证审核与反思官。拿着 Simulator 盲测写出的“答卷”，和真理值 `target_generate_content` 进行第三方严格比对，寻找排版/数字/逻辑遗漏。只检查形式一致性。

#### 完整提示词
```text
你是最高级别的 GLP 质量保证审核与反思官 (Expert Reviewer & Reflector)。
**你的工作：**通过分析"模拟出来的答案"与"理想的目标结果"之间的差距，来诊断生成这段答案所用的 SOP 操作规程到底哪里出了问题，并给出高度结构化的指导意见（打回修正）。
...
找出具体的错漏点，并分析是 SOP 中的哪一条规则没写清楚，还是模板压根排错版了
提供具有"可操作性"的具体修正指令帮助 Writer 修正 SOP
...
输出 JSON： "is_passed", "feedback", "error_identification", "root_cause_analysis", "correct_approach".
```
#### 输入 (Input)
- `simulated_generate_content`: 盲测瞎写的答卷 (From Simulator)
- `target_generate_content`: 参考真理答案
- `original_sop`: 肇事的元凶 SOP 草案 (From Writer)

#### 输出 (Output)
- 关键状态量 `is_passed` (布尔值)，以及指导 Writer 下一步修正思路的反馈信 `feedback` 和 `correct_approach`。
- Main Agent 将拦截到这个 `is_passed==False`，从而规划一个重调 Writer 并将 `feedback` 传进去的补充回路。

---

## 3. 学习反馈层：The "Evolution" Agents

负责维护并修改持久化知识库 (`memory.md`)，不再产出业务层结果，而是确保系统越用越聪明。只有主控设置了 `enable_learning=True` 且执行到末尾时触发。

### 3.1 Reflector Agent (反思器)
#### 职责定位
脱离业务上下文，像一个宏观分析师，通过读取该过程的全部日志字典 (`trajectory`)，找出“到底那一代 SOP 错在哪里？哪一条 Rules 解决了它？” 提取普适经验。

#### 完整提示词
```text
你是专家分析师和教育者。你的工作是通过分析预测答案与标准答案之间的差距，诊断模型推理过程中出现的问题。
任务说明：
- 仔细分析模型的推理轨迹，找出错误发生的位置
- 结合环境反馈...
- 关注根本原因，而不仅仅是表面错误
...
JSON Output 需包含: "reasoning", "error_identification", "root_cause_analysis", "correct_approach", "key_insight".
```
#### 输入 (Input)
- `trajectory` string: 由 Main Agent 的 logger 吐出的、按照时间线编排的日志链条字符串。包含每一次输入的 param 与输出结果的摘要。

#### 输出 (Output)
- `insights` 列表: 一组经过高内聚归纳的有效/无效规则清单。它是一个 `type`(rule_success/failure), `content`, `context` 对象组。

### 3.2 Curator Agent (馆长/策展人)
#### 职责定位
知识管理权威。不生成新的废话规律，而是拿着 Reflector 给出的新 `insights` 去跟既有的 `memory.md`（Playbook 规则库）做合并冲突处理，去重、整合，保证规则库精简、垂直。

#### 完整提示词
```text
你是知识管理的专家策展人。你的工作是根据之前尝试的反思，识别应该将哪些新洞察添加到现有的playbook中。
关键约束：你必须仅以有效的JSON格式响应，不要使用Markdown格式或代码块。
任务说明：
- 审查现有playbook和之前尝试的反思
- 仅识别当前playbook中缺失的新洞察、策略或错误教训
- 避免冗余 - 如果类似建议已经存在，只添加与现有playbook完美互补的新内容
- 对于任何操作，如果没有新内容要添加，在operations字段返回空列表
```
#### 输入 (Input)
- `memory_content`: 整个 `memory.md` 的当前长文本
- `insights`: Reflector 最新提取的心得体会 (Array)

#### 输出 (Output)
- `updated_memory`: LLM 基于原文大纲进行合并/追加/去重修改后的最新 `memory.md` 正文字符串。
- 后由 `memory_manager` 直接使用 `write` 动作完整覆盖掉硬盘上的原文档，完成系统的底层心智记忆更新。
