"""
Quick import test - no API key required.

Tests if all modules can be imported correctly.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

print("=" * 80)
print("DeepAgent SOP Import Test")
print("=" * 80)
print()

all_ok = True

try:
    from deepagent_sop.core.config import Config

    print("✓ Config module imported")
except Exception as e:
    print(f"✗ Config import failed: {e}")
    all_ok = False

try:
    from deepagent_sop.core.base_agent import DeepAgent

    print("✓ Base Agent imported")
except Exception as e:
    print(f"✗ Base Agent import failed: {e}")
    all_ok = False

try:
    from deepagent_sop.core.subagents.writer_agent import WriterAgent

    print("✓ Writer Agent imported")
except Exception as e:
    print(f"✗ Writer Agent import failed: {e}")
    all_ok = False

try:
    from deepagent_sop.core.subagents.simulator_agent import SimulatorAgent

    print("✓ Simulator Agent imported")
except Exception as e:
    print(f"✗ Simulator Agent import failed: {e}")
    all_ok = False

try:
    from deepagent_sop.core.subagents.reviewer_agent import ReviewerAgent

    print("✓ Reviewer Agent imported")
except Exception as e:
    print(f"✗ Reviewer Agent import failed: {e}")
    all_ok = False

try:
    from deepagent_sop.core.learning.reflector_agent import ReflectorAgent

    print("✓ Reflector Agent imported")
except Exception as e:
    print(f"✗ Reflector Agent import failed: {e}")
    all_ok = False

try:
    from deepagent_sop.core.learning.curator_agent import CuratorAgent

    print("✓ Curator Agent imported")
except Exception as e:
    print(f"✗ Curator Agent import failed: {e}")
    all_ok = False

try:
    from deepagent_sop.core.main_agent import MainAgent

    print("✓ Main Agent imported")
except Exception as e:
    print(f"✗ Main Agent import failed: {e}")
    all_ok = False

print()
print("=" * 80)

if all_ok:
    print("✓ All imports successful!")
    print()
    print("Next step: Configure API key and run actual tests")
    print()
    print("1. Copy .env.example to .env")
    print("2. Set OPENVIKING_LLM_API_KEY in .env")
    print("3. Run: python deepagent_sop/tests/test_writer_agent.py")
    print("=" * 80)
    sys.exit(0)
else:
    print("✗ Some imports failed")
    print("=" * 80)
    sys.exit(1)
