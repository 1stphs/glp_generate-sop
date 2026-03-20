# SOP 生成系统 - 两阶段演进架构

基于 LangGraph 的"压测进化型" SOP 自动生成系统。针对 GLP 生物分析领域，实现从原始方案（Protocol）和报告（Report）向极致泛化 SOP 模板的自动化演进。

## 🎯 系统架构概览

本系统采用**两阶段解耦架构**，有效解决 LLM 幻觉并提升 SOP 的工业适应性：

### 阶段一：骨架生成 (Phase 1 - Skeleton Generation)
- **核心目标**：屏蔽复杂实验数据，仅利用 Protocol/Report 的逻辑结构快速构建带 `[XXX]` 插槽的泛化 SOP 骨架
- **关键特性**：强制插槽制、零数据幻觉、确保 SOP 结构的纯粹性
- **输出产物**：包含"核心填写规则"和"通用标准化模板"的初版 SOP

### 阶段二：专家迭代 (Phase 2 - Expert Iteration)
- **核心目标**：接入真实 Excel 数据进行"压力测试"
- **关键特性**：通过 Simulator 模拟执行、Reviewer 核验健壮度、Curator 提炼章节规则
- **输出产物**：经过实战数据压测后进化出的终极 SOP 模板

---

## 📁 目录结构与文件组织

### 输入文件位置

**原始文档存放位置：**
```
original_docx/BV报告/
├── NS25318BV01/
│   ├── NS25318BV01-RAT-BA-REPORT-Final-杨接敏-1@20251226.docx    # 验证报告
│   ├── NS25318BV01生物分析验证方案(SD rat)_Final@20250901.docx    # 验证方案
│   ├── Qced NS25318BV01二次数据汇总@20250916（1-6）.xlsx          # Excel 数据文件
│   └── ...                                                        # 其他 Excel 文件
├── NS25315BV01/
│   └── ...
└── ...
```

**输入文件说明：**
- `.docx` 文件：验证方案（Protocol）和验证报告（Report）
- `.xlsx` 文件：实验结果数据（系统适用性、精密度、回收率、稳定性等）

---

### 数据预处理输出

运行预处理脚本后，原始文档会被解析并保存到以下位置：

```
data_parsed/
├── [Report_ID]/                              # 每个报告一个独立目录
│   ├── merged_docs.md                        # 合并后的方案和报告（Markdown 格式）
│   └── excel_data/                           # Excel 表格解析结果
│       ├── 表1_schedule.md                   # 实验进度表
│       ├── 表5_特异性.md                      # 特异性数据
│       ├── 表9_Inter_QC.md                   # QC 数据
│       ├── 表19_FT.md                        # 冻融稳定性
│       ├── 表20_PSS.md                       # 长期稳定性
│       ├── 表23_溶血效应.md                   # 溶血试验
│       └── ...                               # 其他表格
└── ...
```

**数据预处理脚本：** `scripts/preprocess_data.py`

---

### SOP 生成输出

系统运行后，生成的 SOP 模板和相关资源保存在以下位置：

#### 1. SOP 模板（JSON 格式）

每次传入都对应着一个最终生成的SOP：

```
sop_deeplang/memory/sop_templates/
├── NS25318BV01_all_sops.json                 # 完整的 SOP JSON（包含所有章节）
├── NS25315BV01_all_sops.json
└── ...
```

**JSON 结构说明：**
- 每个章节包含：`section_title`、`core_rules`（核心填写规则）、`template_content`（通用标准化模板）、`report_example`（报告示例）
- 便于程序化处理和章节级别的规则提取

#### 2. SOP 模板（Markdown 格式）

最终用于指导下游任务使用的SOP：

```
sop_deeplang/memory/markdown_sops/
├── GLP遵从性声明和签字页.md
├── 标准曲线及范围.md
├── 批内_批间准确度及精密度.md
├── 回收率.md
├── 溶血效应.md
├── 冻融稳定性.md
├── 结论.md
└── ...
```

**Markdown 格式说明：**
每个 SOP 文件包含以下三部分：

```markdown
## 一、核心填写规则
- 告诉用户如何填写插槽
- 来自 Phase 2 演化的章节规则
- 例如："从验证方案中提取标准曲线回归方程，修约为三位小数"

## 二、通用标准化模板
- 插槽化的标准模板
- 使用 `[XXX]` 占位符标记需要填写的部分
- 例如："本方法线性范围可达{{LLOQ}}~{{ULOQ}} ng/mL"

## 三、报告示例
- 实际填写后的示例
- 展示模板如何应用于真实项目
```

#### 3. 章节规则库（Phase 2 演化产物）

phase2 用于更新的核心规则库：

```
sop_deeplang/memory/chapter_rules/
├── rule_标准曲线及范围.json                  # 标准曲线章节的专属规则
├── rule_批内_批间准确度及精密度.json          # 精密度章节的专属规则
├── rule_回收率.json                         # 回收率章节的专属规则
├── rule_冻融稳定性.json                      # 稳定性章节的专属规则
└── ...
```

**规则文件结构示例：**
```json
{
  "section_title": "标准曲线及范围",
  "rules": [
    {
      "type": "add_requirement",
      "content": "必须显式定义所有统计参数的修约规则和精度要求",
      "rationale": "避免数值修约错误导致的计算偏差",
      "iteration": 1
    }
  ]
}
```

---

## 🚀 快速开始

### 1. 环境准备

确保拥有 Python 3.10+ 环境，并安装依赖：

```bash
# 创建虚拟环境
python3 -m venv .venv
source .venv/bin/activate

# 安装依赖
pip install langgraph openai python-docx pandas python-dotenv
```

配置 `.env` 文件：
```bash
OPENAI_API_KEY=your_api_key_here
OPENAI_BASE_URL=https://api.openai.com/v1
```

### 2. 数据预处理

将原始文档放入对应目录：

```bash
# 将 .docx 和 .xlsx 文件放入以下目录
original_docx/BV报告/[Report_ID]/
├── [Report_ID]生物分析验证方案.docx
├── [Report_ID]-RAT-BA-REPORT-Final.docx
└── Qced [Report_ID]二次数据汇总.xlsx
```

运行预处理脚本：

```bash
python3 scripts/preprocess_data.py
```

**输出位置：**
- 解析后的文档：`data_parsed/[Report_ID]/merged_docs.md`
- 解析后的 Excel 表格：`data_parsed/[Report_ID]/excel_data/*.md`

### 3. 执行 SOP 生成

#### 阶段一：生成初始骨架

```bash
PYTHONPATH=. python3 sop_deeplang/main.py --phase 1 --report [Report_ID] --workers 8
```

**说明：**
- 仅使用 Protocol 和 Report 的逻辑结构
- 生成带插槽的泛化 SOP 骨架
- 不使用 Excel 数据，避免幻觉
- 输出位置：
  - `sop_deeplang/memory/sop_templates/[Report_ID]_all_sops.json`
  - `sop_deeplang/memory/markdown_sops/*.md`

**可选参数：**
- `--limit N`：仅处理前 N 个章节（用于测试）
- `--workers N`：并行处理线程数（默认 5）

#### 阶段二：专家迭代及压力测试

```bash
PYTHONPATH=. python3 sop_deeplang/main.py --phase 2 --report [Report_ID] --workers 8
```

**说明：**
- 接入真实 Excel 数据进行压测
- 通过 Simulator → Reviewer → Curator 闭环迭代
- 自动生成并更新章节规则库
- 最终 SOP 覆盖阶段一的初版
- 输出位置：
  - `sop_deeplang/memory/sop_templates/[Report_ID]_all_sops.json`（更新）
  - `sop_deeplang/memory/markdown_sops/*.md`（更新）
  - `sop_deeplang/memory/chapter_rules/rule_*.json`（新增/更新）

**可选参数：**
- `--limit N`：仅处理前 N 个章节
- `--workers N`：并行处理线程数（默认 5）

### 4. 使用生成的 SOP

查看生成的 SOP 模板：

```bash
# 查看 Markdown 格式的 SOP
cat sop_deeplang/memory/markdown_sops/标准曲线及范围.md

# 查看 JSON 格式的 SOP（程序化处理）
cat sop_deeplang/memory/sop_templates/NS25318BV01_all_sops.json
```

查看章节规则：

```bash
# 查看某个章节的演化规则
cat sop_deeplang/memory/chapter_rules/rule_标准曲线及范围.json
```

---

## 📊 基于 SOP 生成报告（简要说明）

本系统还支持使用已生成的 SOP 模板来生成新的验证报告（测试 SOP 的泛化能力）。

### 输入
- SOP 模板：`sop_deeplang/memory/sop_templates/[Report_ID]_all_sops.json`
- 新的方案和 Excel 数据：`data_parsed/[New_Report_ID]/`
- 报告编号：用于填充 project_info

### 输出
- JSON 格式报告：`report_generation/output.json`
- Word 格式报告：`data_parsed/[New_Report_ID]/final_report.docx`

### 执行步骤

**第一步：准备输入数据**
```bash
python3 report_generation/prepare_data.py \
  --sop sop_deeplang/memory/sop_templates/NS25318BV01_all_sops.json \
  --data data_parsed/SS25255NM01_test \
  --report_id SS25255NM01 \
  --output report_generation/sections_data.json
```

**第二步：LLM 生成报告内容**
```bash
PYTHONPATH=. .venv/bin/python3 report_generation/generate_report.py \
  report_generation/project_info.json \
  report_generation/sections_data.json \
  report_generation/output.json
```

**第三步：转换为 Word 文档**
```bash
python3 report_generation/convert_to_docx.py \
  --input report_generation/output.json \
  --output data_parsed/SS25255NM01_test/final_report.docx
```

---

## 🧠 核心技术特点

### 1. 两阶段解耦架构
- **Phase 1**：冷启动快速生成骨架，零数据幻觉
- **Phase 2**：实战数据压测，持续进化规则库

### 2. 插槽化 SOP 模板
- 使用 `[XXX]` 或 `{{XXX}}` 占位符
- 将 SOP 分离为"规则"和"模板"两部分
- 人类可直接阅读和填写

### 3. 章节级规则演化
- 每个章节维护专属规则库
- Phase 2 通过 Curator 自动提炼新规则
- 规则库可跨项目复用

### 4. 双轨模拟压测
- **微观压测**：用真实 Excel 数据填充插槽，检测结构缺失
- **宏观压测**：根据 SOP 反向推演实验流程，检测逻辑漏洞

### 5. LangGraph 动态编排
- Master Agent 动态路由复杂章节
- 简单章节快速通过，复杂章节触发多轮迭代

---

## 📁 项目目录总览

```
glp_generate-sop/
├── main.py                               # 主入口
├── scripts/
│   └── preprocess_data.py                # 数据预处理脚本
├── sop_deeplang/                         # 核心包
│   ├── main.py                           # SOP 生成主程序
│   ├── core/                             # LangGraph 引擎
│   ├── nodes/                            # Agent 节点（Writer, Simulator, Reviewer, Curator）
│   ├── utils/                            # 工具类
│   ├── skills/                           # Agent 基础技能（与 memory 同级）
│   ├── memory/                           # 知识资产库
│   │   ├── chapter_rules/                # 章节规则（Phase 2 演化）
│   │   ├── markdown_sops/                # SOP Markdown 模板
│   │   └── sop_templates/                # SOP JSON 模板
│   └── sandbox/
│       └── excel_parser.py               # Excel 解析沙盒
├── report_generation/                    # 报告生成模块
├── original_docx/                        # 原始文档输入
│   └── BV报告/
├── data_parsed/                          # 预处理后数据
│   ├── [Report_ID]/
│   │   ├── merged_docs.md
│   │   └── excel_data/
└── README.md                             # 本文档
```

---

## 🛠️ 核心优化记录

1. **评分逻辑一致性**：Reviewer 拥有"一票否决权"，优先尊重人工/模型判定而非仅看分数
2. **知识阻断放宽**：确保"偏离"、"特殊情况"等低信息量章节也能生成标准声明模板
3. **长文本感知增强**：Writer 节点上下文处理能力提升至 5000 字符
4. **并发效率提升**：支持通过 `--workers` 参数调整并行处理任务数
5. **规则自动演化**：Phase 2 的 Curator 节点自动提炼并保存章节规则

---

## 💡 使用建议

1. **首次使用**：建议先运行 Phase 1 生成初版 SOP，再运行 Phase 2 进行优化
2. **多项目复用**：规则库可跨项目复用，随着处理项目增多，SOP 模板会越来越完善
3. **质量控制**：可以人工审查生成的 SOP，手动调整 `markdown_sops/` 中的模板
4. **增量学习**：每处理一个新的报告，都会丰富规则库，提升后续生成质量

---

*Powered by DeepLang Team - 致力于构建最具工业美感的 GLP 数字化工具*
