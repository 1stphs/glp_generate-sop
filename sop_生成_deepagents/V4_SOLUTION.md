# V4 改进方案总结

## 🎯 核心改进

### 需求 1：输入改造 ✅
- 从 `report_all.json` 读取数据
- 按章节处理：`original_content` + `generate_content`
- 自动过滤无效章节（目录、声明等）

### 需求 2：输出改造 ✅

#### 1. 审计日志（主 Agent 生成）
```
memory/audit_logs/
└── [章节名]_audit.jsonl
```

每行一个 JSON：
```json
{
  "timestamp": "2026-03-14T15:11:57",
  "experiment_type": "LC-MS_MS结构化验证",
  "section_title": "引言",
  "version": "V4",
  "sop_id": "350510722908165",
  "quality_assessment": {
    "is_passed": false,
    "score": 2.0,
    "feedback": "缺少温度参数"
  }
}
```

#### 2. Rules（Curator 写入）
```
memory/rules/
└── [章节名]_rules.json
```

JSON 格式：
```json
{
  "section_title": "引言",
  "updated_at": "2026-03-16T14:30:00",
  "rules": [
    {
      "rule_id": "R001",
      "content": "必须包含验证试验名称和编号",
      "created_at": "2026-03-16T14:30:00"
    }
  ]
}
```

#### 3. SOP 模板（持续优化）
```
memory/sop_templates/
└── [章节名]_template.json
```

JSON 格式：
```json
{
  "section_title": "引言",
  "updated_at": "2026-03-16T14:30:00",
  "core_principles": [
    "明确验证目的",
    "列出所有参与人员"
  ],
  "template": "# 引言\n\n## 1.1 验证试验名称\n...",
  "examples": [
    "示例1：LC-MS/MS方法验证"
  ]
}
```

## 📁 新文件结构

```
sop_生成_deepagents/
├── main_v4.py                    # 分章节处理主程序
├── memory_manager_v4.py          # V4 记忆管理器
├── subagents_config_v4.py        # V4 Subagent 配置
├── report_all.json               # 输入数据
└── memory/
    ├── audit_logs/               # 审计日志（JSONL）
    │   ├── 引言_audit.jsonl
    │   └── 材料和方法_audit.jsonl
    ├── rules/                    # 规则库（JSON）
    │   ├── 引言_rules.json
    │   └── 材料和方法_rules.json
    └── sop_templates/            # SOP 模板（JSON）
        ├── 引言_template.json
        └── 材料和方法_template.json
```

## 🔑 关键设计

### 1. 结合 DeepAgents 框架

**使用 FilesystemBackend**：
```python
backend = FilesystemBackend(root_dir="./")
agent = create_deep_agent(..., backend=backend)
```
- Curator 可以使用 `edit_file` 工具更新 JSON
- 所有 Subagent 可以读取 memory/ 中的文件

**分章节处理**：
```python
for section in sections:
    # 加载历史规则和模板
    rules = memory.load_rules(section_title)
    template = memory.load_sop_template(section_title)

    # 传递给 Agent
    result = agent.invoke({...})

    # 保存结果
    memory.log_audit(...)
    memory.save_sop_template(...)
```

### 2. 持续优化机制

每次处理章节时：
1. 加载历史规则和模板
2. Agent 基于历史知识生成
3. 如果失败，Curator 更新规则
4. 下次自动复用新规则

## 🚀 使用方法

```bash
# 运行 V4 版本
python main_v4.py

# 查看输出
ls memory/audit_logs/
ls memory/rules/
ls memory/sop_templates/
```

## 📊 输出示例

### 审计日志
```bash
cat memory/audit_logs/引言_audit.jsonl
```

### 规则库
```bash
cat memory/rules/引言_rules.json
```

### SOP 模板
```bash
cat memory/sop_templates/引言_template.json
```
