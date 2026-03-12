"""
入口初始化节点 (Initialization Node)

V3 架构升级：
优先读取接口直传的 `chapter_list`，仅在未提供时回退读取本地 JSON 文件。
节点职责是将输入章节封装为 `ChapterState` 的列表形式 `mapped_chapters`，
供后续并发路由（Fan-out）使用。
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

from workflows.sop_generation.state import GlobalState, ChapterState

logger = logging.getLogger(__name__)


def initialization_node(state: GlobalState) -> dict:
    """
    数据接入与初始化节点函数
    
    优先读取 state.chapter_list；未提供时回退读取 report_json_path/mockData/report.json，
    并将数据组装成并发子图状态列表。
    
    Args:
        state: LangGraph 全局共享状态 GlobalState
    Returns:
        状态更新字典，主要是填充 mapped_chapters
    """
    logger.info("[Initialization] 开始处理项目初始化数据")

    # 获取项目 ID (用于 OpenViking 路径绑定)
    project_id = state.get("project_id", f"PROJ_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}")

    try:
        if "chapter_list" in state:
            report_data = state.get("chapter_list")
            if not isinstance(report_data, list):
                raise ValueError("state.chapter_list 必须是数组")
            logger.info("[Initialization] 使用接口直传章节数据源: state.chapter_list")
        else:
            # 本文件位于 src/workflows/sop_generation/nodes/，向上4级到项目根目录
            project_root = Path(__file__).resolve().parents[4]
            report_path = project_root / "mockData" / "report.json"

            # 兼容传入的 report_json_path，如果未传入则默认使用 mockData/report.json
            incoming_report_path = state.get("report_json_path")
            if incoming_report_path and str(incoming_report_path).strip():
                report_path = Path(incoming_report_path)
                logger.info(f"[Initialization] 使用外部指定的 json 数据源: {report_path}")
            else:
                logger.info(f"[Initialization] 使用默认数据源: {report_path}")

            if not report_path.exists():
                raise ValueError(f"找不到固定数据源文件: {report_path}")

            with report_path.open("r", encoding="utf-8") as f:
                report_data = json.load(f)

        if not isinstance(report_data, list):
            raise ValueError("初始化数据源必须是数组")

        # 根据 Workflow-B 输出结构：section_protocol 是原始输入，section_report 是目标内容。
        mapped_chapters = []

        for item in report_data:
            if not isinstance(item, dict):
                raise ValueError("初始化数据源章节项必须是对象")

            # 兼容两种来源字段：
            # 1) API 章节列表：section_protocol / section_report
            # 2) 本地 mockData/report.json：original_content / generate_content
            section_protocol = str(
                item.get("section_protocol")
                or item.get("original_content")
                or ""
            )
            section_report = str(
                item.get("section_report")
                or item.get("generate_content")
                or ""
            )

            child_thread_id = str(item.get("child_thread_id", "") or "").strip()
            chapter_state: ChapterState = {
                "project_id": project_id,
                "section_id": item.get("id") or item.get("section_title"),
                "section_title": item.get("section_title", "未命名章节"),
                "original_content": section_protocol,
                "target_generate_content": section_report,
                "retry_count": 0,
                "is_passed": False,
                "status": "RUNNING",
            }
            if child_thread_id:
                chapter_state["child_thread_id"] = child_thread_id
            mapped_chapters.append(chapter_state)
                
        logger.info(f"[Initialization] 成功提取 {len(mapped_chapters)} 个待并发处理章节，项目 ID: {project_id}")

        # 放行至下一步，并向 Global 压入初始待办列表
        return {
            "project_id": project_id,
            "current_phase": "fan_out",
            "mapped_chapters": mapped_chapters,
            "sse_summary": {
                "workflow": "sop_generation",
                "node": "initialization",
                "phase": "任务拆解",
                "phase_state": "completed",
                "status": "running",
                "message": f"Devin 已完成章节拆解，共识别 {len(mapped_chapters)} 个并发任务，即将开始分发。",
                "metrics": {
                    "completed": 0,
                    "total": len(mapped_chapters),
                    "percent": 0.0,
                },
            },
        }

    except Exception as e:
        logger.error(f"[Initialization] 解析 JSON 数据异常: {e}")
        return {
            "error_log": [{
                "node": "initialization",
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }],
            "sse_summary": {
                "workflow": "sop_generation",
                "node": "initialization",
                "phase": "任务拆解",
                "phase_state": "failed",
                "status": "failed",
                "message": f"Devin 章节数据解析失败，无法继续。错误：{e}",
                "metrics": {"completed": 0, "total": 0, "percent": 0.0},
            },
        }
