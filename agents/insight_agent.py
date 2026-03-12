"""
Insight Agent - Extract Insights from Execution Trajectories

This agent:
1. Analyzes execution trajectories (complete process logs)
2. Identifies what worked and what didn't
3. Extracts reusable lessons and patterns
4. Categorizes insights by type and applicability

Key Design:
- Evidence-driven: Every insight must have supporting evidence from trajectory
- Context-aware: Each insight must specify applicable scenarios
- Categorized: Differentiate between rule-level and process-level insights
"""

from typing import Dict, Any, List
import json


class InsightAgent:
    """
    Insight Agent: Extracts valuable insights from execution trajectories.

    Input: trajectory (complete execution process)
    Output: insights (experience content + application scenarios)

    The trajectory contains:
    - Execution steps
    - Rules used
    - Problems encountered
    - Solutions attempted
    - Quality scores

    Insights extracted include:
    - Type: rule_success | rule_failure | problem_solution | pattern_discovery
    - Content: Specific experience description
    - Context: When this insight is applicable
    - Evidence: Supporting evidence from trajectory
    - Applicability: SOP types, chapters, quality thresholds
    """

    def __init__(self, llm_config: Dict[str, Any]):
        """
        Initialize Insight Agent.

        Args:
            llm_config: Configuration for LLM client
        """
        self.llm_config = llm_config

    def extract(self, trajectory: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract insights from execution trajectory.

        Args:
            trajectory: Complete execution trajectory containing:
                - steps: List of execution steps
                - rules_used: List of rules applied
                - problems: Issues encountered
                - solutions: Solutions tried
                - metrics: Quality scores, tokens, latency
                - iterations: Iteration history

        Returns:
            List of insights, where each insight has:
            - type: rule_success | rule_failure | problem_solution | pattern_discovery
            - content: Specific experience description
            - context: When this insight is applicable
            - evidence: Evidence from trajectory
            - applicability:
                - sop_types: List of applicable SOP types
                - chapters: List of applicable chapters
                - quality_threshold: Minimum quality score
        """

        system_prompt = self._get_system_prompt()
        user_prompt = f"""执行轨迹：{json.dumps(trajectory, ensure_ascii=False, indent=2)}

请从中提取有价值的insights。"""

        # TODO: Implement LLM call
        response = ""

        return self._parse_insights(response)

    def _get_system_prompt(self) -> str:
        """
        Get the system prompt for Insight Agent.

        Key emphasis:
        - Evidence-driven extraction
        - Context tagging for applicability
        - Differentiation of insight types
        """
        return """你是Insight Agent，负责从执行轨迹中提取有价值的经验。

你的任务：
分析给定的执行轨迹（trajectory），提取出：
1. 哪些规则是有效的，为什么？
2. 哪些规则是无效的，为什么？
3. 遇到了什么问题，是如何解决的？
4. 有哪些通用化的经验可以复用？

输出格式：
```json
{
  "insights": [
    {
      "type": "rule_success | rule_failure | problem_solution | pattern_discovery",
      "content": "具体的经验内容描述",
      "context": "这个经验在什么场景下有效",
      "evidence": "支持这个经验的证据（从trajectory中提取）",
      "applicability": {
        "sop_types": ["rule_template", "complex_composite"],
        "chapters": ["验证报告", "GLP声明"],
        "quality_threshold": 4.0
      }
    }
  ],
  "summary": "对本次轨迹的经验总结（自然语言）"
}
```

重要：
- 只提取有足够证据支持的经验
- 区分"规则级别"和"流程级别"的经验
- 每个insight都要标注适用场景
- content要具体、可操作
- evidence要引用trajectory中的具体部分

分析维度：
1. 规则有效性：helpful vs harmful
2. 质量评估：哪些因素影响了质量
3. 迭代效果：迭代是否带来了改进
4. 泛化能力：经验是否可以应用到其他场景
"""

    def _parse_insights(self, response: str) -> List[Dict[str, Any]]:
        """
        Parse insights from LLM response.

        TODO: Implement JSON parsing and validation
        """
        return []
