"""
Phase 1 占位符节点

为尚未实现的 Worker Agent（Data Extractor / SOP Writer / SOP Reviewer / Human Review）
提供占位实现，确保图能够在 Phase 1 正常编译、运行和测试。

每个占位符节点会：
1. 打印日志说明当前被调用
2. 返回最小必要字段，使工作流可以向前推进（用于集成测试）
"""

from __future__ import annotations

import logging

from workflows.sop_generation.state import SopGenerationState

logger = logging.getLogger(__name__)


def data_extractor_placeholder_node(state: SopGenerationState) -> dict:
    """
    Data Extractor 占位节点（Phase 2 实现）。

    当前行为：返回一个空的 extracted_data，
    使 Router 路由进入 section_generation 阶段。
    """
    logger.info("[Data Extractor Placeholder] 节点被调用（Phase 2 待实现）")
    # TODO: Phase 2 替换为真实数据提取逻辑
    return {
        "extracted_data": {
            "_placeholder": True,
            "protocol": {},
            "excel": {},
            "mapping_rules": [],
            "global_params": {},
        },
        "current_phase": "section_generation",
    }


def sop_writer_placeholder_node(state: SopGenerationState) -> dict:
    """
    SOP Writer 占位节点（Phase 3 实现）。

    当前行为：将 current_section 标记为完成，推进 pending_sections。
    """
    current_section = state.get("current_section", "unknown")
    pending = state.get("pending_sections", [])
    completed = state.get("completed_sections", [])

    logger.info(f"[SOP Writer Placeholder] 处理章节：{current_section}（Phase 3 待实现）")

    # 模拟写入草稿
    updated_pending = [s for s in pending if s != current_section]
    updated_completed = [*completed, current_section]

    # TODO: Phase 3 替换为真实 SOP 生成逻辑

    return {
        "pending_sections": updated_pending,
        "completed_sections": updated_completed,
        "generated_content": {
            **state.get("generated_content", {}),
            current_section: f"[Placeholder] 章节 {current_section} 的生成内容",
        },
        # 推进 Router 继续调度
        "current_phase": "section_generation",
    }


def sop_reviewer_placeholder_node(state: SopGenerationState) -> dict:
    """
    SOP Reviewer 占位节点（Phase 4 实现）。

    当前行为：直接返回 pass，使工作流进入人工审核阶段。
    """
    logger.info("[SOP Reviewer Placeholder] 节点被调用（Phase 4 待实现）")
    # TODO: Phase 4 替换为真实 GLP 合规审查逻辑
    return {
        "review_result": {
            "status": "pass",
            "violations": [],
            "warnings": [],
            "failed_sections": [],
        },
        "current_phase": "human_review",
    }


def human_review_placeholder_node(state: SopGenerationState) -> dict:
    """
    人工审核等待节点（Phase 5 实现）。

    当前行为：直接批准，工作流完成。
    生产环境中此节点应通过 LangGraph interrupt() 挂起等待用户操作。
    """
    logger.info("[Human Review Placeholder] 节点被调用（Phase 5 待实现）")
    # TODO: Phase 5 替换为真实 interrupt() + API 恢复机制
    return {
        "human_decision": {
            "approved": True,
            "revision_sections": [],
            "comments": "占位自动批准",
        },
        "current_phase": "human_review",
    }
