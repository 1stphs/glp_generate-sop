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
        Generate SOP using Grok with enhancement mode.

        Args:
            state: Current workflow state

        Returns:
            Updated state with generated SOP content
        """
        section_title = state["section_title"]
        protocol_content = state.get("protocol_content", "")
        report_content = state.get("original_report_content", "")
        previous_sop = state.get("previous_sop", "")
        data_index = state.get("data_index", 1)

        self.memory.log_node_execution(
            section_title,
            "writer",
            {"data_index": data_index, "has_previous_sop": bool(previous_sop)},
        )

        skill_content = self.memory.load_skill("writer")

        if data_index == 1:
            prompt_suffix = f"""
            
【本次生成目标】：
生成初始SOP版本。

【新数据集】：
--- 验证方案 (Protocol) 内容片段 ---
{protocol_content}

--- GLP 报告 (Report) 内容片段 ---
{report_content}

请根据上述真实数据切片输出该章节对应的SOP内容，切勿编造虚假数据项。
"""
        else:
            prompt_suffix = f"""
            
【上一次SOP（已优化）】：
{previous_sop}

【本次增强目标】：
基于上一次SOP，结合新的验证方案和报告，生成更泛化、更通用的SOP版本。

【新数据集】：
--- 验证方案 (Protocol) 内容片段 ---
{protocol_content}

--- GLP 报告 (Report) 内容片段 ---
{report_content}

请根据最新的数据切片输出增强后的SOP内容，确保只覆盖文档中实际存在的数据项和要求。
"""

        prompt = f"""你是GLP-SOP生成专家，精通FDA 21 CFR Part 11/GLP法规要求。

# Writer Skill (v{WRITER_SKILL_VERSION})
{skill_content}

{prompt_suffix}"""

        try:
            response = self.client.chat.completions.create(
                model=self.config["model"],
                messages=[{"role": "system", "content": prompt}],
            )

            content = response.choices[0].message.content
            sop_content = content.strip() if content else ""

            iteration = state.get("iteration", 1)

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
