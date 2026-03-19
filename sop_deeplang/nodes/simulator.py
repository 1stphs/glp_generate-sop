"""
Simulator Node - Blind Test SOP Executability
SOP Generation System V6 - DeepLang
"""

import json
from typing import Dict, Any
from openai import OpenAI
from memory_manager_v6 import MemoryManagerV6
from config_v6 import MODEL_CONFIG, SIMULATOR_SKILL_VERSION


class SimulatorNode:
    """Simulator Node: Blind test SOP without looking at ground truth"""

    def __init__(self):
        self.memory = MemoryManagerV6()
        self.config = MODEL_CONFIG["simulator"]

        # Initialize OpenAI client (for Grok)
        self.client = OpenAI(
            api_key=self.config["api_key"], base_url=self.config["base_url"]
        )

    def __call__(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform blind test on the generated SOP.

        Args:
            state: Current workflow state

        Returns:
            Updated state with simulation results
        """
        section_title = state["section_title"]
        sop_content = state.get("sop_content", "")
        protocol_content = state.get("protocol_content", "")

        skill_content = self.memory.load_skill("simulator")

        prompt = f"""你是一名极其死板的 GLP 生物分析基层实验操作员。

你的任务是：仔细阅读别人发给你的一段 SOP (标准操作规程) 文本，然后在脑海里严格一步步执行它。

【极其关键的要求】：执行完成后，你必须告诉我你在这部分实验里做出来的【量化数据、中间计算结果或明确的步骤现象】。
如果有任何模糊不清、没有写明浓度或用量导致你算不出结果的地方，请诚实地报告"规程缺失必要参数无法推演"。

执行优先级要求：先遵循"核心填写规则"，再按"通用模板"生成；"示例"仅作参考，不得直接照抄示例内容。

输出强约束：你的最终输出必须与 SOP 的通用模板/示例在格式与文风上保持一致，且可直接放进报告正文。
禁止输出任何解释性语句、分析语句、询问语句、免责声明、前言或结尾。

# Simulator Skill (v{SIMULATOR_SKILL_VERSION})
{skill_content}

【执行实验节点】：{section_title}

【方案原始内容 protocol_content】：
{protocol_content[:2000]}

【你收到的 SOP 规程说明书】：
{sop_content}

请严格按 SOP 执行并输出模拟生成结果。最终只输出可直接粘贴到报告中的正文内容，不要输出任何解释、说明、提问或额外话术。
"""

        try:
            response = self.client.chat.completions.create(
                model=self.config["model"],
                messages=[{"role": "system", "content": prompt}],
            )

            content = response.choices[0].message.content
            simulated_output = content.strip() if content else ""

            can_complete = len(simulated_output) > 50
            problems = []

            if can_complete:
                print(f"🔬 [{section_title}] Simulator盲测: 可执行")
                print(f"   生成了 {len(simulated_output)} 字符的模拟报告")
            else:
                print(f"🔬 [{section_title}] Simulator盲测: 失败")
                print(f"   输出过短或为空，无法执行")

            result = {
                "can_complete": can_complete,
                "problems": problems,
                "simulated_output": simulated_output,
            }

            self.memory.log_node_execution(section_title, "simulator", result)

            return {**state, "simulation_result": result}

        except Exception as e:
            print(f"❌ [{section_title}] Simulator盲测失败: {e}")
            return {
                **state,
                "simulation_result": {
                    "can_complete": False,
                    "problems": [
                        {
                            "type": "simulator_error",
                            "description": str(e),
                            "impact": "high",
                        }
                    ],
                },
                "error": str(e),
            }
