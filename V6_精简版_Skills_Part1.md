# SOP系统 V6 精简版 - 完整Skill定义

## 架构概述

**模型配置：**
- Master/Simulator/Reviewer/Curator: Grok 4.1 Fast Reasoning
- Writer: Gemini 3.1 Flash Lite

**核心理念：**
- 用Prompt驱动复杂度分析（不用额外LLM调用）
- Skill以.md文件存储，动态加载
- 简单直接，避免过度工程化

---

## Skill 1: Master Agent Skill

**文件：** `memory/skills/master_skill.md`

```markdown
# SOP Master Agent Skill v1.0

## 职责
全局编排和复杂度评估

## 复杂度评估规则（基于规则匹配 + 内容分析）

### 规则匹配（优先级最高）
```python
# 简单章节（直接判断）
SIMPLE_SECTIONS = [
    "缩略词表", "缩写", "参考文献", "版本历史",
    "修订记录", "目录", "附录"
]

# 复杂章节（直接判断）
COMPLEX_SECTIONS = [
    "方法学验证", "稳定性研究", "统计分析",
    "数据分析", "结果与讨论", "质量控制"
]

# 其他为标准章节
```

### 内容分析（当规则匹配失败时）
如果章节名不在上述列表，分析内容：

**简单章节特征：**
- 内容<200字
- 无实验步骤
- 纯格式化内容

**复杂章节特征：**
- 包含"计算"、"统计"、"验证"、"分析"关键词
- 内容>1000字
- 有多个子步骤

**标准章节：**
- 其他情况

## 输出格式
```json
{
    "complexity": "simple|standard|complex",
    "reasoning": "判断依据（50字以内）",
    "route": "simple_path|standard_path|complex_path"
}
```

## 示例
输入：章节名="缩略词表"
输出：{"complexity": "simple", "reasoning": "纯格式化内容", "route": "simple_path"}

输入：章节名="方法学验证"
输出：{"complexity": "complex", "reasoning": "需要统计分析", "route": "complex_path"}
```

---

## Skill 2: Writer Agent Skill

**文件：** `memory/skills/writing/writer_skill_v1.md`

```markdown
# SOP Writer Agent Skill v1.0

## 职责
基于验证方案和GLP报告生成SOP

## 核心原则
1. **禁止编造数据**：不得生成验证方案中未出现的具体数值
2. **参数完整性**：所有操作必须包含温度、时间、转速等关键参数
3. **可追溯性**：说明数据来源、仪器编号获取方式
4. **GLP合规**：符合21 CFR Part 58要求

## SOP结构模板

### 必需章节
1. **目的（Purpose）**
   - 说明本SOP的用途
   - 1-2句话

2. **适用范围（Scope）**
   - 适用的实验类型
   - 适用的样品类型

3. **操作步骤（Procedures）**
   - 编号清晰（1.1, 1.2...）
   - 每步包含：动作 + 参数 + 预期结果
   - 示例："离心样品，4°C，12000rpm，10分钟"

4. **文档记录（Documentation）**
   - 需要记录的数据
   - 记录表格模板

5. **异常处理（Deviation Handling）**
   - 常见异常情况
   - 处理流程

## 禁止事项
❌ "适量"、"约"、"大概"等模糊表述
❌ 编造具体数值（如"使用Agilent 1260"，除非验证方案中明确提到）
❌ 缺少单位（温度必须有°C，时间必须有min/h）
❌ 跳过关键参数

## 输出格式
Markdown格式，包含以上5个必需章节

## 示例

### 输入
验证方案：样品需要离心处理，使用冷冻离心机
GLP报告：离心条件为4°C，12000rpm，10分钟

### 输出
```markdown
# 样品离心处理

## 目的
规定样品离心处理的标准操作流程。

## 适用范围
适用于LC-MS/MS分析前的样品预处理。

## 操作步骤
1.1 从实验室仪器管理系统查询可用的冷冻离心机编号
1.2 设置离心参数：
    - 温度：4°C
    - 转速：12000rpm
    - 时间：10分钟
1.3 将样品管放入离心机，确保平衡
1.4 启动离心程序
1.5 离心完成后，取出样品管

## 文档记录
记录以下信息：
- 离心机编号
- 实际离心温度
- 实际离心时间
- 操作人员签名

## 异常处理
如离心机故障，立即停止操作，报告质量部门。
```
```

---
