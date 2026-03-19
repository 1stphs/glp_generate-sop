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
    MAX_DATASETS,
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


def load_report_data() -> List[Dict[str, Any]]:
    """
    加载report_all.json数据文件。

    Returns:
        章节数据列表，每个章节包含 section_title, original_content, generate_content
    """
    base_dir = Path(__file__).parent.parent / "mockData"
    report_file = base_dir / "report_all.json"

    with open(report_file, "r", encoding="utf-8") as f:
        return json.load(f)


def prepare_sections_from_report(
    report_data: List[Dict[str, Any]], max_sections: int = 5
) -> List[Dict[str, str]]:
    """
    从report_all.json准备章节列表。

    Args:
        report_data: 章节数据列表
        max_sections: 最大章节数量

    Returns:
        章节列表，每个章节包含 section_title, protocol_content, original_report_content
    """
    sections = []
    for section_info in report_data[:max_sections]:
        original_content = section_info.get("original_content", "")
        generate_content = section_info.get("generate_content", "")

        sections.append(
            {
                "section_title": section_info["section_title"],
                "protocol_content": original_content
                if original_content and original_content != "未在验证方案中找到对应内容"
                else "",
                "original_report_content": generate_content if generate_content else "",
            }
        )

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

        # 打印传入的方案和报告数据
        protocol_data = section.get("protocol_content", "")
        report_data = section.get("original_report_content", "")
        
        print(f"\n--- [传入数据预览] ---")
        print(f"📄 方案数据 (protocol_content) | 长度: {len(protocol_data)} 字符")
        if protocol_data:
            preview = protocol_data[:200].replace('\n', ' ')
            print(f"   预览: {preview}..." if len(protocol_data) > 200 else f"   预览: {preview}")
        else:
            print("   状态: 空 / 未在验证方案中找到对应内容")
            
        print(f"\n📄 报告数据 (original_report_content) | 长度: {len(report_data)} 字符")
        if report_data:
            preview = report_data[:200].replace('\n', ' ')
            print(f"   预览: {preview}..." if len(report_data) > 200 else f"   预览: {preview}")
        else:
            print("   状态: 空")
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

    # Load report data
    print("📂 加载数据...")
    report_data = load_report_data()

    # Filter sections that need processing (is_process = True)
    all_sections = [s for s in report_data if s.get("is_process", False)]
    print(f"   ✓ 加载 {len(report_data)} 个章节")
    print(f"   ✓ 其中 {len(all_sections)} 个章节需要处理")

    # Limit to MAX_DATASETS sections per batch
    sections_per_batch = 20
    total_batches = (len(all_sections) + sections_per_batch - 1) // sections_per_batch

    # Limit by MAX_DATASETS
    max_batches_to_process = min(MAX_DATASETS, total_batches)

    if not all_sections:
        print("   ✗ 没有需要处理的章节")
        return

    print(
        f"   🔢 本次将处理: {max_batches_to_process} 批，每批最多 {sections_per_batch} 个章节"
    )

    # Check for existing checkpoint
    checkpoint = memory.get_checkpoint()
    if checkpoint > 0:
        print(f"   📍 检测到checkpoint: 批次 {checkpoint} 已处理")
        print(f"   📚 将从批次 {checkpoint + 1} 开始继续...")
    else:
        print(f"   📍 无checkpoint，从头开始处理...")

    print()

    # Initialize generator
    generator = SOPSGeneratorV6()

    # Process each batch sequentially
    all_results = []
    start_batch = checkpoint  # 0 means start from beginning, 1 means batch 1 is done

    # Check if checkpoint indicates all batches are already processed
    if checkpoint >= max_batches_to_process:
        print(f"\n⚠️  所有 {max_batches_to_process} 批次均已处理完成")
        print(f"   最后处理的批次: {checkpoint}")
        print(f"\n提示:")
        print(f"   1. 如需重新处理，删除 checkpoint: rm memory/dataset_checkpoint.json")
        print(f"   2. 如需修改章节数量，编辑 report_all.json")
        print(f"\n✨ 无需处理的章节")
        return

    for batch_idx in range(start_batch, max_batches_to_process):
        batch_num = batch_idx + 1  # 1-based index
        print(f"\n{'=' * 70}")
        print(f"🔄 开始处理批次 {batch_num}/{max_batches_to_process}")
        print(f"{'=' * 70}\n")

        # Get sections for this batch
        start_section = batch_idx * sections_per_batch
        end_section = min(start_section + sections_per_batch, len(all_sections))
        batch_sections = all_sections[start_section:end_section]

        # Prepare sections from report data
        sections = prepare_sections_from_report(
            batch_sections, max_sections=len(batch_sections)
        )
        print(f"   识别到 {len(sections)} 个章节:")
        for i, section in enumerate(sections, 1):
            print(f"      {i}. {section['section_title']}")

        # Load previous SOPs for enhancement mode (if not first batch)
        previous_sops = {}
        if batch_num > 1:
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

        from concurrent.futures import ThreadPoolExecutor, as_completed

        # Process sections
        batch_results = []
        
        # Determine number of workers
        max_workers = min(5, len(sections)) if sections else 0
        if max_workers > 0:
            print(f"\n   ⚡ 启用并发处理: {max_workers} 线程")
            
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_to_section = {
                    executor.submit(
                        generator.process_section,
                        section,
                        data_index=batch_num,
                        previous_sop=previous_sops.get(section["section_title"], "")
                    ): section["section_title"]
                    for section in sections
                }
                
                for future in as_completed(future_to_section):
                    section_title = future_to_section[future]
                    try:
                        result = future.result()
                        batch_results.append(result)
                        all_results.append(result)
                    except Exception as exc:
                        print(f"❌ [{section_title}] 并发处理异常: {exc}")
                        failed_result = {
                            "section_title": section_title,
                            "success": False,
                            "final_score": 1.0,
                            "iteration_count": 0,
                            "complexity": "unknown",
                            "route": "unknown",
                            "error": str(exc),
                        }
                        batch_results.append(failed_result)
                        all_results.append(failed_result)

        # Save generated SOPs for next iteration
        print(f"\n   💾 保存生成的SOP用于下一次迭代...")
        for result in batch_results:
            section_title = result["section_title"]
            sop_content = result.get("sop_content", "")
            if sop_content:
                memory.save_previous_sop(section_title, sop_content)
                print(f"      ✓ {section_title}: {len(sop_content)} 字符")

        # Save checkpoint
        memory.save_checkpoint(batch_num)
        print(f"\n   ✅ 批次 {batch_num} 处理完成，checkpoint已保存")

        # Batch summary
        success_count = sum(1 for r in batch_results if r.get("success", False))
        print(f"\n   📊 批次 {batch_num} 汇总:")
        print(f"      ✓ 成功: {success_count}/{len(batch_results)}")
        print(
            f"      ✗ 失败: {len(batch_results) - success_count}/{len(batch_results)}"
        )

        # Detailed results for this batch
        for result in batch_results:
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

    # Show score progression across batches
    print("\n📈 各批次平均评分:")
    for batch_idx in range(max_batches_to_process):
        batch_num_local = batch_idx + 1
        batch_results_local = [
            r for r in all_results if f"批次{batch_num_local}" in str(r)
        ]
        if batch_results_local:
            avg_score = sum(r.get("final_score", 0) for r in batch_results_local) / len(
                batch_results_local
            )
            print(f"   批次 {batch_num_local}: {avg_score:.2f}")

    print("\n" + "=" * 70)
    print("✨ 所有数据集处理完毕")
    print("=" * 70)


if __name__ == "__main__":
    main()
