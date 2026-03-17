import json
import threading
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from deepagents import create_deep_agent
from deepagents.backends import FilesystemBackend
from subagents_config_v4 import SUBAGENTS_LIST_V4
from memory_manager_v4 import MemoryManagerV4
from config import SMART_MODEL, MAX_ITERATIONS

# 初始化
memory = MemoryManagerV4("./memory")
backend = FilesystemBackend(root_dir="./", virtual_mode=False)
print_lock = threading.Lock()

def create_sop_agent():
    """创建主 Agent"""
    agent = create_deep_agent(
        model=f"openai:{SMART_MODEL}",
        system_prompt="你是 SOP 生成系统的协调者",
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
    skip_titles = []

    for section in data:
        title = section.get("section_title", "")
        original = section.get("original_content", "")
        generated = section.get("generate_content", "")

        if title and title not in skip_titles and (original or generated):
            valid_sections.append(section)

    return valid_sections

def safe_print(msg: str):
    """线程安全的打印"""
    with print_lock:
        print(msg)

def extract_json_from_text(text: str) -> dict:
    """从文本中提取 JSON"""
    import re

    # 尝试提取 ```json ... ``` 代码块
    json_match = re.search(r'```json\s*(\{.*?\})\s*```', text, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except:
            pass

    # 尝试直接解析整个文本
    try:
        return json.loads(text)
    except:
        pass

    # 尝试找到第一个 { 到最后一个 }
    start = text.find('{')
    end = text.rfind('}')
    if start != -1 and end != -1:
        try:
            return json.loads(text[start:end+1])
        except:
            pass

    return None

def process_section_worker(agent, section: dict):
    """处理单个章节"""
    section_title = section.get("section_title", "")
    original_content = section.get("original_content", "")
    generate_content = section.get("generate_content", "")

    safe_print(f"\n{'='*70}")
    safe_print(f"📝 开始处理: {section_title}")
    safe_print(f"{'='*70}")

    try:
        # 加载历史规则和模板
        rules = memory.load_rules(section_title)
        sop_template = memory.load_sop_template(section_title)

        iteration = 0
        final_score = 0
        final_sop_content = ""

        while iteration < MAX_ITERATIONS:
            iteration += 1
            safe_print(f"\n🔄 迭代 {iteration}/{MAX_ITERATIONS}")

            # Step 1: Writer 生成 SOP
            safe_print("  ├─ 📝 Writer 生成 SOP...")
            writer_prompt = f"""
请为章节"{section_title}"生成 SOP。

【验证方案】
{original_content[:1000]}

【GLP 报告参考】
{generate_content[:1000]}

【历史规则】
{json.dumps(rules, ensure_ascii=False, indent=2)[:500]}

请按照你的 system prompt 输出 JSON 格式的结果。
"""
            writer_result = agent.invoke({"messages": [{"role": "user", "content": f"@writer {writer_prompt}"}]})

            # 提取 writer 输出
            writer_output = ""
            if writer_result and "messages" in writer_result:
                for msg in writer_result["messages"]:
                    if hasattr(msg, 'content'):
                        writer_output += str(msg.content) + "\n"

            writer_json = extract_json_from_text(writer_output)
            if not writer_json:
                safe_print(f"  ├─ ⚠️  Writer 未返回有效 JSON，使用原始输出")
                sop_content = writer_output
                cited_rules = []
            else:
                sop_content = writer_json.get("sop_content", writer_output)
                cited_rules = writer_json.get("cited_rule_ids", [])

            safe_print(f"  ├─ ✅ Writer 完成，引用规则: {cited_rules}")

            # Step 2: Simulator 盲测
            safe_print("  ├─ 🧪 Simulator 盲测...")
            simulator_prompt = f"""
请盲测以下 SOP：

{sop_content[:2000]}

请按照你的 system prompt 输出 JSON 格式的结果。
"""
            simulator_result = agent.invoke({"messages": [{"role": "user", "content": f"@simulator {simulator_prompt}"}]})

            simulator_output = ""
            if simulator_result and "messages" in simulator_result:
                for msg in simulator_result["messages"]:
                    if hasattr(msg, 'content'):
                        simulator_output += str(msg.content) + "\n"

            safe_print(f"  ├─ ✅ Simulator 完成")

            # Step 3: Reviewer 审核
            safe_print("  ├─ 🔍 Reviewer 审核...")
            reviewer_prompt = f"""
请审核 Simulator 的输出。

【Simulator 输出】
{simulator_output[:1500]}

【Ground Truth】
{generate_content[:1500]}

请按照你的 system prompt 输出 JSON 格式的评分结果。
"""
            reviewer_result = agent.invoke({"messages": [{"role": "user", "content": f"@reviewer {reviewer_prompt}"}]})

            reviewer_output = ""
            if reviewer_result and "messages" in reviewer_result:
                for msg in reviewer_result["messages"]:
                    if hasattr(msg, 'content'):
                        reviewer_output += str(msg.content) + "\n"

            reviewer_json = extract_json_from_text(reviewer_output)
            if not reviewer_json:
                safe_print(f"  ├─ ⚠️  Reviewer 未返回有效 JSON，默认评分 3")
                score = 3.0
            else:
                score = float(reviewer_json.get("score", 3.0))

            safe_print(f"  ├─ ✅ Reviewer 评分: {score}/5")

            final_score = score
            final_sop_content = sop_content

            # 如果评分 >= 4，通过
            if score >= 4:
                safe_print(f"  └─ ✅ 评分通过，结束迭代")
                break

            # 评分 < 4，调用 Reflector 和 Curator
            safe_print(f"  ├─ 🔬 Reflector 诊断...")
            reflector_prompt = f"""
请分析失败原因。

【Writer 输出】
{sop_content[:1000]}

【Cited Rules】
{cited_rules}

【Reviewer 评分】
{json.dumps(reviewer_json, ensure_ascii=False, indent=2)[:1000]}

请按照你的 system prompt 输出 JSON 格式的诊断结果。
"""
            reflector_result = agent.invoke({"messages": [{"role": "user", "content": f"@reflector {reflector_prompt}"}]})

            reflector_output = ""
            if reflector_result and "messages" in reflector_result:
                for msg in reflector_result["messages"]:
                    if hasattr(msg, 'content'):
                        reflector_output += str(msg.content) + "\n"

            safe_print(f"  ├─ ✅ Reflector 完成")

            # Curator 更新规则
            safe_print(f"  ├─ 📚 Curator 更新规则...")
            curator_prompt = f"""
请更新章节"{section_title}"的规则。

【Reflector 诊断】
{reflector_output[:1500]}

请按照你的 system prompt 输出 JSON 格式的操作结果，并使用 write_file 更新规则文件。
"""
            curator_result = agent.invoke({"messages": [{"role": "user", "content": f"@curator {curator_prompt}"}]})

            safe_print(f"  └─ ✅ Curator 完成")

            # 重新加载规则
            rules = memory.load_rules(section_title)

        # 保存结果
        with print_lock:
            memory.log_audit({
                "experiment_type": "LC-MS_MS结构化验证",
                "section_title": section_title,
                "version": "V5_Explicit",
                "sop_id": str(section.get("id", "")),
                "iterations": iteration,
                "quality_assessment": {
                    "is_passed": final_score >= 4,
                    "score": final_score,
                    "feedback": f"迭代 {iteration} 次后完成"
                }
            })

            if final_score >= 4:
                memory.save_sop_template(section_title, {
                    "template": final_sop_content,
                    "score": final_score,
                    "iterations": iteration
                })

        safe_print(f"\n✅ {section_title} 处理完成，最终评分: {final_score}/5")
        return True

    except Exception as e:
        safe_print(f"\n❌ {section_title} 失败: {str(e)}")
        import traceback
        safe_print(traceback.format_exc())
        return False

def main():
    """主函数"""
    safe_print("\n" + "="*70)
    safe_print("🚀 SOP 生成系统 V5 - 显式调用 Subagents")
    safe_print("="*70 + "\n")

    # 加载数据
    report_data = load_report_data("report_all.json")
    sections = filter_sections(report_data)
    safe_print(f"✓ 找到 {len(sections)} 个有效章节\n")

    # 创建 Agent
    agent = create_sop_agent()

    # 测试单个章节
    test_section = sections[0]
    safe_print(f"🧪 测试章节: {test_section['section_title']}\n")
    process_section_worker(agent, test_section)

    safe_print("\n" + "="*70)
    safe_print("✅ 测试完成")
    safe_print("="*70)

if __name__ == "__main__":
    main()
