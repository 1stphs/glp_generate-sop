"""
SOP Reviewer Agent - 三方质量审核

对比三个输入进行质量审核：
1. target_generate_content (目标报告内容）
2. current_sop (当前SOP)
3. simulated_generate_content (模拟执行结果)

审核口径：只审核"结构/形式/模板一致性"
"""

from typing import Dict, Any


class SOPReviewer:
    """
    SOP Reviewer Agent: 三方质量审核

    功能：
    1. 三方对比验证
    2. 结构/形式/模板一致性审核
    3. 不因具体数值差异判定失败
    4. 输出 is_passed 和 feedback
    """

    def __init__(self, llm_config: Dict[str, Any]):
        """
        初始化SOP Reviewer

        Args:
            llm_config: LLM配置
        """
        self.llm_config = llm_config

    def review_sop(
        self,
        chapter_id: str,
        section_title: str,
        target_generate_content: str,
        current_sop: str,
        simulated_generate_content: str,
        original_content: str = "",
    ) -> Dict[str, Any]:
        """
        审核SOP质量

        Args:
            chapter_id: 章节ID
            section_title: 章节标题
            target_generate_content: 目标报告内容
            current_sop: 当前SOP
            simulated_generate_content: 模拟执行结果
            original_content: 原始方案内容

        Returns:
            {
                "is_passed": "是否通过",
                "feedback": "反馈意见",
                "metrics": {
                    "tokens": "Token消耗",
                    "latency": "延迟"
                }
            }
        """
        # 构建提示
        system_prompt = self._get_system_prompt()
        user_prompt = self._build_user_prompt(
            section_title,
            target_generate_content,
            current_sop,
            simulated_generate_content,
            original_content,
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        # TODO: 调用LLM进行审核
        # response = self._call_llm(messages)
        # result = self._parse_review(response)

        # 暂时返回模拟结果
        mock_result = self._generate_mock_review()

        return {
            "is_passed": mock_result["is_passed"],
            "feedback": mock_result["feedback"],
            "metrics": {"tokens": 600, "latency": 4.0},
        }

    def _get_system_prompt(self) -> str:
        """获取系统提示词"""
        return """你是GLP质量保证（QA）审核员。

你的任务是：对比三方输入，审核SOP（标准操作规程）的质量。

【审核范围限定】：
你只能审核以下三个方面：
1. **结构一致性**：SOP是否符合标准三段结构（核心填写规则、通用模板、示例）
2. **形式一致性**：SOP的格式、排版、层级是否规范
3. **模板一致性**：SOP的通用模板是否便于理解和填写

【重要：不得审核的内容】：
- 具体数值、日期、名称等事实性差异（只要在合理范围内就通过）
- 内容的详尽程度（只看是否有明显遗漏）
- 专业术语的准确性（不做学术性评判）

【判定标准】：
- **通过 (is_passed=true)**：SOP在结构和形式上完全符合要求，模板清晰易用
- **不通过 (is_passed=false)**：SOP存在结构错误、格式混乱或模板不清晰
- **退回意见 (feedback)**：如果不通过，给出具体的修改建议（针对结构/形式/模板）

输出格式：
必须使用JSON格式输出审核结果：
{
  "is_passed": true或false,
  "feedback": "具体的修改意见或空字符",
  "reason": "判定原因（如果失败）"
}

【审核原则】：
1. 结构优先：三段结构完整，段落层次清晰
2. 模板实用：模板易于理解和填写，不模糊
3. 形式规范：格式统一，无混乱排版
4. 只审形式：不纠结具体数值准确性，只要合理即可"""

    def _build_user_prompt(
        self,
        section_title: str,
        target_content: str,
        current_sop: str,
        simulated_content: str,
        original_content: str = "",
    ) -> str:
        """构建用户提示词"""
        prompt = f"""章节标题：{section_title}

目标报告内容：
{target_content[:500]}...

当前SOP：
{current_sop[:500]}...

模拟执行结果：
{simulated_content[:500]}...

"""
        if original_content:
            prompt += f"""原始方案内容（仅供参考，不作为审核标准）：
{original_content[:300]}...

"""

        prompt += """请进行三方对比审核。

【审核重点】：
1. 对比 target_generate_content 和 current_sop 的结构与形式
2. 检查 simulated_generate_content 是否符合 current_sop 的模板
3. 评估 current_sop 的模板是否清晰易用

【重要】：
- 只审核结构、形式和模板一致性
- 不因具体数值差异判定失败
- 给出具体的修改建议（如果未通过）

请按照要求的JSON格式输出审核结果。"""

        return prompt

    def _parse_review(self, response: str) -> Dict[str, Any]:
        """解析审核结果"""
        # TODO: 实现JSON解析
        import json

        try:
            return json.loads(response)
        except:
            # 解析失败，返回默认结果
            return self._generate_mock_review()

    def _generate_mock_review(self) -> Dict[str, Any]:
        """生成模拟审核结果（用于测试）"""
        return {
            "is_passed": True,
            "feedback": "",
            "reason": "结构完整，模板清晰，符合要求",
        }
