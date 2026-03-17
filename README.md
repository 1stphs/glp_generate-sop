# GLP SOP 自动化生成系统 (GLP SOP Auto-Generator)

基于 [DeepAgents](https://github.com/deepagents/deepagents) 框架构建的高级 AI 智能体协作系统。该系统专门用于自动化生成、评估、验证并持续优化 GLP（药物非临床研究质量管理规范）报告的 SOP（标准操作规程），具备**异步交互**与**闭环自进化**的强大能力。

## 🎯 核心价值 & 系统架构

本项目摒弃了传统的“大段文本对话”模式，转而采用**“Serverless 微服务”+“API 结构化输出”**的设计理念，构建了一个无需人工干预、可无限循环的“自动驾驶知识炼丹炉”。

系统核心为一个经典的 **Actor-Critic 自我进化飞轮**，由 5 个高度专业化的 Subagent 组成：

1. ✍️ **Writer (Generator / 考生)**
   * **职责**：基于传入的【原始方案】和系统记忆中的【历史规则】，生成当前章节的 SOP 初稿。
   * **特点**：被要求输出明确的规则引用来源，做到“知其然并知其所以然”。
2. 🧪 **Simulator (盲测器)**
   * **职责**：在不看“标准答案（Ground Truth）”的情况下，仅凭 Writer 生成的 SOP 指令，尝试还原出符合要求的 GLP 报告内容。
3. 🔍 **Reviewer (判卷老师)**
   * **职责**：对比 Simulator 的盲测输出与真实的 GLP 报告（标准答案），进行严格的对照打分。
4. 🔬 **Reflector (诊断专家)**
   * **职责**：当评分不达标时，介入诊断。进行根因分析（Root Cause Analysis），指出 SOP 哪里写错了、为什么错，并对引用的历史规则进行有效性评估（Helpful / Harmful）。
5. 📚 **Curator (教材主编)**
   * **职责**：吸收 Reflector 的诊断教训，提炼出具有普适性的经验（Insights），并通过系统化的 JSON `ADD/UPDATE` 操作，将新知识像打补丁一样沉淀到长效记忆（Playbook / Rules）中。

> 💡 **防数据泄露/过拟合设计**：Curator 在提炼规则时，被系统严格要求“必须提炼能在盲考环境下指导学生的方法论”，阻止模型死记硬背标准答案中的具体数据，从机制上消除了幻觉与过拟合。

## 📁 目录结构

```text
.
├── sop_生成_deepagents/         # 核心代码与逻辑目录
│   ├── main_v4.py & main_v5.py  # 核心执行引擎（推荐查看 main_v5.py 了解显式 Subagent 调用工作流）
│   ├── memory_manager_v4.py     # 记忆管理系统，负责持久化规则、模板和审计日志
│   ├── subagents_config_v4.py   # Subagent 相关的设定、模型和 Prompts 配置
│   ├── requirements.txt         # Python 依赖
│   └── memory/                  # 系统的持久化记忆库空间
│       ├── rules/               # 自动优化的 SOP 规则库 (.json)
│       ├── sop_templates/       # 评分达标后沉淀的高质量 SOP 模板 (.json)
│       └── audit_logs/          # 每次执行的详细审计追踪日志 (.jsonl)
├── mockData/                    # 示例数据、原始语料与测试报文
│   └── report_all.json          # 包含了用于生成和对照的 `original_content` 与 `generate_content` 数据
├── 提示词工程分析_prompts.md      # 核心原理解析：非常详细的提示词与架构设计分析
└── sop_templates_collection.md  # 生成的各个章节（如仪器、操作人员、依从性声明等）高质量 SOP 模板集合
```

## 🔄 核心工作流 (Workflow)

运行系统时，系统对于 `report_all.json` 中的每一个有效章节执行以下循环：

1. **加载长效记忆**：读取该章节过去沉淀的 Rules 和 Templates。
2. **生成与校验**：`Writer` 生成 -> `Simulator` 盲测 -> `Reviewer` 评分。
3. **合格判断**：
   - 评分 $\ge 4.0$：测试通过，将验证合格的 SOP 保存至 `memory/sop_templates/`。
   - 评分 $< 4.0$：触发进化机制。`Reflector` 分析错误 -> `Curator` 提取增量规则更新到 `memory/rules/`。
4. **迭代循环**：进入下一轮迭代（最大可迭代 5 次），使用更新后的规则重新生成，直到达标。
5. **审计追踪**：无论成功失败，所有交互过程与质量评估都会记录进 `audit_logs/`，保证 GLP 质量体系下的完全可追溯。

## 🚀 快速启动

### 1. 环境准备

确保你已安装 Python 3.8+ 环境。进入工作目录并安装依赖：

```bash
cd sop_生成_deepagents
pip install -r requirements.txt
```

### 2. 配置环境变量

复制环境模板并配置你的大模型 API：

```bash
cp .env.example .env
```

编辑 `.env` 文件（需要配置支持 OpenAI 格式的 API 接口，建议使用 Claude 3.5 Sonnet / Opus 等高智商大模型以获得最佳推理效果）：

```ini
OPENAI_API_KEY="sk-xxxxxx"
OPENAI_BASE_URL="https://api.your-provider.com/v1"
```

### 3. 开始自动生成与学习

启动 V5 版本的显式工作流主程序：

```bash
python main_v5.py
```

执行后，你可以在控制台实时看到智能体间的协作对话。优化后的数据将落盘在 `sop_生成_deepagents/memory` 文件夹内的对应子目录中。

---

*由 Agentic 理念驱动的未来工作方式探索，追求工程化、高质量与强鲁棒性的内容生成典范。*
