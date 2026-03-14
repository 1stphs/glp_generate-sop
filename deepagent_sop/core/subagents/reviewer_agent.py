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
    - Enforce rules based on experiment_type
    - Identify format, structure, content issues
    - Provide actionable feedback for improvement
    """

    def __init__(self, llm_config: Dict[str, Any]):
        self.llm_config = llm_config
        self.agent = DeepAgent(system_prompt=get_prompt("reviewer"), **llm_config)

    def review(
        self,
        simulated_generate_content: str,
        target_generate_content: str,
        original_sop: str,
        original_content: str = "",
        experiment_type: str = "小分子模板"
    ) -> Dict[str, Any]:
        """
        Review SOP quality.
        """
        user_prompt = self._build_prompt(
            simulated_generate_content,
            target_generate_content,
            original_sop,
            original_content,
            experiment_type
        )
        response = self.agent.run(user_prompt)
        return self._parse_response(response)

    def _build_prompt(
        self,
        simulated_content: str,
        target_content: str,
        original_sop: str,
        original_content: str,
        experiment_type: str
    ) -> str:
        """Build user prompt."""
        prompt = f"""【当前所属实验类型】：{experiment_type}

**目标优质报告内容 (Ground Truth)**:
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
请严格进行三方比对。找出模拟作答结果和目标优质报告内容之间的任何排版、换行或字段丢失差异（必须基于当前实验类型的校验红线，忽略完全合理的举例随机名称替换）。

若不通过，请务必找到导致这个差异产生的**根本原因**（SOP 哪不严密），并在 `correct_approach` 和 `feedback` 中给出可执行的 SOP 修改建议。请直接输出纯 JSON，不包含 Markdown。
"""
        return prompt

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
                "is_passed": False,
                "feedback": "解析失败的致命反馈，必须修正JSON格式",
                "error_identification": "无法解析响应",
                "root_cause_analysis": f"响应格式错误: {response[:200]}...",
                "correct_approach": "请重新输出JSON格式",
            }
