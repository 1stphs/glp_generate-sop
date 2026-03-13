"""
Simple integration test for DeepAgent SOP system.

Tests if the system can run end-to-end with real data from workflow-b.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from deepagent_sop.core.main_agent import MainAgent
from deepagent_sop.core.config import Config


def load_test_data():
    """Load protocol and report data from workflow-b."""

    data_dir = Path(__file__).parent.parent.parent / "data" / "workflow-b"

    with open(data_dir / "protocol_content.json", "r", encoding="utf-8") as f:
        protocol_data = json.load(f)

    with open(data_dir / "report_content.json", "r", encoding="utf-8") as f:
        report_data = json.load(f)

    with open(data_dir / "structure.json", "r", encoding="utf-8") as f:
        structure_data = json.load(f)

    return protocol_data, report_data, structure_data


def test_sop_generation():
    """Test SOP generation with a simple section."""

    print("=" * 80)
    print("DeepAgent SOP Integration Test")
    print("=" * 80)

    try:
        api_key = Config.get_llm_api_key()
        print(f"✓ API key found (provider: {Config.get_llm_provider()})")
    except RuntimeError as e:
        print(f"✗ Configuration error: {e}")
        return False

    print(f"✓ Model: {Config.get_llm_model()}")
    print(f"✓ API Base: {Config.get_llm_api_base() or 'default'}")
    print()

    protocol_data, report_data, structure_data = load_test_data()
    print("✓ Test data loaded from workflow-b")
    print()

    section_title = "验证试验名称"

    original_content = protocol_data["protocol_content1"][:3000]
    target_generate_content = report_data["report_content1"][:3000]

    print(f"Testing section: {section_title}")
    print(f"Protocol content length: {len(original_content)} chars")
    print(f"Report content length: {len(target_generate_content)} chars")
    print("-" * 80)
    print("Initializing Main Agent...")
    print("-" * 80)

    llm_config = {
        "api_provider": Config.get_llm_provider(),
        "model": Config.get_llm_model(),
        "temperature": Config.get_llm_temperature(),
        "max_tokens": 2048,
    }

    main_agent = MainAgent(llm_config=llm_config)

    print("✓ Main Agent initialized")
    print()
    print("-" * 80)
    print("Running task...")
    print("-" * 80)

    user_query = f"""
    请为【{section_title}】章节生成SOP。

    原始方案内容：
    {original_content}

    目标报告内容：
    {target_generate_content}

    要求：
    1. 分析原始方案和目标报告的差异
    2. 提取转换规则
    3. 生成结构化的SOP（包含核心规则、模板和示例）
    4. 进行1轮验证和优化
    """

    try:
        result = main_agent.run(
            user_query=user_query,
            enable_learning=False,
        )

        print()
        print("=" * 80)
        print("TEST PASSED!")
        print("=" * 80)
        print()
        print("Task Understanding:")
        print(result["task_understanding"])
        print()
        print("-" * 80)
        print("Plan:")
        print(json.dumps(result["plan"], indent=2, ensure_ascii=False))
        print()
        print("-" * 80)
        print("Final Result:")
        print(json.dumps(result["final_result"], indent=2, ensure_ascii=False))
        print()
        print("-" * 80)
        print("Summary:")
        print(result["summary"])
        print()
        print(f"Trajectory steps: {len(result['trajectory'])}")
        print("=" * 80)

        return True

    except Exception as e:
        print()
        print("=" * 80)
        print("TEST FAILED!")
        print("=" * 80)
        print(f"Error: {e}")
        print()
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_sop_generation()
    sys.exit(0 if success else 1)
