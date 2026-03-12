"""
SOP 生成工作流 LangGraph V3 图定义

架构：基于 LangGraph Send API 的 Map-Reduce 扇出并发图
阶段：
1. 主图 START -> initialization_node (提取 Json 数据)
2. initialization_node -> 条件边 (Fan-out 扇出) -> [并发 n 个 Chapter Sub-graph]
3. Chapter Sub-graph 内部：
   entry -> sop_writer_node (Node 4) -> simulator_node (Node 6) -> reviewer_node (Node 7)
   如果失败且重试未到限制：reviewer_node -> retry_counter -> sop_writer_node
   通过或超限：reviewer_node -> pass_exit/failure_exit -> END
4. n 个 Sub-graph 结束后，汇合至 reduce_marker 节点（Join Barrier）
5. reduce_marker -> aggregation_node
6. aggregation_node -> END (输出聚合结果)
"""

from __future__ import annotations

import re
from uuid import uuid4

from langgraph.graph import END, START, StateGraph

from workflows.sop_generation.state import ChapterState, GlobalState
from workflows.sop_generation.routing import map_chapters_to_parallel_nodes
from workflows.sop_generation.nodes.aggregation_node import aggregation_node
from workflows.sop_generation.nodes.data_extractor_node import initialization_node
from workflows.sop_generation.nodes.simulator_node import simulator_node
from workflows.sop_generation.nodes.sop_reviewer_node import sop_reviewer_node
from workflows.sop_generation.nodes.sop_writer_node import sop_writer_node
from workflows.sop_generation.section_update import update_single_section_with_polling

MAX_TOTAL_ATTEMPTS = 3


def _build_simulator_input(state: ChapterState) -> dict:
    """
    构建传给 Simulator 的最小必要输入，显式剔除 target_generate_content 防止泄露。
    """
    return {
        "section_title": state.get("section_title", ""),
        "original_content": state.get("original_content", ""),
        "current_sop": state.get("current_sop", ""),
        "status": state.get("status", "RUNNING"),
        "is_passed": state.get("is_passed", False),
        "retry_count": state.get("retry_count", 0),
        "sop_type": state.get("sop_type"),
    }


def _call_simulator_with_sanitized_input(state: ChapterState) -> dict:
    return simulator_node(_build_simulator_input(state))


def _safe_child_thread_id(raw: str, section_id: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_-]+", "_", str(raw or "").strip())
    cleaned = cleaned.strip("_")
    if cleaned:
        return cleaned

    section_token = re.sub(r"[^A-Za-z0-9_-]+", "_", str(section_id or "chapter")).strip("_")
    if not section_token:
        section_token = "chapter"
    return f"sop_chapter__{section_token}__{uuid4().hex[:12]}"


# ==========================================
# 构建单章节子图 (Chapter Sub-graph)
# ==========================================
def build_chapter_sub_graph(*, checkpointer: object | None = None):
    builder = StateGraph(ChapterState)

    # 注册正式节点
    builder.add_node("sop_writer", sop_writer_node)
    builder.add_node("simulator", _call_simulator_with_sanitized_input)
    builder.add_node("reviewer", sop_reviewer_node)

    # 局部顺序流
    builder.add_edge(START, "sop_writer")
    builder.add_edge("sop_writer", "simulator")
    builder.add_edge("simulator", "reviewer")

    def retry_counter_node(state: ChapterState) -> dict:
        retry_count = state.get("retry_count", 0)
        return {
            "retry_count": retry_count + 1,
            "status": "RUNNING",
            # 清理上一轮的生成结果与模拟数据，避免重试时受历史数据污染
            "current_sop": "",
            "simulated_generate_content": "",
        }

    def pass_exit_node(_: ChapterState) -> dict:
        return {"status": "PASSED"}

    def failure_exit_node(_: ChapterState) -> dict:
        return {"status": "Need Human Review"}

    builder.add_node("retry_counter", retry_counter_node)
    builder.add_node("pass_exit", pass_exit_node)
    builder.add_node("failure_exit", failure_exit_node)

    builder.add_edge("retry_counter", "sop_writer")
    builder.add_edge("pass_exit", END)
    builder.add_edge("failure_exit", END)

    # 局部条件路由
    def route_in_subgraph(state: ChapterState) -> str:
        if state.get("is_passed"):
            return "pass_exit"

        retry_count = int(state.get("retry_count", 0))
        attempt_count = retry_count + 1  # 当前轮次 = 首次执行 + 已发生重试次数
        if attempt_count < MAX_TOTAL_ATTEMPTS:
            return "retry_counter"
        return "failure_exit"

    builder.add_conditional_edges(
        "reviewer",
        route_in_subgraph,
        {
            "retry_counter": "retry_counter",
            "pass_exit": "pass_exit",
            "failure_exit": "failure_exit",
        },
    )
    return builder.compile(checkpointer=checkpointer, name="sop_generation_chapter")


# ==========================================
# 构建主图 (Main Graph)
# ==========================================
def build_graph(
    *,
    checkpointer: object | None = None,
    chapter_sub_graph: object | None = None,
):
    if chapter_sub_graph is None:
        chapter_sub_graph = build_chapter_sub_graph(checkpointer=checkpointer)

    main_builder = StateGraph(GlobalState)

    # 注册初始化节点
    main_builder.add_node("initialization", initialization_node)

    async def call_chapter_sub_graph(state: ChapterState):
        """封装子图调用，按章节独立 thread_id 记录 checkpoint，并在完成后立即回写。"""
        child_thread_id = _safe_child_thread_id(
            str(state.get("child_thread_id", "")),
            str(state.get("section_id") or state.get("section_title") or "chapter"),
        )
        config = {"configurable": {"thread_id": child_thread_id}}
        result = await chapter_sub_graph.ainvoke(state, config=config)
        if isinstance(result, dict):
            result.setdefault("child_thread_id", child_thread_id)
            section_update_result = await update_single_section_with_polling(result)
        else:
            section_update_result = {
                "id": "",
                "ok": "false",
                "attempts": "0",
                "error": "chapter_sub_graph 返回结果不是字典，无法执行 section update",
            }

        return {
            "completed_chapters": [result],
            "section_update_results": [section_update_result],
        }

    def reduce_marker_node(state: GlobalState) -> dict:
        """
        汇合标记节点（Join Barrier）。
        此节点没有任何逻辑，仅作为一个同步点，等待所有并发的 chapter_sub_graph 结束。
        """
        return {"current_phase": "merge"}

    main_builder.add_node("chapter_sub_graph", call_chapter_sub_graph)
    main_builder.add_node("reduce_marker", reduce_marker_node)
    main_builder.add_node("aggregation", aggregation_node)

    # 主流程逻辑
    main_builder.add_edge(START, "initialization")

    # 初始化后的 Fan-out
    main_builder.add_conditional_edges(
        "initialization",
        map_chapters_to_parallel_nodes,
        ["chapter_sub_graph"],
    )

    # 并发节点全部指向汇合点 (关键：利用单向边实现 Reduce 等待)
    main_builder.add_edge("chapter_sub_graph", "reduce_marker")

    main_builder.add_edge("reduce_marker", "aggregation")
    main_builder.add_edge("aggregation", END)

    return main_builder.compile(checkpointer=checkpointer, name="sop_generation_parent")


chapter_sub_graph = build_chapter_sub_graph()
graph = build_graph(chapter_sub_graph=chapter_sub_graph)
