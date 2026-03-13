"""
DeepAgent SOP - Complete autonomous multi-agent system

This package implements a fully autonomous multi-agent system for SOP generation.

Architecture:
- MainAgent: Autonomous orchestrator (natural language driven)
- WriterAgent: SOP generation from protocol/report
- SimulatorAgent: Blind testing of SOP effectiveness
- ReviewerAgent: Quality evaluation
- ReflectorAgent: Insight extraction from trajectory
- CuratorAgent: Memory management and optimization
"""

from .core.main_agent import MainAgent
from .core.base_agent import DeepAgent

__all__ = ["MainAgent", "DeepAgent"]
__version__ = "1.0.0"
