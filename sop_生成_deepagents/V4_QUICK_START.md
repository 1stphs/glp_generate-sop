# V4 改进方案 - 快速对比

## ✅ 已完成

### 需求 1：输入改造
- ✅ 从 `report_all.json` 读取
- ✅ 分章节处理
- ✅ 使用 `original_content` + `generate_content`

### 需求 2：输出改造

#### 1. 审计日志
- ✅ 位置：`memory/audit_logs/[章节]_audit.jsonl`
- ✅ 格式：JSONL（每行一个 JSON）
- ✅ 字段：timestamp, experiment_type, quality_assessment 等

#### 2. Rules
- ✅ 位置：`memory/rules/[章节]_rules.json`
- ✅ 格式：JSON
- ✅ 分章节存储
- ✅ Curator 可更新

#### 3. SOP 模板
- ✅ 位置：`memory/sop_templates/[章节]_template.json`
- ✅ 格式：JSON
- ✅ 包含：core_principles, template, examples
- ✅ 持续优化

## 📁 核心文件

| 文件 | 作用 |
|------|------|
| `memory_manager_v4.py` | 记忆管理（3层输出） |
| `subagents_config_v4.py` | Subagent 配置 |
| `main_v4.py` | 分章节处理主程序 |
| `V4_SOLUTION.md` | 完整方案说明 |

## 🚀 快速开始

```bash
python main_v4.py
```

## 📊 输出结构

```
memory/
├── audit_logs/          # 审计日志
│   └── 引言_audit.jsonl
├── rules/               # 规则库
│   └── 引言_rules.json
└── sop_templates/       # SOP 模板
    └── 引言_template.json
```

## 🔑 关键特性

1. **结合 DeepAgents**：使用 FilesystemBackend
2. **分章节处理**：每个章节独立存储
3. **持续优化**：每次加载历史，失败时更新
4. **JSON 格式**：易于解析和更新
