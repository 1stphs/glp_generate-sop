"""
Node 4: SOP Writer Agent 节点

目标：
将章节 SOP 输出约束为固定三段结构：
1) 核心填写规则
2) 通用模板
3) 示例
"""

from __future__ import annotations

import json
import logging
import re
from typing import Literal

from pydantic import BaseModel, Field

from workflows.sop_generation.state import ChapterState
from tools.llm_client import chat_completion, ModelRouter
from prompts.registry import PromptRegistry
from workflows.meta.complexity_analyzer import analyze_complexity
from workflows.meta.rag_kb import KnowledgeBase
from workflows.meta.metrics import metrics_collector

logger = logging.getLogger(__name__)

VALID_SOP_TYPES = {"simple_insert", "rule_template", "complex_composite"}


class SopWriterResult(BaseModel):
    reasoning: str = Field(description="你的思维链/推理过程/详细分析，请逐步分析原始内容与目标内容的映射关系与排版规则。")
    sop_type: Literal["simple_insert", "rule_template", "complex_composite"] = Field(
        description="SOP 类型：simple_insert / rule_template / complex_composite"
    )
    core_rules: list[str] = Field(description="核心填写规则，列表形式。")
    template_text: str = Field(description="通用模板正文。")
    examples: str | list[str] = Field(description="示例内容。复杂组合型可返回多条示例。")


def _normalize_rule(rule: str) -> str:
    cleaned = re.sub(r"^\s*(?:[-*]|\d+[.)、])\s*", "", str(rule or "").strip())
    return cleaned


def _enforce_rule_count(sop_type: str, rules: list[str]) -> list[str]:
    filtered = [_normalize_rule(r) for r in rules if _normalize_rule(r)]
    defaults = {
        "simple_insert": [
            "固定输出通用模板的内容，不做额外解析和改写。",
            "不得补充模板中未定义的新字段或新信息。",
        ],
        "rule_template": [
            "先从原始内容提取模板需要的字段，再按模板位置填充。",
            "字段名称、格式和书写顺序需与目标报告保持一致。",
            "缺失字段必须按模板约束保留占位，不可臆造数据。",
            "输出仅包含模板要求的内容，不添加解释性文本。",
        ],
        "complex_composite": [
            "先判断适用情形，再选择对应的模板分支输出。",
            "每个情形需遵循独立规则并保持字段一致性。",
            "涉及异常/例外时必须给出判定依据与结论表述。",
            "若模板要求分段输出，必须严格按分段格式生成。",
            "禁止跨情形混用语句，避免逻辑冲突。",
            "输出仅包含模板要求内容，不添加说明性文字。",
        ],
    }

    limits = {
        "simple_insert": (1, 2),
        "rule_template": (2, 4),
        "complex_composite": (3, 6),
    }
    minimum, maximum = limits[sop_type]
    if len(filtered) < minimum:
        filtered.extend(defaults[sop_type][: minimum - len(filtered)])
    return filtered[:maximum]


def _normalize_examples(examples: str | list[str]) -> str:
    if isinstance(examples, list):
        lines = [str(item).strip() for item in examples if str(item).strip()]
        return "\n\n".join(lines)
    return str(examples or "").strip()


def _render_sop_markdown(sop_type: str, core_rules: list[str], template_text: str, examples: str | list[str]) -> str:
    rules = _enforce_rule_count(sop_type, core_rules)
    template = str(template_text or "").strip()
    example_text = _normalize_examples(examples)

    if not template:
        template = "[请按模板填写核心字段]"
    if not example_text:
        example_text = template

    lines = ["## 一、核心填写规则"]
    lines.extend([f"{idx}. {rule}" for idx, rule in enumerate(rules, start=1)])
    lines.extend(["", "## 二、通用模板", template, "", "## 三、示例", example_text])
    return "\n".join(lines).strip()


def _infer_sop_type(
    target_generate_content: str,
    feedback: str,
    existing_sop_type: str | None,
) -> str:
    if existing_sop_type in VALID_SOP_TYPES and feedback:
        feedback_lower = feedback.lower()
        change_hint = [
            "改为", "切换", "类型", "simple_insert", "rule_template", "complex_composite",
            "简单插入", "规则+模板", "复杂组合"
        ]
        if not any(token in feedback_lower for token in change_hint):
            return existing_sop_type

    target = (target_generate_content or "").strip()
    merged = f"{target}\n{feedback or ''}".lower()

    complex_signals = [
        "情形a", "情形b", "除", "其余", "若", "否则", "例外", "异常", "分两段", "分别",
    ]
    if any(signal in merged for signal in complex_signals):
        return "complex_composite"

    simple_target = target.replace("\n", "").strip()
    if simple_target and len(simple_target) <= 80 and "[" not in simple_target and "]" not in simple_target:
        return "simple_insert"

    return "rule_template"


def _fallback_sop_payload(section_title: str, sop_type: str, reason: str) -> dict:
    fallback_type = sop_type if sop_type in VALID_SOP_TYPES else "rule_template"
    logger.warning(
        "[Node 4 - Writer] (%s) sop_writer_format_fallback=true, reason=%s",
        section_title,
        reason,
    )

    if fallback_type == "simple_insert":
        rules = ["固定输出通用模板内容，不做解析与扩展。"]
        template = "[固定文本内容]"
        examples = template
    elif fallback_type == "complex_composite":
        rules = [
            "根据条件选择模板分支，不得混用分支语句。",
            "异常分支需说明评估逻辑与结论。",
            "输出格式严格按照模板分段要求。",
        ]
        template = (
            "[情形A：异常但可接受] ...\n"
            "[情形B：全部符合] ..."
        )
        examples = [
            "[情形A：异常但可接受]\n...\n\n...",
            "[情形B：全部符合]\n...",
        ]
    else:
        fallback_type = "rule_template"
        rules = [
            "先提取模板需要字段，再按模板顺序填充。",
            "字段名与格式必须和目标报告一致。",
        ]
        template = "**字段A**：[值A]\n**字段B**：[值B]"
        examples = "**字段A**：示例值A\n**字段B**：示例值B"

    markdown = _render_sop_markdown(fallback_type, rules, template, examples)
    return {"current_sop": markdown, "sop_type": fallback_type}


def sop_writer_node(state: ChapterState) -> dict:
    """
    SOP Writer Agent 节点 (Node 4)。

    输出固定三段 SOP 结构，并返回 sop_type。
    """
    section_title = state.get("section_title", "未命名章节")
    logger.info(f"[Node 4 - Writer] 开始起草/修改章节: {section_title}")

    original_content = state.get("original_content", "")
    target_generate_content = state.get("target_generate_content", "")
    status = state.get("status", "RUNNING")
    is_passed = state.get("is_passed", False)
    retry_count = state.get("retry_count", 0)
    feedback = state.get("feedback", "")
    current_sop = state.get("current_sop", "")
    simulated_generate_content = state.get("simulated_generate_content", "")
    existing_sop_type = state.get("sop_type")
    suggested_sop_type = _infer_sop_type(target_generate_content, feedback, existing_sop_type)
    
    # 仅使用本地内存知识库做 Few-Shot 召回，避免依赖外部存储。
    few_shot_examples = KnowledgeBase.retrieve_examples(suggested_sop_type)

    # 直接使用 state 中已注入的章节内容作为 Prompt 输入。
    protocol_context = original_content
    report_context = target_generate_content
    
    prompt_sys = PromptRegistry.get_prompt("sop_writer_sys")

    # 构建当前任务的上下文提示词
    if retry_count == 0:
        prompt_user = PromptRegistry.get_prompt(
            "sop_writer_user_first",
            section_title=section_title,
            original_content=protocol_context,
            target_generate_content=report_context,
            few_shot_context=few_shot_examples
        )
    else:
        # 重复失败尝试时，需分析上一轮的 feedback 和模拟出来的虚拟结果
        prompt_user = PromptRegistry.get_prompt(
            "sop_writer_user_retry",
            section_title=section_title,
            original_content=protocol_context,
            target_generate_content=report_context,
            current_sop=current_sop,
            status=status,
            is_passed=is_passed,
            retry_count=retry_count,
            simulated_generate_content=state.get("simulated_generate_content", ""),
            feedback=state.get("feedback", ""),
            few_shot_context=few_shot_examples
        )

    messages = [
        {"role": "system", "content": prompt_sys},
        {"role": "user", "content": prompt_user},
    ]

    # 1. 复杂度分析
    section_data = {
        "target_generate_content": target_generate_content,
        "sop_type": suggested_sop_type,
    }
    complexity = analyze_complexity(**section_data)
    
    # 2. 根据复杂度分配模型
    routed_model = ModelRouter.get_routed_model(complexity.level)
    
    logger.debug(f"[Node 4 - Writer] ({section_title}) 复杂度={complexity.level}, 分配模型={routed_model}, 正在调用...")
    
    try:
        logger.debug(f"[Node 4 - Writer] ({section_title}) 进行结构化最终生成...")
        raw_json, tokens, latency, model = chat_completion(
            messages,
            model=routed_model,
            temperature=0.1,
            max_tokens=1600,
            response_format=SopWriterResult,
        )
        total_tokens = tokens
        total_latency = latency
        
        try:
            parsed = json.loads(raw_json)
        except json.JSONDecodeError as decode_err:
            logger.warning(
                "[Node 4 - Writer] (%s) 结构化返回解析失败，执行一次低温重试: %s",
                section_title,
                decode_err,
            )
            raw_json_retry, tokens3, lat3, mod3 = chat_completion(
                messages,
                model=routed_model,
                temperature=0.0,
                max_tokens=1600,
                response_format=SopWriterResult,
            )
            total_tokens += tokens3
            total_latency += lat3
            parsed = json.loads(raw_json_retry)

        # 记录 Writer 的指标 (暂未判断 passed，传 False，稍后 Reviewer 决定)
        metrics_collector.record_generation(
            chapter=f"{section_title}_Writer",
            tokens=total_tokens,
            latency=total_latency,
            passed=False,
            retries=retry_count,
            model=model
        )

        sop_type = str(parsed.get("sop_type", suggested_sop_type)).strip()
        if sop_type not in VALID_SOP_TYPES:
            sop_type = suggested_sop_type

        core_rules = parsed.get("core_rules", [])
        if not isinstance(core_rules, list):
            core_rules = [str(core_rules)]

        template_text = parsed.get("template_text", "")
        examples = parsed.get("examples", "")

        markdown = _render_sop_markdown(sop_type, core_rules, template_text, examples)
        logger.info(f"[Node 4 - Writer] ({section_title}) 撰写完成，类型={sop_type}, Length={len(markdown)}")
        return {
            "current_sop": markdown,
            "sop_type": sop_type,
            "sse_summary": {
                "workflow": "sop_generation",
                "node": "sop_writer",
                "phase": "SOP 起草",
                "phase_state": "completed",
                "status": "running",
                "message": f"Sophie 已完成《{section_title}》 SOP 起草，类型：{sop_type}。",
            },
        }
    except Exception as e:
        logger.error(f"[Node 4 - Writer] ({section_title}) 调用失败: {e}")
        fallback = _fallback_sop_payload(section_title, suggested_sop_type, str(e))
        fallback["sse_summary"] = {
            "workflow": "sop_generation",
            "node": "sop_writer",
            "phase": "SOP 起草",
            "phase_state": "failed",
            "status": "running",
            "message": f"Sophie 起草《{section_title}》失败，已调用备用方案。错误：{e}",
        }
        return fallback
