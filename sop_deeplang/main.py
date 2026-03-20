import argparse
from pathlib import Path
from typing import List, Dict, Any
from sop_deeplang.utils.config import validate_config, MAX_DATASETS
from sop_deeplang.utils.data_loader import get_available_reports, load_preprocessed_sections
from sop_deeplang.core.engine import SOPSGeneratorV6
from sop_deeplang.core.state import MasterState

def run_phase_1(engine: SOPSGeneratorV6, report_id: str):
    """Generate generic SOP skeleton from merged protocol/report."""
    print(f"\n🚀 Starting Phase 1: Skeleton Generation for {report_id}")
    sections = load_preprocessed_sections(report_id)
    
    if not sections:
        print("✗ No sections found for Phase 1.")
        return
        
    for section in sections:
        initial_state: MasterState = {
            "section_title": section["section_title"],
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
            "data_index": 1,
            "previous_sop": "",
            "all_protocol_contents": [],
            "all_report_contents": [],
            "phase": 1
        }
        engine.process_section(initial_state)
    
    print(f"✅ Phase 1 complete for {report_id}")

def run_phase_2(engine: SOPSGeneratorV6, report_id: str):
    """Refine SOP using real data iteration."""
    print(f"\n🚀 Starting Phase 2: Expert Iteration for {report_id}")
    # Implementation for Phase 2 will involve loading Excel data and iterating
    # For now, we execute Phase 2 over the same sections but with phase=2 flag
    sections = load_preprocessed_sections(report_id)
    
    for section in sections:
        # Load Phase 1 SOP as previous_sop
        previous_sop = engine.memory.load_sop_template(section["section_title"])
        
        initial_state: MasterState = {
            "section_title": section["section_title"],
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
            "data_index": 2, # Simulated dataset 2
            "previous_sop": previous_sop["sop_content"] if previous_sop else "",
            "all_protocol_contents": [],
            "all_report_contents": [],
            "phase": 2
        }
        engine.process_section(initial_state)
    
    print(f"✅ Phase 2 complete for {report_id}")

def main():
    parser = argparse.ArgumentParser(description="SOP Generation System V6 - Modular Engine")
    parser.add_argument("--phase", type=int, choices=[1, 2], default=1, help="Execution phase (1: Skeleton, 2: Expert)")
    parser.add_argument("--report", type=str, help="Specific report ID to process")
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
        run_phase_1(engine, report_id)
    else:
        run_phase_2(engine, report_id)

if __name__ == "__main__":
    main()
