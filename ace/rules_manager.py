"""
Rules Manager - Manages Rules by SOP Type and Chapter

This module manages rules organized by:
- SOP Type: rule_template, simple_insert, complex_composite
- Chapter: Each chapter has its own rules
- Rules ID: Each rule has a unique identifier

Design:
- Type-based organization
- Chapter-based storage
- Rule tracking with metrics
"""

from typing import Dict, Any, List
from pathlib import Path
from datetime import datetime
import json
import uuid


class RulesManager:
    """
    Rules Manager: Manages experience rules by SOP type and chapter.

    Data Structure:
    {
      "version": "1.0",
      "rules": {
        "<sop_type>": {
          "<chapter_id>": {
            "<rule_id>": {
              "id": "rule_xxx",
              "content": "Rule content",
              "tags": ["tag1", "tag2"],
              "metrics": {
                "helpful": 10,
                "harmful": 0,
                "usage_count": 15
              },
              "created_at": "ISO-8601",
              "updated_at": "ISO-8601"
            }
          }
        }
      }
    }
    """

    def __init__(self, base_dir: str = "agent_memory/rules"):
        """
        Initialize Rules Manager.

        Args:
            base_dir: Directory for rules storage
        """
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.rules_file = self.base_dir / "rules.json"

    def get_rules(self, sop_type: str, chapter_id: str) -> List[Dict[str, Any]]:
        """
        Get rules for a specific SOP type and chapter.

        Args:
            sop_type: SOP type (rule_template, simple_insert, complex_composite)
            chapter_id: Chapter identifier

        Returns:
            List of rules for the given type and chapter
        """
        rules_data = self._load_rules()

        if sop_type not in rules_data["rules"]:
            return []

        if chapter_id not in rules_data["rules"][sop_type]:
            return []

        chapter_rules = rules_data["rules"][sop_type][chapter_id]
        return list(chapter_rules.values())

    def add_rule(
        self, sop_type: str, chapter_id: str, content: str, tags: List[str] = []
    ) -> str:
        """
        Add a new rule.

        Args:
            sop_type: SOP type
            chapter_id: Chapter identifier
            content: Rule content
            tags: Optional list of tags

        Returns:
            Unique rule ID (rule_xxx)
        """
        rules_data = self._load_rules()

        # Initialize type if needed
        if sop_type not in rules_data["rules"]:
            rules_data["rules"][sop_type] = {}

        # Initialize chapter if needed
        if chapter_id not in rules_data["rules"][sop_type]:
            rules_data["rules"][sop_type][chapter_id] = {}

        # Generate unique rule ID
        rule_id = f"rule_{uuid.uuid4().hex[:8]}"

        # Add rule
        rules_data["rules"][sop_type][chapter_id][rule_id] = {
            "id": rule_id,
            "content": content,
            "tags": tags or [],
            "metrics": {"helpful": 0, "harmful": 0, "usage_count": 0},
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        }

        # Save rules
        self._save_rules(rules_data)

        return rule_id

    def update_rule_metrics(
        self,
        rule_id: str,
        helpful: int = 0,
        harmful: int = 0,
        increment_usage: bool = False,
    ):
        """
        Update rule metrics.

        Args:
            rule_id: Rule identifier
            helpful: Increment helpful count by this amount
            harmful: Increment harmful count by this amount
            increment_usage: Whether to increment usage count
        """
        rules_data = self._load_rules()

        # Find and update the rule
        for sop_type, chapters in rules_data["rules"].items():
            for chapter_id, chapter_rules in chapters.items():
                if rule_id in chapter_rules:
                    metrics = chapter_rules[rule_id]["metrics"]
                    metrics["helpful"] += helpful
                    metrics["harmful"] += harmful
                    if increment_usage:
                        metrics["usage_count"] += 1
                    chapter_rules[rule_id]["updated_at"] = datetime.now().isoformat()

                    # Save and return
                    self._save_rules(rules_data)
                    return

        # Rule not found
        print(f"Warning: Rule {rule_id} not found")

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get rules statistics.

        Returns:
            Statistics including:
            - total_rules: Total number of rules
            - total_helpful: Total helpful count
            - total_harmful: Total harmful count
            - sop_types: List of SOP types with rules
        """
        rules_data = self._load_rules()

        total_rules = 0
        total_helpful = 0
        total_harmful = 0
        sop_types = set()

        for sop_type, chapters in rules_data["rules"].items():
            sop_types.add(sop_type)
            for chapter_id, chapter_rules in chapters.items():
                total_rules += len(chapter_rules)
                for rule in chapter_rules.values():
                    metrics = rule.get("metrics", {})
                    total_helpful += metrics.get("helpful", 0)
                    total_harmful += metrics.get("harmful", 0)

        return {
            "total_rules": total_rules,
            "total_helpful": total_helpful,
            "total_harmful": total_harmful,
            "sop_types": list(sop_types),
        }

    def _load_rules(self) -> Dict[str, Any]:
        """Load rules from file."""
        if not self.rules_file.exists():
            return {
                "version": "1.0",
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "rules": {},
            }

        with open(self.rules_file, "r", encoding="utf-8") as f:
            return json.load(f)

    def _save_rules(self, rules_data: Dict[str, Any]):
        """Save rules to file."""
        rules_data["updated_at"] = datetime.now().isoformat()

        with open(self.rules_file, "w", encoding="utf-8") as f:
            json.dump(rules_data, f, ensure_ascii=False, indent=2)
