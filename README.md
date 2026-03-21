# SOP 生成系统 - 两阶段演进架构

基于 LangGraph 的"压测进化型" SOP 自动生成系统。针对 GLP 生物分析领域，实现从原始方案（Protocol）和报告（Report）向极致泛化 SOP 模板的自动化演进。

## 🎯 系统架构概览

本系统采用**两阶段解耦架构**，有效解决 LLM 幻觉并提升 SOP 的工业适应性：

### 阶段一：骨架生成 (Phase 1 - Skeleton Generation)
- **核心目标**：屏蔽复杂实验数据，仅利用 Protocol/Report 的逻辑结构快速构建带 `[XXX]` 插槽的泛化 SOP 骨架。
- **关键特性**：强制插槽制、零数据幻觉、确保 SOP 结构的纯粹性。系统会跳过大模型复杂度研判，强制将所有章节标记为 Simple 绕过深层模拟盲测评审机制，直接跑出第一套全量草稿。
- **输出产物**：包含 50+ 细分章节"核心填写规则"和"通用标准化模板"的初版 SOP。

### 阶段二：专家迭代 (Phase 2 - Expert Iteration)
- **核心目标**：接入真实数据（提取出的文段/Excel等参数）进行"压力测试"。
- **关键特性**：Master Agent 分流，自动激活大模型复杂评估。对于复杂章节使用 Simulator 模拟试验、Reviewer 核验健壮度（打分低于及格线则多次重写）、Curator 提炼出错章节的防呆规则。
- **输出产物**：经过对抗搏杀及实战数据压测后，进化出的终极 SOP 模板。

---

## 📁 目录结构与文件组织

完整跑完项目业务流程后，真正用到的核心文件夹及其用途说明如下：

### 输入文件位置（原始输入流）

**原始文档存放位置：**
```text
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
- `.docx` 文件：包含具体的实验操作验证方案（Protocol）和汇总验证报告（Report）。

---

### 数据预处理输出（预处理数据中枢）

运行预处理脚本后，系统会精准抽取 Word 中的原生 TOC（目录）逻辑结构，并配合固定补偿表，将原始文档分片拆解保存。

```text
data_parsed/
├── [Report_ID]/                              # 每个报告一个独立目录
│   ├── filtered_data.json                    # 抽取的核心产物（包含 50+ 个映射了方案及报告的细分段落字典，是后续大模型的唯一生成输入源）
│   └── excel_data/                           # Excel 表格解析结果
│       ├── 表1_schedule.md                   # 实验进度表
│       ├── 表5_特异性.md                      # 特异性数据
│       ├── 表9_Inter_QC.md                   # QC 数据
│       ├── 表19_FT.md                        # 冻融稳定性
│       └── ...                               # 其他表格
└── ...
```

**数据预处理脚本：** `scripts/preprocess_data.py`

---

### SOP 生成输出（大模型资产中心）

系统运行后，系统的一切 AI 资源都保存在 `sop_deeplang/memory/` 目录下：

#### 1. SOP 模板（JSON 格式，便于系统二次提取）

每次传入都对应着一个包含全量数据的集合阵列，汇总式存放了所有大模型的处理成果：

```text
sop_deeplang/memory/sop_templates/
├── NS25318BV01_all_sops.json                 # 完整的 SOP JSON（包含所有章节）
├── NS25315BV01_all_sops.json
└── ...
```

**JSON 结构说明：**
- 每个章节包含：`section_title`、`core_rules`（核心填写规则）、`template_content`（通用标准化模板）、`report_example`（报告示例）。

#### 2. SOP 模板（Markdown 格式，可交付成果库）

这里即是最终用于指导下游任务或人类查看使用的具体单章节独立文档：

```text
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
1. **一、核心填写规则**（告诉用户如何填写插槽，来自提炼的章节规则）。
2. **二、通用标准化模板**（含 `[XXX]` 占位符且具有严格表述和图表占位的标准模板）。
3. **三、报告示例**（基于现有项目实际填写的数据示例）。

#### 3. 章节规则库（Phase 2 演化产物防抖机制）

存储了大模型在复杂实验的模拟考核中犯错后，自动反思总结的规避条款库。

```text
sop_deeplang/memory/chapter_rules/
├── rule_标准曲线及范围.json                  # 标准曲线章节的专属规则
├── rule_批内_批间准确度及精密度.json          # 精密度章节的专属规则
├── rule_回收率.json                         # 回收率章节的专属规则
├── rule_冻融稳定性.json                      # 稳定性章节的专属规则
└── ...
```

#### 4. 透明监督室（AI对战审计日志）

打分盲审溯源日志地：

```text
sop_deeplang/memory/audit_logs/
├── audit_2026-03-21.jsonl                    # 记录每日所有的节点触发操作
└── ...
```

**说明：** 记录了 Master 的等级判断、Simulator 找出的缺失细节及 Reviewer 的残酷评分与退回重写原因（JSONL），开发查证与复盘专用。

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

### 2. 数据预处理（全量分片萃取）

将原始文档放入对应目录：

```bash
# 将 .docx 和 .xlsx 文件放入以下目录
original_docx/BV报告/[Report_ID]/
├── [Report_ID]生物分析验证方案.docx
├── [Report_ID]-RAT-BA-REPORT-Final.docx
└── Qced [Report_ID]二次数据汇总.xlsx
```

运行预处理脚本（本过程依据自动抓取的 TOC 生成树目录）：

```bash
python3 scripts/preprocess_data.py
```

**关键输出位置：**
- 解析后的章节分片结果：`data_parsed/[Report_ID]/filtered_data.json`

### 3. 执行 SOP 生成

#### 阶段一：生成初始骨架

```bash
PYTHONPATH=. python3 sop_deeplang/main.py --phase 1 --report [Report_ID] --workers 10
```

**说明：**
- 仅使用提取出的输入，绕过复杂博弈盲推机制。
- 采用 10 线程并发跑出第一版骨架，带插槽的泛化 SOP 大面生成。

#### 阶段二：专家迭代及深度压力测试

```bash
PYTHONPATH=. python3 sop_deeplang/main.py --phase 2 --report [Report_ID] --workers 10
```

**说明：**
- 针对提取好的数据字典，大模型主动审查复杂度。
- 复杂章节进入 Simulator（盲测） → Reviewer（打分退回重做） → Curator（提取排雷法则）的极限测试与多轮迭代，极耗 Token 但质量绝佳。
- 最终生成的完美版本会覆盖掉第一阶段生成的对应草稿。

### 4. 使用生成的 SOP

```bash
# 查看 Markdown 格式的 SOP 最直观成效
cat sop_deeplang/memory/markdown_sops/标准曲线及范围.md

# 查看 JSON 格式的 SOP（程序后续二次解析专用）
cat sop_deeplang/memory/sop_templates/NS25318BV01_all_sops.json
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

### 2. 完美的 TOC 细粒度控制
- 引入了基于 Word 真实生成目录的切分提取。相较于过往依赖盲猜或正则表达式带来的数百局部的丢失，通过新的大纲结构完美抽取出如“主要操作人员”、“指导原则”、“批内_批间准确度及精密度”等 50+ 个细分颗粒单元。

### 3. 插槽化 SOP 模板
- 使用 `[XXX]` 或 `{{XXX}}` 占位符
- 将 SOP 分离为"规则"和"模板"两部分

### 4. 双轨模拟编排
- **微观/宏观压测**：结合 Master Agent 的动态路由，系统不再直接丢给大模型草草了事，而是让无前置经验的大模型执行“盲测推演实验步骤”，以此找出真正可落地的 SOP 逻辑漏洞。

---

## 📁 项目目录总览

```text
glp_generate-sop/
├── main.py                               # 主入口
├── scripts/
│   └── preprocess_data.py                # 数据预处理脚本 (含 TOC 提纯与分离切块)
├── sop_deeplang/                         # 核心包
│   ├── main.py                           # SOP 生成主程序
│   ├── core/                             # LangGraph 引擎
│   ├── nodes/                            # Agent 节点（Writer, Simulator, Reviewer, Curator）
│   ├── utils/                            # 工具类
│   ├── skills/                           # Agent 基础技能库
│   ├── memory/                           # 知识资产库
│   │   ├── audit_logs/                   # 打分盲审日志溯源文件 (排错)
│   │   ├── chapter_rules/                # 章节防错规则（Phase 2 演化沉淀）
│   │   ├── markdown_sops/                # SOP Markdown 独立文档成品文件
│   │   └── sop_templates/                # 涵盖全内容的 JSON 数据大仓
│   └── sandbox/
│       └── excel_parser.py               # Excel 解析沙盒
├── report_generation/                    # 报告生成模块下游利用
├── original_docx/                        # 原始文档输入
│   └── BV报告/
├── data_parsed/                          # 预处理后核心输入层数据
│   ├── [Report_ID]/
│   │   ├── filtered_data.json            # 被高度整理细分的最核心生成阵列入口 (*更新)
│   │   └── excel_data/
└── README.md                             # 本文档
```

---

## 🛠️ 核心优化记录

1. **精准结构化解析**：以真实文档自动生成的 TOC 目录树作为主骨架，提取成功率翻倍（原本仅约10章节增加至最高56段细分），真正实现大纲无死角匹配。
2. **评分逻辑一致性**：Reviewer 拥有"一票否决权"，优先尊重人工/模型判定而非仅看分数
3. **知识阻断放宽**：确保"偏离"、"特殊情况"等低信息量章节也能生成标准声明模板
4. **并发效率提升**：拆切小巧的 JSON 组装极大减少了等待期，完全释放了利用 `--workers 10` 进行并行处理的优势。
5. **规则自动演化**：Phase 2 的 Curator 节点自动提炼并保存长久有用的章节错误规避指南。

---

## 💡 使用建议

1. **首次使用**：建议先运行 `--phase 1` 配合 10 线程飞速生成全景初版框架摸底，之后直接挑重点切换 `--phase 2` 深度打磨评审优化质量。
2. **多项目复用**：规则库可跨项目复用，随着处理项目增多甚至碰壁踩坑，Curator 生成的规则会让以后的模板容错率飞升。
3. **质量控制**：通过直接修改 `markdown_sops/` 中的最终呈现结果进行人工兜底，系统会自动读取和校对后续。

---

*Powered by DeepLang Team - 致力于构建最具工业美感的 GLP 数字化工具*
