# 记忆系统重构方案 (Experiment-Aware Memory System)

## 1. 背景与问题分析
当前的记忆系统采用扁平化的文件存储方式：
- [chapter_rules/](file:///Users/pangshasha/Documents/github/glp_generate-sop/sop_deeplang/utils/memory_manager.py#561-571): 存储章节级别的规则，所有实验类型公用。
- `markdown_sops/`: 存储生成的 MD 文件，文件名仅包含章节名。
- `sop_templates/`: 存储完整的 SOP JSON，虽然文件名带有 `report_id`，但缺乏更高层级的“实验类型”聚合。

**问题**：
- 随着实验类型（如：大鼠 PK、食蟹猴 PD、体外稳定性等）增加，不同实验类型的 SOP 规范、章节规则和历史记忆会发生冲突。
- 检索匹配效率低：无法根据实验类型快速定位最相关的历史记忆。

## 2. 核心设计思想：实验类型命名空间 (Experiment Namespacing)
引入 **Experiment Type (实验类型)** 作为核心分类维度。所有的记忆（规则、SOP、模板）都将按照实验类型进行物理隔离。

### 2.1 目录结构调整
根据 `original_docx` 中的定义，我们将建立以下目录结构：
```text
memory/
├── experiments/               # 按实验类型隔离的记忆
│   ├── BV报告/                # 实验类型 1
│   │   ├── chapter_rules/     # 该类型特有的章节规则
│   │   ├── markdown_sops/     # 该类型生成的历史 SOP
│   │   └── templates/         # 该类型特有的 SOP 模板
│   ├── 全身主动过敏试验_被动皮肤过敏试验/  # 实验类型 2 (由于冒号特殊字符，建议路径名稍作处理，显示保留中文)
│   ├── 局部刺激试验/           # 实验类型 3
│   └── 溶血试验/               # 实验类型 4
└── audit_logs/                # 审计日志
```
> [!IMPORTANT]
> 文件夹名称将直接使用中文，与 `original_docx` 保持一致，增加可读性。部分包含特殊字符（如冒号）的文件夹名在文件系统中会进行安全转义，但在逻辑层保持对应。

### 2.2 检索匹配策略
当传入新的报告方案数据时，通过以下维度进行快速检索匹配：
1. **Experiment Type Match**: 优先匹配同类型的实验记忆。
2. **Metadata Tagging**: 在 SOP 模板中记录更丰富的元数据（如：化合物类别、分析技术等）。
3. **Semantic Search (可选)**: 如果文件量巨大，可以引入简单的向量索引（但在初期，目录树+标签匹配最快速且清晰）。

## 3. 拟议变更

### 3.1 [MemoryManager](file:///Users/pangshasha/Documents/github/glp_generate-sop/sop_deeplang/utils/memory_manager.py#30-629) 改重构
- 构造函数支持传入 `experiment_type`。
- 所有读写操作自动路由到 `memory/experiments/{experiment_type}/`。
- 提供 `MemoryManager.get_best_match_sop(section, experiment_type)` 方法。

### 3.2 `MasterState` 与 `Engine` 增强
- `MasterState` 增加 `experiment_type` 字段。
- `Engine` 在初始化各个 Node 时，确保它们感知当前的实验类型上下文。

## 4. 实施流程
1. **第一阶段：目录结构迁移**：将现有 `default` 实验的相关数据迁移到新结构。
2. **第二阶段：代码逻辑重构**：修改 [MemoryManager](file:///Users/pangshasha/Documents/github/glp_generate-sop/sop_deeplang/utils/memory_manager.py#30-629) 和 `Engine` 核心逻辑。
3. **第三阶段：检索增强**：实现跨实验类型的自动路由和检索。

## 5. 预期收益
- **隔离性**：不同实验类型的规则互不干扰。
- **扩展性**：新增实验类型只需增加一个文件夹。
- **效率**：直接定位到对应类型的历史 SOP，大幅提升检索速度。
