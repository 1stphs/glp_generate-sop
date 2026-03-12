import logging
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from workflows.sop_generation.state import GlobalState
from workflows.meta.metrics import metrics_collector

logger = logging.getLogger(__name__)


def _dump_completed_chapters_to_local(project_id: str, completed: list[dict]) -> str:
    """将 completed_chapters 结果落盘到 tests/output/*.json。"""
    project_root = Path(__file__).resolve().parents[4]
    output_dir = project_root / "tests" / "output"
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    output_path = output_dir / f"completed_chapters_{project_id}_{timestamp}.json"
    payload = {
        "project_id": project_id,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "chapter_count": len(completed),
        "completed_chapters": completed,
    }
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return str(output_path)


def _sanitize_completed_chapters(completed: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    清理导出字段，避免重复或超大 payload。

    当前重点去除 `extracted_data`（其内容可能包含全量章节，导致每章重复膨胀）。
    """
    sanitized: list[dict[str, Any]] = []
    for chapter in completed:
        if not isinstance(chapter, dict):
            continue
        chapter_clean = dict(chapter)
        chapter_clean.pop("extracted_data", None)
        sanitized.append(chapter_clean)
    return sanitized

def aggregation_node(state: GlobalState) -> dict:
    """
    聚合节点：汇总章节结果并落盘 completed_chapters JSON。
    """
    logger.info("[Aggregation] 开始执行章节聚合...")
    
    project_id = state.get("project_id", "UNKNOWN")
    completed_raw = state.get("completed_chapters", [])
    completed = _sanitize_completed_chapters(completed_raw if isinstance(completed_raw, list) else [])
    need_human_count = sum(1 for chapter in completed if chapter.get("status") == "Need Human Review")
    
    if not completed:
        logger.warning("[Aggregation] 没有找到已完成章节，跳过生成。")
        return {}
    logger.info(
        "[Aggregation] 已完成章节=%s, Need Human Review=%s",
        len(completed),
        need_human_count,
    )

    completed_output_path = None
    try:
        completed_output_path = _dump_completed_chapters_to_local(project_id, completed)
        logger.info("[Aggregation] completed_chapters 已落盘：%s", completed_output_path)
    except Exception as e:
        logger.error("[Aggregation] completed_chapters 落盘失败: %s", e)

    # 打印本次大盘指标
    report_md = metrics_collector.generate_report()
    logger.info(f"\n{report_md}\n")

    return {
        "completed_chapters_output_path": completed_output_path,
        "current_phase": "completed",
        "sse_summary": {
            "workflow": "sop_generation",
            "node": "aggregation",
            "phase": "结果汇总",
            "phase_state": "completed",
            "status": "completed",
            "message": f"Devin 已完成全部 {len(completed)} 个章节聚合，SOP 生成流程结束。",
            "metrics": {
                "completed": len(completed),
                "total": len(completed),
                "percent": 100.0,
                "need_human_review": need_human_count,
            },
        },
    }
