# DeepAgent SOP 自动化生成框架

本项目是一个基于大模型（LLM）的智能体群（Multi-Agent System），旨在通过逆向工程从实验原始资料和目标报告中提取标准化操作规程（SOP），并将其持久化为动态的 Rules（规则库）和 SOP Templates（模板库）。

## 核心架构：三层记忆系统

系统采用了重构后的结构化 JSON 存储，分为三层感知：
1.  **Rules 层 (`memory/rules/`)**：按实验类型存储高度泛化的、具有指令性的“实战经验”。这是系统的大脑。
2.  **SOP Templates 层 (`memory/sop_templates/`)**：按实验类型和章节存储校验通过的 SOP 模板。
3.  **Audit Log 层 (`memory/audit_log/`)**：记录每一场执行的完整轨迹和质量指标，用于后期审计与进化分析。

## 如何启动项目

### 1. 环境配置
- **Python**: ≥ 3.10
- **依赖管理**: 推荐使用 `uv` 或 `pip`
  ```bash
  pip install -r requirements.txt
  ```
- **环境变量**: 复制 `.env.example` 为 `.env`，并配置您的 LLM API Key (支持 OpenAI 格式、DeepSeek 等)。

### 2. 运行全链路测试/演示
我们提供了一个标准的测试脚本，展示了从 Writer 到 Reviewer 的完整闭环流程：
```bash
python deepagent_sop/tests/test_full_pipeline.py
```
该脚本将演示：
1.  **Writer** 逆向生成第一版 SOP。
2.  **Simulator** 盲测该 SOP。
3.  **Reviewer** 找茬并输出反馈。
4.  **Reflector & Curator** 提炼经验并写入 Rules 层。

### 3. 主程序入口
您可以参考 `deepagent_sop/main.py` 通过 API 或者直接调用 `MainAgent` 类来启动任务：
```python
from deepagent_sop.core.main_agent import MainAgent

main_agent = MainAgent(llm_config={...})
result = main_agent.run(
    user_query="为【小分子模板】实验类型中的『16.2声明』章节生成SOP",
    experiment_type="小分子模板"
)
```

## 关于后续优化生成质量

> **问：后续优化生成质量是否只需要调整提示词？**

**答案是：提示词（Prompting）是最快且最核心的手段，但不是唯一。**

1.  **提示词优化（核心）**：
    -   **Writer Agent**: 如果 SOP 结构不够精准，需调整 `WRITER_SYSTEM_PROMPT` 中关于 HTML 表格或占位符的约束。
    -   **Reviewer Agent**: 如果找茬不够狠，需在 `REVIEWER_SYSTEM_PROMPT` 中增加更严苛的排版核验逻辑。
    -   所有提示词现在均统一管理在 `deepagent_sop/core/utils/prompt_manager.py`。

2.  **Rules 经验池积累（自动优化）**：
    -   系统的生成质量会随着 Rules 库的丰富而自动提高。
    -   您可以手动在 `memory/rules/rules_{experiment_type}.json` 中加入您认为“必踩的坑”或“绝对禁令”，系统在下一次生成该章节或该类型 SOP 时会自动读取这些 Rules。

3.  **模型能力的选择**：
    -   `main_agent.py` 中区分为 `smart_llm` (负责写作与思考) 和 `fast_llm` (负责模拟与审核)。
    -   如果逻辑推导错误多，建议给 `Writer` 配置能力更强的模型（如 GPT-4o, Claude-3.5-Sonnet）。

4.  **Few-Shot（少量样本）引导**：
    -   如果某些章节极难生成，可以在 `prompt_manager.py` 中为对应的 Agent 加入 1-2 个该实验类型下的“完美生成案例”。


