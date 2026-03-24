import os
import json
from pathlib import Path
from typing import List, Dict, Any

def load_preprocessed_sections(report_id: str, experiment_type: str = "BV报告") -> List[Dict[str, Any]]:
    """
    Load preprocessed Protocol/Report sections from filtered_data.json.
    Hierarchical path: data_parsed/{experiment_type}/{report_id}/filtered_data.json
    """
    project_root = Path(__file__).parent.parent.parent
    base_dir = project_root / "data_parsed" / experiment_type / report_id
    json_file = base_dir / "filtered_data.json"
    
    if not json_file.exists():
        print(f"Warning: Preprocessed JSON not found at {json_file}")
        return []
        
    with open(json_file, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    sections = []
    for item in data:
        sections.append({
            "section_title": item.get("section_title", "Unknown"),
            "protocol_content": item.get("original_content", ""),
            "original_report_content": item.get("generate_content", "")
        })
        
    return sections

def get_available_reports(experiment_type: str = "BV报告") -> List[str]:
    """List all available preprocessed report IDs for a given experiment type."""
    project_root = Path(__file__).parent.parent.parent
    base_dir = project_root / "data_parsed" / experiment_type
    
    if not base_dir.exists():
        return []
        
    return [d.name for d in base_dir.iterdir() if d.is_dir() and not d.name.startswith(".")]
