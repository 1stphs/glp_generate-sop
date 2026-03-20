from typing import TypedDict, List, Dict, Any

class MasterState(TypedDict):
    """
    Common state for LangGraph workflow
    """
    # Input
    section_title: str
    protocol_content: str
    original_report_content: str
    
    # Internal variables
    complexity: str
    route: str
    reasoning: str
    iteration: int
    
    # Artifacts
    sop_content: str
    reviewer_score: float
    is_pass: bool
    failure_cause: str
    
    # For Phase 2 / Iterative
    data_index: int
    previous_sop: str
    
    # Meta / Multi-source
    all_protocol_contents: List[str]
    all_report_contents: List[str]
    phase: int  # 1: Skeleton, 2: Expert
    report_id: str  # Added for organized persistence
