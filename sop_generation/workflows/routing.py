"""
LangGraph V3 路由函数

负责控制整个 SOP 生成主流程的动态跳转，
特别是利用 `Send` API 实现向每个章节发射独占的子图执行任务（Fan-out）。
"""

from __future__ import annotations

import logging
from typing import List

from langgraph.types import Send
from workflows.sop_generation.state import GlobalState, ChapterState

logger = logging.getLogger(__name__)


def map_chapters_to_parallel_nodes(state: GlobalState) -> List[Send]:
    """
    核心并发派发器 (Fan-out)
    
    读取 GlobalState 中的 mapped_chapters 集合。
    对于集合中的每一个 ChapterState，均通过 Send("chapter_sub_graph", data)
    将该状态作为输入，独立且并发地启动一个 chapter_sub_graph 的执行流。
    """
    chapters_to_process = state.get("mapped_chapters", [])
    if not chapters_to_process:
        logger.warning("[并发路由] 发现 0 个可处理的章节！系统将直接终止。")
        return []
        
    sends = []
    for idx, chapter in enumerate(chapters_to_process):
        # 抛出具体的 ChapterState 发送到名为 "chapter_sub_graph" 的节点
        sends.append(Send("chapter_sub_graph", chapter))
        
    logger.info(f"[并发路由] 成功向 Chapter Sub-Graph 发射了 {len(sends)} 个并发任务。")
    return sends


def route_after_subgraphs_complete(state: GlobalState) -> str:
    """
    Reduce / 汇集后的最终流向。

    当前策略固定为“先汇总再产出”，即无论章节是否为 Need Human Review，
    主图都继续进入 aggregation 节点生成产物。
    """
    completed_chapters = state.get("completed_chapters", [])
    need_human_count = sum(1 for c in completed_chapters if c.get("status") == "Need Human Review")
    logger.info(
        "[全局汇集] 汇总完成：章节数=%s, Need Human Review=%s。流向 aggregation。",
        len(completed_chapters),
        need_human_count,
    )
    return "completed"
