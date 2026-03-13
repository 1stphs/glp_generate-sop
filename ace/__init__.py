"""
ACE (Agent-Curator-Environment) System

A playbook-based learning framework with three main components:
- Generator: Produces answers using playbook knowledge
- Reflector: Analyzes outputs and provides feedback
- Curator: Updates the playbook based on feedback

Usage:
    from ace import ACE
    
    ace_system = ACE(
        generator_client=client,
        reflector_client=client,
        curator_client=client,
        generator_model="model-name",
        reflector_model="model-name",
        curator_model="model-name"
    )
"""

from .engine import ACE
from .core import Generator, Reflector, Curator, BulletpointAnalyzer

# Extended components from remote for SOP management
from .audit_log import AuditLog
from .rules_manager import RulesManager
from .sop_templates import SOPTemplates
from .agents.sop_writer import SOPWriter
from .agents.sop_simulator import SOPSimulator
from .agents.sop_reviewer import SOPReviewer

__all__ = [
    'ACE', 
    'Generator', 
    'Reflector', 
    'Curator', 
    'BulletpointAnalyzer',
    'AuditLog',
    'RulesManager',
    'SOPTemplates',
    'SOPWriter',
    'SOPSimulator',
    'SOPReviewer',
]

__version__ = "1.0.0"
