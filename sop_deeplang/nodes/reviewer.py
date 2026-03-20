"""
Reviewer Node - Quality Audit and Scoring
SOP Generation System V6 - DeepLang
"""

import json
from typing import Dict, Any
from openai import OpenAI
from sop_deeplang.utils.memory_manager import MemoryManager
from sop_deeplang.utils.config import MODEL_CONFIG, REVIEWER_SKILL_VERSION


class ReviewerNode:
    """Reviewer Node: Quality audit and scoring (harsh mode)"""

    def __init__(self):
        self.memory = MemoryManager()
        self.config = MODEL_CONFIG["reviewer"]

        # Initialize OpenAI client (for Grok)
        self.client = OpenAI(
            api_key=self.config["api_key"], base_url=self.config["base_url"]
        )

    def __call__(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Review generated SOP by comparing Simulator output with original report.

        Args:
            state: Current workflow state

        Returns:
            Updated state with review results
        """
        section_title = state["section_title"]
        sop_content = state.get("sop_content", "")
        original_report_content = state.get("original_report_content", "")
        simulation_result = state.get("simulation_result", {})
        phase = state.get("phase", 1)

        simulated_output = simulation_result.get("simulated_output", "")

        skill_content = self.memory.load_skill("reviewer")

        phase_context = ""
        if phase == 2:
            chapter_rules = self.memory.load_chapter_rule(section_title)
            rules_str = json.dumps(chapter_rules, ensure_ascii=False, indent=2) if chapter_rules else "无特定章节规则"
            phase_context = f"""
### 【阶段 2：审计重点 (Phase 2 Audit Focus)】
1. **规则一致性**：SOP 中的“核心填写规则”部分是否准确体现了以下章节规则？
   {rules_str}
2. **插槽健壮度**：根据 Simulator 的模拟报告，插槽是否足以支撑复杂数据的代入？是否出现了“插槽维度不足”的标记？
3. **去幻觉校验**：即便在第二阶段，SOP 模板中也严禁出现具体实测数值，必须保持插槽化。
"""

        prompt = f"""你是GLP质量审计专家（FDA Inspector风格）。

你的任务是：对比【Simulator 按照SOP生成的模拟报告】和【原始GLP报告内容】，判断SOP质量。

# Reviewer Skill (v{REVIEWER_SKILL_VERSION})
{skill_content}

{phase_context}

【待评审的SOP规程】：
{sop_content}

【Simulator生成的模拟报告】：
{simulated_output if simulated_output else "（未生成模拟报告）"}

【原始GLP报告参考】：
{original_report_content[:2000]}

# 评分要求 (1-5分)
- **4分及以上**：结构完整，规则清晰，插槽足以应对真实数据，无数据幻觉。
- **3分及以下**：规则遗漏，或插槽维度不足导致真实数据无法准确装载（需在 critical_issues 中说明）。

输出结果必须为纯 JSON 格式。
"""

        try:
            response = self.client.chat.completions.create(
                model=self.config["model"],
                messages=[{"role": "system", "content": prompt}],
                response_format={"type": "json_object"},
            )

            content = response.choices[0].message.content
            result_text = content.strip() if content else ""
            result = json.loads(result_text)

            score = result.get("score", 1)
            is_pass = result.get("is_pass", False)
            critical_issues = result.get("critical_issues", [])
            summary = result.get("summary", "")

            self.memory.log_node_execution(section_title, "reviewer", result)

            status_str = '✓通过' if is_pass else '✗失败'
            print(
                f"🔍 [{section_title}] Reviewer评分: {score}/5 {status_str}"
            )
            if score >= 4 and not is_pass:
                print(f"   ⚠️  [警告] 评分虽高，但因关键项审计严重不合规被“一票否决”！")
            if summary:
                print(f"   📝 总结: {summary}")
            if critical_issues:
                print(f"   ⚠️  Critical问题 ({len(critical_issues)}个):")
                for i, issue in enumerate(critical_issues, 1):
                    if isinstance(issue, dict):
                        issue_text = issue.get("issue", issue.get("title", str(issue)))
                        location = issue.get("location", "")
                        suggestion = issue.get("suggestion", "")
                    else:
                        issue_text = str(issue)
                        location = ""
                        suggestion = ""
                    
                    print(f"      {i}. {issue_text}")
                    if location:
                        print(f"         位置: {location}")
                    if suggestion:
                        print(f"         建议: {suggestion}")

            return {
                **state,
                "reviewer_score": score,
                "is_pass": is_pass,
                "reviewer_result": result,
            }

        except Exception as e:
            print(f"❌ [{section_title}] Reviewer审核失败: {e}")
            return {
                **state,
                "reviewer_score": 1.0,
                "is_pass": False,
                "reviewer_result": {
                    "score": 1,
                    "is_pass": False,
                    "critical_issues": [
                        {"issue": "系统错误", "location": "系统", "suggestion": str(e)}
                    ],
                    "summary": "审核过程失败",
                },
                "error": str(e),
            }
