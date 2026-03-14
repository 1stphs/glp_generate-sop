"""
Curator Agent - Maintains and updates memory

Integrates new insights into memory.
Based on prompt from ace/prompts/curator.py
"""

import json
import re
from typing import Dict, Any, List
from ..base_agent import DeepAgent
from ..utils.prompt_manager import get_prompt


class CuratorAgent:
    """
    Curator Agent: Maintains and optimizes memory Rules

    Responsibilities:
    - Receive insights from Reflector
    - Generate specific ADD operations for the Playbook/Rules
    - Strictly guard against data leakage (no specific values allowed in rules)
    """

    def __init__(self, llm_config: Dict[str, Any]):
        """
        Initialize Curator Agent.

        Args:
            llm_config: LLM configuration
        """
        self.llm_config = llm_config
        self.agent = DeepAgent(system_prompt=get_prompt("curator"), **llm_config)

    def extract_operations(
        self, current_playbook: str, insights: List[Dict[str, Any]], question_context: str
    ) -> Dict[str, Any]:
        """
        Extract 'operations' to be applied to the Rules file.

        Args:
            current_playbook: Existing Rules
            insights: New insights extracted by Reflector
            question_context: Context of the current task/chapter

        Returns:
            {
                "reasoning": "...",
                "operations": [
                    {
                        "type": "ADD",
                        "section": "rules",
                        "content": "..."
                    }
                ]
            }
        """
        insights_str = self._format_insights(insights)

        # Build user prompt according to the new prompt requirements
        user_prompt = f"""
{{
  "playbook_stats": "Total Rules Count: {len(current_playbook.split('Rule ID:')) - 1}",
  "recent_reflection": {json.dumps(insights_str, ensure_ascii=False)},
  "current_playbook": {json.dumps(current_playbook, ensure_ascii=False)},
  "question_context": {json.dumps(question_context, ensure_ascii=False)}
}}
"""

        # Call LLM
        response = self.agent.run(user_prompt)

        # Parse response
        result = self._parse_response(response)

        if not result or "operations" not in result:
            return {
                "reasoning": "解析失败或未产生有效操作",
                "operations": []
            }

        return result

    def _format_insights(self, insights: List[Dict[str, Any]]) -> str:
        """Format insights as readable text."""
        lines = []
        for insight in insights:
            insight_type = insight.get("type", "unknown")
            content = insight.get("content", "")
            context = insight.get("context", "")

            lines.append(f"- Type: {insight_type}")
            lines.append(f"  Content: {content}")
            lines.append(f"  Context: {context}")
            lines.append("")

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
                "reasoning": f"JSON解析致命失败: {response[:200]}...",
                "operations": []
            }
