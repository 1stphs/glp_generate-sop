import os
import json
from pathlib import Path
from typing import List, Dict, Any

def load_preprocessed_sections(report_id: str) -> List[Dict[str, Any]]:
    """
    Load preprocessed Protocol/Report sections and Excel data for a specific report.
    """
    base_dir = Path(__file__).parent.parent.parent / "data_parsed" / report_id
    merged_docs_file = base_dir / "merged_docs.md"
    excel_dir = base_dir / "excel_data"
    
    if not merged_docs_file.exists():
        print(f"Warning: Merged docs not found at {merged_docs_file}")
        return []
        
    # Parse merged_docs.md into sections
    with open(merged_docs_file, "r", encoding="utf-8") as f:
        content = f.read()
        
    sections = []
    # Split by ## Heading
    raw_sections = content.split("\n## ")
    for rs in raw_sections:
        if not rs.strip() or rs.startswith("# "):
            continue
            
        lines = rs.split("\n")
        title = lines[0].strip()
        body = "\n".join(lines[1:]).strip()
        
        # Split body into Protocol and Report
        # Format is ### Protocol (方案)\n...\n### Report (报告)\n...
        parts = body.split("### Report (报告)")
        protocol_part = parts[0].replace("### Protocol (方案)", "").strip()
        report_part = parts[1].split("---")[0].strip() if len(parts) > 1 else ""
        
        sections.append({
            "section_title": title,
            "protocol_content": protocol_part,
            "original_report_content": report_part
        })
        
    return sections

def get_available_reports() -> List[str]:
    """List all available preprocessed report IDs."""
    base_dir = Path(__file__).parent.parent.parent / "data_parsed"
    return [d.name for d in base_dir.iterdir() if d.is_dir() and not d.name.startswith(".")]
