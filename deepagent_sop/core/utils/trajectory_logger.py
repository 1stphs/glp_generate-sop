"""
Trajectory Logger - Record execution traces

Records the complete execution trajectory of Main Agent including:
- Decision steps (Main Agent's autonomous decisions)
- Execution steps (Sub-agent execution results)
- Timestamps and reasoning
"""

import json
from typing import Dict, Any, List
from datetime import datetime


class TrajectoryLogger:
    """
    Manages trajectory logging for DeepAgent.

    Trajectory structure:
    - Each step includes: step_num, agent, type, input, output, timestamp, reasoning
    - Types: decision (Main Agent), execution (sub-agent)
    """

    def __init__(self):
        """Initialize TrajectoryLogger."""
        self.trajectory: List[Dict[str, Any]] = []

    def log_decision(
        self,
        step_num: int,
        agent_name: str,
        input_data: Dict[str, Any],
        output_data: Dict[str, Any],
        reasoning: str,
    ):
        """
        Log a Main Agent decision.

        Args:
            step_num: Step number
            agent_name: Agent name (typically "main_agent")
            input_data: Input to the decision
            output_data: Output of the decision
            reasoning: Reasoning behind the decision
        """
        entry = {
            "step": step_num,
            "agent": agent_name,
            "type": "decision",
            "input": input_data,
            "output": output_data,
            "reasoning": reasoning,
            "timestamp": datetime.now().isoformat(),
        }

        self.trajectory.append(entry)

    def log_execution(
        self,
        step_num: int,
        agent_name: str,
        input_data: Dict[str, Any],
        output_data: Dict[str, Any],
    ):
        """
        Log a sub-agent execution.

        Args:
            step_num: Step number
            agent_name: Agent name (writer, simulator, reviewer, etc.)
            input_data: Input to the agent
            output_data: Output from the agent
        """
        entry = {
            "step": step_num,
            "agent": agent_name,
            "type": "execution",
            "input": input_data,
            "output": output_data,
            "timestamp": datetime.now().isoformat(),
        }

        self.trajectory.append(entry)

    def get_trajectory(self) -> List[Dict[str, Any]]:
        """
        Get complete trajectory.

        Returns:
            Complete trajectory as list of entries
        """
        return self.trajectory

    def get_summary(self) -> Dict[str, Any]:
        """
        Get trajectory summary.

        Returns:
            Summary statistics
        """
        total_steps = len(self.trajectory)
        decision_steps = [s for s in self.trajectory if s.get("type") == "decision"]
        execution_steps = [s for s in self.trajectory if s.get("type") == "execution"]

        # Count by agent
        agent_counts = {}
        for entry in self.trajectory:
            agent = entry.get("agent", "unknown")
            agent_counts[agent] = agent_counts.get(agent, 0) + 1

        return {
            "total_steps": total_steps,
            "decision_steps": len(decision_steps),
            "execution_steps": len(execution_steps),
            "agent_counts": agent_counts,
            "start_time": self.trajectory[0].get("timestamp")
            if self.trajectory
            else None,
            "end_time": self.trajectory[-1].get("timestamp")
            if self.trajectory
            else None,
        }

    def clear(self):
        """Clear trajectory."""
        self.trajectory = []

    def save_to_file(self, file_path: str):
        """
        Save trajectory to JSON file.

        Args:
            file_path: Path to save trajectory
        """
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(self.trajectory, f, ensure_ascii=False, indent=2)

    def load_from_file(self, file_path: str):
        """
        Load trajectory from JSON file.

        Args:
            file_path: Path to load trajectory from
        """
        with open(file_path, "r", encoding="utf-8") as f:
            self.trajectory = json.load(f)

    def format_as_markdown(self) -> str:
        """
        Format trajectory as Markdown.

        Returns:
            Markdown formatted trajectory
        """
        if not self.trajectory:
            return "# Trajectory\n\nNo steps recorded."

        lines = ["# Execution Trajectory\n"]
        lines.append(f"\n**Total Steps**: {len(self.trajectory)}\n")
        lines.append("---\n")

        for entry in self.trajectory:
            step_num = entry.get("step", "?")
            agent = entry.get("agent", "unknown")
            step_type = entry.get("type", "unknown")
            timestamp = entry.get("timestamp", "")
            reasoning = entry.get("reasoning", "")

            lines.append(f"## Step {step_num}: {agent} ({step_type})")
            lines.append(f"\n**Time**: {timestamp}\n")

            if reasoning:
                lines.append(f"**Reasoning**: {reasoning}\n")

            # Input
            input_data = entry.get("input", {})
            if input_data:
                lines.append("**Input**:")
                for key, value in input_data.items():
                    lines.append(f"- {key}: {str(value)[:100]}...")
                lines.append("")

            # Output
            output_data = entry.get("output", {})
            if output_data:
                lines.append("**Output**:")
                for key, value in output_data.items():
                    lines.append(f"- {key}: {str(value)[:100]}...")
                lines.append("")

            lines.append("---\n")

        return "\n".join(lines)

    def get_agent_steps(self, agent_name: str) -> List[Dict[str, Any]]:
        """
        Get all steps for a specific agent.

        Args:
            agent_name: Agent name to filter by

        Returns:
            List of steps for the agent
        """
        return [step for step in self.trajectory if step.get("agent") == agent_name]
