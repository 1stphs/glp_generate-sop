# DeepAgent - Natural Language Driven Multi-Agent System

**基于自然语言驱动的DeepAgent架构，用于自动化SOP生成和经验管理**

## 📋 目录

- [架构概述](#架构概述)
- [核心特性](#核心特性)
- [快速开始](#快速开始)
- [架构详解](#架构详解)
  - [Agents层](#agents层)
  - [ACE子系统](#ace子系统)
  - [Playbook](#playbook)
  - [测试数据](#测试数据)
  - [工作流程](#工作流程)
- [开发指南](#开发指南)

## 架构概述

本项目采用**完全自然语言驱动**的DeepAgent架构，通过Master Agent自主决策，协调多个子Agent完成复杂任务。

### 核心设计原则

1. **自然语言驱动**：所有决策基于对任务的自然语言理解，不预设固定workflow
2. **自主规划**：Master Agent根据任务描述动态规划执行步骤
3. **两次调用模式**：
   - 第一次：Master Agent → trajectory（完整执行过程）
   - 第二次：trajectory → insights（经验提取）→ playbook（经验库更新）
4. **经验持续学习**：通过ACE子系统持续积累和优化经验
5. **ACE三文件结构**：审计、Rules、SOP模板完全分离，数据流清晰

### 项目结构

\`\`\`
glp_generate-sop/
├── agents/                           # 🧠 核心Agents层
│   ├── master_agent.py               # 🔑 Master Agent（大脑）
│   ├── insight_agent.py             # 📊 Insight Agent（经验提取）
│   ├── playbook_agent.py            # 📚 Playbook Agent（经验库）
│   └── utils/                      # 🔧 工具模块
│       ├── prompt_template.py         # Prompt模板管理
│       └── memory.py                 # 共享记忆管理
│
├── ace/                              # 🔄 ACE子系统
│   ├── agents/                       # 三个核心Agent
│   │   ├── __init__.py
│   │   ├── sop_writer.py              # SOP Writer
│   │   ├── sop_simulator.py           # SOP Simulator
│   │   └── sop_reviewer.py             # SOP Reviewer
│   │
│   ├── audit_log.py                  # (1) 审计：时间、版本、sop、id、type、curation、metrics、quality_assessment
│   ├── rules_manager.py               # (2) Rules：sop_type、分章节的rules、rules_id
│   ├── sop_templates.py              # (3) SOP模板：一种type对应一个模板，sop分章节存储
│   ├── reflector.py                   # 反思器（质量评估）
│   └── curator.py                    # 策展人（规则提炼）
│
├── playbook/                          # 💾 持久化经验库
│   └── README.md                     # 数据结构说明
│
├── data/                             # 📊 测试数据目录
│   └── README.md                    # 数据格式说明
│
└── tests/                             # 🧪 测试入口
    ├── test_master_agent.py         # Master Agent自主决策测试
    ├── test_ace_flow.py              # ACE流程测试
    └── README.md                     # 测试说明
\`\`\`

## 核心特性

### 1. 完全自然语言驱动

**Master Agent**的关键特性：
- ✅ 理解自然语言任务
- ✅ 自主规划和拆解任务
- ✅ 动态选择要调用的子Agent
- ✅ 不预设任何固定workflow
- ✅ 输出思考过程（reasoning）和决策理由

### 2. 两次调用模式

**第一次调用**：
\`\`\`
Master Agent → 生成trajectory
\`\`\`

**第二次调用**：
\`\`\`
trajectory → Insight Agent → insights
            ↓
            Playbook Agent → 更新playbook
\`\`\`

### 3. ACE子系统三文件结构

| 文件 | 字段 | 说明 |
|------|------|------|
| `audit_log.py` | timestamp, version, sop, sop_id, sop_type, curation, metrics, quality_assessment | 完整审计日志 |
| `rules_manager.py` | sop_type, chapter_id, rules_id, content, tags, metrics (helpful/harmful/usage) | 按类型和章节组织规则 |
| `sop_templates.py` | template (type→template), chapter_sops (chapter→sops by type) | 模板+分章节SOP |

## 快速开始

### 环境要求

\`\`\`bash
# Python版本
python --version  # 需要3.10+

# 安装依赖
pip install -r requirements.txt
\`\`\`

### 运行测试

\`\`\`bash
# 测试Master Agent
python tests/test_master_agent.py

# 测试ACE流程
python tests/test_ace_flow.py
\`\`\`

### 预期输出

测试运行后，会在以下目录生成文件：
\`\`\`
test_output/
├── audit_log/audit_log.json       # 完整审计日志
├── rules/rules.json              # 规则管理
├── sop_templates/sop_templates.json # SOP模板
└── playbook/playbooks.json       # 持久化经验库
\`\`\`

## 架构详解

### Agents层

#### Master Agent (`agents/master_agent.py`)

**职责**：系统核心大脑，完全自主决策

**关键特性**：
- ✅ 理解自然语言任务
- ✅ 自主规划和拆解任务
- ✅ 动态选择要调用的子Agent
- ✅ 协调整体流程，处理异常
- ✅ 收集结果并返回给用户

**Prompt设计重点**：
- 强调"不要预设workflow"
- 强制输出"思考过程"
- 强制说明"决策理由"
- 只列出可用子Agent，不规定调用顺序

#### Insight Agent (`agents/insight_agent.py`)

**职责**：从执行轨迹中提取经验教训

**关键特性**：
- ✅ 证据驱动提取
- ✅ 标注适用场景
- ✅ 区分经验类型（rule_success, rule_failure, problem_solution, pattern_discovery）

#### Playbook Agent (`agents/playbook_agent.py`)

**职责**：管理持久化经验库

**关键特性**：
- ✅ LLM驱动的规则匹配（非简单关键词搜索）
- ✅ LLM驱动的playbook更新（智能去重和清理）
- ✅ 质量维护（删除无效规则）

#### SOP Generation Agents

从 \`\`\`glp_langgraph_local\`\`\` 移植的三个核心Agent：

##### SOPWriter (`ace/agents/sop_writer.py`)
**职责**：生成标准化SOP
**功能**：
- 根据章节内容生成SOP
- 输出固定三段结构（核心规则、通用模板、示例）
- 支持三种SOP类型：simple_insert, rule_template, complex_composite

**输出格式**：
\`\`\`markdown
## 一、核心填写规则
1. 规则1
2. 规则2

## 二、通用模板
[模板内容]

## 三、示例
[示例内容]
\`\`\`

##### SOPSimulator (`ace/agents/sop_simulator.py`)
**职责**：模拟执行SOP
**功能**：
- 仅根据original_content和current_sop模拟执行
- 防止作弊（不读取target_generate_content）
- 输出模拟执行结果

**重要约束**：严格只使用original_content作为输入

**输出格式**：模拟报告内容（匹配SOP模板格式）

##### SOPReviewer (`ace/agents/sop_reviewer.py`)
**职责**：三方质量审核
**功能**：
- 对比三个输入：
  - target_generate_content（实际报告）
  - current_sop（生成的SOP）
  - simulated_generate_content（模拟执行结果）
- 审核口径：只审核"结构/形式/模板一致性"
- 不因具体数值差异判定失败

**输出**：is_passed + feedback

**审核范围**：限定为结构、形式和模板一致性，不审核数值准确性

### ACE子系统

#### AuditLog (`ace/audit_log.py`)
记录所有执行细节

#### RulesManager (`ace/rules_manager.py`)
按SOP类型和章节组织规则

#### SOPTemplates (`ace/sop_templates.py`)
管理SOP模板和章节SOP

#### Reflector (`ace/reflector.py`)
分析SOP质量

#### Curator (`ace/curator.py`)
从成功执行中提取和提炼规则

## 数据流向

\`\`\`
原始数据 (protocol + report)
    ↓
SOP Writer
    ↓
current_sop
    ↓
SOP Simulator
    ↓
simulated_generate_content
    ↓
SOP Reviewer (三方对比)
    ↓
is_passed + feedback
    ↓
Master Agent 决定是否继续迭代
\`\`\`

## 下一步

- [ ] 实现LLM客户端集成
- [ ] 添加JSON解析（所有agent的响应解析）
- [ ] 创建完整集成测试
- [ ] 连接AuditLog、RulesManager进行持久化
- [ ] 性能优化和缓存

## 相关文档

- [Agents层详细说明](agents/README.md)
- [ACE子系统详细说明](ace/README.md)
- [Playbook数据结构](playbook/README.md)
- [测试数据格式](data/README.md)
- [测试入口说明](tests/README.md)

## 许可证

本项目采用MIT许可证。
