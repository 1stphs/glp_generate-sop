import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor
from sop_deeplang.utils.config import validate_config, MAX_DATASETS
from sop_deeplang.utils.data_loader import get_available_reports, load_preprocessed_sections
from sop_deeplang.core.engine import SOPSGeneratorV6
from sop_deeplang.core.state import MasterState

def is_table_section(title: str, content: str) -> bool:
    """Determine if a section is just a raw data table or appendix."""
    title_clean = title.strip()
    
    # Strictly ignore appendices and tables
    # "附录", "附表", "附图" often contain raw data that doesn't need SOPs
    ignore_keywords = ["附录", "附表", "附图", "Annex", "Appendix"]
    if any(kw in title_clean for kw in ignore_keywords):
        return True

    # If title starts with '表' or '图' and doesn't contain '目录'
    if (title_clean.startswith("表") or title_clean.startswith("图")) and "目录" not in title_clean:
        # If content has a markdown table structure or is very short
        if "|---|" in content or len(content) < 50:
            return True
    return False

def truncate_at_archival(sections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Truncate the section list after '归档'."""
    truncated_list = []
    for section in sections:
        truncated_list.append(section)
        # Match '归档' robustly
        title = section["section_title"].strip()
        if "归档" in title or "Archival" in title:
            print(f"🛑 Truncating at section: {section['section_title']}")
            break
    return truncated_list

def process_section_task(engine: SOPSGeneratorV6, section: Dict[str, Any], report_id: str, phase: int):
    """Helper for parallel execution of a single section."""
    section_title = section["section_title"]
    
    # Load Phase 1 SOP as previous_sop if in Phase 2
    previous_sop_content = ""
    if phase == 2:
        previous_sop = engine.memory.load_sop_template(section_title)
        previous_sop_content = previous_sop["sop_content"] if previous_sop else ""

    initial_state: MasterState = {
        "section_title": section_title,
        "protocol_content": section["protocol_content"],
        "original_report_content": section["original_report_content"],
        "complexity": "",
        "route": "",
        "reasoning": "",
        "iteration": 1,
        "sop_content": "",
        "reviewer_score": 1.0,
        "is_pass": False,
        "failure_cause": "",
        "data_index": 1 if phase == 1 else 2,
        "previous_sop": previous_sop_content,
        "all_report_contents": [section["original_report_content"]],
        "phase": phase,
        "report_id": report_id,
        "section_type": "UNKNOWN"
    }
    engine.process_section(initial_state)

def run_phase_1(engine: SOPSGeneratorV6, report_id: str, limit: Optional[int] = None, workers: int = 5):
    """Generate generic SOP skeleton from merged protocol/report."""
    print(f"\n🚀 Starting Phase 1: Skeleton Generation for {report_id} (Parallel: {workers} workers)")
    all_sections = load_preprocessed_sections(report_id)
    
    # Apply Archival truncation
    active_sections = truncate_at_archival(all_sections)

    # Filter out table-only sections and appendices
    sections = [s for s in active_sections if not is_table_section(s["section_title"], s["protocol_content"] + s["original_report_content"])]
    skipped_count = len(active_sections) - len(sections)
    if skipped_count > 0:
        print(f"⏩ Filtered out {skipped_count} data-only/appendix sections.")

    if not sections:
        print("✗ No valid sections found for Phase 1.")
        return
        
    if limit:
        sections = list(sections)[:limit]
        print(f"📌 Limited to first {limit} sections.")

    with ThreadPoolExecutor(max_workers=workers) as executor:
        for section in sections:
            executor.submit(process_section_task, engine, section, report_id, 1)
    
    print(f"✅ Phase 1 complete for {report_id}")

def run_phase_2(engine: SOPSGeneratorV6, report_id: str, limit: Optional[int] = None, workers: int = 5):
    """Refine SOP using real data iteration."""
    print(f"\n🚀 Starting Phase 2: Expert Iteration for {report_id} (Parallel: {workers} workers)")
    all_sections = load_preprocessed_sections(report_id)
    
    # Apply Archival truncation
    active_sections = truncate_at_archival(all_sections)

    # Filter out table-only sections and appendices
    sections = [s for s in active_sections if not is_table_section(s["section_title"], s["protocol_content"] + s["original_report_content"])]
    skipped_count = len(active_sections) - len(sections)
    if skipped_count > 0:
        print(f"⏩ Filtered out {skipped_count} data-only/appendix sections.")

    if not sections:
        print("✗ No valid sections found for Phase 2.")
        return

    if limit:
        sections = list(sections)[:limit]
        print(f"📌 Limited to first {limit} sections.")
    
    with ThreadPoolExecutor(max_workers=workers) as executor:
        for section in sections:
            executor.submit(process_section_task, engine, section, report_id, 2)
    
    print(f"✅ Phase 2 complete for {report_id}")

def main():
    parser = argparse.ArgumentParser(description="SOP Generation System V6 - Modular Engine")
    parser.add_argument("--phase", type=int, choices=[1, 2], default=1, help="Execution phase (1: Skeleton, 2: Expert)")
    parser.add_argument("--limit", type=int, help="Limit processing to first N sections")
    parser.add_argument("--report", type=str, help="Specific report ID to process")
    parser.add_argument("--workers", type=int, default=5, help="Number of parallel workers")
    args = parser.parse_args()

    if not validate_config():
        print("✗ Configuration invalid. Check .env")
        return

    available_reports = get_available_reports()
    if not available_reports:
        print("✗ No preprocessed data found in data_parsed/")
        return

    report_id = args.report if args.report else available_reports[0]
    print(f"📂 Processing Report: {report_id}")

    engine = SOPSGeneratorV6()
    
    if args.phase == 1:
        run_phase_1(engine, report_id, args.limit, args.workers)
    else:
        run_phase_2(engine, report_id, args.limit, args.workers)

if __name__ == "__main__":
    main()
