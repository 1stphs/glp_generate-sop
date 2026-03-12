"""
Node 7: SOP Reviewer Agent 节点
V3 架构升级 - 单章节三方一致性校验

在 Chapter Sub-graph (并发子图) 中运行。
职责：
扮演最终质检员。对比三个输入：
1. target_generate_content (目标报告内容)
2. current_sop (Node 4 写的流程)
3. simulated_generate_content (Node 6 盲测推演出的结果)

要求：
用结构化输出 (JSON) 判定 `is_passed`。
如果有任何冲突、遗漏、数值对不上，必须填 false，并在 feedback 中详述具体退回要求，
从而触发子图重试回流。
"""

from __future__ import annotations

import logging
from pydantic import BaseModel, Field
from workflows.sop_generation.state import ChapterState
from tools.llm_client import chat_completion
from prompts.registry import PromptRegistry
from workflows.meta.metrics import metrics_collector

logger = logging.getLogger(__name__)

REVIEW_SCOPE_CONSTRAINT = (
    "【审核口径限定】\n"
    "1) 仅审核“结构/形式/模板一致性”，包括段落结构、字段形式、输出风格是否符合 SOP 要求。\n"
    "2) 不得因具体数值、日期、名称、事实准确性差异判定失败。\n"
    "3) 判定重点：simulated_generate_content 是否符合 current_sop 的输出形式，"
    "且与 target_generate_content 的形式保持一致。"
)

DATA_ACCURACY_FEEDBACK_KEYWORDS = (
    "数值", "数字", "日期", "时间", "浓度", "百分比", "单位", "名称", "型号", "批号", "具体内容", "不一致",
)
FORMAT_FEEDBACK_KEYWORDS = (
    "格式", "结构", "模板", "段落", "层级", "字段", "排版", "样式", "形式", "风格",
)


def _is_data_accuracy_only_feedback(feedback: str) -> bool:
    text = str(feedback or "").strip()
    if not text:
        return False
    has_data_mismatch = any(token in text for token in DATA_ACCURACY_FEEDBACK_KEYWORDS)
    has_format_mismatch = any(token in text for token in FORMAT_FEEDBACK_KEYWORDS)
    return has_data_mismatch and not has_format_mismatch


class ReviewResult(BaseModel):
    reasoning: str = Field(description="你的思维链/推理过程/详细分析，请逐字对比模拟结果与目标报告并指出差异。")
    error_identification: str = Field(description="具体哪里错了？")
    root_cause_analysis: str = Field(description="为什么会导致这个错误？是因为 Writer 遗漏了特定规则还是模板排版有误？")
    correct_approach: str = Field(description="针对错误，Writer 应该制定什么具体的 SOP 规则或修改什么模板排版？")
    is_passed: bool = Field(description="三方比对是否通过？如果不一致请填 false。")
    feedback: str = Field(description="综合你的分析，给出具体的修改指令（要求 Actionable），用于反馈给 Writer 进行重试。")


def sop_reviewer_node(state: ChapterState) -> dict:
    """
    SOP Reviewer Agent 节点 (Node 7)
    
    Args:
        state: Chapter Sub-graph 传递的 Payload
        
    Returns:
        更新状态片段，存入 `is_passed` 和 `feedback`。
    """
    section_title = state.get("section_title", "未命名章节")
    logger.info(f"[Node 7 - Reviewer] 开始三方比对校验章节: {section_title}")
    
    original_content = state.get("original_content", "")
    target_generate_content = state.get("target_generate_content", "")
    current_sop = state.get("current_sop", "")
    simulated_generate_content = state.get("simulated_generate_content", "")
    
    prompt_sys = f"{PromptRegistry.get_prompt('sop_reviewer_sys')}\n\n{REVIEW_SCOPE_CONSTRAINT}"
    
    prompt_user = PromptRegistry.get_prompt(
        "sop_reviewer_user",
        section_title=section_title,
        target_generate_content=target_generate_content,
        current_sop=current_sop,
        simulated_generate_content=simulated_generate_content,
        original_content=original_content,
    )
    
    prompt_user = f"{prompt_user}\n\n{REVIEW_SCOPE_CONSTRAINT}"

    messages = [
        {"role": "system", "content": prompt_sys},
        {"role": "user", "content": prompt_user}
    ]
    
    try:
        logger.debug(f"[Node 7 - Reviewer] ({section_title}) 正在调用带 Schema 的 LLM 审查...")
        # 强制使用 response_format 来要求返回合法的 JSON 符合 ReviewResult
        result_json_str, tokens, latency, model = chat_completion(messages, temperature=0.1, max_tokens=1024, response_format=ReviewResult)
        
        # chat_completion 配合 response_format 会返回 JSON 字符串，我们需要解析它
        import json
        result_data = json.loads(result_json_str)
        
        is_passed = result_data.get("is_passed", False)
        # 截取详细的反馈信息
        error_ident = result_data.get("error_identification", "")
        root_cause = result_data.get("root_cause_analysis", "")
        correct_appr = result_data.get("correct_approach", "")
        feedback = result_data.get("feedback", "")
        
        # 将结构化的分析组装进 feedback 中供 writer 更好地阅读
        if not is_passed:
            feedback = f"【错误定性】{error_ident}\n【根因分析】{root_cause}\n【正确修改策略】{correct_appr}\n【执行指令】{feedback}"

        # 口径兜底：如果仅因数值/事实差异被判失败，自动按“结构优先”放行。
        if not is_passed and _is_data_accuracy_only_feedback(feedback):
            logger.info(
                "[Node 7 - Reviewer] (%s) 按结构优先口径忽略数值准确性差异，自动放行。",
                section_title,
            )
            is_passed = True
            feedback = "已按结构优先口径放行（忽略数值/事实准确性差异）。"
        
        # 记录 Reviewer 指标
        metrics_collector.record_generation(
            chapter=f"{section_title}_Reviewer",
            tokens=tokens,
            latency=latency,
            passed=is_passed,
            retries=state.get("retry_count", 0),
            model=model
        )
        
        logger.info(f"[Node 7 - Reviewer] ({section_title}) 审查结束。通过={is_passed}")
        if not is_passed:
            logger.info(f" -> 驳回意见: {feedback}")

        phase_state = "completed" if is_passed else "failed"
        message = (
            f"Ryan 对《{section_title}》审查通过，准备入库。"
            if is_passed
            else f"Ryan 对《{section_title}》提出驳回：{feedback[:80]}..."
        )
        return {
            "is_passed": is_passed,
            "feedback": feedback,
            "sse_summary": {
                "workflow": "sop_generation",
                "node": "sop_reviewer",
                "phase": "质量审核",
                "phase_state": phase_state,
                "status": "running",
                "message": message,
            },
        }
        
    except Exception as e:
        logger.error(f"[Node 7 - Reviewer] ({section_title}) 审查判定发生异常: {e}")
        
        metrics_collector.record_generation(
            chapter=f"{section_title}_Reviewer_ERR",
            tokens=0,
            latency=0.0,
            passed=False,
            retries=state.get("retry_count", 0),
            model="error"
        )
        
        # 保底机制：如果 Reviewer 炸了，不信任通过，强制要求人工/报错
        return {
            "is_passed": False,
            "feedback": f"Reviewer节点系统级崩溃出错，需要重试或介入。错误信息: {e}",
            "sse_summary": {
                "workflow": "sop_generation",
                "node": "sop_reviewer",
                "phase": "质量审核",
                "phase_state": "failed",
                "status": "running",
                "message": f"Ryan 审核《{section_title}》发生异常，需人工介入。错误：{e}",
            },
        }
