"""
Reviewer Node - Quality Audit and Scoring
SOP Generation System V6 - DeepLang
"""

import json
from typing import Dict, Any
from openai import OpenAI
from memory_manager import MemoryManager
from config import MODEL_CONFIG, REVIEWER_SKILL_VERSION


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

        simulated_output = simulation_result.get("simulated_output", "")

        skill_content = self.memory.load_skill("reviewer")

        prompt = f"""你是GLP质量审计专家（FDA Inspector风格）。

你的任务是：对比【Simulator 按照SOP生成的模拟报告】和【原始GLP报告内容】，判断SOP质量。

# Reviewer Skill (v{REVIEWER_SKILL_VERSION})
{skill_content}

【待评审的SOP规程】：
{sop_content}

【Simulator生成的模拟报告】：
{simulated_output if simulated_output else "（未生成模拟报告）"}

【原始GLP报告参考】：
{original_report_content[:2000]}

# 评审标准

1. 对比准确性：模拟报告的内容是否与原始报告的关键信息一致
2. 完整性检查：SOP是否包含了所有必要的参数和步骤
3. 可执行性判断：按照SOP能否真正生成可用的报告
4. 评分标准：1-5分，4分及以上为通过

# 任务要求

输出JSON格式的审核结果。
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

            print(
                f"🔍 [{section_title}] Reviewer评分: {score}/5 {'✓通过' if is_pass else '✗失败'}"
            )
            if summary:
                print(f"   📝 总结: {summary}")
            if critical_issues:
                print(f"   ⚠️  Critical问题 ({len(critical_issues)}个):")
                for i, issue in enumerate(critical_issues, 1):
                    issue_text = issue.get("issue", str(issue))
                    location = issue.get("location", "")
                    suggestion = issue.get("suggestion", "")
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
