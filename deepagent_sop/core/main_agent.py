"""
Main Agent - Autonomous Orchestrator

Core brain that autonomously plans and coordinates all sub-agents.
Based on prompt from agents/master_agent.py
"""

import os
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
from .learning.skill_builder_agent import SkillBuilderAgent
from .utils.memory_manager import MemoryManager
from .utils.trajectory_logger import TrajectoryLogger
from .utils.prompt_manager import get_prompt, MAIN_SYSTEM_PROMPT
from .utils.skill_manager import SkillManager


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
        self.reviewer = ReviewerAgent(fast_config)

        # Learning and Evolution
        self.reflector = ReflectorAgent(smart_config)
        self.curator = CuratorAgent(smart_config)
        self.skill_builder = SkillBuilderAgent(smart_config)

        # Uses the new multi-dimensional storage manager
        self.memory_manager = MemoryManager(base_dir=memory_path)
        self.skill_manager = SkillManager(skill_dir=os.path.join(memory_path, "skills"))
        self.trajectory_logger = TrajectoryLogger()

    def run(self, user_query: str, experiment_type: str = "小分子模板", enable_learning: bool = True, max_turns: int = 15) -> Dict[str, Any]:
        """
        Execute task with dynamic ReAct loop.
        """
        global_memory_context = "\n".join(self.memory_manager.query_rules(experiment_type=experiment_type))
        
        # Identifying chapter (one-shot query)
        chapter_res = self.agent.run(
            f"请识别以下任务的章节ID。\n任务：{user_query}\n实验类型：{experiment_type}\n请输出 JSON: {{'chapter_id': '...'}}"
        )
        try:
            chapter_id = json.loads(chapter_res).get("chapter_id", "未知章节")
        except:
            chapter_id = "未知章节"

        state = {
            "current_sop": "",
            "is_passed": False,
            "score": 0,
            "last_feedback": "",
            "last_pathology": "",
            "forged_skills": self.skill_manager.list_skills(experiment_type),
            "iteration_count": 0,
            "turns": []
        }

        print(f"🚀 [ROOT] 开始执行任务: {chapter_id} ({experiment_type})")

        for turn in range(1, max_turns + 1):
            state["iteration_count"] = turn
            print(f"\n[TURN {turn}/{max_turns}] 主控大脑决策中...")
            
            # 1. Decide next action
            decision = self._decide_next_action(user_query, experiment_type, chapter_id, state)
            
            if decision.get("is_task_completed"):
                print("🏁 主控大脑确认任务已按最高标准完成。")
                break
                
            action = decision.get("next_action", {})
            target_agent = action.get("target_agent")
            directive = action.get("directive", "")
            input_data = action.get("required_input_data", {})
            
            print(f"📡 调度指令 -> [{target_agent}]: {directive[:100]}...")
            
            # 3. Execute action
            result = self._execute_action(target_agent, experiment_type, chapter_id, directive, input_data, state)
            
            # 4. Update state
            state["turns"].append({
                "turn": turn,
                "agent": target_agent,
                "directive": directive,
                "result": result
            })
            
            if target_agent == "simulator":
                state["simulated_generate_content"] = result.get("simulated_generate_content", "")

            # Standard updates
            if "current_sop" in result: state["current_sop"] = result["current_sop"]
            if "is_passed" in result: state["is_passed"] = result["is_passed"]
            if "score" in result: state["score"] = result["score"]
            if "feedback" in result: state["last_feedback"] = result["feedback"]
            if "pathology_analysis" in result: state["last_pathology"] = result["pathology_analysis"]
            if target_agent == "skill_builder" and "skill_name" in result:
                state["forged_skills"].append(result["skill_name"])

            # 4. Learning trigger (if reflector or curator was called, learning happened)
            if target_agent == "curator":
                print("✨ 知识库已完成动态扩容。")

        # Persistence
        if state["is_passed"] and state["current_sop"]:
            self.memory_manager.save_sop(experiment_type, chapter_id, state["current_sop"], state["score"])
            print(f"💾 SOP 完美版已落盘入库。")

        return {
            "is_passed": state["is_passed"],
            "turns": turn,
            "final_sop": state["current_sop"],
            "summary": f"执行完成，共耗费 {turn} 个决策周期。"
        }

    def _decide_next_action(self, user_query: str, experiment_type: str, chapter_id: str, state: Dict[str, Any]) -> Dict[str, Any]:
        snapshot = {
            "user_query": user_query,
            "experiment_type": experiment_type,
            "chapter_id": chapter_id,
            "is_passed_last_time": state["is_passed"],
            "score": state["score"],
            "last_feedback": state["last_feedback"],
            "last_pathology": state["last_pathology"],
            "forged_skills": state["forged_skills"],
            "history_summary": [f"T{t['turn']}: {t['agent']} -> {t['result'].get('is_passed', 'N/A')}" for t in state["turns"][-3:]]
        }
        
        # Add rules context if available
        rules_context = "\n".join(self.memory_manager.query_rules(experiment_type, chapter_id))
        
        prompt = f"系统当前状态快照:\n{json.dumps(snapshot, ensure_ascii=False, indent=2)}\n\n规则参考:\n{rules_context[:2000]}\n\n请做出决策。"
        
        response = self.agent.run(prompt)
        try:
            return json.loads(response)
        except:
            # Fallback
            return {"is_task_completed": False, "next_action": {"target_agent": "writer", "directive": "继续完善SOP"}}

    def _execute_action(self, agent_name: str, experiment_type: str, chapter_id: str, directive: str, input_data: Any, state: Dict[str, Any]) -> Dict[str, Any]:
        # Resolve skill output if requested in input_data or directive
        skill_outputs = []
        for skill_name in state["forged_skills"]:
            try:
                # We try to run all relevant skills to get their context
                # In a more advanced version, we'd only run specific ones per Main's request
                output = self.skill_manager.execute_skill(experiment_type, skill_name, input_data)
                skill_outputs.append(f"--- Skill: {skill_name} Output ---\n{json.dumps(output, ensure_ascii=False)}")
            except:
                pass

        params = {
            "experiment_type": experiment_type,
            "section_title": chapter_id,
            "extra_instructions": directive,
            "original_content": input_data,
            "current_sop": state["current_sop"],
            "memory": "\n".join(self.memory_manager.query_rules(experiment_type, chapter_id)),
            "feedback": state["last_feedback"],
            "pathology_analysis": state["last_pathology"],
            "forged_skills": "\n\n".join(skill_outputs)
        }
        
        if agent_name == "writer":
            # If input_data is a dict from ReAct, we might need a specific field
            target_content = input_data if isinstance(input_data, str) else ""
            return self.writer.generate_sop(
                target_generate_content=target_content,
                **params
            )
        elif agent_name == "simulator":
            return self.simulator.simulate(**params)
        elif agent_name == "reviewer":
            # Reviewer needs special handling for simulated content
            # If the last turn was simulator, we get its result
            sim_content = ""
            for turn_record in reversed(state["turns"]):
                if turn_record["agent"] == "simulator":
                    sim_content = turn_record["result"].get("simulated_generate_content", "")
                    break
            
            return self.reviewer.review(
                simulated_generate_content=sim_content,
                target_generate_content=input_data if isinstance(input_data, str) else "",
                original_content="", 
                experiment_type=experiment_type,
                current_sop=state["current_sop"]
            )
        elif agent_name == "reflector":
            return self.reflector.extract(state["turns"], experiment_type)
        elif agent_name == "curator":
            return self.curator.extract_operations(
                current_playbook=params["memory"],
                insights=[{"content": state["last_pathology"], "type": "pathology"}],
                question_context=f"修订 {chapter_id}"
            )
        elif agent_name == "skill_builder":
            skill_data = self.skill_builder.forge_skill(directive)
            if "python_code" in skill_data:
                self.skill_manager.save_skill(experiment_type, skill_data["skill_name"], skill_data["python_code"])
            return skill_data
        else:
            return {"error": f"Unknown agent {agent_name}"}

    def _execute_skill(self, experiment_type: str, skill_name: str, input_data: Any) -> Any:
        return self.skill_manager.execute_skill(experiment_type, skill_name, input_data)
