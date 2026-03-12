from __future__ import annotations

import asyncio
import logging
import os
from typing import Any

from tools.foxuai_client import req_template_section_update

logger = logging.getLogger(__name__)

SECTION_UPDATE_MAX_ATTEMPTS = max(1, int(os.getenv("SOP_SECTION_UPDATE_MAX_ATTEMPTS", "5")))
SECTION_UPDATE_RETRY_INTERVAL_SECONDS = max(
    0.0,
    float(os.getenv("SOP_SECTION_UPDATE_RETRY_INTERVAL_SECONDS", "1.5")),
)


def build_section_update_payload(chapter: dict[str, Any]) -> dict[str, Any]:
    return {
        "sop": str(chapter.get("current_sop", "") or ""),
        "section_report_debug": str(chapter.get("simulated_generate_content", "") or ""),
        "generate_status": str(chapter.get("status", "") or ""),
    }


def is_foxuai_success(resp: Any) -> bool:
    if not isinstance(resp, dict):
        return False
    if resp.get("success") is False:
        return False
    code = resp.get("code")
    if isinstance(code, int) and code >= 400:
        return False
    return True


async def poll_section_update(section_id: str, payload: dict[str, Any]) -> tuple[bool, str | None, int]:
    last_error: str | None = None
    for attempt in range(1, SECTION_UPDATE_MAX_ATTEMPTS + 1):
        try:
            resp = await asyncio.to_thread(req_template_section_update, section_id, payload)
            if not is_foxuai_success(resp):
                raise ValueError(f"section update 响应异常: {resp}")
            return True, None, attempt
        except Exception as exc:
            last_error = str(exc)
            logger.warning(
                "[SopGenerationSectionUpdate] section_id=%s update attempt=%s/%s failed: %s",
                section_id,
                attempt,
                SECTION_UPDATE_MAX_ATTEMPTS,
                last_error,
            )
            if attempt < SECTION_UPDATE_MAX_ATTEMPTS and SECTION_UPDATE_RETRY_INTERVAL_SECONDS > 0:
                await asyncio.sleep(SECTION_UPDATE_RETRY_INTERVAL_SECONDS)
    return False, last_error, SECTION_UPDATE_MAX_ATTEMPTS


async def update_single_section_with_polling(chapter: dict[str, Any], *, index: int | None = None) -> dict[str, str]:
    section_id = str(chapter.get("section_id", "") or chapter.get("id", "")).strip()
    result: dict[str, str] = {
        "id": section_id,
        "ok": "false",
        "attempts": "0",
    }
    if index is not None:
        result["index"] = str(index)

    if not section_id:
        result["error"] = "章节缺少 section_id/id，无法执行 update"
        return result

    payload = build_section_update_payload(chapter)
    ok, err, attempts = await poll_section_update(section_id, payload)
    result["attempts"] = str(attempts)
    result["ok"] = "true" if ok else "false"
    if err:
        result["error"] = str(err)
    return result


def summarize_section_update_results(results: list[dict[str, Any]]) -> dict[str, Any]:
    normalized = [item for item in results if isinstance(item, dict)]
    total = len(normalized)
    success_count = sum(1 for item in normalized if str(item.get("ok", "")).lower() == "true")
    failed_items = [item for item in normalized if str(item.get("ok", "")).lower() != "true"]
    failed_count = len(failed_items)

    if failed_count == 0:
        status = "updated"
    elif success_count == 0:
        status = "update_failed"
    else:
        status = "partial_failed"

    return {
        "status": status,
        "total": total,
        "success_count": success_count,
        "failed_count": failed_count,
        "errors": failed_items,
    }
