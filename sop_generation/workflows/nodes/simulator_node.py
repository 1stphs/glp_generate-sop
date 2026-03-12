"""
Node 6: Simulator (模拟器) 节点
V3 架构升级 - 防作弊与盲测推演核心

在 Chapter Sub-graph (并发子图) 中运行。
职责：
扮演一个严格的“标准内容生成执行者”。它禁止读取目标报告内容 target_generate_content，
仅凭 `original_content` 与上一节点 (Node 4) 编写出的 `current_sop`，
以第一人称去“执行”这个规程，并推演、输出在这个步骤中产生的虚构（模拟）数据。

目的：防止模型在比对审查时，因为看到了两边而直接抄袭通过。
强迫 Writer 必须把所需的必要参数、规格都在 SOP 中写明。
"""

from __future__ import annotations

import logging
from typing import Any, Mapping

from tools.llm_client import chat_completion

logger = logging.getLogger(__name__)


def simulator_node(state: Mapping[str, Any]) -> dict:
    """
    Simulator Agent 节点 (Node 6)
    
    Args:
        state: Chapter Sub-graph 传递的 Payload
        
    Returns:
        更新状态片段，存入 `simulated_generate_content`。
    """
    if "target_generate_content" in state:
        raise ValueError(
            "simulator_node input cannot include target_generate_content; "
            "please sanitize input before calling this node."
        )

    section_title = state.get("section_title", "未命名章节")
    logger.info(f"[Node 6 - Simulator] 开始盲测推演章节: {section_title}")
    
    current_sop = state.get("current_sop", "")
    original_content = state.get("original_content", "")
    
    # 防作弊：严禁将 target_generate_content 注入该节点的 Prompt
    prompt_sys = (
        "你是一名极其死板的 GLP 生物分析基层实验操作员。\n"
        "你的任务是：仔细阅读别人发给你的一段 SOP (标准操作规程) 文本，然后在脑海里严格一步步执行它。\n"
        "【极其关键的要求】：执行完成后，你必须告诉我你在这部分实验里做出来的【量化数据、中间计算结果或明确的步骤现象】。"
        "如果有任何模糊不清、没有写明浓度或用量导致你算不出结果的地方，请诚实地报告“规程缺失必要参数无法推演”。\n"
        "执行优先级要求：先遵循“核心填写规则”，再按“通用模板”生成；“示例”仅作参考，不得直接照抄示例内容。\n"
        "输出强约束：你的最终输出必须与 SOP 的通用模板/示例在格式与文风上保持一致，且可直接放进报告正文。\n"
        "禁止输出任何解释性语句、分析语句、询问语句、免责声明、前言或结尾。"
    )
    
    prompt_user = (
        f"【执行实验节点】：{section_title}\n\n"
        f"【方案原始内容 original_content】：\n{original_content}\n\n"
        f"【你收到的 SOP 规程说明书】：\n{current_sop}\n\n"
        "请严格按 SOP 执行并输出模拟生成结果。\n"
        "最终只输出可直接粘贴到报告中的正文内容，不要输出任何解释、说明、提问或额外话术。"
    )
    
    messages = [
        {"role": "system", "content": prompt_sys},
        {"role": "user", "content": prompt_user}
    ]
    
    try:
        logger.debug(f"[Node 6 - Simulator] ({section_title}) 正在闭卷推演...")
        llm_result = chat_completion(messages, temperature=0.1, max_tokens=1024)
        # chat_completion 会返回 (content_or_msg, tokens, latency, model)，
        # 这里只保留可展示的正文字符串，避免把元数据写入 state。
        content_or_msg = llm_result[0] if isinstance(llm_result, tuple) else llm_result
        if hasattr(content_or_msg, "content"):
            content_or_msg = getattr(content_or_msg, "content", "")
        simulated_generate_content = str(content_or_msg or "")
        logger.info(f"[Node 6 - Simulator] ({section_title}) 推演完成。")

        return {
            "simulated_generate_content": simulated_generate_content,
            "sse_summary": {
                "workflow": "sop_generation",
                "node": "simulator",
                "phase": "流程推演",
                "phase_state": "completed",
                "status": "running",
                "message": f"Sam 已完成《{section_title}》闭卷推演，模拟执行结果就绪。",
            },
        }
    except Exception as e:
        logger.error(f"[Node 6 - Simulator] ({section_title}) 推演失败: {e}")
        return {
            "simulated_generate_content": f"推演失败，大模型调用异常: {e}",
            "sse_summary": {
                "workflow": "sop_generation",
                "node": "simulator",
                "phase": "流程推演",
                "phase_state": "failed",
                "status": "running",
                "message": f"Sam 推演《{section_title}》失败，错误：{e}",
            },
        }
