"""
Section Aligner - Resolves semantic mismatches between Protocol, Report, and Excel titles.
SOP Generation System V6 - DeepLang
"""

import json
import difflib
from pathlib import Path
from typing import List, Dict, Any, Optional

class SectionAligner:
    """
    Handles mapping of raw titles to canonical titles.
    Uses a report-specific JSON map and fuzzy matching fallback.
    """

    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.report_maps_dir = self.base_dir / "report_maps"
        self.report_maps_dir.mkdir(parents=True, exist_ok=True)

    def _get_map_file(self, report_id: str) -> Path:
        return self.report_maps_dir / f"{report_id}_canonical_map.json"

    def load_map(self, report_id: str) -> Dict[str, str]:
        """Load the canonical map for a specific report."""
        map_file = self._get_map_file(report_id)
        if not map_file.exists():
            return {}
        try:
            with open(map_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def save_map(self, report_id: str, mapping: Dict[str, str]):
        """Save the canonical map for a specific report."""
        map_file = self._get_map_file(report_id)
        with open(map_file, "w", encoding="utf-8") as f:
            json.dump(mapping, f, ensure_ascii=False, indent=2)

    def align_title(self, raw_title: str, canonical_list: List[str], report_id: str = "default", threshold: float = 0.6) -> str:
        """
        Align a raw title to a canonical title.
        1. Check the persistent map.
        2. Use fuzzy matching.
        3. Fallback to raw_title.
        """
        # 1. Check persistent map
        report_map = self.load_map(report_id)
        if raw_title in report_map:
            return report_map[raw_title]

        # 2. Fuzzy match against canonical list
        matches = difflib.get_close_matches(raw_title, canonical_list, n=1, cutoff=threshold)
        if matches:
            canonical_title = matches[0]
            return canonical_title

        # Special semantic rules
        if "稳定性" in raw_title and any("Stability" in c for c in canonical_list):
            for c in canonical_list:
                if "Stability" in c: return c
        
        return raw_title

    def update_map(self, report_id: str, raw_title: str, canonical_title: str):
        """Update and save the map with a new mapping."""
        report_map = self.load_map(report_id)
        report_map[raw_title] = canonical_title
        self.save_map(report_id, report_map)
