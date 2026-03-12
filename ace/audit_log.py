"""
Audit Log - Records All Execution Details

This module manages the audit log that records:
- Timestamp: When the iteration occurred
- Version: Which version (Version1/2/3)
- SOP: The generated SOP content
- SOP ID: Unique identifier for the SOP
- SOP Type: Type of SOP (rule_template, simple_insert, etc.)
- Curation: Modification records from curator
- Metrics: Token usage, latency, model used
- Quality Assessment: Quality score and feedback

Design:
- Persistent JSON storage
- Chapter-organized structure
- Iteration history tracking
"""

from typing import Dict, Any, List
from datetime import datetime
from pathlib import Path
import json


class AuditLog:
    """
    Audit Log Manager: Records all execution details.

    Data Structure:
    {
      "version": "1.0",
      "created_at": "ISO-8601 timestamp",
      "updated_at": "ISO-8601 timestamp",
      "chapters": {
        "<chapter_id>": {
          "chapter_title": "Chapter title",
          "iterations": {
            "<version>_iteration<N>": {
              "timestamp": "ISO-8601",
              "version": "Version1/2/3",
              "iteration": 1,
              "sop": "SOP content",
              "sop_id": "sop_xxx",
              "sop_type": "rule_template",
              "curation": { /* modification records */ },
              "metrics": {
                "tokens": 1000,
                "latency_sec": 5.2,
                "model": "gpt-4o"
              },
              "quality_assessment": {
                "quality_score": 4.5,
                "feedback": "Quality feedback"
              }
            }
          }
        }
      }
    }
    """

    def __init__(self, base_dir: str = "agent_memory/audit_log"):
        """
        Initialize Audit Log.

        Args:
            base_dir: Directory for audit log storage
        """
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.log_file = self.base_dir / "audit_log.json"

    def log_iteration(self, entry: Dict[str, Any]):
        """
        Log an iteration.

        Args:
            entry: Iteration data containing:
                - chapter_id: Chapter identifier
                - chapter_title: Chapter title
                - version: Version (Version1/2/3)
                - iteration: Iteration number
                - sop: Generated SOP content
                - sop_id: Unique SOP identifier
                - sop_type: SOP type
                - curation: Curation records (optional)
                - metrics: Token usage, latency, model
                - quality_assessment: Quality score and feedback (optional)
        """
        # Load existing log
        log_data = self._load_log()

        # Initialize chapter if needed
        chapter_id = entry.get("chapter_id", "")
        if chapter_id not in log_data["chapters"]:
            log_data["chapters"][chapter_id] = {
                "chapter_title": entry.get("chapter_title", ""),
                "iterations": {},
            }

        # Create iteration key
        version = entry.get("version", "")
        iteration = entry.get("iteration", 1)
        iteration_key = f"{version}_iteration{str(iteration)}"

        # Add iteration record
        log_data["chapters"][chapter_id]["iterations"][iteration_key] = {
            "timestamp": datetime.now().isoformat(),
            "version": version,
            "iteration": iteration,
            "sop": entry.get("sop", ""),
            "sop_id": entry.get("sop_id", f"sop_{datetime.now().timestamp()}"),
            "sop_type": entry.get("sop_type", ""),
            "curation": entry.get("curation", {}),
            "metrics": entry.get("metrics", {}),
            "quality_assessment": entry.get("quality_assessment", {}),
        }

        # Save log
        self._save_log(log_data)

    def get_chapter_iterations(self, chapter_id: str) -> List[Dict[str, Any]]:
        """
        Get all iterations for a chapter.

        Args:
            chapter_id: Chapter identifier

        Returns:
            List of iteration records
        """
        log_data = self._load_log()

        if chapter_id not in log_data["chapters"]:
            return []

        iterations = log_data["chapters"][chapter_id].get("iterations", {})
        return list(iterations.values())

    def get_latest_iteration(
        self, chapter_id: str, version: str = ""
    ) -> Dict[str, Any]:
        """
        Get the latest iteration for a chapter.

        Args:
            chapter_id: Chapter identifier
            version: Version filter (optional)

        Returns:
            Latest iteration record or empty dict
        """
        iterations = self.get_chapter_iterations(chapter_id)

        # Filter by version if specified
        if version:
            iterations = [i for i in iterations if i.get("version") == version]

        # Sort by timestamp (newest first)
        iterations.sort(key=lambda x: x.get("timestamp", ""), reverse=True)

        return iterations[0] if iterations else {}

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get audit log statistics.

        Returns:
            Statistics including:
            - total_chapters: Number of chapters
            - total_iterations: Total iterations
            - total_tokens: Total tokens used
            - avg_quality_score: Average quality score
        """
        log_data = self._load_log()

        total_iterations = 0
        total_tokens = 0
        quality_scores = []

        for chapter in log_data["chapters"].values():
            iterations = chapter.get("iterations", {})
            total_iterations += len(iterations)

            for iteration in iterations.values():
                total_tokens += iteration.get("metrics", {}).get("tokens", 0)

                qa = iteration.get("quality_assessment", {})
                score = qa.get("quality_score")
                if score is not None:
                    quality_scores.append(score)

        avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0

        return {
            "total_chapters": len(log_data["chapters"]),
            "total_iterations": total_iterations,
            "total_tokens": total_tokens,
            "avg_quality_score": avg_quality,
        }

    def _load_log(self) -> Dict[str, Any]:
        """Load audit log from file."""
        if not self.log_file.exists():
            return {
                "version": "1.0",
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "chapters": {},
            }

        with open(self.log_file, "r", encoding="utf-8") as f:
            return json.load(f)

    def _save_log(self, log_data: Dict[str, Any]):
        """Save audit log to file."""
        log_data["updated_at"] = datetime.now().isoformat()

        with open(self.log_file, "w", encoding="utf-8") as f:
            json.dump(log_data, f, ensure_ascii=False, indent=2)
