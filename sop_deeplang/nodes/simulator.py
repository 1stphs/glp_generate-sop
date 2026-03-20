"""
Simulator Node - Blind Test SOP Executability
SOP Generation System V6 - DeepLang
"""

import json
from typing import Dict, Any
from openai import OpenAI
from sop_deeplang.utils.memory_manager import MemoryManager
from sop_deeplang.utils.config import MODEL_CONFIG, SIMULATOR_SKILL_VERSION
from sop_deeplang.utils.table_mapper import TableMapper


class SimulatorNode:
    """Simulator Node: Blind test SOP without looking at ground truth"""

    def __init__(self):
        self.memory = MemoryManager()
        self.table_mapper = TableMapper()
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
        report_id = state.get("report_id", "default")
        phase = state.get("phase", 1)

        skill_content = self.memory.load_skill("simulator")

        tables_context = ""
        micro_test_instruction = ""
        
        if phase == 2:
            # Load Excel tables for Micro-testing
            related_tables = self.table_mapper.get_related_tables(section_title, report_id)
            if related_tables:
                tables_context = "\n### 【待代入的真实 Excel 数据 (Excel Data for Micro-test)】\n"
                for t in related_tables:
                    tables_context += f"\n- 表名: {t['table_name']}\n{t['content']}\n"
                
                micro_test_instruction = """
【微观压测任务】：
由于当前是第二阶段，你手里有真实的 Excel 数据结构。请你尝试将这些 Excel 中的维度和数值特征“代入”到 SOP 的插槽中。
1. **槽位匹配度**：SOP 中的插槽（如 [XXX]）是否足够多、足够合理，能装得下这些真实数据？
2. **结构缺失**：如果真实数据有“批内/批间”之分，但 SOP 只有一个通用[CV%]槽位，请指出“插槽维度不足”。
"""

        prompt = f"""你是一名极其死板的 GLP 生物分析基层实验操作员。

你的任务是：仔细阅读别人发给你的一段 SOP (标准操作规程) 文本，然后在脑海里严格一步步执行它。

【核心任务】：执行完成后，你必须告诉我你在这部分实验里做出来的【量化数据、中间计算结果或明确的步骤现象】。
如果有任何模糊不清、没有写明浓度或用量导致你算不出结果的地方，请诚实地报告"规程缺失必要参数无法推演"。

{micro_test_instruction}

# Simulator Skill (v{SIMULATOR_SKILL_VERSION})
{skill_content}

【执行实验节点】：{section_title}

{tables_context}

【方案原始内容 protocol_content】：
{protocol_content[:2000]}

【你收到的 SOP 规程说明书】：
{sop_content}

请开始模拟并将执行结果输出。"""

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
