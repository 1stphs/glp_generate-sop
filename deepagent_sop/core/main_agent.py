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
    Main Agent - Autonomous Orchestrator

    Responsibilities:
    - Understand user tasks from natural language
    - Query context precisely by experiment_type and chapter_id
    - Coordinate sub-agents (Writer, Simulator, Reviewer)
    - Pass learning metadata to Reflector and Curator
    - Atomically save SOP and Audit Logs to designated paths
    """

    def __init__(
        self,
        llm_config: Dict[str, Any],
        memory_path: str = "deepagent_sop/memory",
    ):
        self.llm_config = llm_config
        
        from .config import Config
        smart_config = llm_config.copy()
        smart_config["model"] = Config.get_smart_llm_model()
        
        fast_config = llm_config.copy()
        fast_config["model"] = Config.get_fast_llm_model()

        # 主控台需要高智商
        self.agent = DeepAgent(system_prompt=get_prompt("main"), **smart_config)

        # 核心写作与反思需最高能力
        self.writer = WriterAgent(smart_config)
        self.reflector = ReflectorAgent(smart_config)
        self.curator = CuratorAgent(smart_config)
        
        # 刻板机械的步骤执行与对撞审查用极速版降本增效
        self.simulator = SimulatorAgent(fast_config)
        self.reviewer = ReviewerAgent(fast_config)

        # Uses the new multi-dimensional storage manager
        self.memory_manager = MemoryManager(base_dir=memory_path)
        self.trajectory_logger = TrajectoryLogger()

    def run(self, user_query: str, experiment_type: str = "小分子模板", enable_learning: bool = True) -> Dict[str, Any]:
        """
        Execute task autonomously.

        Args:
            user_query: Task description
            experiment_type: Global categorization domain for rules/sops (e.g. 小分子模板)
            enable_learning: Whether to trigger learning loop
        """
        # Step 1: Pre-fetch global rules for this exact experiment type to give MainAgent some basic idea
        # We fetch all chapters for planning
        global_memory_context = "\n".join(self.memory_manager.query_rules(experiment_type=experiment_type))

        planning_query = f"""
任务：{user_query}
当前指定的实验类型 (experiment_type)：{experiment_type}

该实验类型下 Rules 层的存量规则库速览：
{global_memory_context[:2000]}

请自主决策：
- 提取任务中的目标章节 (chapter_id) 是什么？
- 规划流转步骤（Writer -> Simulator -> Reviewer 是标准路径）。

输出 JSON 格式：
{{
    "understanding": "...",
    "task_type": "sop_generation | query_only | ...",
    "chapter_id": "提取到的章节名，如果无可填'全局'",
    "steps": [
        {{
            "step_num": 1,
            "agent": "writer | simulator | reviewer | ...",
            "params": {{"需要填入哪些参数"}},
            "reasoning": "..."
        }}
    ]
}}
"""
        planning_response = self.agent.run(planning_query)
        plan = self._parse_planning(planning_response)
        
        chapter_id = plan.get("chapter_id", "未分类章节")

        self.trajectory_logger.log_decision(
            step_num=1,
            agent_name="main_agent",
            input_data={"user_query": user_query, "experiment_type": experiment_type},
            output_data={"plan": plan},
            reasoning=plan.get("understanding", ""),
        )

        current_state = {}
        for step_info in plan.get("steps", []):
            step_num = len(self.trajectory_logger.trajectory) + 1
            agent_name = step_info.get("agent")
            params = step_info.get("params", {})
            reasoning = step_info.get("reasoning", "")

            # 注入 experiment_type 标签，解决上下文真空问题
            params["experiment_type"] = experiment_type

            # If assigning to writer, fetch surgically precise rules as its context
            if agent_name == "writer":
                precise_memory = self.memory_manager.query_rules(experiment_type, chapter_id)
                params["memory"] = "\n".join(precise_memory)
                params["section_title"] = chapter_id  # 确保章节名传递

            self.trajectory_logger.log_decision(
                step_num=step_num,
                agent_name="main_agent",
                input_data={"step": step_info},
                output_data={"decision": "planned_step"},
                reasoning=reasoning,
            )

            result = self._execute_subagent(agent_name, params)

            self.trajectory_logger.log_execution(
                step_num=len(self.trajectory_logger.trajectory) + 1,
                agent_name=agent_name,
                input_data=params,
                output_data=result,
            )
            current_state.update(result)

        # Log daily Audit
        iteration_data = {
            "version": "Version1",
            "sop": str(current_state.get("current_sop", current_state.get("simulated_generate_content", "")))[:1000],
            "sop_id": f"sop_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "experiment_type": experiment_type,
            "quality_assessment": {"is_passed": current_state.get("is_passed"), "feedback": current_state.get("feedback")}
        }
        
        # Save SOP conditionally
        if current_state.get("current_sop") and current_state.get("is_passed", True):
            self.memory_manager.save_sop(
                experiment_type=experiment_type,
                chapter_id=chapter_id,
                content=current_state.get("current_sop"),
                quality_score=current_state.get("score", 5.0)
            )

        # Step 4: Learning loop
        if enable_learning:
            self.trajectory_logger.log_decision(
                step_num=len(self.trajectory_logger.trajectory) + 1,
                agent_name="main_agent",
                input_data={"enable_learning": True},
                output_data={"decision": "进入学习反思阶段"},
                reasoning="提取本次运行高价值经验并固化至 Rules 层",
            )

            trajectory_log = self.trajectory_logger.get_trajectory()
            insights_res = self.reflector.extract(trajectory_log, experiment_type=experiment_type)
            insights = insights_res.get("insights", []) or [insights_res]

            # Fetch the precise current playbook block to let Curator know what already exists
            current_playbook_block = "\n".join(self.memory_manager.query_rules(experiment_type, chapter_id))
            
            curator_res = self.curator.extract_operations(
               current_playbook=current_playbook_block,
               insights=insights,
               question_context=f"针对 {experiment_type} 类型的 {chapter_id} 相关的 SOP 验证"
            )

            # Apply ADD operations specifically to the experimental domain and chapter
            operations = curator_res.get("operations", [])
            self.memory_manager.apply_rules_operations(experiment_type, chapter_id, operations)
            
            iteration_data["curation"] = {"operations_added": len(operations)}

        # Persist audit
        self.memory_manager.log_iteration(iteration_data)

        return {
            "task_understanding": plan.get("understanding", ""),
            "plan": plan,
            "trajectory": self.trajectory_logger.get_trajectory(),
            "final_result": current_state,
            "summary": self._generate_summary(plan, current_state),
        }

    def _execute_subagent(self, agent_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        if agent_name == "writer":
            return self.writer.generate_sop(
                original_content=params.get("original_content", ""),
                target_generate_content=params.get("target_generate_content", ""),
                section_title=params.get("section_title", ""),
                experiment_type=params.get("experiment_type", "小分子模板"),
                memory=params.get("memory", ""),
                feedback=params.get("feedback", ""),
                existing_sop=params.get("existing_sop", ""),
            )
        elif agent_name == "simulator":
            return self.simulator.simulate(
                section_title=params.get("section_title", ""),
                original_content=params.get("original_content", ""),
                current_sop=params.get("current_sop", ""),
                experiment_type=params.get("experiment_type", "小分子模板"),
            )
        elif agent_name == "reviewer":
            return self.reviewer.review(
                simulated_generate_content=params.get("simulated_generate_content", ""),
                target_generate_content=params.get("target_generate_content", ""),
                original_sop=params.get("original_sop", ""),
                original_content=params.get("original_content", ""),
                experiment_type=params.get("experiment_type", "小分子模板"),
            )
        else:
            return {"error": f"Unknown agent: {agent_name}"}

    def _parse_planning(self, response: str) -> Dict[str, Any]:
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", response, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(1))
                except:
                    pass

            match = re.search(r"\{.*\}", response, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group())
                except:
                    pass

            return {
                "understanding": f"未找到JSON格式: {response[:200]}...",
                "task_type": "query_only",
                "chapter_id": "全局",
                "steps": [
                    {
                        "step": 1,
                        "agent": "writer",
                        "params": {},
                        "reasoning": "默认流转",
                    }
                ],
            }

    def _generate_summary(self, plan: Dict[str, Any], final_result: Dict[str, Any]) -> str:
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
- 主要成果已落地为 JSON 或文本。
"""
        return summary
