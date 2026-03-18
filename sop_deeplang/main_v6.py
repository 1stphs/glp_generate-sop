"""
SOP Generation System V6 - Main Entry Point (使用真实数据)
基于LangGraph的多模型SOP自动生成系统

使用真实数据：
- protocol_content.json: 验证方案
- report_content.json: GLP报告
"""

import json
import re
from pathlib import Path
from typing import Dict, Any, List, TypedDict

# LangGraph imports
try:
    from langgraph.graph import StateGraph, END
except ImportError:
    print("Error: langgraph not installed. Run: pip install langgraph")
    exit(1)

# Local imports
from config_v6 import (
    BASE_DIR,
    MEMORY_DIR,
    MAX_ITERATIONS,
    validate_config,
    MASTER_SKILL_VERSION,
)
from memory_manager_v6 import MemoryManagerV6
from nodes.master import (
    MasterState,
    format_verify_node,
    should_route_simple,
    should_retry_complex,
    MasterAgent,
)
from nodes.writer import WriterNode
from nodes.simulator import SimulatorNode
from nodes.reviewer import ReviewerNode
from nodes.curator import CuratorNode


def parse_sections_from_protocol(content: str) -> List[Dict[str, str]]:
    """
    从验证方案中解析章节列表。

    使用预定义的主要章节列表。
    """
    # 预定义的主要章节（基于GLP验证方案的标准结构）
    main_sections = [
        "引言",
        "材料和方法",
        "方法学验证内容和接受标准",
        "数据处理",
        "归档",
    ]

    sections = []

    for i, title in enumerate(main_sections, 1):
        sections.append(
            {
                "section_title": title,
                "protocol_content": f"验证方案 - 章节 {i}: {title}",
                "original_report_content": f"GLP报告 - 章节 {i}: {title}",
            }
        )

    return sections


def load_real_data(index: int) -> tuple[str, str]:
    """
    加载真实的验证方案和GLP报告数据。

    Args:
        index: 数据集索引（从1开始）

    Returns:
        (protocol_content, report_content)
    """
    base_dir = Path(
        "/Users/pangshasha/Documents/github/glp_generate-sop/mockData/workflow-b"
    )

    # 加载验证方案
    protocol_file = base_dir / "protocol_content.json"
    with open(protocol_file, "r", encoding="utf-8") as f:
        protocol_data = json.load(f)

    # 加载GLP报告
    report_file = base_dir / "report_content.json"
    with open(report_file, "r", encoding="utf-8") as f:
        report_data = json.load(f)

    # 使用指定索引的数据
    protocol_content = protocol_data.get(f"protocol_content{index}", "")
    report_content = report_data.get(f"report_content{index}", "")

    return protocol_content, report_content


def prepare_sections(
    protocol_content: str, report_content: str, max_sections: int = 5
) -> List[Dict[str, str]]:
    """
    准备章节列表。

    Args:
        protocol_content: 验证方案内容
        report_content: GLP报告内容
        max_sections: 最大章节数量

    Returns:
        章节列表
    """
    # 从验证方案中解析章节
    sections = parse_sections_from_protocol(protocol_content)

    # 限制章节数量
    sections = sections[:max_sections]

    # 为每个章节添加完整的内容引用（用于AI理解上下文）
    for section in sections:
        # 截取相关内容片段（用于上下文）
        title = section["section_title"]

        # 从protocol中查找相关内容
        protocol_snippet = ""
        if title in protocol_content:
            idx = protocol_content.find(title)
            protocol_snippet = protocol_content[max(0, idx - 100) : idx + 500]
        else:
            # 如果找不到精确匹配，使用前2000字作为上下文
            protocol_snippet = protocol_content[:2000]

        # 从report中查找相关内容
        report_snippet = ""
        if title in report_content:
            idx = report_content.find(title)
            report_snippet = report_content[max(0, idx - 100) : idx + 500]
        else:
            report_snippet = report_content[:2000]

        # 更新内容
        section["protocol_content"] = protocol_snippet
        section["original_report_content"] = report_snippet

    return sections


class SOPSGeneratorV6:
    """SOP Generator V6 - LangGraph-based workflow"""

    def __init__(self):
        self.memory = MemoryManagerV6()

        # Initialize nodes
        self.master = MasterAgent()
        self.writer = WriterNode()
        self.simulator = SimulatorNode()
        self.reviewer = ReviewerNode()
        self.curator = CuratorNode()

        # Build workflow graph
        self.workflow = self._build_workflow()

    def _build_workflow(self) -> StateGraph:
        """Build LangGraph workflow with complexity-based routing"""

        # Create state graph
        workflow = StateGraph(MasterState)

        # Add nodes
        workflow.add_node("master", self.master)
        workflow.add_node("writer", self.writer)
        workflow.add_node("simulator", self.simulator)
        workflow.add_node("reviewer", self.reviewer)
        workflow.add_node("curator", self.curator)
        workflow.add_node("format_verify", format_verify_node)
        workflow.add_node("save_template", self._save_template_node)
        workflow.add_node("log_complete", self._log_complete_node)

        # Set entry point
        workflow.set_entry_point("master")

        workflow.add_conditional_edges(
            "master",
            lambda state: "writer",
            {"writer": "writer"},
        )

        def should_format_verify_or_simulator(state: MasterState) -> str:
            return "format_verify" if state["route"] == "simple_path" else "simulator"

        workflow.add_conditional_edges(
            "writer",
            should_format_verify_or_simulator,
            {"format_verify": "format_verify", "simulator": "simulator"},
        )

        workflow.add_edge("format_verify", "save_template")
        workflow.add_edge("save_template", "log_complete")
        workflow.add_edge("log_complete", END)

        workflow.add_edge("simulator", "reviewer")

        # Reviewer decision: pass -> save, fail -> retry
        def should_retry_or_end(state: MasterState) -> str:
            if state.get("is_pass", False):
                return "save_template"
            else:
                if state.get("iteration", 1) < MAX_ITERATIONS:
                    return "curator"
                else:
                    return "save_template"

        workflow.add_conditional_edges(
            "reviewer",
            should_retry_or_end,
            {"save_template": "save_template", "curator": "curator"},
        )

        # Curator -> Writer (with incremented iteration)
        workflow.add_edge("curator", "writer")

        # Save template -> log -> END
        workflow.add_edge("save_template", "log_complete")
        workflow.add_edge("log_complete", END)

        # Compile workflow
        return workflow.compile()

    def _save_template_node(self, state: MasterState) -> MasterState:
        """Save final SOP template to memory (save all results, passed or failed)"""
        section_title = state["section_title"]
        sop_content = state.get("sop_content", "")
        score = state.get("reviewer_score", 1.0)
        iteration = state.get("iteration", 1)

        # Save all results regardless of score (preserve even failed outputs)
        is_pass = score >= 4

        self.memory.save_sop_template(
            section_title,
            sop_content,
            {
                "complexity": state.get("complexity", "unknown"),
                "score": score,
                "iteration": iteration,
                "route": state.get("route", "unknown"),
                "is_pass": is_pass,
            },
        )

        if is_pass:
            print(f"💾 [{section_title}] 模板已保存 (评分: {score}) ✓")
        else:
            print(f"💾 [{section_title}] 结果已保存 (评分: {score}) ⚠️ 未达标")

        return state

    def _log_complete_node(self, state: MasterState) -> MasterState:
        """Log execution completion"""
        section_title = state["section_title"]
        score = state.get("reviewer_score", 1.0)
        iteration = state.get("iteration", 1)

        self.memory.log_execution_complete(section_title, score, iteration)

        print(f"✅ [{section_title}] 执行完成 (迭代{iteration}次, 最终评分: {score})")

        return state

    def process_section(
        self,
        section: Dict[str, Any],
        data_index: int = 1,
        previous_sop: str = "",
    ) -> Dict[str, Any]:
        """
        Process a single section through workflow.

        Args:
            section: Dictionary with section_title, original_content, generate_content
            data_index: Current dataset index (1-based)
            previous_sop: Previous SOP for enhancement mode

        Returns:
            Result dictionary with processing status and metrics
        """
        section_title = section.get("section_title", "")
        mode = "增强模式" if data_index > 1 else "初始模式"
        print(f"\n{'=' * 70}")
        print(f"📋 开始处理章节: {section_title} (数据集{data_index} | {mode})")
        if previous_sop:
            print(f"📚 使用上一次SOP作为参考 (长度: {len(previous_sop)} 字符)")
        print(f"{'=' * 70}\n")

        # Initial state
        initial_state: MasterState = {
            "section_title": section_title,
            "protocol_content": section.get("protocol_content", ""),
            "original_report_content": section.get("original_report_content", ""),
            "complexity": "",
            "route": "",
            "reasoning": "",
            "iteration": 1,
            "sop_content": "",
            "reviewer_score": 1.0,
            "is_pass": False,
            "failure_cause": "",
            "data_index": data_index,
            "previous_sop": previous_sop,
            "all_protocol_contents": [],
            "all_report_contents": [],
        }

        try:
            # Run workflow
            result = self.workflow.invoke(initial_state)

            # Return result summary
            return {
                "section_title": section_title,
                "success": result.get("reviewer_score", 1.0) >= 4,
                "final_score": result.get("reviewer_score", 1.0),
                "iteration_count": result.get("iteration", 1),
                "complexity": result.get("complexity", "unknown"),
                "route": result.get("route", "unknown"),
                "sop_content": result.get("sop_content", ""),
            }

        except Exception as e:
            print(f"❌ [{section_title}] 处理失败: {e}")
            import traceback

            traceback.print_exc()

            return {
                "section_title": section_title,
                "success": False,
                "final_score": 1.0,
                "iteration_count": 0,
                "complexity": "unknown",
                "route": "unknown",
                "error": str(e),
            }


def main():
    """Main execution function with multi-dataset iteration"""
    print("\n" + "=" * 70)
    print("🚀 SOP 生成系统 V6 - DeepLang (多数据集迭代模式)")
    print("=" * 70 + "\n")

    # Validate configuration
    if not validate_config():
        print("⚠️  API Keys not configured. Please check .env file.")
        print("   Required: OPENAI_API_KEY, GEMINI_API_KEY")
        print("\n   提示: 如果没有配置API，系统将无法正常运行。")
        return

    # Initialize memory and ensure previous_sops.json exists
    memory = MemoryManagerV6()
    if not memory.previous_sops_file.exists():
        with open(memory.previous_sops_file, "w") as f:
            json.dump({}, f)

    # Load all available datasets
    print("📂 加载数据集...")
    all_protocol_contents = []
    all_report_contents = []

    max_data_sets = 10  # Try to load up to 10 datasets
    for i in range(max_data_sets):
        protocol, report = load_real_data(i + 1)
        if protocol and report:
            all_protocol_contents.append(protocol)
            all_report_contents.append(report)
            print(f"   ✓ 数据集 {i + 1}: {len(protocol)} + {len(report)} 字符")
        else:
            break

    if not all_protocol_contents:
        print("   ✗ 没有可用数据集")
        return

    print(f"\n   共 {len(all_protocol_contents)} 份数据集可用")

    # Check for existing checkpoint
    checkpoint = memory.get_checkpoint()
    if checkpoint > 0:
        print(f"   📍 检测到checkpoint: 数据集 {checkpoint} 已处理")
        print(f"   📚 将从数据集 {checkpoint + 1} 开始继续...")
    else:
        print(f"   📍 无checkpoint，从头开始处理...")

    print()

    # Initialize generator
    generator = SOPSGeneratorV6()

    # Process each dataset sequentially
    all_results = []
    start_index = checkpoint  # 0 means start from beginning, 1 means dataset 1 is done

    # Check if checkpoint indicates all datasets are already processed
    if checkpoint >= len(all_protocol_contents):
        print(f"\n⚠️  所有 {len(all_protocol_contents)} 个数据集均已处理完成")
        print(f"   最后处理的数据集: {checkpoint}")
        print(f"\n提示:")
        print(f"   1. 如需重新处理，删除 checkpoint: rm memory/dataset_checkpoint.json")
        print(
            f"   2. 如需添加新数据集，请在 protocol_content.json 和 report_content.json 中添加"
        )
        print(
            f"      protocol_content{checkpoint + 1} 和 report_content{checkpoint + 1}"
        )
        print(f"\n✨ 无需处理的数据集")
        return

    for dataset_idx in range(start_index, len(all_protocol_contents)):
        data_index = dataset_idx + 1  # 1-based index
        print(f"\n{'=' * 70}")
        print(f"🔄 开始处理数据集 {data_index}/{len(all_protocol_contents)}")
        print(f"{'=' * 70}\n")

        protocol_content = all_protocol_contents[dataset_idx]
        report_content = all_report_contents[dataset_idx]

        # Parse sections from current dataset
        sections = prepare_sections(protocol_content, report_content, max_sections=5)
        print(f"   识别到 {len(sections)} 个章节:")
        for i, section in enumerate(sections, 1):
            print(f"      {i}. {section['section_title']}")

        # Load previous SOPs for enhancement mode (if not first dataset)
        previous_sops = {}
        if data_index > 1:
            print(f"\n   📚 加载上一次生成的SOP作为参考...")
            for section in sections:
                section_title = section["section_title"]
                previous_sop = memory.load_previous_sop(section_title)
                if previous_sop:
                    previous_sops[section_title] = previous_sop
                    print(f"      ✓ {section_title}: {len(previous_sop)} 字符")
                else:
                    print(f"      ⚠ {section_title}: 未找到上一次SOP")
        else:
            print(f"\n   🆕 初始模式: 生成第一批SOP")

        # Process sections
        dataset_results = []
        for section in sections:
            section_title = section["section_title"]
            previous_sop = previous_sops.get(section_title, "")
            result = generator.process_section(
                section, data_index=data_index, previous_sop=previous_sop
            )
            dataset_results.append(result)
            all_results.append(result)

        # Save generated SOPs for next iteration
        print(f"\n   💾 保存生成的SOP用于下一次迭代...")
        for result in dataset_results:
            section_title = result["section_title"]
            sop_content = result.get("sop_content", "")
            if sop_content:
                memory.save_previous_sop(section_title, sop_content)
                print(f"      ✓ {section_title}: {len(sop_content)} 字符")

        # Save checkpoint
        memory.save_checkpoint(data_index)
        print(f"\n   ✅ 数据集 {data_index} 处理完成，checkpoint已保存")

        # Dataset summary
        success_count = sum(1 for r in dataset_results if r.get("success", False))
        print(f"\n   📊 数据集 {data_index} 汇总:")
        print(f"      ✓ 成功: {success_count}/{len(dataset_results)}")
        print(
            f"      ✗ 失败: {len(dataset_results) - success_count}/{len(dataset_results)}"
        )

        # Detailed results for this dataset
        for result in dataset_results:
            status = "✓" if result.get("success") else "✗"
            print(
                f"      {status} {result['section_title']}: "
                f"评分={result.get('final_score', 0):.1f}, "
                f"复杂度={result.get('complexity', '?')}, "
                f"迭代={result.get('iteration_count', 0)}次"
            )

    # Overall summary
    print("\n" + "=" * 70)
    print("📊 全局汇总")
    print("=" * 70)

    total_success = sum(1 for r in all_results if r.get("success", False))
    print(f"✓ 总成功: {total_success}/{len(all_results)}")
    print(f"✗ 总失败: {len(all_results) - total_success}/{len(all_results)}")
    if all_results:
        print(
            f"📈 平均评分: {sum(r.get('final_score', 0) for r in all_results) / len(all_results):.2f}"
        )

    # Show score progression across datasets
    print("\n📈 各数据集平均评分:")
    for dataset_idx in range(len(all_protocol_contents)):
        data_index = dataset_idx + 1
        dataset_results = [
            r
            for r in all_results
            if r.get("section_title", "").startswith("章节")
            and f"数据集{data_index}" in str(r)
        ]
        if dataset_results:
            avg_score = sum(r.get("final_score", 0) for r in dataset_results) / len(
                dataset_results
            )
            print(f"   数据集 {data_index}: {avg_score:.2f}")

    print("\n" + "=" * 70)
    print("✨ 所有数据集处理完毕")
    print("=" * 70)


if __name__ == "__main__":
    main()
