"""
SOP 生成系统 V4 - 分章节处理版本
核心改进：
1. 从 report_all.json 读取数据
2. 分章节处理
3. 三层输出：audit_logs / rules / sop_templates
"""

import json
from pathlib import Path
from deepagents import create_deep_agent
from deepagents.backends import FilesystemBackend
from subagents_config_v4 import SUBAGENTS_LIST_V4
from memory_manager_v4 import MemoryManagerV4
from config import SMART_MODEL

# 初始化
memory = MemoryManagerV4("./memory")
backend = FilesystemBackend(root_dir="./")

# 主 Agent 提示词
MAIN_SYSTEM_PROMPT = """你是 SOP 生成系统的主控 Agent。

## 任务
为每个章节生成高质量的 SOP。

## 工作流程
1. writer 生成 SOP
2. simulator 盲测
3. reviewer 审核评分
4. 如果评分 < 4：
   - reflector 诊断
   - curator 更新规则
   - 迭代改进（最多 3 次）

## 输出要求
- 每次迭代后记录审计日志
- Curator 更新章节规则
- 最终保存 SOP 模板
"""

def create_sop_agent():
    """创建主 Agent"""
    agent = create_deep_agent(
        model=f"openai:{SMART_MODEL}",
        system_prompt=MAIN_SYSTEM_PROMPT,
        subagents=SUBAGENTS_LIST_V4,
        backend=backend
    )
    return agent

def load_report_data(json_path: str = "report_all.json") -> list:
    """加载 report_all.json"""
    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)

def filter_sections(data: list) -> list:
    """过滤有效章节"""
    valid_sections = []
    skip_titles = ["目录", "验证报告", "GLP遵从性声明和签字页", "质量保证声明"]

    for section in data:
        title = section.get("section_title", "")
        original = section.get("original_content", "")
        generated = section.get("generate_content", "")

        if title and title not in skip_titles and (original or generated):
            valid_sections.append(section)

    return valid_sections

def process_section(agent, section: dict, iteration: int = 1) -> dict:
    """处理单个章节"""
    section_title = section.get("section_title", "")
    original_content = section.get("original_content", "")
    generate_content = section.get("generate_content", "")

    print(f"\n{'='*70}")
    print(f"📝 处理章节: {section_title} (迭代 {iteration})")
    print('='*70)

    # 加载历史规则和模板
    rules = memory.load_rules(section_title)
    sop_template = memory.load_sop_template(section_title)

    user_message = f"""
请为以下章节生成 SOP：

【章节名称】
{section_title}

【验证方案（original_content）】
{original_content[:1000]}

【GLP 报告参考（generate_content）】
{generate_content[:1000]}

【历史规则】
{json.dumps(rules, ensure_ascii=False, indent=2)}

【历史模板】
{json.dumps(sop_template, ensure_ascii=False, indent=2)}

【任务要求】
1. writer 生成 SOP
2. simulator 盲测
3. reviewer 审核（评分 >= 4 通过）
4. 如评分 < 4：reflector 诊断 + curator 更新规则
"""

    result = agent.invoke({"messages": [{"role": "user", "content": user_message}]})

    # 提取结果
    final_sop = ""
    quality_score = 0.0
    feedback = ""

    if result and "messages" in result:
        for msg in result["messages"]:
            if hasattr(msg, 'content') and isinstance(msg.content, str):
                final_sop += msg.content + "\n"

    return {
        "section_title": section_title,
        "sop_content": final_sop,
        "quality_score": quality_score,
        "feedback": feedback
    }

def main():
    """主函数"""
    print("\n" + "="*70)
    print("🚀 SOP 生成系统 V4 - 分章节处理")
    print("="*70 + "\n")

    # 加载数据
    print("📂 加载 report_all.json...")
    report_data = load_report_data("report_all.json")
    sections = filter_sections(report_data)
    print(f"✓ 找到 {len(sections)} 个有效章节\n")

    # 创建 Agent
    agent = create_sop_agent()

    # 处理所有章节
    for i, section in enumerate(sections, 1):
        section_title = section.get("section_title", "")

        try:
            # 处理章节
            result = process_section(agent, section)

            # 记录审计日志
            memory.log_audit({
                "experiment_type": "LC-MS_MS结构化验证",
                "section_title": section_title,
                "version": "V4",
                "sop_id": str(section.get("id", "")),
                "quality_assessment": {
                    "is_passed": result["quality_score"] >= 4,
                    "score": result["quality_score"],
                    "feedback": result["feedback"]
                }
            })

            # 保存 SOP 模板（如果通过）
            if result["quality_score"] >= 4:
                memory.save_sop_template(section_title, {
                    "template": result["sop_content"],
                    "core_principles": [],
                    "examples": []
                })

            print(f"✅ {section_title} 处理完成\n")

        except Exception as e:
            print(f"❌ {section_title} 处理失败: {e}\n")
            continue

    print("\n" + "="*70)
    print("✅ 批量处理完成")
    print("="*70)
    print(f"""
输出位置：
- 审计日志: memory/audit_logs/
- 规则库: memory/rules/
- SOP 模板: memory/sop_templates/
""")

if __name__ == "__main__":
    main()
