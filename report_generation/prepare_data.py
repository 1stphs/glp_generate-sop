import json
import os
import re
import argparse
from pathlib import Path

def prepare_report_data(sop_path, data_dir, output_path, report_id):
    print(f"[*] Preparing report data using SOP: {sop_path}")
    
    # 1. Load SOP Templates
    if not os.path.exists(sop_path):
        print(f"Error: SOP file {sop_path} not found.")
        return
        
    with open(sop_path, 'r', encoding='utf-8') as f:
        sop_data = json.load(f)
    
    # 2. Load De-identified Merged Docs (Protocol only)
    md_path = Path(data_dir) / "merged_docs.md"
    if not md_path.exists():
        print(f"Error: Data file {md_path} not found.")
        return
        
    with open(md_path, 'r', encoding='utf-8') as f:
        md_content = f.read()
    
    # Parse MD into dict by chapter title
    protocol_map = {}
    sections = md_content.split("\n## ")
    for sec in sections:
        if not sec.strip(): continue
        lines = sec.split("\n")
        title = lines[0].strip("# ").strip()
        body = "\n".join(lines[1:])
        
        if "### Protocol (方案)" in body:
            proto_content = body.split("### Protocol (方案)")[1].split("###")[0].strip()
            protocol_map[title] = proto_content

    # 3. Load Excel Data
    excel_dir = Path(data_dir) / "excel_data"
    excel_map = {}
    if excel_dir.exists():
        for file in excel_dir.glob("*.json"):
            with open(file, "r", encoding="utf-8") as f:
                table_data = json.load(f)
                excel_map[file.stem] = table_data

    # 4. Integrate
    results = []
    for item in sop_data:
        section_title = item.get("section_title")
        sop_content = item.get("sop_content")
        
        if not sop_content or "无明确数据支持" in sop_content:
            continue
            
        print(f" [+] Matching section: {section_title}")
        original_content = protocol_map.get(section_title, "无方案原文数据")
        
        related_tables = []
        for t_name, t_content in excel_map.items():
            if t_name in original_content or section_title in t_name:
                related_tables.append(t_content)
        
        if not related_tables:
            related_tables = list(excel_map.values())[:3]

        results.append({
            "id": section_title,
            "section_title": section_title,
            "original_content": original_content,
            "sop": sop_content,
            "excel_parsed": related_tables
        })

    # 5. Save output
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    # 6. Save project_info.json
    project_info = {
        "report_id": report_id,
        "study_director": "钱哲元",
        "test_facility": "上海益诺思生物技术股份有限公司"
    }
    with open(os.path.join(os.path.dirname(output_path), 'project_info.json'), 'w', encoding='utf-8') as f:
        json.dump(project_info, f, ensure_ascii=False, indent=2)

    print(f"\n✨ Integrated {len(results)} sections into {output_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Prepare input data for generate_report.py")
    parser.add_argument("--sop", required=True, help="Path to SOP templates JSON")
    parser.add_argument("--data", required=True, help="Path to de-identified data directory (test folder)")
    parser.add_argument("--report_id", default="TEST_REPORT", help="Report ID for project_info")
    parser.add_argument("--output", default="report_generation/sections_data.json", help="Output JSON path")
    
    args = parser.parse_args()
    prepare_report_data(args.sop, args.data, args.output, args.report_id)
