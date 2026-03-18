"""
Master Node - Complexity Analysis and Routing (AI Agent)
SOP Generation System V6 - DeepLang

这是一个真正的 Agent，使用 LLM 来判断章节复杂度。
"""

import json
from typing import Dict, Any, TypedDict
from openai import OpenAI
from memory_manager_v6 import MemoryManagerV6
from config_v6 import MODEL_CONFIG, MASTER_SKILL_VERSION


class MasterState(TypedDict):
    section_title: str
    protocol_content: str
    original_report_content: str
    complexity: str
    route: str
    reasoning: str
    iteration: int
    sop_content: str
    reviewer_score: float
    is_pass: bool
    failure_cause: str
    data_index: int
    previous_sop: str
    all_protocol_contents: list
    all_report_contents: list
    previous_sop: str


class MasterAgent:
    """Master Agent: Uses LLM to assess complexity and determine routing path"""

    def __init__(self):
        self.memory = MemoryManagerV6()
        self.config = MODEL_CONFIG["master"]

        # Initialize OpenAI client (for Grok)
        self.client = OpenAI(
            api_key=self.config["api_key"], base_url=self.config["base_url"]
        )

    def __call__(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Assess complexity using LLM and determine routing path.

        Args:
            state: Current workflow state

        Returns:
            Updated state with complexity assessment
        """
        section_title = state["section_title"]
        protocol_content = state.get("protocol_content", "")
        original_report_content = state.get("original_report_content", "")

        # Load Complexity Analysis Skill
        skill_content = self.memory.load_skill("master")

        # Load existing template if available (for reference)
        existing_template = self.memory.load_sop_template(section_title)
        template_context = ""
        if existing_template:
            template_context = f"\n【现有 SOP 模板参考】：\n{existing_template['sop_content'][:300]}...\n"

        # Build prompt
        prompt = f"""你是复杂度分析专家，请基于以下内容判断章节的复杂度并确定路由路径。

# Complexity Analysis Skill (v{MASTER_SKILL_VERSION})
{skill_content}

# 输入内容

【章节名称】：{section_title}

【验证方案】：
{protocol_content[:3000]}

【GLP 报告参考】：
{original_report_content[:3000]}

{template_context}

# 任务要求

1. 严格按照 Complexity Analysis Skill 中的判断标准进行评估
2. 复杂度只输出 "simple" 或 "complex"，不要输出 "standard"
3. 路由路径：
   - simple: 简单章节 → simple_path (Writer → Format Verify → END)
   - complex: 复杂章节 → complex_path (Writer → Simulator → Reviewer → (FAIL)  → Curator → Writer (循环）
4. 输出简洁的理由（50 字以内）
5. 输出格式：JSON

请输出JSON格式的分析结果。"""

        try:
            # Generate using Grok
            response = self.client.chat.completions.create(
                model=self.config["model"],
                messages=[{"role": "system", "content": prompt}],
                temperature=self.config["temperature"],
                response_format={"type": "json_object"},
            )

            result_text = response.choices[0].message.content.strip()
            result = json.loads(result_text)

            # Extract key metrics
            complexity = result.get("complexity", "complex")
            reasoning = result.get("reasoning", "内容需要分析处理")

            # Determine route based on complexity
            route_mapping = {
                "simple": "simple_path",
                "complex": "complex_path",
            }
            route = route_mapping[complexity]

            # Initialize iteration count if not present
            if "iteration" not in state:
                state["iteration"] = 1

            # Log execution start
            self.memory.log_execution_start(section_title, complexity, route)

            # Log node execution
            self.memory.log_node_execution(
                section_title,
                "master",
                {"complexity": complexity, "route": route, "reasoning": reasoning},
            )

            print(
                f"🎯 [{section_title}] 复杂度: {complexity} | 路由: {route} | 原因: {reasoning}"
            )

            return {
                **state,
                "complexity": complexity,
                "route": route,
                "reasoning": reasoning,
            }

        except Exception as e:
            print(f"❌ [{section_title}] Master 分析失败: {e}")

            # Fallback: default to complex (more conservative)
            return {
                **state,
                "complexity": "complex",
                "route": "complex_path",
                "reasoning": f"分析失败，默认复杂: {str(e)}",
            }


def format_verify_node(state: MasterState) -> MasterState:
    """
    Format Verify Node (for simple path): Verify output format only.
    """
    section_title = state["section_title"]
    sop_content = state.get("sop_content", "")

    # Basic format check
    has_title = "##" in sop_content
    has_content = len(sop_content.strip()) > 0

    # For simple sections, we're lenient - just check basic format
    is_pass = has_title and has_content
    state["is_pass"] = is_pass
    state["reviewer_score"] = 5.0 if is_pass else 1.0

    # Log completion
    memory = MemoryManagerV6()
    if is_pass:
        memory.save_sop_template(
            section_title,
            sop_content,
            {
                "complexity": state["complexity"],
                "score": 5.0,
                "iteration": state["iteration"],
            },
        )
        memory.log_execution_complete(section_title, 5.0, state["iteration"])

    print(f"✓ [{section_title}] 格式验证: {'通过' if is_pass else '失败'}")

    return state


def should_route_simple(state: MasterState) -> str:
    """Route decision for simple path"""
    return "format_verify" if state["route"] == "simple_path" else "writer"


def should_retry_complex(state: MasterState) -> str:
    """Route decision for complex path retry logic"""
    if state.get("route") == "complex_path" and not state.get("is_pass", False):
        if state.get("iteration", 1) < 3:  # Max 3 iterations
            return "analyzer"  # Go to failure analysis
        else:
            return "end"  # Give up after max iterations
    return "end"
