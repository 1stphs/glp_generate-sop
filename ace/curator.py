"""
Curator - Extracts and Refines Rules

This module:
- Extracts rules from successful executions
- Refines rules for reusability
- Identifies patterns
- Generates new rules

Design:
- Pattern-based rule extraction
- Generalization for reusability
- Metadata tagging
"""

from typing import Dict, Any, List


class Curator:
    """
    Curator: Extracts and refines rules from successful executions.

    Tasks:
    1. Analyze successful SOPs
    2. Extract reusable rules
    3. Generalize rules for other chapters
    4. Tag rules with metadata
    5. Identify patterns

    Input:
    - High-quality SOP (quality >= threshold)
    - Reflection results
    - Execution context

    Output:
    - New rules extracted
    - Rule refinement suggestions
    - Pattern discoveries
    """

    def __init__(self, llm_config: Dict[str, Any], quality_threshold: float = 4.0):
        """
        Initialize Curator.

        Args:
            llm_config: Configuration for LLM client
            quality_threshold: Minimum quality score to extract rules
        """
        self.llm_config = llm_config
        self.quality_threshold = quality_threshold

    def curate(
        self,
        chapter_id: str,
        section_title: str,
        generated_sop: str,
        reflection: Dict[str, Any],
        execution_context: Dict[str, Any] = {},
    ) -> Dict[str, Any]:
        """
        Curate and extract rules from execution.

        Args:
            chapter_id: Chapter identifier
            section_title: Chapter title
            generated_sop: Generated SOP
            reflection: Reflection results
            execution_context: Full execution context

        Returns:
            Curation result containing:
            - new_rules: List of extracted rules
            - refined_rules: List of refined existing rules
            - patterns: List of discovered patterns
            - summary: Natural language summary
        """

        # Only curate if quality meets threshold
        quality_score = reflection.get("quality_score", 0)
        if quality_score < self.quality_threshold:
            return {
                "new_rules": [],
                "refined_rules": [],
                "patterns": [],
                "summary": "Quality score below threshold, skipping curation",
            }

        system_prompt = self._get_system_prompt()
        user_prompt = self._build_user_prompt(
            chapter_id, section_title, generated_sop, reflection, execution_context
        )

        # TODO: Implement LLM call
        response = ""

        return self._parse_curation(response)

    def _get_system_prompt(self) -> str:
        """Get system prompt for curation."""
        return """你是规则策展专家。

你的任务：
从高质量的SOP执行中提取和提炼可复用的经验规则。

策展目标：
1. **规则提取**：从成功的SOP中提取具体规则
2. **泛化处理**：将具体经验泛化，使其适用于其他场景
3. **模式识别**：发现通用的模式和最佳实践
4. **元数据标注**：为规则标注适用场景和类型

策展原则：
- 只从质量 >= {threshold} 的SOP中提取规则
- 规则要具体、可操作
- 规则要足够通用，可以复用
- 避免规则重复和冗余

输出格式：
```json
{
  "new_rules": [
    {
      "content": "具体的规则内容",
      "applicability": {
        "sop_types": ["rule_template", "complex_composite"],
        "chapters": ["验证报告", "GLP声明"],
        "context": "在什么情况下有效"
      },
      "evidence": "支持这个规则的证据"
    }
  ],
  "refined_rules": [
    {
      "rule_id": "rule_xxx",
      "old_content": "原始规则内容",
      "refined_content": "改进后的规则内容",
      "reason": "改进原因"
    }
  ],
  "patterns": [
    {
      "type": "pattern_type",
      "description": "模式描述",
      "examples": ["示例1", "示例2"]
    }
  ],
  "summary": "策展总结（自然语言）"
}
```

重要：
- 规则要避免包含具体实例值（日期、编号等）
- 保持规则的清晰性和可操作性
- 标注好适用场景，方便后续查询
""".format(threshold=self.quality_threshold)

    def _build_user_prompt(
        self,
        chapter_id: str,
        section_title: str,
        generated_sop: str,
        reflection: Dict[str, Any],
        execution_context: Dict[str, Any] = {},
    ) -> str:
        """Build user prompt for curation."""
        prompt = f"""章节标题：{section_title}

章节ID：{chapter_id}

生成的SOP：
{generated_sop[:1000]}...

质量评估：
- 评分：{reflection.get("quality_score", 0)}
- 评估：{reflection.get("quality_assessment", "")[:500]}...

"""

        if execution_context:
            prompt += f"""执行上下文：
{str(execution_context)[:500]}...
"""

        prompt += """
请从这个成功的执行中提取和提炼可复用的规则。"""

        return prompt

    def _parse_curation(self, response: str) -> Dict[str, Any]:
        """Parse curation response."""
        # TODO: Implement JSON parsing
        return {"new_rules": [], "refined_rules": [], "patterns": [], "summary": ""}
