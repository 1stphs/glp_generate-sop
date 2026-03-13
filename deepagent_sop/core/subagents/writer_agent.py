"""
Writer Agent - SOP Generation Specialist

Generates SOP from protocol and report pairs.
Based on prompt from sop_generation/prompts/registry.py
"""

import json
import re
from typing import Dict, Any
from ..base_agent import DeepAgent
from ..utils.prompt_manager import get_prompt


class WriterAgent:
    """
    Writer Agent: Generates SOP from original_content and target_generate_content

    Responsibilities:
    - Analyze protocol and report differences
    - Extract transformation rules
    - Generate structured SOP (core rules, template, examples)
    - Determine SOP type (simple_insert, rule_template, complex_composite)
    """

    def __init__(self, llm_config: Dict[str, Any]):
        """
        Initialize Writer Agent.

        Args:
            llm_config: LLM configuration
        """
        self.llm_config = llm_config
        self.agent = DeepAgent(system_prompt=get_prompt("writer"), **llm_config)

    def generate_sop(
        self,
        original_content: str,
        target_generate_content: str,
        section_title: str,
        memory: str = "",
        feedback: str = "",
        existing_sop: str = "",
    ) -> Dict[str, Any]:
        """
        Generate SOP from protocol and report.

        Args:
            original_content: Original protocol content
            target_generate_content: Target report content
            section_title: Section title
            memory: Relevant memory content
            feedback: Feedback from previous iteration (optional)
            existing_sop: Existing SOP for retry (optional)

        Returns:
            {
                "sop_type": "rule_template | simple_insert | complex_composite",
                "current_sop": "Structured SOP content",
                "reasoning": "Chain of thought",
                "confidence": 0.0-1.0,
                "core_rules": [...],
                "template_text": "...",
                "examples": "..."
            }
        """
        # Infer SOP type from content
        sop_type = self._infer_sop_type(target_generate_content, original_content)

        # Build user prompt
        if feedback and existing_sop:
            # Retry case
            user_prompt = self._build_retry_prompt(
                section_title,
                original_content,
                target_generate_content,
                existing_sop,
                feedback,
                memory,
            )
        else:
            # First generation
            user_prompt = self._build_first_time_prompt(
                section_title,
                original_content,
                target_generate_content,
                memory,
            )

        # Call LLM
        response = self.agent.run(user_prompt)

        # Parse response
        result = self._parse_response(response)

        # Add inferred SOP type
        if "sop_type" not in result:
            result["sop_type"] = sop_type

        return result

    def _infer_sop_type(self, target_content: str, original_content: str) -> str:
        """
        Infer SOP type from content.

        Args:
            target_content: Target report content
            original_content: Original protocol content

        Returns:
            SOP type: simple_insert, rule_template, or complex_composite
        """
        content = (target_content + " " + original_content).lower()

        # Complex composite signals
        complex_signals = [
            "情形a",
            "情形b",
            "除",
            "其余",
            "若",
            "否则",
            "例外",
            "异常",
            "分两段",
            "分别",
            "case a",
            "case b",
            "otherwise",
        ]
        if any(signal in content for signal in complex_signals):
            return "complex_composite"

        # Simple insert signals
        simple_content = target_content.replace("\n", "").strip()
        if (
            simple_content
            and len(simple_content) <= 80
            and "[" not in simple_content
            and "]" not in simple_content
        ):
            return "simple_insert"

        # Default: rule_template
        return "rule_template"

    def _build_first_time_prompt(
        self,
        section_title: str,
        original_content: str,
        target_content: str,
        memory: str,
    ) -> str:
        """Build prompt for first-time generation."""
        prompt = f"""【当前处理章节】{section_title}

**方案原始内容:**:
{original_content}

**目标优质报告内容:**:
{target_content}
"""

        if memory:
            prompt += f"""
**相关经验**:
{memory}
"""

        prompt += """
**你的任务：**
首次生成 SOP。请直接输出纯 JSON 对象。
在 reasoning 字段中，仔细观察 `target_generate_content` 中的分段、文字结构与包含的所有数字指标。确保在生成的 `template_text` 和 `core_rules` 时不丢失哪怕一个小数点，并且绝对不准产生多余的换行或空行！
"""

        return prompt

    def _build_retry_prompt(
        self,
        section_title: str,
        original_content: str,
        target_content: str,
        existing_sop: str,
        feedback: str,
        memory: str,
    ) -> str:
        """Build prompt for retry after feedback."""
        prompt = f"""【当前处理章节】{section_title}

**方案原始内容:**:
{original_content}

**目标优质报告内容:**:
{target_content}

**【上一轮 SOP (Current Playbook)】**:
{existing_sop}

**【判卷老师反馈**】**:
{feedback}
"""

        if memory:
            prompt += f"""
**相关经验**:
{memory}
"""

        prompt += """
**你的任务：**
这是针对之前失败生成的修复尝试。上一轮生成的 SOP 因为判卷老师指出的一系列错误而被驳回。

在 reasoning 中分析：
1. 为什么上一轮会被退回？
2. 之前的 `current_sop` 哪里出了错（少了换行？漏了标点？忽略了特定数值提取）？
3. 我该如何修订 `core_rules` 或 `template_text` 才能绕开这些错误？

务必死死盯住反馈信息中的"遗漏"或"排版错位"问题。根据反馈定向修正。请直接输出完全合法的 JSON 对象。
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
                "sop_type": "rule_template",
                "current_sop": "未能解析响应",
                "reasoning": f"解析失败: {response[:200]}...",
                "confidence": 0.0,
                "core_rules": [],
                "template_text": "",
                "examples": "",
            }
