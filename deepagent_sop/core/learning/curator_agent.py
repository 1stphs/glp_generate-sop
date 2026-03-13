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
    Curator Agent: Maintains and optimizes memory

    Responsibilities:
    - Integrate new insights into memory
    - Deduplicate existing content
    - Clean up ineffective insights
    - Maintain memory quality
    """

    def __init__(self, llm_config: Dict[str, Any]):
        """
        Initialize Curator Agent.

        Args:
            llm_config: LLM configuration
        """
        self.llm_config = llm_config
        self.agent = DeepAgent(system_prompt=get_prompt("curator"), **llm_config)

    def update(
        self, memory_content: str, insights: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Update memory with new insights.

        Args:
            memory_content: Current memory content
            insights: New insights to integrate

        Returns:
            {
                "updated_memory": "Complete updated memory",
                "changes_summary": {
                    "added_insights": 5,
                    "updated_insights": 3,
                    "removed_insights": 1,
                    "duplicates_found": 2
                },
                "recommendations": "Management recommendations"
            }
        """
        # Format insights as text
        insights_str = self._format_insights(insights)

        # Build user prompt
        user_prompt = f"""**Current Memory**:
{memory_content[:5000]}...

**New Insights**:
{insights_str}

Please integrate these new insights into the memory.
"""

        # Call LLM
        response = self.agent.run(user_prompt)

        # Parse response
        result = self._parse_response(response)

        # If parsing failed, return original memory
        if not result or "updated_memory" not in result:
            return {
                "updated_memory": memory_content,
                "changes_summary": {
                    "added_insights": 0,
                    "updated_insights": 0,
                    "removed_insights": 0,
                    "duplicates_found": 0,
                },
                "recommendations": "Failed to update memory - returned original",
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
                "updated_memory": "",
                "changes_summary": {
                    "added_insights": 0,
                    "updated_insights": 0,
                    "removed_insights": 0,
                    "duplicates_found": 0,
                },
                "recommendations": f"解析失败: {response[:200]}...",
            }
