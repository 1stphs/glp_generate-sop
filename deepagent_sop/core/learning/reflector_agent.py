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
    - Identify successful patterns and failed attempts
    - Extract actionable insights
    - Tag insights with applicability metadata
    """

    def __init__(self, llm_config: Dict[str, Any]):
        """
        Initialize Reflector Agent.

        Args:
            llm_config: LLM configuration
        """
        self.llm_config = llm_config
        self.agent = DeepAgent(system_prompt=get_prompt("reflector"), **llm_config)

    def extract(self, trajectory: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Extract insights from trajectory.

        Args:
            trajectory: Complete execution trajectory

        Returns:
            {
                "insights": [
                    {
                        "type": "rule_success | rule_failure | problem_solution | pattern_discovery",
                        "content": "Insight content",
                        "context": "Applicable scenario",
                        "evidence": "Evidence from trajectory",
                        "applicability": {...}
                    }
                ],
                "summary": "Natural language summary"
            }
        """
        # Build prompt from trajectory
        trajectory_str = self._format_trajectory(trajectory)

        user_prompt = f"""**Trajectory**:
{trajectory_str}

Please analyze this trajectory and extract valuable insights.
"""

        # Call LLM
        response = self.agent.run(user_prompt)

        # Parse response
        result = self._parse_response(response)

        return result

    def _format_trajectory(self, trajectory: List[Dict[str, Any]]) -> str:
        """Format trajectory as readable text."""
        lines = []
        for entry in trajectory:
            step_num = entry.get("step", "?")
            agent = entry.get("agent", "unknown")
            step_type = entry.get("type", "unknown")
            reasoning = entry.get("reasoning", "")

            lines.append(f"Step {step_num}: {agent} ({step_type})")
            if reasoning:
                lines.append(f"Reasoning: {reasoning}")

            # Include key input/output info
            input_data = entry.get("input", {})
            output_data = entry.get("output", {})

            if input_data:
                lines.append(f"Input keys: {list(input_data.keys())}")
            if output_data:
                lines.append(f"Output keys: {list(output_data.keys())}")

            lines.append("---")

        return "\n".join(lines)

    def _parse_response(self, response: str) -> Dict[str, Any]:
        """
        Parse LLM response as JSON.

        Args:
            response: LLM response string

        Returns:
            Parsed dictionary
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

            # Return mock data if parsing fails
            return {
                "insights": [],
                "summary": f"解析失败: {response[:200]}...",
            }
