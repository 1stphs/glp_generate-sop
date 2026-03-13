"""
SOP Simulator Agent - 模拟执行SOP

根据 original_content 和 current_sop 模拟执行SOP
防止作弊：不读取 target_generate_content
"""

from typing import Dict, Any


class SOPSimulator:
    """
    SOP Simulator Agent: 模拟执行SOP

    功能：
    1. 严格按照SOP指示执行
    2. 仅使用 original_content 作为输入
    3. 模拟填写过程
    4. 输出模拟结果
    """

    def __init__(self, llm_config: Dict[str, Any]):
        """
        初始化SOP Simulator

        Args:
            llm_config: LLM配置
        """
        self.llm_config = llm_config

    def simulate_execution(
        self,
        chapter_id: str,
        section_title: str,
        original_content: str,
        current_sop: str,
    ) -> Dict[str, Any]:
        """
        模拟执行SOP

        Args:
            chapter_id: 章节ID
            section_title: 章节标题
            original_content: 原始方案内容
            current_sop: 当前SOP

        Returns:
            {
                "simulated_generate_content": "模拟生成的报告内容",
                "metrics": {
                    "tokens": "Token消耗",
                    "latency": "延迟"
                }
            }
        """
        # 构建提示
        system_prompt = self._get_system_prompt()
        user_prompt = self._build_user_prompt(
            section_title, original_content, current_sop
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        # TODO: 调用LLM模拟执行
        # response = self._call_llm(messages)
        # simulated_content = self._parse_simulation(response)

        # 暂时返回模拟结果
        mock_simulated = self._generate_mock_simulation(section_title, original_content)

        return {
            "simulated_generate_content": mock_simulated,
            "metrics": {"tokens": 800, "latency": 3.0},
        }

    def _get_system_prompt(self) -> str:
        """获取系统提示词"""
        return """你是一名极其死板的GLP生物分析基层实验操作员。

你的任务：严格按照SOP（标准操作规程）执行，生成模拟报告。

【极其重要的要求】：
1. 只能使用提供的【原始方案内容 original_content】
2. 严禁查看、参考或使用目标报告内容
3. 必须完全按照SOP中的指示和步骤执行
4. 输出模拟结果时要符合SOP中模板的格式

执行步骤：
1. 仔细阅读SOP中的核心填写规则
2. 按照通用模板填写内容
3. 参考示例进行模拟填写

输出要求：
- 模拟的报告内容必须符合SOP中模板的格式
- 填写的数值、日期等要合理（基于原始方案）
- 不得添加SOP中未要求的任何信息
- 保持语言风格一致

如果SOP中有特定的填写要求（如"逐字复制"、"保留所有数字"等），必须严格遵守。

最后只输出模拟生成的报告正文内容，不要输出任何解释、说明或额外文字。"""

    def _build_user_prompt(
        self, section_title: str, original_content: str, current_sop: str
    ) -> str:
        """构建用户提示词"""
        prompt = f"""章节标题：{section_title}

原始方案内容（仅限使用此内容）：
{original_content[:800]}...

你收到的SOP（标准操作规程）：
{current_sop[:1000]}...

请严格按照SOP执行，生成模拟报告内容。

【重要】：
- 只能使用原始方案内容，不得编造
- 严格遵循SOP中的填写规则和模板格式
- 输出要符合模板的结构和字段要求

最后只输出模拟报告正文，不要包含任何解释或说明。"""

        return prompt

    def _parse_simulation(self, response: str) -> str:
        """解析模拟结果"""
        # TODO: 实现JSON解析
        return response

    def _generate_mock_simulation(
        self, section_title: str, original_content: str
    ) -> str:
        """生成模拟结果（用于测试）"""
        # 简单模拟：从原始内容提取部分信息
        lines = original_content.split("\n")
        mock_lines = lines[:10] if len(lines) > 10 else lines

        return f"""【{section_title}】模拟报告：

{chr(10).join(mock_lines)}

（以上为模拟生成的报告内容）"""
