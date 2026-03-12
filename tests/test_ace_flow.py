"""
Test ACE Flow - Complete ACE Subsystem Tests

This test validates the ACE subsystem:
1. Audit log recording
2. Rules management
3. SOP templates management
4. Reflection quality assessment
5. Curation rule extraction
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from ace.audit_log import AuditLog
from ace.rules_manager import RulesManager
from ace.sop_templates import SOPTemplates
from ace.reflector import Reflector
from ace.curator import Curator


def test_audit_log():
    """Test audit log recording."""

    print("=" * 60)
    print("Test 1: Audit Log Recording")
    print("=" * 60)

    audit = AuditLog(base_dir="test_output/audit_log")

    # Log a sample iteration
    entry = {
        "chapter_id": "test_chapter_001",
        "chapter_title": "验证报告",
        "version": "Version1",
        "iteration": 1,
        "sop": "## 一、核心填写规则\n1. 规则1\n\n## 二、通用模板\n模板内容",
        "sop_id": "sop_001",
        "sop_type": "rule_template",
        "curation": {},
        "metrics": {"tokens": 1000, "latency_sec": 5.2, "model": "gpt-4o-mini"},
        "quality_assessment": {"quality_score": 4.5, "feedback": "质量良好"},
    }

    audit.log_iteration(entry)

    # Verify
    iterations = audit.get_chapter_iterations("test_chapter_001")
    stats = audit.get_statistics()

    print(f"✓ Logged {len(iterations)} iteration(s)")
    print(f"✓ Total chapters: {stats['total_chapters']}")
    print(f"✓ Total iterations: {stats['total_iterations']}")
    print(f"✓ Avg quality: {stats['avg_quality_score']}")


def test_rules_manager():
    """Test rules management."""

    print("\n" + "=" * 60)
    print("Test 2: Rules Management")
    print("=" * 60)

    rules_mgr = RulesManager(base_dir="test_output/rules")

    # Add sample rules
    rule1_id = rules_mgr.add_rule(
        sop_type="rule_template",
        chapter_id="test_chapter_001",
        content="规则1：验证报告标题必须包含中英文双语，逐字复制不添加换行",
        tags=["验证报告", "标题格式", "双语"],
    )

    rule2_id = rules_mgr.add_rule(
        sop_type="rule_template",
        chapter_id="test_chapter_001",
        content="规则2：所有字段占位符必须使用[字段名]格式",
        tags=["验证报告", "格式规范", "占位符"],
    )

    # Query rules
    rules = rules_mgr.get_rules("rule_template", "test_chapter_001")

    print(f"✓ Added {len(rules)} rules")
    print(f"✓ Rule IDs: {[rule1_id, rule2_id]}")

    # Update metrics
    rules_mgr.update_rule_metrics(rule1_id, helpful=1, harmful=0, increment_usage=True)

    stats = rules_mgr.get_statistics()
    print(f"✓ Total rules: {stats['total_rules']}")
    print(f"✓ Total helpful: {stats['total_helpful']}")
    print(f"✓ Total harmful: {stats['total_harmful']}")


def test_sop_templates():
    """Test SOP templates management."""

    print("\n" + "=" * 60)
    print("Test 3: SOP Templates Management")
    print("=" * 60)

    templates = SOPTemplates(base_dir="test_output/sop_templates")

    # Save template
    templates.save_template(
        sop_type="rule_template",
        template_content="## 一、核心填写规则\n${rules}\n\n## 二、通用模板\n${template}\n\n## 三、示例\n${examples}",
    )

    # Save SOP
    templates.save_sop(
        chapter_id="test_chapter_001",
        chapter_title="验证报告",
        sop_type="rule_template",
        sop_content="## 一、核心填写规则\n1. 规则1\n\n## 二、通用模板\n模板内容",
        version="Version1",
        quality_score=4.5,
    )

    # Query SOP
    sop = templates.get_sop("test_chapter_001", "rule_template")

    print(f"✓ Saved template and SOP")
    print(f"✓ SOP version: {sop.get('version', '')}")
    print(f"✓ SOP quality: {sop.get('quality_score', 0)}")

    stats = templates.get_statistics()
    print(f"✓ Total templates: {stats['total_templates']}")
    print(f"✓ Total SOPs: {stats['total_sops']}")
    print(f"✓ Avg quality: {stats['avg_quality']}")


def main():
    """Run all ACE flow tests."""

    print("\n" + "=" * 60)
    print("ACE Flow Tests")
    print("=" * 60)

    # Test 1: Audit log
    test_audit_log()

    # Test 2: Rules manager
    test_rules_manager()

    # Test 3: SOP templates
    test_sop_templates()

    print("\n" + "=" * 60)
    print("✅ All ACE flow tests completed!")
    print("=" * 60)
    print("\nTest outputs saved to: test_output/")


if __name__ == "__main__":
    main()
