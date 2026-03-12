# ACE (Agent-Curator-Environment)

## 项目介绍 (Introduction)

ACE (Agent-Curator-Environment) 是一个具备自我进化能力的自动化大模型智能体（Agent）系统。该系统不仅仅是一个接收 Prompt 并输出结果的工具，它通过维护一个**本地经验库（Playbook）**来指导具体任务的严谨执行。

更重要的是，在每次任务执行结束后，系统会启动反思与提炼机制（Reflector & Curator），不断沉淀成功的执行经验和排雷失败的教训，形成真正意义上的**闭环学习引擎**。结合人类在环（Human-in-the-loop）的严格审批机制，系统能够在保证业务安全可控的前提下，“越用越聪明”，持续提升自动化能力。

---

## 核心架构 (Architecture)

该系统经过深度重构，采用了极为优雅清晰的**三层隔离技术架构**：

### 1. 第一层：存储层 (Storage Layer) —— 本地化动态经验库 (Local Playbook)
- **核心职责**：持久化存储从各项任务中学习到的“经验规则”（Bullets）。
- **实现机制**：完全依赖轻量级的本地文件系统（默认位于路径 `agent_memory/playbooks/base_rules.json`）。系统执行读写隔离原则，所有经验以 JSON 格式存储，便于机器结构化读写以及局部的增量更新。
- **数据结构**：所有经验被高度原子化，每一条规则标准包含以下字段：
  - `id`: 经验唯一标识（例：`rule-glp-001`）。
  - `tags`: 任务场景标签数组，用于快速检索匹配。
  - `content`: 具体、详细且可直接执行的业务逻辑/指令内容。
  - `metrics`: 效果评估指标（统计该规则在历史任务中被判定为 `helpful` 还是 `harmful` 的次数），作为日后清理无效规则的依据。

### 2. 第二层：检索层 (Retrieval Layer) —— 插件化上下文引擎 (Context Plugin)
- **核心职责**：在正式执行任务前，智能提取当前任务所需的经验，避免将整个庞大的全局经验库全部塞入 LLM 导致上下文污染、超载或丢失焦点。
- **实现机制**：作为挂载在大模型调用链上的前置拦截中间件（`ContextEnhancer`）。它通过轻量级的关键词机制，分析当前用户指令，从第一层 JSON 文件库中精准过滤出 `tags` 匹配度高的业务条目。
- **能力输出**：将抽取出的多条离散格式经验，拼接包装成一段专属的 System Playbook 文本（包含该规则的效能评估指标），前置注入给大模型作为“纪律指引”。

### 3. 第三层：认知层 (Cognitive Layer) —— 闭环学习与审批引擎 (ACE Engine)
这是整个项目的大脑中枢，负责任务控制、自我反思以及通过防线机制保障生态安全。
- **核心职能**：串联多 Agent 协同流，并引入安全门（Approval）。
- **实现机制**：包含四大功能组件：
  - **Generator (执行者)**：接收来自 Context Plugin 增强的专属上下文，并实际去执行任务、产生结果输出或代码调用。
  - **Reflector (反思者)**：充当“复盘官”，基于 Generator 的详细执行轨迹、运行报错日志及标准答案对照，深度分析此阶段的问题，并为刚刚引用的规则打上效果标签（Helpful / Harmful）。
  - **Curator (策展者)**：充当“书籍编撰者”，根据 Reflector 提供的大量教训，去粗取精，提炼出具有普遍复用价值的**全新格式化规则描述**。
  - **ApprovalInterceptor (审批拦截器)**：出于生产安全考量，在新规则提炼好准备写入 Local Playbook 前发挥最后一道防线的作用。系统会挂起进程并通过控制台（CLI `y/n/a`）或界面弹窗拦截反馈：“发现新经验，是否加入经验库？” 只有经开发者人工确认，该智慧结晶才完成真正入库，实现生态繁荣与业务安全的统一。

---

## 快速使用说明 (How to Use)

### 1. 环境准备
- **语言依赖**: Python >= 3.10
- **环境搭建**: 建议使用 `uv` 来加速环境配置与包管理（或直接使用 pip）。
  ```bash
  uv sync  # (如果存在 uv 配置)
  # 或者
  pip install -r pyproject.toml # (依据具体配置情况)
  ```
- **密钥配置**: 复制一份 `.env.example` 并重命名为 `.env`，填入您使用的大语言模型（如 OpenAI、Anthropic、智谱等） API Key 设置。

### 2. 项目核心目录导读
```text
ace/
├── ace/                         # 主干代码库
│   ├── engine.py                # -> 主力引擎，控制训练与闭环运行流程，封装 ACE 核心类
│   ├── core/                    # -> 架构三层抽象具体代码点
│   │   ├── storage.py           # (第一层) JSON文件持久化读写
│   │   ├── retrieval.py         # (第二层) Prompt上下文装配检索
│   │   ├── approval.py          # (第三层) 人机交互CLI审批确认
│   │   ├── generator.py         # (第三层) 任务执行智体
│   │   ├── reflector.py         # (第三层) 复盘打标智体
│   │   └── curator.py           # (第三层) 教训提炼智体
│   └── utils/                   # -> 通用支撑函数 (Playbook 解析、日志等)
├── agent_memory/                #
│   └── playbooks/               # -> 本地 JSON 经验库统一存储路径 (base_rules.json)
└── pyproject.toml               # Python 依赖配置文件
```

### 3. 代码体验示例 (Quick Start)
您可以在您的业务入口代码（如 `main.py`）中，只需按如下方式引入 ACE 系统：

```python
from ace.engine import ACE

# 1. 实例化核心系统对象
ace_system = ACE(
    api_provider="openai",        # 供应商配置
    generator_model="gpt-4o",     # 负责推导调用的主模型
    reflector_model="gpt-4o",     # 负责反思复盘的模型
    curator_model="gpt-4o"        # 负责凝练规则的模型
)

# 2. 准备运行参数配置
config = {
    "task_name": "demo_task",
    "curator_frequency": 1,       # 进行反思总结的频次
    "max_num_rounds": 3,          # 如果做错了允许让 Reflector 指导重试的轮次
    "use_json_mode": False
}

test_data = [
    {
        "question": "解析如下文本并提取关键数字", 
        "context": "项目A总成本 30200 元", 
        "target": "30200"
    }
]

# 3. 驱动作业执行 (开启 eval_only 测试 或 online 训练模式)
# 在执行过程中如果 Curator 总结出了新的普适性经验，终端会提示拦截进行审批
ace_system.run(
    mode="online", 
    test_samples=test_data,
    data_processor=your_data_processor_instance,  # 支持您特定的数据处理器评判真伪
    config=config
)
```

### 4. 经验库日常干预
您不仅可以等待系统自我进化更新规则，由于系统的存储采取了第一层的可读性 JSON 文件设计，您随时可以在运行停止时，使用任何文档编辑器打开 `agent_memory/playbooks/base_rules.json` 进行硬核的“手术刀式”微调，大模型下一次载入时将直接遵循您的最新人工意志！
