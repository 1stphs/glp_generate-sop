"""
DeepAgent Architecture

This module implements a fully natural language-driven multi-agent system.

Architecture:
- MasterAgent: Core brain that autonomously plans and executes tasks
- InsightAgent: Extracts insights and lessons from execution trajectories
- PlaybookAgent: Manages persistent knowledge base (playbooks)

Key Design Principles:
1. Complete natural language driving - no hardcoded workflows
2. Master Agent makes autonomous decisions based on task understanding
3. Two-call pattern: trajectory → insights → playbook update
4. All agents communicate through shared memory context
"""

from .master_agent import MasterAgent
from .insight_agent import InsightAgent
from .playbook_agent import PlaybookAgent

__all__ = [
    "MasterAgent",
    "InsightAgent",
    "PlaybookAgent",
]
