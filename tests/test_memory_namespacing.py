import os
import shutil
from pathlib import Path
from sop_deeplang.core.engine import SOPSGeneratorV6
from sop_deeplang.core.state import MasterState

def test_memory_isolation():
    memory_base = Path("memory/experiments")
    
    # Clean up previous tests
    if memory_base.exists():
        shutil.rmtree(memory_base)
    
    # 1. Test Experiment Type A
    print("\n--- Testing Experiment Type A ---")
    engine_a = SOPSGeneratorV6(experiment_type="Test_Exp_A")
    state_a: MasterState = {
        "section_title": "Test_Section",
        "protocol_content": "Protocol A",
        "original_report_content": "Report A",
        "complexity": "simple",
        "route": "simple_path",
        "reasoning": "Test",
        "iteration": 1,
        "sop_content": "SOP Content A",
        "reviewer_score": 5.0,
        "is_pass": True,
        "failure_cause": "",
        "data_index": 1,
        "previous_sop": "",
        "all_report_contents": ["Report A"],
        "phase": 1,
        "report_id": "Report_A",
        "experiment_type": "Test_Exp_A"
    }
    engine_a._save_template_node(state_a)
    
    path_a = memory_base / "Test_Exp_A" / "markdown_sops" / "Test_Section.md"
    assert path_a.exists(), f"File A not found at {path_a}"
    print(f"✅ Experiment A file saved at {path_a}")

    # 2. Test Experiment Type B
    print("\n--- Testing Experiment Type B ---")
    engine_b = SOPSGeneratorV6(experiment_type="Test_Exp_B")
    state_b = state_a.copy()
    state_b["experiment_type"] = "Test_Exp_B"
    state_b["sop_content"] = "SOP Content B"
    engine_b._save_template_node(state_b)
    
    path_b = memory_base / "Test_Exp_B" / "markdown_sops" / "Test_Section.md"
    assert path_b.exists(), f"File B not found at {path_b}"
    print(f"✅ Experiment B file saved at {path_b}")
    
    # 3. Verify Isolation
    with open(path_a, "r") as f:
        content_a = f.read()
    with open(path_b, "r") as f:
        content_b = f.read()
        
    assert content_a == "SOP Content A"
    assert content_b == "SOP Content B"
    print("✅ Isolation verified: Files have different content in different folders.")

if __name__ == "__main__":
    try:
        test_memory_isolation()
        print("\n✨ ALL MEMORY ISOLATION TESTS PASSED ✨")
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
