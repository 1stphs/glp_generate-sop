"""
Writer Node - Generate SOP based on Skill
SOP Generation System V6 - DeepLang
"""

import json
from typing import Dict, Any
from openai import OpenAI
from sop_deeplang.utils.memory_manager import MemoryManager
from sop_deeplang.utils.config import (
    MODEL_CONFIG, 
    WRITER_SKILL_VERSION,
    STATIC_SECTIONS,
    SIMPLE_SECTIONS,
    COMPLEX_SECTIONS,
    COMPLEX_KEYWORDS
)
from sop_deeplang.utils.table_mapper import TableMapper


class WriterNode:
    """Writer Node: Generates SOP using Grok"""

    def __init__(self):
        self.memory = MemoryManager()
        self.table_mapper = TableMapper()
        self.config = MODEL_CONFIG["writer"]

        # Initialize OpenAI client (for Grok)
        self.client = OpenAI(
            api_key=self.config["api_key"], base_url=self.config["base_url"]
        )

    def _identify_section_type(self, title: str, content: str) -> str:
        """Categorize section to determine prompting strategy."""
        title = title.strip()
        
        # 0. Check for Table/Figure only sections
        if title.startswith("表") or title.startswith("图") or "附表" in title or "附图" in title:
            # Special case for directories
            if "目录" in title: return "STATIC"
            return "SKIP_TABLE"
            
        if any(s in title for s in STATIC_SECTIONS):
            return "STATIC"
        if any(s in title for s in SIMPLE_SECTIONS):
            return "SIMPLE"
        if any(s in title for s in COMPLEX_SECTIONS) or any(k in title for k in COMPLEX_KEYWORDS):
            return "COMPLEX"
            
        # Default based on length/content
        if len(content) < 300: return "SIMPLE"
        return "COMPLEX"

    def __call__(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate SOP using Grok with enhancement mode.
        """
        section_title = state["section_title"]
        protocol_content = state.get("protocol_content", "")
        report_content = state.get("original_report_content", "")
        previous_sop = state.get("previous_sop", "")
        report_id = state.get("report_id", "default")
        data_index = state.get("data_index", 1)
        phase = state.get("phase", 1)

        # 1. Identify Section Type
        s_type = self._identify_section_type(section_title, protocol_content + report_content)
        
        if s_type == "SKIP_TABLE":
            print(f"⏩ [{section_title}] 检测为纯数据表，跳过 SOP 生成")
            return {**state, "sop_content": f"<!-- SKIP: {section_title} is a data table -->"}

        self.memory.log_node_execution(
            section_title,
            "writer",
            {"data_index": data_index, "type": s_type, "phase": phase},
        )

        skill_content = self.memory.load_skill("writer")

        # 2. Select Prompt Mode based on type and phase
        if s_type == "STATIC":
            prompt_mode = f"""
### 【静态结构模式 (Static Mode)】
**目标**：仅生成该章节的结构化占位模板。
**具体要求**：
1. 严禁生成任何“填写规则”或“计算逻辑”。
2. 保持简洁，仅保留原本章节该有的标题、页码占位符或声明文本。
"""
        elif s_type == "SIMPLE":
            prompt_mode = f"""
### 【标准改写模式 (Simple/Rewrite Mode)】
**目标**：从原文中提取关键信息并按照 SOP 格式进行标准化改写。
**具体要求**：
1. 严禁编造信息，严禁发散性写作。
2. 仅保留核心陈述语句，并对动态部分进行插槽化（如 `[试验编号]`）。
3. 即使原文内容极少（如“无偏离”），也必须生成基于该声明的标准化 SOP 模板，严禁输出“无明确数据支持”。
4. 严禁生成大段的操作规程。
"""
        elif phase == 1:
            prompt_mode = f"""
### 【阶段 1：骨架生成模式 (Phase 1: Skeleton Mode)】
**核心目标**：生成一个标准化的、包含插槽（Placeholder）的 SOP 骨架草稿。
**严禁事项**：
1. 严禁编造任何数值。
2. 严禁输出与实验流程无关的解释性文字。
**插槽规则**：
使用 `[XXX]` 格式占位。
"""
        else:
            # Phase 2: Loading Chapter Rules and Excel data
            chapter_rules = self.memory.load_chapter_rule(section_title)
            related_tables = self.table_mapper.get_related_tables(section_title, report_id)
            
            tables_context = ""
            if related_tables:
                tables_context = "\n### 【关联 Excel 数据结构 (Excel Context)】\n"
                for t in related_tables:
                    tables_context += f"\n- 表名: {t['table_name']}\n{t['content']}\n"
            
            rules_context = ""
            if chapter_rules:
                rules_context = f"\n### 【本章节专属进化规则 (Chapter-specific Rules)】\n{json.dumps(chapter_rules, ensure_ascii=False, indent=2)}\n"

            prompt_mode = f"""
### 【专家迭代模式 (Phase 2: Expert Mode)】
**核心目标**：基于真实的 Excel 数据特征和章节规则，对 V1 骨架进行“结构性升维”。
{rules_context}
{tables_context}
**任务要求**：
1. **结构重组**：确保插槽能覆盖 Excel 数据维度。
2. **输出格式**：包含 `## 一、核心填写规则` 和 `## 二、通用标准化模板`。
"""

        prompt = f"""你是GLP-SOP生成专家。
# Global Writer Skill (v{WRITER_SKILL_VERSION})
{skill_content}

{prompt_mode}

# 参考输入资料
--- 验证方案 (Protocol) ---
{protocol_content[:5000]}
--- GLP 报告 (Report) ---
{report_content[:5000]}
--- 上一版本 SOP (Previous Version) ---
{previous_sop}

请开始生成。
"""

        try:
            response = self.client.chat.completions.create(
                model=self.config["model"],
                messages=[{"role": "system", "content": prompt}],
            )

            content = response.choices[0].message.content
            sop_content = content.strip() if content else ""

            print(f"📝 [{section_title}] Writer生成完成 (类型: {s_type}, 阶段: {phase})")

            return {**state, "sop_content": sop_content, "section_type": s_type}

        except Exception as e:
            print(f"❌ [{section_title}] Writer生成失败: {e}")
            return {**state, "sop_content": "", "error": str(e)}
