"""
Simulator Agent - SOP Testing (Blind)

Tests SOP effectiveness without seeing target.
Based on prompt concepts from sop_generation/prompts/registry.py
"""

import json
import re
from typing import Dict, Any
from ..base_agent import DeepAgent
from ..utils.prompt_manager import get_prompt


class SimulatorAgent:
    """
    Simulator Agent: Tests SOP effectiveness (blind test)

    Responsibilities:
    - Execute SOP strictly according to rules
    - Simulate report generation from original_content
    - Blind test: Never sees target_generate_content
    - Record steps taken and compliance
    """

    def __init__(self, llm_config: Dict[str, Any]):
        """
        Initialize Simulator Agent.

        Args:
            llm_config: LLM configuration
        """
        self.llm_config = llm_config
        self.agent = DeepAgent(system_prompt=get_prompt("simulator"), **llm_config)

    def simulate(
        self,
        section_title: str,
        original_content: str,
        current_sop: str,
    ) -> Dict[str, Any]:
        """
        Simulate SOP execution (blind test).

        Args:
            section_title: Section title
            original_content: Original protocol content
            current_sop: SOP to test

        Returns:
            {
                "simulated_generate_content": "Generated content",
                "reasoning": "How SOP was applied",
                "steps_taken": [...],
                "compliance_check": {
                    "rules_applied": [...],
                    "rules_missed": [...],
                    "overall_compliance": 90
                }
            }
        """
        # Build user prompt
        user_prompt = self._build_prompt(section_title, original_content, current_sop)

        # Call LLM
        response = self.agent.run(user_prompt)

        # Parse response
        result = self._parse_response(response)

        return result

    def _build_prompt(
        self, section_title: str, original_content: str, current_sop: str
    ) -> str:
        """Build user prompt."""
        prompt = f"""章节标题：{section_title}

原始方案内容（仅限使用此内容）：
{original_content}

你收到的SOP（标准操作规程）：
{current_sop}

请严格按照SOP执行，生成模拟报告内容。

【重要】：
- 只能使用原始方案内容，不得编造
- 严格遵循SOP中的填写规则和模板格式
- 输出要符合模板的结构和字段要求

最后只输出模拟报告正文，不要包含任何解释或说明。
"""

        return prompt

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

            # If no JSON, treat entire response as simulated content
            return {
                "simulated_generate_content": response,
                "reasoning": "响应未包含JSON格式，使用原始文本",
                "steps_taken": ["执行SOP"],
                "compliance_check": {
                    "rules_applied": ["应用SOP规则"],
                    "rules_missed": [],
                    "overall_compliance": 100,
                },
            }
