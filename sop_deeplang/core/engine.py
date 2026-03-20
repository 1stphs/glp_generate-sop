from typing import Dict, List, Any
from langgraph.graph import StateGraph, END
from sop_deeplang.utils.config import MAX_ITERATIONS
from sop_deeplang.utils.memory_manager import MemoryManager
from sop_deeplang.core.state import MasterState
from sop_deeplang.nodes.master import MasterAgent, format_verify_node
from sop_deeplang.nodes.writer import WriterNode
from sop_deeplang.nodes.simulator import SimulatorNode
from sop_deeplang.nodes.reviewer import ReviewerNode
from sop_deeplang.nodes.curator import CuratorNode

class SOPSGeneratorV6:
    """SOP Generator V6 - LangGraph-based workflow"""

    def __init__(self):
        self.memory = MemoryManager()

        # Initialize nodes
        self.master = MasterAgent()
        self.writer = WriterNode()
        self.simulator = SimulatorNode()
        self.reviewer = ReviewerNode()
        self.curator = CuratorNode()

        # Build workflow graph
        self.workflow = self._build_workflow()

    def _build_workflow(self) -> StateGraph:
        """Build LangGraph workflow with complexity-based routing"""

        # Create state graph
        workflow = StateGraph(MasterState)

        # Add nodes
        workflow.add_node("master", self.master)
        workflow.add_node("writer", self.writer)
        workflow.add_node("simulator", self.simulator)
        workflow.add_node("reviewer", self.reviewer)
        workflow.add_node("curator", self.curator)
        workflow.add_node("format_verify", format_verify_node)
        workflow.add_node("save_template", self._save_template_node)
        workflow.add_node("log_complete", self._log_complete_node)

        # Set entry point
        workflow.set_entry_point("master")

        # Master decides path
        workflow.add_edge("master", "writer")

        def should_format_verify_or_simulator(state: MasterState) -> str:
            # If phase 1 OR section is not complex, skip simulator/reviewer loop
            s_type = state.get("section_type", "COMPLEX")
            if state.get("phase") == 1 or s_type != "COMPLEX":
                 return "format_verify"
            return "simulator"

        workflow.add_conditional_edges(
            "writer",
            should_format_verify_or_simulator,
            {"format_verify": "format_verify", "simulator": "simulator"},
        )

        workflow.add_edge("format_verify", "save_template")
        workflow.add_edge("save_template", "log_complete")
        workflow.add_edge("log_complete", END)

        workflow.add_edge("simulator", "reviewer")

        def should_retry_or_end(state: MasterState) -> str:
            if state.get("is_pass", False):
                return "save_template"
            else:
                if state.get("iteration", 1) < MAX_ITERATIONS:
                    return "curator"
                else:
                    return "save_template"

        workflow.add_conditional_edges(
            "reviewer",
            should_retry_or_end,
            {"save_template": "save_template", "curator": "curator"},
        )

        workflow.add_edge("curator", "writer")

        return workflow.compile()

    def _save_template_node(self, state: MasterState) -> MasterState:
        """Save final SOP template to memory"""
        section_title = state["section_title"]
        sop_content = state.get("sop_content", "")
        score = state.get("reviewer_score", 1.0)
        iteration = state.get("iteration", 1)
        # Use is_pass from state if it exists, otherwise fallback to score-based
        is_pass = state.get("is_pass", score >= 4)

        self.memory.save_sop_template(
            section_title,
            sop_content,
            {
                "complexity": state.get("complexity", "unknown"),
                "score": score,
                "iteration": iteration,
                "route": state.get("route", "unknown"),
                "is_pass": is_pass,
                "phase": state.get("phase", 1),
                "report_id": state.get("report_id", "default")
            },
            report_id=state.get("report_id", "default")
        )
        return state

    def _log_complete_node(self, state: MasterState) -> MasterState:
        """Log execution completion"""
        section_title = state["section_title"]
        score = state.get("reviewer_score", 1.0)
        iteration = state.get("iteration", 1)
        self.memory.log_execution_complete(section_title, score, iteration)
        return state

    def process_section(self, initial_state: MasterState) -> Dict[str, Any]:
        """Process a single section through workflow."""
        try:
            result = self.workflow.invoke(initial_state)
            return {
                "section_title": result["section_title"],
                "success": result.get("reviewer_score", 1.0) >= 4,
                "final_score": result.get("reviewer_score", 1.0),
                "iteration_count": result.get("iteration", 1),
                "complexity": result.get("complexity", "unknown"),
                "route": result.get("route", "unknown"),
                "sop_content": result.get("sop_content", ""),
            }
        except Exception as e:
            print(f"❌ Error processing {initial_state['section_title']}: {e}")
            return {"success": False, "error": str(e)}
