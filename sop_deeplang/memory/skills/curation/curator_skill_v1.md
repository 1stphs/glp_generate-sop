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

### 示例1：添加参数完整性原则
输入：
```json
{
    "root_cause": "missing_info",
    "detail": "操作步骤缺少关键参数（温度、转速）",
    "fix_strategy": "在步骤1.1中明确添加：温度4°C，转速12000rpm，时间10分钟"
}
```

输出：
```json
{
    "update_type": "add_principle",
    "new_rule": "离心步骤必须包含：温度、转速、时间三个参数",
    "rationale": "避免操作参数不明确导致实验失败"
}
```

更新后的Writer Skill片段：
```markdown
## 核心原则
...
5. **离心参数完整性**：离心步骤必须包含温度、转速、时间
```

### 示例2：添加禁止模糊表述规则
输入：
```json
{
    "root_cause": "ambiguous_terms",
    "detail": "使用'适量'等模糊表述，无法精确执行",
    "fix_strategy": "将'适量'替换为具体数值和单位"
}
```

输出：
```json
{
    "update_type": "add_prohibition",
    "new_rule": "禁止使用'适量'、'约'、'大概'等模糊表述",
    "rationale": "确保操作可精确重复"
}
```

更新后的Writer Skill片段：
```markdown
## 禁止事项
...
❌ 禁止使用"适量"、"约"、"大概"等模糊表述
```

### 示例3：添加可追溯性原则
输入：
```json
{
    "root_cause": "compliance_gap",
    "detail": "缺少GLP要求的可追溯性信息",
    "fix_strategy": "添加步骤：从实验室仪器管理系统查询并记录仪器编号"
}
```

输出：
```json
{
    "update_type": "add_principle",
    "new_rule": "必须说明仪器编号/型号的获取方式，确保可追溯性",
    "rationale": "符合GLP合规要求，满足FDA审计需求"
}
```

更新后的Writer Skill片段：
```markdown
## 核心原则
...
6. **仪器可追溯性**：必须说明仪器编号/型号的获取方式
```

## Skill版本管理

每次更新后，Skill文件版本号递增：
- `writer_skill_v1.0.md` → `writer_skill_v1.1.md`
- 保留历史版本以便回溯

## 自动更新逻辑

Curator执行以下操作：
1. 读取当前版本的Writer Skill
2. 根据根因分析结果生成新规则
3. 将新规则插入到适当位置
4. 保存为新版本文件（版本号+0.1）
5. 更新系统配置中的当前Skill版本号
