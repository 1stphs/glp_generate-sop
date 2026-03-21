import os
import json
from pathlib import Path
from typing import List, Dict, Any

def load_preprocessed_sections(report_id: str) -> List[Dict[str, Any]]:
    """
    Load preprocessed Protocol/Report sections from filtered_data.json.
    """
    base_dir = Path(__file__).parent.parent.parent / "data_parsed" / report_id
    json_file = base_dir / "filtered_data.json"
    
    if not json_file.exists():
        print(f"Warning: Preprocessed JSON not found at {json_file}")
        return []
        
    with open(json_file, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    sections = []
    for item in data:
        sections.append({
            "section_title": item["section_title"],
            "protocol_content": item.get("original_content", ""),
            "original_report_content": item.get("generate_content", "")
        })
        
    return sections

def get_available_reports() -> List[str]:
    """List all available preprocessed report IDs."""
    base_dir = Path(__file__).parent.parent.parent / "data_parsed"
    return [d.name for d in base_dir.iterdir() if d.is_dir() and not d.name.startswith(".")]
