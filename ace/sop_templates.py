"""
SOP Templates - Manages Templates and SOPs by Chapter

This module manages:
- Templates: One template per SOP type
- SOPs: Chapter-specific SOPs

Design:
- Type-based templates
- Chapter-based SOP storage
- Version tracking
"""

from typing import Dict, Any, List
from pathlib import Path
from datetime import datetime
import json


class SOPTemplates:
    """
    SOP Templates Manager: Manages templates and SOPs.

    Data Structure:
    {
      "version": "1.0",
      "templates": {
        "<sop_type>": {
          "template_content": "Template content",
          "created_at": "ISO-8601",
          "updated_at": "ISO-8601"
        }
      },
      "chapter_sops": {
        "<chapter_id>": {
          "chapter_title": "Chapter title",
          "sops": {
            "<sop_type>": {
              "sop_content": "SOP content",
              "version": "Version1/2/3",
              "quality_score": 4.5,
              "created_at": "ISO-8601",
              "updated_at": "ISO-8601"
            }
          }
        }
      }
    }
    """

    def __init__(self, base_dir: str = "agent_memory/sop_templates"):
        """
        Initialize SOP Templates Manager.

        Args:
            base_dir: Directory for templates storage
        """
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.templates_file = self.base_dir / "sop_templates.json"

    def get_template(self, sop_type: str) -> str:
        """
        Get template for a specific SOP type.

        Args:
            sop_type: SOP type (rule_template, simple_insert, complex_composite)

        Returns:
            Template content or empty string if not found
        """
        templates_data = self._load_templates()

        if sop_type not in templates_data["templates"]:
            return ""

        return templates_data["templates"][sop_type].get("template_content", "")

    def save_template(self, sop_type: str, template_content: str):
        """
        Save or update template for a SOP type.

        Args:
            sop_type: SOP type
            template_content: Template content
        """
        templates_data = self._load_templates()

        # Add or update template
        if sop_type not in templates_data["templates"]:
            templates_data["templates"][sop_type] = {}

        templates_data["templates"][sop_type] = {
            "template_content": template_content,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        }

        # Save templates
        self._save_templates(templates_data)

    def save_sop(
        self,
        chapter_id: str,
        chapter_title: str,
        sop_type: str,
        sop_content: str,
        version: str = "latest",
        quality_score: float = 0,
    ):
        """
        Save SOP for a chapter and type.

        Args:
            chapter_id: Chapter identifier
            chapter_title: Chapter title
            sop_type: SOP type
            sop_content: SOP content
            version: Version identifier
            quality_score: Quality score
        """
        templates_data = self._load_templates()

        # Initialize chapter if needed
        if chapter_id not in templates_data["chapter_sops"]:
            templates_data["chapter_sops"][chapter_id] = {
                "chapter_title": chapter_title,
                "sops": {},
            }

        # Add or update SOP
        templates_data["chapter_sops"][chapter_id]["sops"][sop_type] = {
            "sop_content": sop_content,
            "version": version,
            "quality_score": quality_score,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        }

        # Save templates
        self._save_templates(templates_data)

    def get_sop(self, chapter_id: str, sop_type: str) -> Dict[str, Any]:
        """
        Get SOP for a chapter and type.

        Args:
            chapter_id: Chapter identifier
            sop_type: SOP type

        Returns:
            SOP record or empty dict if not found
        """
        templates_data = self._load_templates()

        if chapter_id not in templates_data["chapter_sops"]:
            return {}

        return templates_data["chapter_sops"][chapter_id]["sops"].get(sop_type, {})

    def get_chapter_sops(self, chapter_id: str) -> List[Dict[str, Any]]:
        """
        Get all SOPs for a chapter.

        Args:
            chapter_id: Chapter identifier

        Returns:
            List of SOP records
        """
        templates_data = self._load_templates()

        if chapter_id not in templates_data["chapter_sops"]:
            return []

        chapter = templates_data["chapter_sops"][chapter_id]
        sops_dict = chapter.get("sops", {})
        return list(sops_dict.values())

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get SOP templates statistics.

        Returns:
            Statistics including:
            - total_templates: Number of templates
            - total_sops: Total number of SOPs
            - total_chapters: Number of chapters with SOPs
            - avg_quality: Average quality score
        """
        templates_data = self._load_templates()

        total_templates = len(templates_data["templates"])
        total_sops = 0
        total_chapters = len(templates_data["chapter_sops"])
        quality_scores = []

        for chapter in templates_data["chapter_sops"].values():
            for sop_record in chapter.get("sops", {}).values():
                total_sops += 1
                score = sop_record.get("quality_score")
                if score is not None:
                    quality_scores.append(score)

        avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0

        return {
            "total_templates": total_templates,
            "total_sops": total_sops,
            "total_chapters": total_chapters,
            "avg_quality": avg_quality,
        }

    def _load_templates(self) -> Dict[str, Any]:
        """Load templates from file."""
        if not self.templates_file.exists():
            return {
                "version": "1.0",
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "templates": {},
                "chapter_sops": {},
            }

        with open(self.templates_file, "r", encoding="utf-8") as f:
            return json.load(f)

    def _save_templates(self, templates_data: Dict[str, Any]):
        """Save templates to file."""
        templates_data["updated_at"] = datetime.now().isoformat()

        with open(self.templates_file, "w", encoding="utf-8") as f:
            json.dump(templates_data, f, ensure_ascii=False, indent=2)
