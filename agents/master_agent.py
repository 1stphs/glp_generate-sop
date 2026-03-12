"""
Master Agent - Core Brain of the System

This is the central orchestrator that:
1. Understands user tasks from natural language descriptions
2. Autonomously plans and decomposes tasks
3. Decides which sub-agents to call and in what order
4. Coordinates the overall execution flow
5. Collects results and returns them to the user

Key Design:
- Completely natural language driven - NO hardcoded workflows
- Makes autonomous decisions based on task understanding
- Must output reasoning process (for auditability)
- Must explain decision rationale (for human understanding)
"""

from typing import Dict, Any, List
import json


class MasterAgent:
    """
    Master Agent: The autonomous core brain of the DeepAgent system.

    This agent receives natural language task descriptions and autonomously:
    1. Understands user intent
    2. Plans task decomposition
    3. Decides which sub-agents to call
    4. Coordinates overall execution
    5. Handles exceptions and errors
    6. Returns final results

    CRITICAL: Do NOT predefine any workflows. Make autonomous decisions
    based entirely on natural language understanding.
    """

    def __init__(self, llm_config: Dict[str, Any]):
        """
        Initialize Master Agent.

        Args:
            llm_config: Configuration for LLM client
                - api_provider: "openai", "anthropic", etc.
                - model: Model name
                - temperature: Generation temperature
                - max_tokens: Max tokens per response
        """
        self.llm_config = llm_config
        self.context = {}

    def execute(self, user_task: str) -> Dict[str, Any]:
        """
        Execute user task from natural language description.

        Args:
            user_task: Natural language task description
                Example: "用第1份protocol和report生成5个章节的SOP，并进行3轮迭代优化"

        Returns:
            Dictionary containing:
            - reasoning: How Master Agent understood the task
            - plan: Execution plan (which agents to call, in what order)
            - execution_results: Results from each sub-agent
            - final_summary: Final answer to user
        """

        # Call LLM with system prompt that emphasizes autonomous decision making
        system_prompt = self._get_system_prompt()
        user_prompt = f"""用户任务：{user_task}

请自主完成这个任务。"""

        # TODO: Implement LLM call
        response = ""

        return self._parse_master_response(response)

    def _get_system_prompt(self) -> str:
        """
        Get the system prompt for Master Agent.

        This is CRITICAL - it must emphasize:
        1. Natural language decision making
        2. No predefined workflows
        3. Autonomous planning
        4. Reasoning output
        """
        return """你是Master Agent，是整个系统的核心大脑。

你的职责：
1. 理解用户的自然语言任务
2. 自主规划和拆解任务
3. 调用合适的子Agent完成工作
4. 协调整体流程，处理异常
5. 收集结果并返回给用户

可用的子Agent：
- InsightAgent: 从执行轨迹中提取经验和教训
  输入：trajectory（完整执行过程）
  输出：insights（经验内容 + 应用场景）

- PlaybookAgent: 管理和查询持久化经验库
  输入：query 或 insights
  输出：matching_rules 或 updated_playbook

- ACE系统: 生成SOP、反思质量、提炼规则
  包含：Generator（生成器）, Reflector（反思器）, Curator（策展人）
  功能：经验生成 + 管理
  
工作方式：
- 完全基于自然语言决策
- 不要写死任何流程
- 根据任务描述动态选择要调用的Agent
- 保持对话式的思考过程
- 每一步都要说明你的决策理由

输出格式：
你的响应应该包含：
1. 思考过程（reasoning）：你如何理解任务，打算怎么做
2. 执行计划（plan）：你要调用哪些Agent，按什么顺序
3. 执行结果（execution_results）：每个Agent的返回结果
4. 最终总结（final_summary）：给用户的最终答案

重要约束：
- 必须用自然语言描述你的决策
- 不要预设任何固定的workflow
- 每次任务都要重新规划
- 如果遇到不确定的情况，明确说明并尝试最优方案

示例任务分析：
用户说："生成5个章节的SOP并进行3轮迭代"
你的思考应该包括：
- 需要加载哪些数据
- 需要调用ACE系统生成SOP
- 需要控制迭代次数
- 最后需要提取trajectory
- 是否需要更新playbook
"""

    def _parse_master_response(self, response: str) -> Dict[str, Any]:
        """
        Parse Master Agent response.

        TODO: Implement parsing logic to extract:
        - reasoning
        - plan
        - execution_results
        - final_summary
        """
        return {
            "reasoning": "",
            "plan": "",
            "execution_results": {},
            "final_summary": "",
        }
