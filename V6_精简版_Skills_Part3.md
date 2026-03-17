# SOP系统 V6 精简版 - Skills Part3

## Skill 5: Failure Analyzer Skill

**文件：** `memory/skills/analysis/failure_analyzer_skill_v1.md`

```markdown
# Failure Analyzer Skill v1.0

## 职责
分析SOP失败的根本原因

## 根因分类

### 1. missing_info（缺失信息）
关键参数或信息未提供

### 2. unclear_logic（逻辑不清）
步骤顺序混乱或逻辑跳跃

### 3. ambiguous_terms（模糊表述）
使用"适量"、"约"等不精确词汇

### 4. compliance_gap（合规性不足）
缺少GLP要求的追溯性或记录要求

## 分析流程
1. 查看Reviewer反馈
2. 识别主要问题类型
3. 提出具体改进策略

## 输出格式
```json
{
    "root_cause": "missing_info|unclear_logic|ambiguous_terms|compliance_gap",
    "detail": "具体说明（100字内）",
    "fix_strategy": "改进策略（具体可执行）"
}
```

## 示例

### 输入
Reviewer反馈：步骤1.1未说明离心温度和转速

### 输出
```json
{
    "root_cause": "missing_info",
    "detail": "操作步骤缺少关键参数（温度、转速）",
    "fix_strategy": "在步骤1.1中明确添加：温度4°C，转速12000rpm"
}
```
```

---

## Skill 6: Curator Skill

**文件：** `memory/skills/curation/curator_skill_v1.md`

```markdown
# Curator Skill v1.0

## 职责
根据失败案例更新Writer Skill

## 核心原则
1. **提炼通用规则**：不包含具体数值
2. **可执行性**：规则必须明确可检查
3. **避免冗余**：不重复已有规则

## 更新流程
1. 读取当前Writer Skill
2. 根据失败原因生成新规则
3. 插入到"核心原则"或"禁止事项"部分
4. 保存新版本

## 规则模板

### 新增核心原则
```markdown
## 核心原则
...
N. **[新规则标题]**：[具体要求]
```

### 新增禁止事项
```markdown
## 禁止事项
...
❌ [新的禁止项]
```

## 输出格式
```json
{
    "update_type": "add_principle|add_prohibition",
    "new_rule": "规则内容",
    "rationale": "制定原因"
}
```

## 示例

### 输入
失败原因：步骤缺少离心参数

### 输出
```json
{
    "update_type": "add_principle",
    "new_rule": "离心步骤必须包含：温度、转速、时间三个参数",
    "rationale": "避免操作参数不明确导致实验失败"
}
```

### 更新后的Writer Skill
```markdown
## 核心原则
...
5. **离心参数完整性**：离心步骤必须包含温度、转速、时间
```
```

---

## 完整工作流示例

### 场景：处理"样品离心"章节

**Step 1: Master评估**
```
输入：章节名="样品离心"
输出：complexity="standard", route="standard_path"
```

**Step 2: Writer生成**
```
基于writer_skill_v1.md生成SOP
输出：包含5个必需章节的Markdown
```

**Step 3: Simulator盲测**
```
发现问题：步骤1.1未说明离心温度
输出：can_complete=false
```

**Step 4: Reviewer评分**
```
评分：2/5（Critical问题）
输出：is_pass=false
```

**Step 5: Failure Analyzer**
```
根因：missing_info
策略：添加温度参数
```

**Step 6: Curator更新Skill**
```
新增规则："离心步骤必须包含温度、转速、时间"
保存到writer_skill_v1.1.md
```

**Step 7: Writer重新生成**
```
使用更新后的Skill
输出：包含完整参数的SOP
```

**Step 8: 再次评审**
```
评分：4.5/5
输出：is_pass=true → END
```

---

## 项目结构

```
sop_生成_deepagents/
├── main_v6.py                          # LangGraph主程序
├── config_v6.py                        # 模型配置
├── memory/
│   ├── skills/
│   │   ├── master_skill.md
│   │   ├── writing/
│   │   │   ├── writer_skill_v1.0.md
│   │   │   └── writer_skill_v1.1.md   # Curator更新后
│   │   ├── simulation/
│   │   │   └── simulator_skill_v1.md
│   │   ├── evaluation/
│   │   │   └── reviewer_skill_v1.md
│   │   ├── analysis/
│   │   │   └── failure_analyzer_skill_v1.md
│   │   └── curation/
│   │       └── curator_skill_v1.md
│   ├── sop_templates/                  # 最终通过的SOP
│   │   ├── 样品离心.md
│   │   └── 主要仪器.md
│   └── audit_logs/                     # 审计日志
│       └── 2026-03-17.jsonl
└── requirements.txt
```

---

## 下一步：开始实施？
