"""
Reviewer Agent - SOP Quality Evaluation

Evaluates SOP quality by comparing with target.
Based on prompt from sop_generation/prompts/registry.py
"""

import json
import re
from typing import Dict, Any
from ..base_agent import DeepAgent
from ..utils.prompt_manager import get_prompt


class ReviewerAgent:
    """
    Reviewer Agent: Evaluates SOP quality

    Responsibilities:
    - Compare simulated content with target content
    - Identify format, structure, content issues
    - Provide actionable feedback for improvement
    - Evaluate only: structure, format, template consistency
    - NOT evaluate: specific factual differences (e.g., name changes)
    """

    def __init__(self, llm_config: Dict[str, Any]):
        """
        Initialize Reviewer Agent.

        Args:
            llm_config: LLM configuration
        """
        self.llm_config = llm_config
        self.agent = DeepAgent(system_prompt=get_prompt("reviewer"), **llm_config)

    def review(
        self,
        simulated_generate_content: str,
        target_generate_content: str,
        original_sop: str,
        original_content: str = "",
    ) -> Dict[str, Any]:
        """
        Review SOP quality.

        Args:
            simulated_generate_content: Simulator generated content
            target_generate_content: Target report content (ground truth)
            original_sop: SOP used for generation
            original_content: Original protocol content (optional, for reference only)

        Returns:
            {
                "is_passed": true/false,
                "feedback": {
                    "format_issues": [...],
                    "content_issues": [...],
                    "missing_elements": [...]
                },
                "error_identification": "...",
                "root_cause_analysis": "...",
                "correct_approach": "..."
            }
        """
        # Build user prompt
        user_prompt = self._build_prompt(
            simulated_generate_content,
            target_generate_content,
            original_sop,
            original_content,
        )

        # Call LLM
        response = self.agent.run(user_prompt)

        # Parse response
        result = self._parse_response(response)

        return result

    def _build_prompt(
        self,
        simulated_content: str,
        target_content: str,
        original_sop: str,
        original_content: str,
    ) -> str:
        """Build user prompt."""
        prompt = f"""**目标优质报告内容**:
{target_content}

**正在审查的 SOP 草案**:
{original_sop}

**盲测模拟作答结果**:
{simulated_content}
"""

        if original_content:
            prompt += f"""
**防幻觉参考_方案原始内容**:
{original_content}
"""

        prompt += """
**你的任务：**
请严格进行三方比对。找出模拟作答结果和目标优质报告内容之间的任何排版、换行或字段丢失差异（忽略完全合理的举例随机名称替换）。

若不通过，请务必找到导致这个差异产生的**根本原因**（SOP 哪不严密），并在 `correct_approach` 和 `feedback` 中给出可执行的 SOP 修改建议。

请直接输出纯 JSON，不包含 Markdown。
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

            # Return mock data if parsing fails
            return {
                "is_passed": False,
                "feedback": {
                    "format_issues": ["解析失败"],
                    "content_issues": [],
                    "missing_elements": [],
                },
                "error_identification": "无法解析响应",
                "root_cause_analysis": f"响应格式错误: {response[:200]}...",
                "correct_approach": "请重新输出JSON格式",
            }
