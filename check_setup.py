#!/usr/bin/env python3
"""
Quick test script to verify DeepAgent SOP setup.

This script checks if everything is configured correctly before running full tests.
"""

import sys
from pathlib import Path

print("=" * 80)
print("DeepAgent SOP Setup Check")
print("=" * 80)
print()

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

print(f"Project root: {project_root}")
print()

all_ok = True

check_1 = (project_root / "data" / "workflow-b" / "protocol_content.json").exists()
print(f"1. Test data exists: {'✓' if check_1 else '✗'}")
if not check_1:
    print("   Missing: data/workflow-b/protocol_content.json")
    all_ok = False

check_2 = (project_root / "deepagent_sop" / "core" / "main_agent.py").exists()
print(f"2. Main Agent exists: {'✓' if check_2 else '✗'}")
if not check_2:
    print("   Missing: deepagent_sop/core/main_agent.py")
    all_ok = False

check_3 = (project_root / "deepagent_sop" / "core" / "config.py").exists()
print(f"3. Config module exists: {'✓' if check_3 else '✗'}")
if not check_3:
    print("   Missing: deepagent_sop/core/config.py")
    all_ok = False

check_4 = (project_root / "deepagent_sop" / "tests" / "test_writer_agent.py").exists()
print(f"4. Test file exists: {'✓' if check_4 else '✗'}")
if not check_4:
    print("   Missing: deepagent_sop/tests/test_writer_agent.py")
    all_ok = False

print()

env_file = project_root / ".env"
if env_file.exists():
    print("5. .env file: ✓")
    with open(env_file, "r") as f:
        env_content = f.read()

    has_key = any(
        "OPENVIKING_LLM_API_KEY=" in line and len(line.split("=")[1].strip()) > 0
        for line in env_content.split("\n")
        if line.startswith("OPENVIKING_LLM_API_KEY=")
    )

    if has_key:
        print("   API key configured: ✓")
    else:
        print("   API key configured: ✗ (please set OPENVIKING_LLM_API_KEY)")
        all_ok = False
else:
    print("5. .env file: ✗")
    print("   Please run: cp .env.example .env")
    print("   Then edit .env and set OPENVIKING_LLM_API_KEY")
    all_ok = False

print()
print("=" * 80)

if all_ok:
    print("✓ All checks passed!")
    print()
    print("You can now run the tests:")
    print()
    print("  Quick test (Writer Agent only):")
    print("  $ python deepagent_sop/tests/test_writer_agent.py")
    print()
    print("  Full integration test (Main Agent):")
    print("  $ python deepagent_sop/tests/test_integration.py")
    print("=" * 80)
    sys.exit(0)
else:
    print("✗ Some checks failed. Please fix the issues above.")
    print("=" * 80)
    sys.exit(1)
