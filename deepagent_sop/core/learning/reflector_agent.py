"""
Reflector Agent - Extracts insights from trajectory

Analyzes execution trajectories to extract valuable insights.
Based on prompt from ace/prompts/reflector.py
"""

import json
import re
from typing import Dict, Any, List
from ..base_agent import DeepAgent
from ..utils.prompt_manager import get_prompt


class ReflectorAgent:
    """
    Reflector Agent: Extracts insights from trajectory

    Responsibilities:
    - Analyze complete trajectory
    - Identify deep cognitive root causes
    - Extract Rules specifically tailored to experiment_type
    """

    def __init__(self, llm_config: Dict[str, Any]):
        self.llm_config = llm_config
        self.agent = DeepAgent(system_prompt=get_prompt("reflector"), **llm_config)

    def extract(self, turns: List[Dict[str, Any]], experiment_type: str = "小分子模板", **kwargs) -> Dict[str, Any]:
        """
        Extract insights from cognitive turns history.
        """
        trajectory_str = self._format_trajectory(turns)

        user_prompt = f"""【当前总结提炼的所属实验类型】：{experiment_type}

**运行轨线 (Trajectory)**:
{trajectory_str}

请在全局上帝视角分析这份轨迹图，找出关键漏洞，并凝练出未来加入该实验类型【Rules 规则库】中的**纯普适性 Key Insight（反踩坑法则）**。
"""
        response = self.agent.run(user_prompt)
        return self._parse_response(response)

    def _format_trajectory(self, turns: List[Dict[Dict[str, Any], Any]]) -> str:
        """Format turns history as readable text."""
        lines = []
        for entry in turns:
            turn_num = entry.get("turn", "?")
            agent = entry.get("agent", "unknown")
            directive = entry.get("directive", "")
            result = entry.get("result", {})

            lines.append(f"Turn {turn_num}: [{agent}]")
            if directive:
                lines.append(f"Directive: {directive}")
            
            # Reasoning
            if isinstance(result, dict) and "reasoning" in result:
                lines.append(f"Reasoning: {result['reasoning']}")
            
            # Blocker escalation
            if isinstance(result, dict) and result.get("blocker_escalation"):
                lines.append(f"🚨 BLOCKER: {result['blocker_escalation']}")

            # Output highlight
            if isinstance(result, dict):
                output_str = json.dumps({k: v for k, v in result.items() if k not in ["current_sop", "template_text", "reasoning"]}, ensure_ascii=False)
                lines.append(f"Output: {output_str[:300]}...")

            lines.append("---")

        return "\n".join(lines)

    def _parse_response(self, response: str) -> Dict[str, Any]:
        """
        Parse LLM response as JSON.
        """
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
                "insights": [{"type": "error", "content": "JSON 格式破裂，无法提炼insight"}],
                "summary": f"解析失败: {response[:200]}...",
            }
