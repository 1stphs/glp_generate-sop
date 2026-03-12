"""
Playbook Agent - Manage Persistent Knowledge Base

This agent:
1. Queries playbook to find relevant rules for a task
2. Updates playbook with new insights
3. Maintains rule quality (removes ineffective rules)
4. Optimizes rule organization

Key Design:
- LLM-driven matching: Not simple keyword matching
- LLM-driven updates: Intelligent deduplication and cleanup
- Every operation must include reasoning for auditability
"""

from typing import Dict, Any, List
import json
from pathlib import Path


class PlaybookAgent:
    """
    Playbook Agent: Manages persistent experience knowledge base.

    Operations:
    1. Query: Find rules relevant to current task context
    2. Update: Integrate new insights into playbook
    3. Cleanup: Remove ineffective rules
    4. Optimize: Improve rule organization

    Query Context includes:
    - Chapter title
    - SOP type
    - Task description

    Update Logic:
    1. Check if insight already exists (content similarity)
    2. If exists, update metrics (helpful/harmful counts)
    3. If not exists, add as new rule
    4. Optimize rule tags and metadata
    5. Delete long-invalid rules (helpful=0, harmful>5)
    """

    def __init__(
        self, llm_config: Dict[str, Any], playbook_path: str = "playbook/playbooks.json"
    ):
        """
        Initialize Playbook Agent.

        Args:
            llm_config: Configuration for LLM client
            playbook_path: Path to playbook file (default: playbook/playbooks.json)
        """
        self.llm_config = llm_config
        default_path = "playbook/playbooks.json"
        self.playbook_path = Path(playbook_path if playbook_path else default_path)
        self.playbook_path.parent.mkdir(parents=True, exist_ok=True)

    def query(self, query_context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Query playbook for rules relevant to task context.

        Args:
            query_context: Context for matching, containing:
                - chapter_title: Chapter being processed
                - sop_type: Type of SOP (rule_template, etc.)
                - task_description: Natural language task description

        Returns:
            List of matched rules, each with:
            - id: Rule unique identifier
            - content: Rule content
            - relevance_score: How relevant to query (0-1)
            - reason: Why this rule matches
            - metrics:
                - helpful: Count of times rule was helpful
                - harmful: Count of times rule was harmful
                - usage_count: Total times used
        """

        # Load playbook
        playbook = self._load_playbook()

        system_prompt = self._get_query_system_prompt()
        user_prompt = f"""任务上下文：{json.dumps(query_context, ensure_ascii=False, indent=2)}

Playbook内容：{json.dumps(playbook, ensure_ascii=False, indent=2)[:5000]}

请查询最相关的规则。"""

        # TODO: Implement LLM call
        response = ""

        return self._parse_matched_rules(response)

    def update(self, insights: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Update playbook with new insights.

        Args:
            insights: Insights extracted by Insight Agent, each containing:
                - type: rule_success | rule_failure | problem_solution | pattern_discovery
                - content: Specific experience
                - context: Applicable scenarios
                - evidence: Supporting evidence
                - applicability: SOP types, chapters, quality threshold

        Returns:
            Updated playbook data:
            - updated_playbook: Complete updated playbook
            - changes_summary:
                - added_rules: Count of new rules added
                - updated_rules: Count of rules updated
                - removed_rules: Count of rules removed
            - recommendations: Natural language suggestions for playbook management
        """

        # Load current playbook
        playbook = self._load_playbook()

        system_prompt = self._get_update_system_prompt()
        user_prompt = f"""新insights：{json.dumps(insights, ensure_ascii=False, indent=2)}

当前playbook：{json.dumps(playbook, ensure_ascii=False, indent=2)[:5000]}

请更新playbook。"""

        # TODO: Implement LLM call
        response = ""

        updated = self._parse_updated_playbook(response)

        # Save updated playbook
        self._save_playbook(updated["updated_playbook"])

        return updated

    def _load_playbook(self) -> Dict[str, Any]:
        """Load playbook from file."""
        if not self.playbook_path.exists():
            return {"version": "1.0", "created_at": "", "updated_at": "", "rules": {}}

        with open(self.playbook_path, "r", encoding="utf-8") as f:
            import json

            return json.load(f)

    def _save_playbook(self, playbook: Dict[str, Any]):
        """Save playbook to file."""
        import json
        from datetime import datetime

        playbook["updated_at"] = datetime.now().isoformat()

        with open(self.playbook_path, "w", encoding="utf-8") as f:
            json.dump(playbook, f, ensure_ascii=False, indent=2)

    def _get_query_system_prompt(self) -> str:
        """Get system prompt for query operation."""
        return """你是Playbook Agent，负责管理和查询持久化经验库。

你的任务：
根据任务上下文，从playbook中查询最相关的经验规则。

匹配标准：
1. 章节相关性：规则是否适用于当前章节
2. SOP类型匹配：规则的sop_type是否匹配
3. 质量分数：优先选择质量更高的规则
4. 历史效果：考虑规则的帮助/有害次数

输出格式：
```json
{
  "matched_rules": [
    {
      "id": "rule_xxx",
      "content": "规则内容",
      "relevance_score": 0.95,
      "reason": "匹配原因（章节、类型、场景都符合）",
      "metrics": {
        "helpful": 10,
        "harmful": 0,
        "usage_count": 15
      }
    }
  ],
  "summary": "查询总结（找到X条规则，最相关的是...）"
}
```

重要：
- 每个规则都要说明匹配原因
- 计算相关性分数并排序
- 如果没有匹配的规则，明确说明"""

    def _get_update_system_prompt(self) -> str:
        """Get system prompt for update operation."""
        return """你是Playbook Agent，负责更新持久化经验库。

你的任务：
将新的insights整合到playbook中。

更新逻辑：
1. 检查insight是否已存在（内容相似度）
2. 如果存在，更新其metrics（helpful/harmful计数）
3. 如果不存在，作为新规则添加
4. 优化规则的tags和metadata
5. 删除长期无效的规则（helpful=0, harmful>5）

输出格式：
```json
{
  "updated_playbook": { /* 完整的更新后playbook */ },
  "changes_summary": {
    "added_rules": 5,
    "updated_rules": 3,
    "removed_rules": 1
  },
  "recommendations": "对playbook管理的建议（自然语言）"
}
```

重要：
- 避免重复规则
- 维护规则质量（删除无效规则）
- 优化规则的组织结构"""

    def _parse_matched_rules(self, response: str) -> List[Dict[str, Any]]:
        """Parse matched rules from response."""
        return []

    def _parse_updated_playbook(self, response: str) -> Dict[str, Any]:
        """Parse updated playbook from response."""
        return {"updated_playbook": {}, "changes_summary": {}, "recommendations": ""}
