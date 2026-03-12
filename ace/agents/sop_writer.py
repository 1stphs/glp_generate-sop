"""
SOP Writer Agent - 生成标准化SOP

生成SOP（核心填写规则、通用模板、示例）
支持三种SOP类型：simple_insert, rule_template, complex_composite
"""

from typing import Dict, Any, List
import json


class SOPWriter:
    """
    SOP Writer Agent: 生成标准化SOP

    功能：
    1. 根据章节内容生成SOP
    2. 输出固定三段结构（核心规则、通用模板、示例）
    3. 支持三种SOP类型
    """

    def __init__(self, llm_config: Dict[str, Any]):
        """
        初始化SOP Writer

        Args:
            llm_config: LLM配置
        """
        self.llm_config = llm_config

    def generate_sop(
        self,
        chapter_id: str,
        section_title: str,
        original_content: str,
        target_generate_content: str,
        existing_sop: str = "",
        feedback: str = "",
    ) -> Dict[str, Any]:
        """
        生成SOP

        Args:
            chapter_id: 章节ID
            section_title: 章节标题
            original_content: 原始方案内容
            target_generate_content: 目标报告内容
            existing_sop: 当前SOP（如果有）
            feedback: 反馈意见（如果有）

        Returns:
            {
                "sop": "SOP内容（Markdown格式）",
                "sop_type": "SOP类型",
                "core_rules": ["核心规则列表"],
                "template_text": "通用模板内容",
                "examples": "示例内容",
                "metrics": {
                    "tokens": "Token消耗",
                    "latency": "延迟"
                }
            }
        """
        # 推断SOP类型
        sop_type = self._infer_sop_type(target_generate_content, feedback)

        # 构建提示
        system_prompt = self._get_system_prompt()
        user_prompt = self._build_user_prompt(
            section_title,
            original_content,
            target_generate_content,
            existing_sop,
            feedback,
            sop_type,
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        # TODO: 调用LLM生成SOP
        # response = self._call_llm(messages)
        # parsed = self._parse_response(response)

        # 暂时返回模拟结果
        mock_sop = self._generate_mock_sop(section_title, sop_type)

        return {
            "sop": mock_sop,
            "sop_type": sop_type,
            "core_rules": self._extract_core_rules(section_title),
            "template_text": self._extract_template(section_title),
            "examples": self._extract_examples(section_title),
            "metrics": {"tokens": 1000, "latency": 5.0},
        }

    def _infer_sop_type(self, target_content: str, feedback: str) -> str:
        """
        推断SOP类型

        Args:
            target_content: 目标内容
            feedback: 反馈

        Returns:
            SOP类型：simple_insert, rule_template, complex_composite
        """
        content = (target_content + " " + feedback).lower()

        # 复杂组合信号
        complex_signals = [
            "情形a",
            "情形b",
            "除",
            "其余",
            "若",
            "否则",
            "例外",
            "异常",
            "分两段",
            "分别",
        ]
        if any(signal in content for signal in complex_signals):
            return "complex_composite"

        # 简单插入信号
        simple_content = target_content.replace("\n", "").strip()
        if simple_content and len(simple_content) <= 80:
            if "[" not in simple_content and "]" not in simple_content:
                return "simple_insert"

        return "rule_template"

    def _get_system_prompt(self) -> str:
        """获取系统提示词"""
        return """你是SOP撰写专家。

你的任务是：根据验证方案和验证报告，生成标准化的SOP（Standard Operating Procedure）。

SOP必须包含三段：
1. 核心填写规则：列出具体的填写规则和要求
2. 通用模板：提供通用的填写模板
3. 示例：给出具体的填写示例

输出格式要求：
- 使用Markdown格式
- 标题使用 "## 一、核心填写规则", "## 二、通用模板", "## 三、示例"
- 核心规则使用有序列表（1. 2. 3.）
- 模板和示例清晰易读
- 避免使用过多的专业术语，保持通俗易懂

SOP类型判断：
- simple_insert: 目标内容为固定短文本，无需字段解析
- rule_template: 需要提取字段并按模板填充
- complex_composite: 包含多种情形或条件分支

重要提醒：
- 确保SOP准确反映验证报告的格式
- 保持规则的具体性和可操作性
- 示例要具有代表性和指导性"""

    def _build_user_prompt(
        self,
        section_title: str,
        original_content: str,
        target_content: str,
        existing_sop: str,
        feedback: str,
        sop_type: str,
    ) -> str:
        """构建用户提示词"""
        prompt = f"""章节标题：{section_title}

SOP类型：{sop_type}

验证方案内容：
{original_content[:500]}...

验证报告内容：
{target_content[:500]}...

"""
        if feedback:
            prompt += f"""反馈意见：
{feedback}

"""

        if existing_sop:
            prompt += f"""当前SOP：
{existing_sop[:300]}...

"""

        prompt += """请生成标准化的SOP（包含三段：核心填写规则、通用模板、示例）。

注意：
- 核心规则要具体、可操作
- 通用模板要清晰、易填写
- 示例要具有代表性"""

        return prompt

    def _parse_response(self, response: str) -> Dict[str, Any]:
        """解析LLM响应"""
        # TODO: 实现JSON解析
        # 暂时返回模拟数据
        return {
            "sop_type": "rule_template",
            "core_rules": ["规则1", "规则2"],
            "template_text": "模板内容",
            "examples": "示例内容",
        }

    def _generate_mock_sop(self, section_title: str, sop_type: str) -> str:
        """生成模拟SOP（用于测试）"""
        return f"""## 一、核心填写规则

1. 填写时注意标题和编号的格式
2. 保持中英文双语的一致性
3. 确保所有必填项都填写完整

## 二、通用模板

【{section_title}】内容模板：
[字段1]：
[字段2]：
[字段3]：

## 三、示例

【{section_title}】示例内容：
[示例1]
[示例2]"""

    def _extract_core_rules(self, section_title: str) -> List[str]:
        """提取核心规则"""
        return [
            f"填写{section_title}时注意格式规范",
            f"确保所有字段必填",
            f"保持内容一致性",
        ]

    def _extract_template(self, section_title: str) -> str:
        """提取模板"""
        return f"【{section_title}】模板字段：\n[字段A]：\n[字段B]：\n[字段C]："

    def _extract_examples(self, section_title: str) -> str:
        """提取示例"""
        return f"【{section_title}】示例1：\n【{section_title}】示例2："
