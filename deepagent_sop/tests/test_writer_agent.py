"""
Unit test for Writer Agent.

Tests if Writer Agent can generate SOP from protocol and report.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from deepagent_sop.core.subagents.writer_agent import WriterAgent
from deepagent_sop.core.config import Config


def test_writer_agent():
    """Test Writer Agent with real data."""

    print("=" * 80)
    print("Writer Agent Unit Test")
    print("=" * 80)

    try:
        api_key = Config.get_llm_api_key()
        print(f"✓ API key found (provider: {Config.get_llm_provider()})")
    except RuntimeError as e:
        print(f"✗ Configuration error: {e}")
        return False

    data_dir = Path(__file__).parent.parent.parent / "data" / "workflow-b"

    with open(data_dir / "protocol_content.json", "r", encoding="utf-8") as f:
        protocol_data = json.load(f)

    with open(data_dir / "report_content.json", "r", encoding="utf-8") as f:
        report_data = json.load(f)

    print("✓ Test data loaded from workflow-b")
    print()

    section_title = "验证试验名称"
    original_content = protocol_data["protocol_content1"][:3000]
    target_generate_content = report_data["report_content1"][:3000]

    print(f"Section: {section_title}")
    print(f"Protocol: {len(original_content)} chars")
    print(f"Report: {len(target_generate_content)} chars")
    print("-" * 80)

    llm_config = {
        "api_provider": Config.get_llm_provider(),
        "model": Config.get_llm_model(),
        "temperature": Config.get_llm_temperature(),
        "max_tokens": 2048,
    }

    writer = WriterAgent(llm_config)
    print("✓ Writer Agent initialized")
    print()

    print("Generating SOP...")
    print("-" * 80)

    try:
        result = writer.generate_sop(
            original_content=original_content,
            target_generate_content=target_generate_content,
            section_title=section_title,
            memory="",
            feedback="",
            existing_sop="",
        )

        print()
        print("=" * 80)
        print("SUCCESS!")
        print("=" * 80)
        print()
        print(f"SOP Type: {result.get('sop_type')}")
        print()
        print("Reasoning:")
        print(result.get("reasoning", "N/A")[:500])
        print()
        print("Core Rules:")
        for i, rule in enumerate(result.get("core_rules", []), 1):
            print(f"  {i}. {rule}")
        print()
        print("Template (first 200 chars):")
        print(result.get("template_text", "")[:200])
        print()
        print("Confidence:", result.get("confidence", "N/A"))
        print("=" * 80)

        return True

    except Exception as e:
        print()
        print("=" * 80)
        print("FAILED!")
        print("=" * 80)
        print(f"Error: {e}")
        print()
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_writer_agent()
    sys.exit(0 if success else 1)
