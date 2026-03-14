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
        pathology_analysis: str = "",
        extra_instructions: str = "",
        current_sop: str = "",
        forged_skills: str = "",
        **kwargs
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
            pathology_analysis: Root cause analysis from Reflector (optional)
            extra_instructions: Dynamic instructions from Main Agent (optional)
            current_sop: Existing SOP for retry (optional)
            forged_skills: Forged Python skills (optional)
            **kwargs: Additional keyword arguments.
        """

        # Build user prompt
        if feedback or pathology_analysis or extra_instructions or current_sop:
            # Retry or refinement case
            user_prompt = self._build_retry_prompt(
                experiment_type,
                section_title,
                original_content,
                target_generate_content,
                current_sop,
                feedback,
                pathology_analysis,
                extra_instructions,
                memory,
                forged_skills,
                **kwargs
            )
        else:
            # First generation
            user_prompt = self._build_first_time_prompt(
                experiment_type,
                section_title,
                original_content,
                target_generate_content,
                memory,
                forged_skills,
                **kwargs
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
        forged_skills: str = "",
        **kwargs
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
        if forged_skills:
            prompt += f"\n**【已锻造的 Python 技能输出(Forged Skills)】**:\n{forged_skills}\n"

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
        current_sop: str,
        feedback: str,
        pathology_analysis: str,
        extra_instructions: str,
        memory: str,
        forged_skills: str = "",
        **kwargs
    ) -> str:
        """Build prompt for retry after feedback."""
        prompt = f"""【当前所属实验类型】：{experiment_type}
【当前处理特定章节】：{section_title}

**方案原始内容:**:
{original_content}

**目标优质报告内容(Ground Truth):**:
{target_content}
"""
        if current_sop:
            prompt += f"\n**【上一轮生成的 SOP 草案】**:\n{current_sop}\n"
        
        if feedback:
            prompt += f"\n**【判卷老师(Reviewer)反馈指令】**:\n{feedback}\n"
            
        if pathology_analysis:
            prompt += f"\n**【病灶深度诊断(Reflector Analysis)】**:\n{pathology_analysis}\n"

        if extra_instructions:
            prompt += f"\n**【主控 Agent 特别纠偏指令(Extra Instructions)】**:\n{extra_instructions}\n"

        if memory:
            prompt += f"\n**该实验类型相关的专属经验(Rules)**:\n{memory}\n"
        
        if forged_skills:
            prompt += f"\n**【已锻造的 Python 技能输出(Forged Skills)】**:\n{forged_skills}\n"

        prompt += """
**你的任务：**
根据以上多维上下文进行 SOP 的精密重构。
务必结合“病灶诊断”和“主控指令”进行定向纠偏。直接输出完全合法的 JSON 对象。
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
