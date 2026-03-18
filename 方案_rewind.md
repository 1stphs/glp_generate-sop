# SOP 自动化生成方案

## 1. 目标

本方案旨在通过多智能体（DeepAgent）系统，实现 SOP（Standard Operating Procedure）的自动生成与质量控制。主要目标包括：

- 对输入内容进行复杂度评估，选择合适的生成流程（workflow）。  
- 支持多种章节类型（简单、标准、复杂）对应不同生成与校验路径。  
- 结合 Simulator 与 Reviewer Agent 对生成结果进行验证与审查。  
- 支持规则更新和质量提升，可迭代改进 SOP 输出。

---

## 2. 系统架构

### 2.1 主 Agent：SOP Master Agent

**职责**：

- 接收映射完毕的输入内容（实验类型、初步规则、模板等）。
- 分析内容，评估任务复杂度（简单、标准、复杂）。
- 根据复杂度选择对应的 workflow。
- 动态调用辅助 Agent（Writer、Simulator、Reviewer）执行生成与校验。

**输入**：

- 内容信息（实验 type、章节信息、规则文本等）  
- 历史 SOP / 经验 prompt（可选）  

**输出**：

- 指定 workflow 路径及生成任务列表  
- 复杂度评估结果

---

### 2.2 Writer Agent

**职责**：

- 根据主 Agent 指定的章节类型（简单、标准、复杂）生成初稿 SOP。
- 简单章节可直接生成，复杂章节需经过 Reviewer 审核后再修改。
- 输出结构化 SOP 文档。

**输入**：

- 章节类型（简单 / 标准 / 复杂）  
- 规则 / Skills / 模板信息  

**输出**：

- 生成的 SOP 初稿（Markdown 或结构化文本）

---

### 2.3 Simulator Agent

**职责**：

- 对生成的 SOP 进行模拟执行（黑箱测试）。  
- 评估 SOP 的可执行性、合规性、格式正确性等指标。  

**输入**：

- Writer Agent 输出的 SOP 初稿  

**输出**：

- 模拟结果（成功 / 失败 / 错误日志）  
- 可选的自动改进建议

---

### 2.4 Reviewer Agent

**职责**：

- 对 Writer 或 Simulator 的结果进行审查和评价。  
- 核对 SOP 与规则的一致性，发现潜在错误或遗漏。  
- 输出修改建议供 Writer Agent 再次生成。

**输入**：

- SOP 初稿 / 模拟结果  
- 规则、模板、评分标准（Skills）  

**输出**：

- 审核结果（PASS / FAIL）  
- 修改意见 / 改进建议

---

### 2.5 Format Verify（简单章节路径）

**职责**：

- 对简单章节生成结果进行格式校验。  
- 确保 SOP 输出符合模板要求。  

**输入**：

- Writer Agent 输出的 SOP  

**输出**：

- 格式验证结果（PASS / FAIL）  

---

## 3. Workflow 分支

根据复杂度评估，SOP Master Agent 调度不同路径：

1. **简单章节**  

- Writer Agent → Format Verify → END

2. **标准章节**  

- Writer Agent → Simulator Agent → Reviewer Agent → PASS → END

3. **复杂章节**  

- Writer Agent → Simulator Agent → Reviewer Agent → FAIL → 重新分析 / 调整策略 → Writer Agent → …（迭代）

- 每轮迭代结束，可通过 Curator 或 Skills 更新规则，生成新的评价标准（Rubric）用于下一轮。

---

## 4. 关键特性

- **动态 workflow**：根据内容复杂度选择不同路径。  
- **多轮迭代能力**：复杂章节可多轮优化，直至 PASS。  
- **结构化输出**：所有 SOP 生成、审核、模拟日志都可序列化存档。  
- **Skills 驱动**：评价标准、规则、指标可以独立维护，便于复用与迭代。  
- **可扩展性**：可动态加入辅助 Agent（如额外分析、日志采集、模板管理等）。

---

## 5. 输入 / 输出概览

| 模块 | 输入 | 输出 |
|------|------|------|
| SOP Master Agent | 映射完成的内容 | Workflow 路径、复杂度评估 |
| Writer Agent | 章节类型、规则、模板 | SOP 初稿 |
| Simulator Agent | SOP 初稿 | 模拟执行结果、错误日志 |
| Reviewer Agent | 模拟结果、SOP | PASS/FAIL、修改建议 |
| Format Verify | 简单章节 SOP | 格式验证结果 |

---

## 6. 可选迭代与优化

- 结合 **Curator Agent** 或 **Evaluator Skill** 对每轮 SOP 输出打分并生成新 Rubric  
- 自动更新规则库，保证 SOP 输出质量随时间提升  
- Hybrid 模式：保留固定 workflow 的稳定性，同时利用 DeepAgent 提供增量智能