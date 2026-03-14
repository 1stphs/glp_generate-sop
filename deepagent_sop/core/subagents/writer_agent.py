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
    - Output experiment_type consistently
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
        experiment_type: str = "小分子模板",
        memory: str = "",
        feedback: str = "",
        existing_sop: str = "",
    ) -> Dict[str, Any]:
        """
        Generate SOP from protocol and report.

        Args:
            original_content: Original protocol content
            target_generate_content: Target report content
            section_title: Section title / Chapter ID
            experiment_type: The overall domain categorization.
            memory: Relevant memory content (Rules)
            feedback: Feedback from previous iteration (optional)
            existing_sop: Existing SOP for retry (optional)

        Returns:
            {
                "experiment_type": "...",
                "current_sop": "Structured SOP content block",
                "reasoning": "Chain of thought",
                "core_rules": [...],
                "template_text": "...",
                "examples": "..."
            }
        """

        # Build user prompt
        if feedback and existing_sop:
            # Retry case
            user_prompt = self._build_retry_prompt(
                experiment_type,
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
                experiment_type,
                section_title,
                original_content,
                target_generate_content,
                memory,
            )

        # Call LLM
        response = self.agent.run(user_prompt)

        # Parse response
        result = self._parse_response(response)
        
        # Enforce experiment_type if missed
        if "experiment_type" not in result:
            result["experiment_type"] = experiment_type

        return result

    def _build_first_time_prompt(
        self,
        experiment_type: str,
        section_title: str,
        original_content: str,
        target_content: str,
        memory: str,
    ) -> str:
        """Build prompt for first-time generation."""
        prompt = f"""【当前所属实验类型】：{experiment_type}
【当前处理特定章节】：{section_title}

**方案原始内容:**:
{original_content}

**目标优质报告内容(Ground Truth):**:
{target_content}
"""

        if memory:
            prompt += f"""
**该实验类型相关的专属经验(Rules)**:
{memory}
"""

        prompt += """
**你的任务：**
根据给定材料，首次逆向生成 SOP。请直接输出纯 JSON 对象。
在 reasoning 字段中，仔细观察 `target_generate_content` 中的分段、文字结构与包含的所有数字指标。确保在生成的 `template_text` 和 `core_rules` 时不丢失哪怕一个小数点，并且绝对不准产生多余的换行或空行！
"""

        return prompt

    def _build_retry_prompt(
        self,
        experiment_type: str,
        section_title: str,
        original_content: str,
        target_content: str,
        existing_sop: str,
        feedback: str,
        memory: str,
    ) -> str:
        """Build prompt for retry after feedback."""
        prompt = f"""【当前所属实验类型】：{experiment_type}
【当前处理特定章节】：{section_title}

**方案原始内容:**:
{original_content}

**目标优质报告内容(Ground Truth):**:
{target_content}

**【上一轮被打回的 SOP 草案】**:
{existing_sop}

**【判卷老师(Reviewer)反馈指令】**:
{feedback}
"""

        if memory:
            prompt += f"""
**该实验类型相关的专属经验(Rules)**:
{memory}
"""

        prompt += """
**你的任务：**
这是针对之前失败生成的修复尝试。上一轮生成的 SOP 因为判卷老师指出的一系列错误而被驳回。

在 reasoning 中分析：
1. 之前的 `current_sop` 哪里出了错（少了换行？漏了标点？忽略了该实验类型里的特定数值提取）？
2. 我该如何修订 `core_rules` 或 `template_text` 才能绕开这些错误？

务必死死盯住老师指令中的"遗漏"或"排版错位"问题，定向重组 SOP 结构。请直接输出完全合法的 JSON 对象。
"""

        return prompt

    def _parse_response(self, response: str) -> Dict[str, Any]:
        """
        Parse LLM response as JSON.
        """
        try:
            parsed = json.loads(response)
        except json.JSONDecodeError:
            match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", response, re.DOTALL)
            if match:
                try:
                    parsed = json.loads(match.group(1))
                except:
                    parsed = None
            else:
                match = re.search(r"\{.*\}", response, re.DOTALL)
                if match:
                    try:
                        parsed = json.loads(match.group())
                    except:
                        parsed = None
                else:
                    parsed = None

        if not parsed:
            return {
                "experiment_type": "未知解析失效分类",
                "current_sop": "未能解析响应",
                "reasoning": f"解析失败: {response[:200]}...",
                "报告规则": [],
                "通用模板": "",
                "示例": "",
            }
            
        # 统一映射到中文字段，对齐业务语义
        # 这样做是为了确保存储层拿到的是干净的结构化数据
        sop_data = {
            "报告规则": parsed.get("报告规则", parsed.get("core_rules", [])),
            "通用模板": parsed.get("通用模板", parsed.get("template_text", "")),
            "示例": parsed.get("示例", parsed.get("examples", ""))
        }
        
        # 将合并后的结构化对象挂载到 current_sop
        parsed["current_sop"] = sop_data

        return parsed
