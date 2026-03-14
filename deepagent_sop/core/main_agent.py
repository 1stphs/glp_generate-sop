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

    def run(self, user_query: str, experiment_type: str = "小分子模板", enable_learning: bool = True, max_retries: int = 6) -> Dict[str, Any]:
        """
        Execute task autonomously with iterative refinement and inner-loop learning.
        """
        # Step 1: Pre-fetch global rules
        global_memory_context = "\n".join(self.memory_manager.query_rules(experiment_type=experiment_type))

        planning_query = f"""
任务：{user_query}
当前指定的实验类型 (experiment_type)：{experiment_type}
规则库速览：{global_memory_context[:1000]}...
请规划流转步骤。输出 JSON。
"""
        planning_response = self.agent.run(planning_query)
        plan = self._parse_planning(planning_response)
        
        chapter_id = plan.get("chapter_id", "未分类章节")
        current_state = {}
        last_feedback = ""
        last_pathology = ""
        extra_instructions = ""
        is_passed = False

        # Advanced Iterative Loop (Flywheel)
        for attempt in range(1, max_retries + 1):
            print(f"\n[ITERATION {attempt}/{max_retries}] 启动认知大闭环...")
            
            # Start of a fresh iteration trajectory
            iteration_steps = []
            
            # Dynamic Troubleshooting (Main Agent Brain Check)
            if attempt > 1:
                extra_instructions = self._troubleshoot_and_override(attempt, last_feedback, last_pathology)

            for step_info in plan.get("steps", []):
                agent_name = step_info.get("agent")
                params = step_info.get("params", {}).copy()
                
                params["experiment_type"] = experiment_type
                params["section_title"] = chapter_id

                if agent_name == "writer":
                    precise_memory = self.memory_manager.query_rules(experiment_type, chapter_id)
                    params["memory"] = "\n".join(precise_memory)
                    params["feedback"] = last_feedback
                    params["pathology_analysis"] = last_pathology
                    params["extra_instructions"] = extra_instructions
                    params["existing_sop"] = current_state.get("current_sop", "")

                result = self._execute_subagent(agent_name, params)
                current_state.update(result)
                
                # Update trajectory for this iteration
                iteration_steps.append({
                    "step": len(iteration_steps) + 1,
                    "agent": agent_name,
                    "input": params,
                    "output": result,
                    "reasoning": result.get("reasoning", "")
                })

            # Check if passed
            is_passed = current_state.get("is_passed", False)
            if is_passed:
                print(f"✅ 第 {attempt} 次迭代 Review 通过！达到落盘标准。")
                break
            
            # Inner-Loop Learning phase (Trigger Reflector/Curator immediately after failure)
            print(f"⚠️ 第 {attempt} 次迭代未通过。触发内环自进化...")
            
            last_feedback = current_state.get("feedback", current_state.get("error_identification", "排版或结构不符"))
            
            if enable_learning:
                # Reflector: Pathology Analysis
                print("🧠 Reflector 正在分析病灶...")
                reflector_res = self.reflector.extract(iteration_steps, experiment_type=experiment_type)
                last_pathology = reflector_res.get("pathology_analysis", "")
                insights = reflector_res.get("rule_performance", []) # Use rule performance as insights
                key_insight = reflector_res.get("key_insight", "")
                
                # Curator: Knowledge Update
                print("📚 Curator 正在更新 Rules 库...")
                curator_res = self.curator.extract_operations(
                    current_playbook="\n".join(self.memory_manager.query_rules(experiment_type, chapter_id)),
                    insights=[{"content": i.get("reason", ""), "type": i.get("label", "neutral")} for i in insights] + [{"content": key_insight, "type": "insight"}],
                    question_context=f"针对 {experiment_type} 的 {chapter_id} 开发中的病灶修复"
                )
                
                ops = curator_res.get("operations", [])
                self.memory_manager.apply_rules_operations(experiment_type, chapter_id, ops)
                print(f"✨ 已应用 {len(ops)} 条新知识补丁。")

        # Final Persistence
        if is_passed and current_state.get("current_sop"):
            self.memory_manager.save_sop(
                experiment_type=experiment_type,
                chapter_id=chapter_id,
                content=current_state.get("current_sop"),
                quality_score=current_state.get("score", 5.0)
            )
            print(f"💾 SOP 最终版本已入库。")

        # Final audit
        self.memory_manager.log_iteration({
            "timestamp": datetime.now().isoformat(),
            "experiment_type": experiment_type,
            "chapter_id": chapter_id,
            "version": "ACE_Iterative_V2",
            "is_passed": is_passed,
            "attempts_made": attempt,
            "final_score": current_state.get("score", 0),
            "last_feedback": last_feedback
        })

        return {
            "is_passed": is_passed,
            "attempts": attempt,
            "final_sop": current_state.get("current_sop"),
            "summary": f"执行完成，迭代 {attempt} 次，结果 {'通过' if is_passed else '未通过'}"
        }

    def _troubleshoot_and_override(self, attempt: int, last_feedback: str, last_pathology: str) -> str:
        """
        Main Agent Brain Check: Proactively analyze if the system is stuck and generate overrides.
        """
        if not last_feedback and not last_pathology:
            return ""
            
        troubleshoot_query = f"""
你现在作为 Master Orchestrator 进行“排点补差”。
当前已执行到第 {attempt} 轮迭代，但上一轮仍未通过。

【最近反馈】：{last_feedback}
【深层病灶】：{last_pathology}

请给 Writer 下达一个极其简短、强力的“热补丁指令（Extra Instructions）”，直击痛点，防止它继续在这个坑里打转。
如果不确定，请留空。
"""
        # 这种高频决策用 fast 模型即可
        from .config import Config
        fast_config = self.llm_config.copy()
        fast_config["model"] = Config.get_fast_llm_model()
        troubleshooter = DeepAgent(system_prompt="你负责生成简短强力的修正指令。", **fast_config)
        
        return troubleshooter.run(troubleshoot_query)

    def _execute_subagent(self, agent_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        if agent_name == "writer":
            return self.writer.generate_sop(
                original_content=params.get("original_content", ""),
                target_generate_content=params.get("target_generate_content", ""),
                section_title=params.get("section_title", ""),
                experiment_type=params.get("experiment_type", "小分子模板"),
                memory=params.get("memory", ""),
                feedback=params.get("feedback", ""),
                pathology_analysis=params.get("pathology_analysis", ""),
                extra_instructions=params.get("extra_instructions", ""),
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
                original_sop=params.get("current_sop", ""),
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
