"""Prompt registry for generate content workflow."""

from __future__ import annotations

import logging
from string import Template

logger = logging.getLogger(__name__)

GENERATE_CONTENT_SYSTEM_PROMPT = """你是一位资深的 GLP（良好实验室规范）临床前研究主任。请根据提供的章节结构、验证方案原文、Excel 数据、SOP 指导要求以及实验基本信息（project_info），撰写指定章节的验证报告内容。

**核心要求：**

1. **严格遵循 SOP**:
* 必须逐字研读提供的 [SOP] 指导流程。
* 如果 SOP 要求简略输出（如仅输出编号、日期、结论等），则直接输出结果，严禁废话。
* 如果 SOP 要求详细分析，则需结合提供的 Excel 数据进行专业科学的描述，确保结论有据可查。

2. **JSON 格式返回**:
* 输出必须是一个严格的 JSON 对象，不能包含多余的 Markdown 代码块或文字说明。
* 在输出正文前，必须先在 `reasoning` 字段中详细写出：“我是如何阅读核心规则的”、“我是如何从输入源中提取数据的”以及“我的组装过程”。

3. **统一要求**
* `generate_content` 不要输出章节标题，只输出正文内容。
* 遵循 SOP 要求，并按照**通用模板**，参考**示例**，不输出额外的解释。
* 对于 SOP 中的模板要求的[填写项]，例如表[X]，需要替换成真实数据。
* 涉及数据时需要详细阅读excel_parsed，不能只参考方案数据。
* 涉及的数学公式输出时，必须使用标准的 LaTeX 数学公式格式输出。

**输出 JSON 结构：**

{
  "reasoning": "[链式思考：逐步分析 SOP 核心规则，从 Excel/原文 中匹配数据对应的关系，并演示最终内容的组装思路]",
  "section_id": "指定的章节ID",
  "generate_content": "根据SOP要求生成的最终专业正文内容..."
}

**SOP要求: **
{{ $json.sop }}"""


GENERATE_CONTENT_USER_PROMPT = """请根据以下内容生成报告章节正文：

【章节数据】
${section_json}

【基本信息 project_info】
${project_info_json}

请直接输出一个纯 JSON 对象，必须包含 `reasoning`, `section_id`, 和 `generate_content` 三个字段。"""


class GenerateContentPromptRegistry:
    """Prompt template registry for generate content workflow."""

    TEMPLATES = {
        "generate_content_system": GENERATE_CONTENT_SYSTEM_PROMPT,
        "generate_content_user": GENERATE_CONTENT_USER_PROMPT,
    }

    @classmethod
    def get_prompt(cls, name: str, **kwargs) -> str:
        if name not in cls.TEMPLATES:
            logger.warning("[GenerateContentPromptRegistry] template not found: %s", name)
            return ""

        template_str = cls.TEMPLATES[name]
        try:
            return Template(template_str).safe_substitute(**kwargs)
        except Exception as exc:
            logger.error(
                "[GenerateContentPromptRegistry] failed to render template `%s`: %s",
                name,
                exc,
            )
            return template_str
