"""
Test Integration - Complete End-to-End Workflow

This test validates the two-call pattern:
1. First call: Master Agent generates trajectory
2. Second call: Insight Agent extracts insights from trajectory
3. Second call (continued): Playbook Agent updates playbook with insights

This demonstrates the complete DeepAgent workflow with natural language driving.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.master_agent import MasterAgent
from agents.insight_agent import InsightAgent
from agents.playbook_agent import PlaybookAgent
from agents.utils.memory import SharedMemory


def complete_workflow(user_task: str):
    """
    Complete workflow demonstrating two-call pattern.

    Steps:
    1. Master Agent generates trajectory
    2. Insight Agent extracts insights from trajectory
    3. Playbook Agent updates playbook with insights
    """

    print("\n" + "=" * 60)
    print("Complete Workflow Test")
    print("=" * 60)

    # Initialize LLM config
    llm_config = {
        "api_provider": "openai",
        "model": "gpt-4o",
        "temperature": 0.2,
        "max_tokens": 4096,
    }

    # Initialize agents
    master = MasterAgent(llm_config)
    insight = InsightAgent(llm_config)
    playbook = PlaybookAgent(
        llm_config, playbook_path="test_output/playbook/playbooks.json"
    )
    memory = SharedMemory()

    # === 第一次调用：Master Agent生成trajectory ===
    print("\n=== 第一次调用：Master Agent生成trajectory ===")
    master_result = master.execute(user_task)

    # Extract trajectory from master result
    # Note: In real implementation, Master Agent would populate trajectory during execution
    # For this test, we create a mock trajectory
    task_id = "integration_test_001"
    memory.new_task(
        task_id,
        {
            "task": user_task,
            "master_plan": master_result.get("plan", ""),
            "master_reasoning": master_result.get("reasoning", ""),
        },
    )

    # Mock trajectory (in real implementation, this would be built during execution)
    trajectory = {
        "task_id": task_id,
        "task_description": user_task,
        "master_plan": master_result.get("plan", ""),
        "execution_steps": [
            {
                "step": "task_planning",
                "agent": "MasterAgent",
                "result": "任务规划和分解",
            },
            {"step": "data_loading", "agent": "MasterAgent", "result": "加载测试数据"},
            {"step": "sop_generation", "agent": "ACE", "result": "生成SOP"},
            {"step": "reflection", "agent": "ACE", "result": "质量评估和反思"},
        ],
        "quality_metrics": {
            "avg_quality_score": 4.2,
            "total_iterations": 3,
            "total_tokens": 5000,
        },
        "used_rules": [
            {
                "rule_id": "rule_001",
                "content": "规则1：双语标题必须逐字复制",
                "helpful": 1,
                "harmful": 0,
            }
        ],
    }

    memory.add_trajectory_step(
        task_id, "MasterAgent", "generate_trajectory", master_result
    )

    # === 第二次调用（第1部分）：Insight Agent提取insights ===
    print("\n=== 第二次调用（第1部分）：Insight Agent提取insights ===")
    insights = insight.extract(trajectory)

    memory.record_agent_output(task_id, "InsightAgent", {"insights": insights})
    memory.add_trajectory_step(
        task_id, "InsightAgent", "extract_insights", {"insights": insights}
    )

    print(f"✓ Extracted {len(insights)} insights")

    # === 第二次调用（第2部分）：Playbook Agent更新playbook ===
    print("\n=== 第二次调用（第2部分）：Playbook Agent更新playbook ===")
    update_result = playbook.update(insights)

    memory.record_agent_output(task_id, "PlaybookAgent", update_result)
    memory.add_trajectory_step(
        task_id, "PlaybookAgent", "update_playbook", update_result
    )

    print(f"✓ Updated playbook: {update_result.get('changes_summary', {})}")

    # === 总结 ===
    print("\n=== 工作流总结 ===")
    full_context = memory.get_full_context(task_id)

    print("\n原始任务:")
    print(full_context.get("context", {}).get("task", ""))

    print("\nMaster Agent规划:")
    print(full_context.get("context", {}).get("master_plan", ""))

    print("\nTrajectory步骤数:")
    print(len(full_context.get("trajectory", [])))

    print("\n提取的Insights数:")
    print(len(insights))

    print("\nPlaybook更新:")
    print(update_result.get("changes_summary", {}))

    return {
        "task_id": task_id,
        "user_task": user_task,
        "trajectory": trajectory,
        "insights": insights,
        "playbook_update": update_result,
    }


def main():
    """Run integration test."""

    print("\n" + "=" * 60)
    print("DeepAgent Integration Test")
    print("=" * 60)

    # Test Case 1: Simple task with trajectory
    print("\n--- Test Case 1: Generate SOPs with insights ---")
    task1 = (
        "用protocol和report数据生成验证报告章节的SOP，进行质量评估，最后提取insights"
    )
    result1 = complete_workflow(task1)

    # Test Case 2: Task with playbook update
    print("\n--- Test Case 2: Generate and update playbook ---")
    task2 = "生成3个章节的SOP，迭代3次，提取insights并更新playbook"
    result2 = complete_workflow(task2)

    print("\n" + "=" * 60)
    print("✅ Integration test completed!")
    print("=" * 60)
    print("\nKey outputs:")
    print("- Test outputs saved to: test_output/")
    print("- Playbook updated at: test_output/playbook/playbooks.json")
    print("- Two-call pattern demonstrated")


if __name__ == "__main__":
    main()
