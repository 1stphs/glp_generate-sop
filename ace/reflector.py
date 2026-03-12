"""
Reflector - Analyzes SOP Quality

This module analyzes:
- SOP quality against requirements
- Rules effectiveness (helpful vs harmful)
- Provides improvement suggestions

Design:
- Quality-focused evaluation
- Rule tagging
- Feedback generation
"""

from typing import Dict, Any, List


class Reflector:
    """
    Reflector: Analyzes SOP quality and rules effectiveness.

    Tasks:
    1. Evaluate SOP quality (1-5 score)
    2. Tag rules as helpful or harmful
    3. Provide specific feedback
    4. Suggest improvements

    Input:
    - Generated SOP
    - Target report (for comparison)
    - Original protocol (for context)
    - Used rules

    Output:
    - Quality score (1-5)
    - Quality assessment (natural language)
    - Rule tags (helpful/harmful for each rule)
    - Improvement suggestions
    """

    def __init__(self, llm_config: Dict[str, Any]):
        """
        Initialize Reflector.

        Args:
            llm_config: Configuration for LLM client
        """
        self.llm_config = llm_config

    def reflect(
        self,
        chapter_id: str,
        section_title: str,
        original_content: str,
        target_generate_content: str,
        generated_sop: str,
        sop_type: str,
        used_rules: List[Dict[str, Any]] = [],
    ) -> Dict[str, Any]:
        """
        Reflect on SOP quality.

        Args:
            chapter_id: Chapter identifier
            section_title: Chapter title
            original_content: Original protocol content
            target_generate_content: Target report content
            generated_sop: Generated SOP
            sop_type: SOP type
            used_rules: Rules used in generation

        Returns:
            Reflection result containing:
            - quality_score: 1-5 rating
            - quality_assessment: Natural language assessment
            - rule_tags: List of rule IDs with tags (helpful/harmful/neutral)
            - improvement_suggestions: List of suggestions
        """

        system_prompt = self._get_system_prompt()
        user_prompt = self._build_user_prompt(
            section_title,
            original_content,
            target_generate_content,
            generated_sop,
            sop_type,
            used_rules,
        )

        # TODO: Implement LLM call
        response = ""

        return self._parse_reflection(response)

    def _get_system_prompt(self) -> str:
        """Get system prompt for reflection."""
        return """你是SOP质量评估专家。

你的任务：
评估生成的SOP质量，并判断使用的规则是否有帮助。

评估维度：
1. **质量评分**：1-5分
   - 5分：完美，无需任何修改
   - 4分：优秀，仅有小问题
   - 3分：良好，有些需要改进
   - 2分：一般，有明显问题
   - 1分：差，需要重新生成

2. **规则有效性**：对每个使用的规则标记
   - helpful: 规则帮助了生成
   - harmful: 规则阻碍了生成
   - neutral: 规则无明显影响

3. **改进建议**：具体可操作的建议

输出格式：
```json
{
  "quality_score": 4.5,
  "quality_assessment": "SOP整体质量优秀...",
  "rule_tags": [
    {
      "rule_id": "rule_xxx",
      "tag": "helpful | harmful | neutral",
      "reason": "该规则帮助准确提取了字段"
    }
  ],
  "improvement_suggestions": [
    "建议1：...",
    "建议2：..."
  ]
}
```

重要：
- 评分要客观，基于事实
- 标注规则时要说明理由
- 建议要具体、可操作"""

    def _build_user_prompt(
        self,
        section_title: str,
        original_content: str,
        target_generate_content: str,
        generated_sop: str,
        sop_type: str,
        used_rules: List[Dict[str, Any]] = [],
    ) -> str:
        """Build user prompt for reflection."""
        prompt = f"""章节标题：{section_title}

SOP类型：{sop_type}

验证方案内容：
{original_content[:500]}...

验证报告内容：
{target_generate_content[:500]}...

生成的SOP：
{generated_sop[:1000]}...

"""

        if used_rules:
            prompt += "使用的规则：\n"
            for rule in used_rules:
                helpful = rule.get("metrics", {}).get("helpful", 0)
                harmful = rule.get("metrics", {}).get("harmful", 0)
                prompt += f"- [{rule.get('id', 'unknown')}] helpful={helpful} harmful={harmful} :: {rule.get('content', '')[:100]}...\n"

        prompt += """
请评估SOP质量并标注规则有效性。"""

        return prompt

    def _parse_reflection(self, response: str) -> Dict[str, Any]:
        """Parse reflection response."""
        # TODO: Implement JSON parsing
        return {
            "quality_score": 0,
            "quality_assessment": "",
            "rule_tags": [],
            "improvement_suggestions": [],
        }
