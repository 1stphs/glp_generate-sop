"""Runner wrapper for background execution of SOP generation graph."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from tools.foxuai_client import req_template_update
from workflows.meta.metrics import metrics_collector
from workflows.sop_generation.graph import graph
from workflows.sop_generation.section_update import is_foxuai_success, summarize_section_update_results

logger = logging.getLogger(__name__)

REQUIRED_SECTION_FIELDS = {
    "id",
    "section_title",
    "parent_section_id",
    "section_protocol",
    "section_report",
}


def _validate_section_list(sections: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not isinstance(sections, list):
        raise ValueError("模板章节列表缺少 data 数组（期望路径：res.data.data）")
    if not sections:
        raise ValueError("模板章节列表为空（期望路径：res.data.data.length > 0）")

    sanitized_sections: list[dict[str, Any]] = []
    for idx, item in enumerate(sections, start=1):
        if not isinstance(item, dict):
            raise ValueError(f"模板章节列表第 {idx} 项不是对象")
        missing = sorted(REQUIRED_SECTION_FIELDS - set(item.keys()))
        if missing:
            missing_str = ", ".join(missing)
            raise ValueError(f"模板章节列表第 {idx} 项缺少字段: {missing_str}")

        payload = {
            "id": item.get("id"),
            "section_title": item.get("section_title"),
            "parent_section_id": item.get("parent_section_id"),
            "section_protocol": item.get("section_protocol"),
            "section_report": item.get("section_report"),
        }
        child_thread_id = str(item.get("child_thread_id", "") or "").strip()
        if child_thread_id:
            payload["child_thread_id"] = child_thread_id
        sanitized_sections.append(payload)

    return sanitized_sections


async def run_sop_generation(
    template_id: str,
    section_list: list[dict[str, Any]] | None = None,
    *,
    graph_runner: object | None = None,
    thread_id: str | None = None,
) -> dict[str, Any]:
    """Run SOP generation graph with API-provided chapter data."""

    normalized_template_id = str(template_id or "").strip()
    if not normalized_template_id:
        raise ValueError("template_id 不能为空")

    graph_to_use = graph_runner or graph
    config = {"configurable": {"thread_id": thread_id}} if thread_id else None

    metrics_collector.reset_session()
    logger.info("[SopGenerationRunner] start template_id=%s (metrics session reset)", normalized_template_id)

    try:
        if section_list is None:
            raise ValueError("section_list 不能为空")
        chapter_list = _validate_section_list(section_list)
        logger.info(
            "[SopGenerationRunner] input validated template_id=%s section_count=%s",
            normalized_template_id,
            len(chapter_list),
        )

        initial_state = {
            "project_id": normalized_template_id,
            "chapter_list": chapter_list,
            "current_phase": "initialization",
            "completed_chapters": [],
            "section_update_results": [],
            "error_log": [],
        }
        logger.info("[SopGenerationRunner] graph invoke start template_id=%s", normalized_template_id)
        final_state = await graph_to_use.ainvoke(initial_state, config=config)
        logger.info("[SopGenerationRunner] graph invoke finished template_id=%s", normalized_template_id)

        completed_chapters = final_state.get("completed_chapters", [])
        chapter_count = len(completed_chapters) if isinstance(completed_chapters, list) else 0
        completed_output_path = final_state.get("completed_chapters_output_path")
        section_update_results = final_state.get("section_update_results", [])
        section_update_result = summarize_section_update_results(
            section_update_results if isinstance(section_update_results, list) else []
        )

        step_update_status = "update_failed"
        step_update_error = None
        try:
            step_resp = await asyncio.to_thread(req_template_update, normalized_template_id, {"step": 7})
            if not is_foxuai_success(step_resp):
                raise ValueError(f"template step update 响应异常: {step_resp}")
            step_update_status = "updated"
        except Exception as exc:
            step_update_status = "update_failed"
            step_update_error = str(exc)

        logger.info(
            "[SopGenerationRunner] template_id=%s status=completed chapter_count=%s output_path=%s section_update_status=%s section_update_failed=%s step_update_status=%s",
            normalized_template_id,
            chapter_count,
            completed_output_path,
            section_update_result["status"],
            section_update_result["failed_count"],
            step_update_status,
        )
        return {
            "template_id": normalized_template_id,
            "status": "completed",
            "chapter_count": chapter_count,
            "output_path": completed_output_path,
            "completed_chapters_output_path": completed_output_path,
            "final_document_path": final_state.get("final_document_path"),
            "current_phase": final_state.get("current_phase"),
            "section_update_status": section_update_result["status"],
            "section_update_total": section_update_result["total"],
            "section_update_success_count": section_update_result["success_count"],
            "section_update_failed_count": section_update_result["failed_count"],
            "section_update_errors": section_update_result["errors"],
            "step_update_status": step_update_status,
            "step_update_error": step_update_error,
        }
    except Exception as exc:
        logger.error(
            "[SopGenerationRunner] template_id=%s status=failed",
            normalized_template_id,
            exc_info=True,
        )
        return {
            "template_id": normalized_template_id,
            "status": "failed",
            "error": str(exc),
        }
