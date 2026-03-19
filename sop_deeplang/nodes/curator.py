"""
Curator Node - Update Writer Skill
SOP Generation System V6 - DeepLang
"""

import json
import re
from typing import Dict, Any
from openai import OpenAI
from memory_manager_v6 import MemoryManagerV6
from config_v6 import MODEL_CONFIG, CURATOR_SKILL_VERSION


class CuratorNode:
    """Curator Node: Update Writer Skill based on failure cases"""

    def __init__(self):
        self.memory = MemoryManagerV6()
        self.config = MODEL_CONFIG["curator"]

        # Initialize OpenAI client (for Grok)
        self.client = OpenAI(
            api_key=self.config["api_key"], base_url=self.config["base_url"]
        )

    def __call__(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update Writer Skill directly from Reviewer feedback.
        """
        section_title = state["section_title"]
        reviewer_result = state.get("reviewer_result", {})

        skill_content = self.memory.load_skill("curator")

        prompt = f"""你是知识库管理员，负责根据Reviewer的反馈更新Writer Skill。

# Curator Skill (v{CURATOR_SKILL_VERSION})
{skill_content}

# Reviewer 反馈结果
{json.dumps(reviewer_result, ensure_ascii=False, indent=2)}

# 任务要求

1. 严格按照Curator Skill中的规则模板生成新规则
2. 提炼通用规则，不要包含具体数值
3. 规则必须明确可检查
4. 输出JSON格式结果，不要任何其他文本

# JSON输出格式（必须严格遵循）

请严格按照以下JSON格式输出，不要修改字段名：

```json
{{
  "update_type": "add_principle",
  "new_rule": "这里填写新规则的简短描述",
  "rationale": "这里填写更新理由，说明为什么需要这条规则"
}}
```

**字段说明**：
- `update_type`: 必须是以下三个值之一
  - "add_principle"：添加核心原则
  - "add_prohibition"：添加禁止事项
  - "add_requirement"：添加具体要求
- `new_rule`: 规则的简短描述（10-30字）
- `rationale`: 更新理由（20-50字）

请输出JSON格式的更新建议。"""

        try:
            # Generate using Grok
            response = self.client.chat.completions.create(
                model=self.config["model"],
                messages=[{"role": "system", "content": prompt}],
                response_format={"type": "json_object"},
            )

            content = response.choices[0].message.content
            result_text = content.strip() if content else ""
            result = json.loads(result_text)

            # Extract key metrics
            update_type = result.get("update_type", "add_principle")
            new_rule = result.get("new_rule", "")
            rationale = result.get("rationale", "")

            # Update Writer Skill file
            new_version = self.memory.update_writer_skill(result)

            # Log node execution
            self.memory.log_node_execution(section_title, "curator", result)

            print(f"📚 [{section_title}] Curator更新Skill: v{new_version}")
            print(f"   类型: {update_type}")
            print(f"   规则: {new_rule}")

            # Increment iteration count
            current_iteration = state.get("iteration", 1)
            new_iteration = current_iteration + 1

            return {
                **state,
                "curator_result": result,
                "new_skill_version": new_version,
                "iteration": new_iteration,
            }

        except Exception as e:
            print(f"❌ [{section_title}] Curator更新失败: {e}")

            # Still increment iteration count to prevent infinite loop
            current_iteration = state.get("iteration", 1)
            new_iteration = current_iteration + 1

            return {
                **state,
                "curator_result": {
                    "update_type": "error",
                    "new_rule": "",
                    "rationale": f"更新失败: {str(e)}",
                },
                "iteration": new_iteration,
                "error": str(e),
            }
