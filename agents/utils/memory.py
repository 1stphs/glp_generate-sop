"""
Shared Memory - Context Management Between Agents

This module provides shared context for agent communication.

Design:
- Key-value storage for passing context
- Context persistence across agent calls
- Context isolation between tasks
"""

from typing import Dict, Any, Optional
from datetime import datetime


class SharedMemory:
    """
    Shared memory for context management between agents.

    Stores:
    1. Task context
    2. Agent outputs
    3. Intermediate results
    4. Execution trajectory

    Features:
    - Context isolation by task ID
    - Timestamp tracking
    - Context querying
    """

    def __init__(self):
        """Initialize shared memory."""
        self.context = {}
        self.current_task_id: str = ""

    def new_task(self, task_id: str, initial_context: Optional[Dict[str, Any]] = None):
        """
        Start a new task context.

        Args:
            task_id: Unique task identifier
            initial_context: Initial context for the task
        """
        self.current_task_id = task_id
        self.context[task_id] = {
            "task_id": task_id,
            "started_at": datetime.now().isoformat(),
            "context": initial_context or {},
            "trajectory": [],
            "agent_outputs": {},
        }

    def update_context(self, task_id: str, key: str, value: Any):
        """
        Update context for a task.

        Args:
            task_id: Task identifier
            key: Context key
            value: Context value
        """
        if task_id in self.context:
            self.context[task_id]["context"][key] = value

    def get_context(self, task_id: str, key: str = "") -> Any:
        """
        Get context for a task.

        Args:
            task_id: Task identifier
            key: Specific key (if None, returns entire context)

        Returns:
            Context value or entire context dict
        """
        if task_id not in self.context:
            return None

        if key is None:
            return self.context[task_id]["context"]

        return self.context[task_id]["context"].get(key)

    def add_trajectory_step(
        self, task_id: str, agent: str, action: str, result: Dict[str, Any]
    ):
        """
        Add a step to the execution trajectory.

        Args:
            task_id: Task identifier
            agent: Which agent was called
            action: What action was performed
            result: Result of the action
        """
        if task_id in self.context:
            self.context[task_id]["trajectory"].append(
                {
                    "timestamp": datetime.now().isoformat(),
                    "agent": agent,
                    "action": action,
                    "result": result,
                }
            )

    def record_agent_output(self, task_id: str, agent: str, output: Dict[str, Any]):
        """
        Record output from an agent.

        Args:
            task_id: Task identifier
            agent: Which agent
            output: Agent output
        """
        if task_id in self.context:
            self.context[task_id]["agent_outputs"][agent] = output

    def get_trajectory(self, task_id: str) -> list:
        """
        Get execution trajectory for a task.

        Args:
            task_id: Task identifier

        Returns:
            List of trajectory steps
        """
        if task_id not in self.context:
            return []

        return self.context[task_id]["trajectory"]

    def get_full_context(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Get full context for a task.

        Args:
            task_id: Task identifier

        Returns:
            Complete task context or None
        """
        return self.context.get(task_id)

    def clear_task(self, task_id: str):
        """
        Clear context for a task.

        Args:
            task_id: Task identifier
        """
        if task_id in self.context:
            del self.context[task_id]

    def list_tasks(self) -> list:
        """
        List all active tasks.

        Returns:
            List of task IDs
        """
        return list(self.context.keys())
