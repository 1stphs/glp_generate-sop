"""
Test Master Agent - Autonomous Decision-Making

This test validates Master Agent's ability to:
1. Understand natural language tasks
2. Plan autonomously without hardcoded workflows
3. Select and coordinate sub-agents
4. Return structured results
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.master_agent import MasterAgent
from agents.utils.memory import SharedMemory


def test_simple_task():
    """Test simple task: Generate SOP for one chapter."""

    print("=" * 60)
    print("Test 1: Simple Task")
    print("=" * 60)

    task = "为验证报告章节生成一个SOP，不进行迭代优化"

    llm_config = {
        "api_provider": "openai",
        "model": "gpt-4o-mini",
        "temperature": 0.2,
        "max_tokens": 2048,
    }

    master = MasterAgent(llm_config)
    result = master.execute(task)

    print("\nReasoning:")
    print(result.get("reasoning", ""))
    print("\nPlan:")
    print(result.get("plan", ""))
    print("\nFinal Summary:")
    print(result.get("final_summary", ""))


def test_complex_task():
    """Test complex task: Generate SOPs with iterations."""

    print("\n" + "=" * 60)
    print("Test 2: Complex Task with Iterations")
    print("=" * 60)

    task = "用第1份protocol和report生成5个章节的SOP，进行3轮迭代优化，最后提取insights并更新playbook"

    llm_config = {
        "api_provider": "openai",
        "model": "gpt-4o",
        "temperature": 0.2,
        "max_tokens": 4096,
    }

    master = MasterAgent(llm_config)
    result = master.execute(task)

    print("\nReasoning:")
    print(result.get("reasoning", ""))
    print("\nPlan:")
    print(result.get("plan", ""))
    print("\nFinal Summary:")
    print(result.get("final_summary", ""))


def test_autonomy():
    """Test that Master Agent makes autonomous decisions."""

    print("\n" + "=" * 60)
    print("Test 3: Autonomy Validation")
    print("=" * 60)

    task = "对比Version1和Version2的SOP质量差异，找出改进点"

    llm_config = {
        "api_provider": "openai",
        "model": "gpt-4o",
        "temperature": 0.3,
        "max_tokens": 2048,
    }

    master = MasterAgent(llm_config)
    result = master.execute(task)

    # Check that Master Agent autonomously planned
    reasoning = result.get("reasoning", "")
    plan = result.get("plan", "")

    # TODO: Implement autonomy checks
    print("\nReasoning:")
    print(reasoning)
    print("\nPlan:")
    print(plan)
    print("\nFinal Summary:")
    print(result.get("final_summary", ""))


def main():
    """Run all Master Agent tests."""

    print("\n" + "=" * 60)
    print("Master Agent Tests")
    print("=" * 60)

    # Test 1: Simple task
    test_simple_task()

    # Test 2: Complex task with iterations
    test_complex_task()

    # Test 3: Autonomy validation
    test_autonomy()

    print("\n" + "=" * 60)
    print("✅ All Master Agent tests completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
