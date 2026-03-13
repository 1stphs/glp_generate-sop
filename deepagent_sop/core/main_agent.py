"""
Main Agent - Autonomous Orchestrator

Core brain that autonomously plans and coordinates all sub-agents.
Based on prompt from agents/master_agent.py
"""

import json
import re
from typing import Dict, Any, List
from datetime import datetime

from .base_agent import DeepAgent
from .subagents.writer_agent import WriterAgent
from .subagents.simulator_agent import SimulatorAgent
from .subagents.reviewer_agent import ReviewerAgent
from .learning.reflector_agent import ReflectorAgent
from .learning.curator_agent import CuratorAgent
from .utils.memory_manager import MemoryManager
from .utils.trajectory_logger import TrajectoryLogger
from .utils.prompt_manager import get_prompt


class MainAgent:
    """
    Main Agent - Autonomous Orchestrator, not executor.

    Only makes decisions, delegates work to sub-agents.

    Responsibilities:
    - Understand user tasks from natural language
    - Autonomous planning (NO hardcoded workflows)
    - Dynamic sub-agent selection and coordination
    - Record complete trajectory
    - Handle learning loop if enabled
    """

    def __init__(
        self,
        llm_config: Dict[str, Any],
        memory_path: str = "deepagent_sop/memory/memory.md",
    ):
        """
        Initialize Main Agent.

        Args:
            llm_config: LLM configuration
            memory_path: Path to memory.md
        """
        self.llm_config = llm_config
        self.memory_path = memory_path

        # Initialize Main Agent's own LLM for planning
        self.agent = DeepAgent(system_prompt=get_prompt("main"), **llm_config)

        # Initialize sub-agents
        self.writer = WriterAgent(llm_config)
        self.simulator = SimulatorAgent(llm_config)
        self.reviewer = ReviewerAgent(llm_config)
        self.reflector = ReflectorAgent(llm_config)
        self.curator = CuratorAgent(llm_config)

        # Initialize utilities
        self.memory_manager = MemoryManager(memory_path)
        self.trajectory_logger = TrajectoryLogger()

    def run(self, user_query: str, enable_learning: bool = True) -> Dict[str, Any]:
        """
        Execute task autonomously.

        Args:
            user_query: User task description (e.g., "生成验证报告章节SOP，3轮迭代")
            enable_learning: Whether to trigger learning loop

        Returns:
            {
                "task_understanding": "Main Agent's understanding of the task",
                "plan": "Autonomous execution plan",
                "trajectory": [Complete decision+execution records],
                "final_result": "Final result",
                "summary": "Summary for the user"
            }
        """
        # Step 1: Load memory
        memory_content = self.memory_manager.read()

        # Step 2: Understand task and plan (core: autonomous decision, not fixed workflow)
        planning_query = f"""
任务：{user_query}

Memory上下文（前2000字）：
{memory_content[:2000]}

请自主决策：
- 需要哪些sub-agent？
- 以什么顺序？
- 每个agent传什么参数？

输出JSON格式：
{{
    "understanding": "你如何理解这个任务",
    "task_type": "sop_generation | query_only | ...",
    "steps": [
        {{
            "step": 1,
            "agent": "writer | simulator | reviewer | ...",
            "params": {{具体的参数}},
            "reasoning": "为什么选这个agent做这件事"
        }}
    ]
}}

🔑 关键：不要预设固定流程！每任务都要重新规划！
"""

        planning_response = self.agent.run(planning_query)
        plan = self._parse_planning(planning_response)

        # Log planning decision
        self.trajectory_logger.log_decision(
            step_num=1,
            agent_name="main_agent",
            input_data={"user_query": user_query},
            output_data={"plan": plan},
            reasoning=plan.get("understanding", ""),
        )

        # Step 3: Execute plan (dynamic, non-fixed)
        current_state = {}
        for step_info in plan.get("steps", []):
            step_num = len(self.trajectory_logger.trajectory) + 1
            agent_name = step_info.get("agent")
            params = step_info.get("params", {})
            reasoning = step_info.get("reasoning", "")

            # Record decision
            self.trajectory_logger.log_decision(
                step_num=step_num,
                agent_name="main_agent",
                input_data={"step": step_info},
                output_data={"decision": "planned_step"},
                reasoning=reasoning,
            )

            # Execute (delegate to sub-agent)
            result = self._execute_subagent(agent_name, params)

            # Record execution result
            self.trajectory_logger.log_execution(
                step_num=len(self.trajectory_logger.trajectory) + 1,
                agent_name=agent_name,
                input_data=params,
                output_data=result,
            )

            # Update state (pass to next step)
            current_state.update(result)

        # Step 4: Learning loop (if enabled)
        if enable_learning:
            # Record learning stage decision
            self.trajectory_logger.log_decision(
                step_num=len(self.trajectory_logger.trajectory) + 1,
                agent_name="main_agent",
                input_data={"enable_learning": True},
                output_data={"decision": "进入学习阶段"},
                reasoning=f"任务执行完成，开始学习",
            )

            # Reflector extracts insights
            trajectory = self.trajectory_logger.get_trajectory()
            insights = self.reflector.extract(trajectory)

            self.trajectory_logger.log_decision(
                step_num=len(self.trajectory_logger.trajectory) + 1,
                agent_name="main_agent",
                input_data={"trajectory_length": len(trajectory)},
                output_data={"insights_count": len(insights.get("insights", []))},
                reasoning=f"提取了{len(insights.get('insights', []))}条insights",
            )

            # Curator updates memory
            new_memory = self.curator.update(
                memory_content, insights.get("insights", [])
            )

            self.trajectory_logger.log_decision(
                step_num=len(self.trajectory_logger.trajectory) + 1,
                agent_name="main_agent",
                input_data={"insights_count": len(insights.get("insights", []))},
                output_data={
                    "updated_memory": True,
                    "changes_summary": new_memory.get("changes_summary", {}),
                },
                reasoning=f"用insights更新memory",
            )

            # Write back to memory
            self.memory_manager.write(new_memory.get("updated_memory", memory_content))

        # Step 5: Return
        return {
            "task_understanding": plan.get("understanding", ""),
            "plan": plan,
            "trajectory": self.trajectory_logger.get_trajectory(),
            "final_result": current_state,
            "summary": self._generate_summary(plan, current_state),
        }

    def _execute_subagent(
        self, agent_name: str, params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute sub-agent based on name and params.

        Args:
            agent_name: Name of agent to execute
            params: Parameters to pass to agent

        Returns:
            Agent execution result
        """
        if agent_name == "writer":
            return self.writer.generate_sop(
                original_content=params.get("original_content", ""),
                target_generate_content=params.get("target_generate_content", ""),
                section_title=params.get("section_title", ""),
                memory=params.get("memory", ""),
                feedback=params.get("feedback", ""),
                existing_sop=params.get("existing_sop", ""),
            )
        elif agent_name == "simulator":
            return self.simulator.simulate(
                section_title=params.get("section_title", ""),
                original_content=params.get("original_content", ""),
                current_sop=params.get("current_sop", ""),
            )
        elif agent_name == "reviewer":
            return self.reviewer.review(
                simulated_generate_content=params.get("simulated_generate_content", ""),
                target_generate_content=params.get("target_generate_content", ""),
                original_sop=params.get("original_sop", ""),
                original_content=params.get("original_content", ""),
            )
        else:
            return {"error": f"Unknown agent: {agent_name}"}

    def _parse_planning(self, response: str) -> Dict[str, Any]:
        """
        Parse Main Agent's planning response.

        Args:
            response: LLM response string

        Returns:
            Parsed plan dictionary
        """
        try:
            # Try to parse as JSON directly
            return json.loads(response)
        except json.JSONDecodeError:
            # Try to extract JSON from markdown code block
            match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", response, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(1))
                except:
                    pass

            # Try to find first JSON object
            match = re.search(r"\{.*\}", response, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group())
                except:
                    pass

            # If not JSON, return a simple plan
            return {
                "understanding": f"未找到JSON格式，Main Agent返回：{response[:200]}...",
                "task_type": "query_only",
                "steps": [
                    {
                        "step": 1,
                        "agent": "writer",
                        "params": {},
                        "reasoning": "默认执行writer",
                    }
                ],
            }

    def _generate_summary(
        self, plan: Dict[str, Any], final_result: Dict[str, Any]
    ) -> str:
        """
        Generate natural language summary.

        Args:
            plan: Execution plan
            final_result: Final execution result

        Returns:
            Summary text
        """
        understanding = plan.get("understanding", "未知任务")
        steps_executed = len(plan.get("steps", []))
        final_status = "completed"

        summary = f"""
任务理解：{understanding}

执行概要：
- 执行了{steps_executed}个步骤
- 最终状态：{final_status}
- 记录了{len(self.trajectory_logger.trajectory)}条trajectory

总结：
- 主要成果：{final_result.get("current_sop", "N/A")}
- 关键洞察：已记录到trajectory
"""
        return summary
