"""
Human Review Agent 节点（Phase 5：人机协作）

架构文档 Section 5 & 6.2 描述的接入点 3/4：

接入点 3: AI 通过审查后，向人工专家展示完整 SOP 草稿供审核
接入点 4: 人工专家提交最终审批决策

实现方式：
  当前 Phase 5 使用"状态暂停+API 恢复"模式：
  1. human_review_node 执行时先检查 human_decision 字段
  2. 若无决策 → 记录等待状态，Router 路由到 END（工作流暂停）
  3. 外部 API（/projects/{id}/human-review）写入决策
  4. 客户端再次调用 /projects/{id}/resume 重新触发工作流
  5. Router 检测到决策后路由到最终交付

Phase 6 升级点：接入 LangGraph interrupt / Command(resume=...) 机制实现真正阻塞式等待

记忆依赖：
  L0: viking://user/{user_id}/PREFERENCES.md    ← 用户偏好（可选）
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from tools.openviking_client import get_client
from utils.workspace_manager import WorkspaceManager
from workflows.sop_generation.state import GlobalState

logger = logging.getLogger(__name__)


def human_review_node(state: GlobalState) -> dict:
    """
    Human Review Agent 主节点。

    判断当前是否已有人工审核决策：
    - 无决策 → 输出等待摘要（发送通知，路由到 END 暂停）
    - approved  → 触发最终文档生成，标记 completed
    - rejected  → 将 revision_sections 写入 pending，返回 section_generation

    Args:
        state: LangGraph 工作流状态

    Returns:
        状态更新字典
    """
    client = get_client()
    project_id = state["project_id"]
    workspace = WorkspaceManager(client, project_id)

    logger.info(f"[Human Review] 项目 {project_id}")

    # ---------- 读取最新决策（优先从黑板读，兼容 API 写入）----------
    human_decision = state.get("human_decision") or {}

    # 若 LangGraph state 中没有，尝试从黑板 STATE.json 读取
    if not human_decision:
        board_state = workspace.get_state()
        human_decision = board_state.get("human_decision", {})

    # ---------- 情况1：无决策 → 暂停等待 ----------
    if not human_decision:
        _notify_waiting(workspace, project_id, state)
        return {
            "current_phase": "human_review",
            # 不更新 human_decision，Router 下次检测到无决策会再次路由到 end
        }

    # ---------- 情况2：需要修改 ----------
    if not human_decision.get("approved", False):
        revision_sections = human_decision.get("revision_sections", [])
        comments = human_decision.get("comments", "")

        logger.info(f"[Human Review] 需修改 {len(revision_sections)} 个章节：{revision_sections}")

        # 将 reviewer_feedback 写入草稿版本记录
        _write_reviewer_feedback(workspace, revision_sections, comments)

        workspace.update_state({
            "current_phase": "section_generation",
            "pending_sections": revision_sections,
            "human_decision": {},     # 清除决策，等待重新生成后再次审核
            "agent_status": {"human_review": "revision_required"},
        })

        return {
            "current_phase": "section_generation",
            "pending_sections": revision_sections,
            "human_decision": {},
        }

    # ---------- 情况3：审核通过 → 结束流程 ----------
    logger.info("[Human Review] 审核通过，结束流程")

    workspace.update_state({
        "current_phase": "completed",
        "workflow_status": "completed",
        "agent_status": {"human_review": "completed"},
        "completed_at": datetime.now(timezone.utc).isoformat(),
    })

    return {
        "current_phase": "completed",
    }


# ---------- 内部辅助函数 ----------

def _notify_waiting(workspace: WorkspaceManager, project_id: str, state: dict) -> None:
    """在黑板写入等待通知，供前端/n8n 轮询检测。"""
    completed = state.get("completed_sections", [])
    review_result = state.get("review_result", {})

    notification = {
        "type": "human_review_required",
        "project_id": project_id,
        "completed_sections": len(completed),
        "review_status": review_result.get("status", "unknown"),
        "waiting_since": datetime.now(timezone.utc).isoformat(),
        "action_url": f"/projects/{project_id}/human-review",
        "draft_url": f"/projects/{project_id}/status",
    }

    workspace.post_message("human_review", "frontend", notification)
    workspace.update_state({
        "agent_status": {"human_review": "waiting"},
        "notification": notification,
    })
    logger.info(f"[Human Review] 已写入等待通知，项目 {project_id}")


def _write_reviewer_feedback(
    workspace: WorkspaceManager,
    revision_sections: list[str],
    comments: str,
) -> None:
    """将人工修改意见写入 v2_reviewer_feedback 版本。"""
    feedback_content = (
        f"# 人工审核反馈\n\n"
        f"**时间**：{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}\n\n"
        f"**需修改章节**：\n"
        + "\n".join(f"- {s}" for s in revision_sections)
        + f"\n\n**审核意见**：\n{comments}\n"
    )
    workspace.write_draft("HUMAN_REVIEW_COMMENTS.md", feedback_content, version="v2_reviewer_feedback")



