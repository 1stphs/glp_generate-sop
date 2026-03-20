import os
import json
from pathlib import Path
from typing import List, Dict, Any

class TableMapper:
    """
    Utility to map Excel data tables to specific SOP chapters/sections.
    Supports keyword matching, configuration-based mapping, and synonym lookup.
    """
    def __init__(self, config_path: str = None):
        if config_path is None:
            # Default location relative to this file
            config_path = Path(__file__).parent.parent / "memory" / "chapter_rules" / "table_mapping.json"
        
        self.config_path = Path(config_path)
        self.mapping = self._load_mapping()

    def _load_mapping(self) -> Dict[str, List[str]]:
        """Load mapping configuration from JSON."""
        if self.config_path.exists():
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                print(f"Error loading mapping config: {e}")
                return {}
        return {}

    def get_related_tables(self, section_title: str, report_id: str) -> List[Dict[str, str]]:
        """
        Find Excel tables (.md files) related to a specific SOP section.
        
        Args:
            section_title: The title of the SOP chapter (e.g., '精密度与准确度')
            report_id: The ID of the report to search in (e.g., 'NS25315BV01')
            
        Returns:
            List of dictionaries containing table name and Markdown content.
        """
        # Logic to find the excel_data directory for this report
        # We assume data_parsed/[report_id]/excel_data/ exists
        root_dir = Path(__file__).parent.parent.parent
        excel_dir = root_dir / "data_parsed" / report_id / "excel_data"
        
        if not excel_dir.exists():
            return []

        # Get all available table markdown files
        all_tables = list(excel_dir.glob("*.md"))
        related = []

        # 1. Identify search patterns for this section
        patterns = []
        # Check direct match in config
        if section_title in self.mapping:
            patterns.extend(self.mapping[section_title])
        
        # Check if section title contains any key from mapping or vice versa (fuzzy)
        for section_key, p_list in self.mapping.items():
            if section_key in section_title or section_title in section_key:
                patterns.extend(p_list)
        
        # Remove duplicates
        patterns = list(set(patterns))

        # 2. Match patterns against table filenames
        for table_path in all_tables:
            table_name = table_path.stem
            matched = False
            
            # Match by patterns
            for p in patterns:
                if p.lower() in table_name.lower():
                    matched = True
                    break
            
            # Match by section title substrings (fallback)
            if not matched:
                # e.g., if section is '血样稳定性', match table '表18_ST' (if '稳定性' keywords match)
                common_keywords = ["精密度", "准确度", "回收率", "特异性", "溶血", "稳定性", "稀释"]
                for kw in common_keywords:
                    if kw in section_title and kw in table_name:
                        matched = True
                        break

            if matched:
                try:
                    with open(table_path, "r", encoding="utf-8") as f:
                        related.append({
                            "table_name": table_name,
                            "content": f.read()
                        })
                except IOError:
                    continue
        
        # Sort by table name to maintain deterministic order (e.g., 表9 before 表10)
        related.sort(key=lambda x: x["table_name"])
        return related

if __name__ == "__main__":
    # Quick test
    mapper = TableMapper()
    test_report = "NS25315BV01"
    test_section = "精密度与准确度"
    tables = mapper.get_related_tables(test_section, test_report)
    print(f"Found {len(tables)} tables for '{test_section}':")
    for t in tables:
        print(f"- {t['table_name']}")
