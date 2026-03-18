"""
Writer Node - Generate SOP based on Skill
SOP Generation System V6 - DeepLang
"""

import json
from typing import Dict, Any
from openai import OpenAI
from memory_manager_v6 import MemoryManagerV6
from config_v6 import MODEL_CONFIG, WRITER_SKILL_VERSION


class WriterNode:
    """Writer Node: Generates SOP using Grok"""

    def __init__(self):
        self.memory = MemoryManagerV6()
        self.config = MODEL_CONFIG["writer"]

        # Initialize OpenAI client (for Grok)
        self.client = OpenAI(
            api_key=self.config["api_key"], base_url=self.config["base_url"]
        )

    def __call__(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate SOP based on validation plan, GLP report reference, and Writer Skill.

        Args:
            state: Current workflow state

        Returns:
            Updated state with SOP content
        """
        section_title = state["section_title"]
        protocol_content = state.get("protocol_content", "")
        original_report_content = state.get("original_report_content", "")
        iteration = state.get("iteration", 1)

        # Load Writer Skill
        skill_content = self.memory.load_skill("writer")

        # Load existing template if available
        existing_template = self.memory.load_sop_template(section_title)
        template_context = ""
        if existing_template:
            template_context = (
                f"\n【现有参考模板】：\n{existing_template['sop_content'][:500]}...\n"
            )

        # Build prompt
        prompt = f"""你是SOP生成专家，请基于以下内容生成高质量的GLP标准操作程序（SOP）。

# Writer Skill (v{WRITER_SKILL_VERSION})
{skill_content}

# 输入内容

【章节名称】：{section_title}

【验证方案】：
{protocol_content[:3000]}

【GLP 报告参考】：
{original_report_content[:3000]}

{template_context}

# 任务要求

1. 严格遵守Writer Skill中的所有核心原则和禁止事项
2. 必须包含5个必需章节：目的、适用范围、操作步骤、文档记录、异常处理
3. 所有操作步骤必须包含完整的参数（温度、时间、转速等）
4. 禁止编造验证方案中未出现的具体数值
5. 输出格式：纯净的Markdown格式，不要任何前言或后语

请直接输出SOP内容，以Markdown格式。"""

        try:
            # Generate using Grok
            response = self.client.chat.completions.create(
                model=self.config["model"],
                messages=[{"role": "system", "content": prompt}],
                temperature=self.config["temperature"],
                max_tokens=4000,
            )

            content = response.choices[0].message.content
            sop_content = content.strip() if content else ""

            # Log node execution
            self.memory.log_node_execution(
                section_title,
                "writer",
                {"sop_content": sop_content, "iteration": iteration},
            )

            print(f"📝 [{section_title}] Writer生成完成 (迭代{iteration})")

            return {**state, "sop_content": sop_content}

        except Exception as e:
            print(f"❌ [{section_title}] Writer生成失败: {e}")
            return {**state, "sop_content": "", "error": str(e)}
