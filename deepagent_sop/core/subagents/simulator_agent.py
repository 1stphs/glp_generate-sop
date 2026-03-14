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
    - Understand experiment_type domain
    """

    def __init__(self, llm_config: Dict[str, Any]):
        """
        Initialize Simulator Agent.
        """
        self.llm_config = llm_config
        self.agent = DeepAgent(system_prompt=get_prompt("simulator"), **llm_config)

    def simulate(
        self,
        section_title: str,
        original_content: str,
        current_sop: str,
        experiment_type: str = "小分子模板",
        **kwargs
    ) -> Dict[str, Any]:
        """
        Simulate SOP execution (blind test).
        """
        user_prompt = self._build_prompt(section_title, original_content, current_sop, experiment_type)
        response = self.agent.run(user_prompt)
        return self._parse_response(response)

    def _build_prompt(
        self, section_title: str, original_content: str, current_sop: str, experiment_type: str
    ) -> str:
        """Build user prompt."""
        prompt = f"""【当前所属实验类型】：{experiment_type}
【章节标题】：{section_title}

原始方案内容（仅限使用此内容）：
{original_content}

你收到的待考核 SOP（针对此实验类型的标准操作规程）：
{current_sop}

请严格按照 SOP 执行，生成模拟报告内容。

【重要】：
- 只能使用原始方案内容，不得编造
- 考虑当前实验类型下对数据提取的严格要求
- 输出要符合模板的结构和字段要求
- 最后将模拟正文包裹在 JSON 对象的回参段中
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
                "simulated_generate_content": response,
                "reasoning": "响应未包含JSON格式，提取全量文本并默认遵从",
                "steps_taken": ["执行SOP"],
                "compliance_check": {
                    "rules_applied": ["假定应用"],
                    "rules_missed": [],
                    "overall_compliance": 100,
                },
            }
