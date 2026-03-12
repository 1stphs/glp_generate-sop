"""
ACE (Agent-Curator-Environment) Subsystem

This module implements the ACE system for experience generation and management.

Components:
1. AuditLog: Records all execution details (time, version, sop, id, type, curation, metrics, quality_assessment)
2. RulesManager: Manages rules by SOP type and chapter
3. SOPTemplates: Manages SOP templates (one type -> one template, SOPs by chapter)
4. Reflector: Analyzes SOP quality and provides feedback
5. Curator: Extracts and refines rules from successful executions

Three Core Agents:
- SOPWriter: Generates standardized SOPs (core rules, template, examples)
- SOPSimulator: Simulates SOP execution
- SOPReviewer: Three-party quality review (structure, format, template consistency)

Architecture:
- Two-call pattern: trajectory → insights → playbook update
- Persistent storage for audit logs and rules
- Quality-driven rule management
"""

from .audit_log import AuditLog
from .rules_manager import RulesManager
from .sop_templates import SOPTemplates
from .reflector import Reflector
from .curator import Curator

from .agents.sop_writer import SOPWriter
from .agents.sop_simulator import SOPSimulator
from .agents.sop_reviewer import SOPReviewer

__all__ = [
    "AuditLog",
    "RulesManager",
    "SOPTemplates",
    "Reflector",
    "Curator",
    "SOPWriter",
    "SOPSimulator",
    "SOPReviewer",
]
