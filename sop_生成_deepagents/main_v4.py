import json
import threading
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from deepagents import create_deep_agent
from deepagents.backends import FilesystemBackend
from subagents_config_v4 import SUBAGENTS_LIST_V4
from memory_manager_v4 import MemoryManagerV4
from config import SMART_MODEL

# 初始化
memory = MemoryManagerV4("./memory")
backend = FilesystemBackend(root_dir="./", virtual_mode=False)
print_lock = threading.Lock()

# 主 Agent 提示词
MAIN_SYSTEM_PROMPT = """你是 SOP 生成 system 的主控 Agent。

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
    # 如果需要跳过某些标题，可以添加到 skip_titles
    skip_titles = []

    for section in data:
        title = section.get("section_title", "")
        original = section.get("original_content", "")
        generated = section.get("generate_content", "")

        # 只要有任何参考内容（原始或生成），且标题有效，就处理
        if title and title not in skip_titles and (original or generated):
            valid_sections.append(section)

    return valid_sections

def parse_sop_content(content: str) -> dict:
    """从 Markdown 内容中提取核心原则和具体示例"""
    import re
    
    core_principles = []
    examples = []
    
    # 策略 1: 尝试从 Markdown 中的 JSON 代码块提取
    json_match = re.search(r'```json\s*(\{.*?\})\s*```', content, re.DOTALL)
    if json_match:
        try:
            data = json.loads(json_match.group(1))
            core_principles = data.get("core_principles", [])
            examples = data.get("examples", [])
        except:
            pass
            
    # 策略 2: 如果策略 1 没结果，使用正则匹配特定章节
    if not core_principles:
        principles_match = re.search(r'## (?:核心原则|注意事项)\s*(.*?)(?=\n##|$)', content, re.DOTALL)
        if principles_match:
            lines = principles_match.group(1).strip().split('\n')
            core_principles = [re.sub(r'^[\s\-\*\d\.]+[\s\.]*', '', line).strip() for line in lines if line.strip()]

    if not examples:
        examples_match = re.search(r'## 示例\s*(.*?)(?=\n##|$)', content, re.DOTALL)
        if examples_match:
            examples = [examples_match.group(1).strip()]

    return {
        "core_principles": core_principles,
        "examples": examples
    }

def safe_print(msg: str):
    """线程安全的打印"""
    with print_lock:
        print(msg)

def process_section_worker(agent, section: dict):
    """处理单个章节的工作函数"""
    section_title = section.get("section_title", "")
    original_content = section.get("original_content", "")
    generate_content = section.get("generate_content", "")

    safe_print(f"📝 开始处理: {section_title}...")

    try:
        # 加载历史规则和模板
        rules = memory.load_rules(section_title)
        sop_template = memory.load_sop_template(section_title)

        user_message = f"""
请为以下章节生成 SOP：

【章节名称】
{section_title}

【验证方案（original_content）】
{original_content[:1500]}

【GLP 报告参考（generate_content）】
{generate_content[:1500]}

【历史规则】
{json.dumps(rules, ensure_ascii=False, indent=2)}

【历史模板】
{json.dumps(sop_template, ensure_ascii=False, indent=2)}

【任务要求】
1. writer 生成 SOP（包含 ## 核心原则 和 ## 示例）
2. simulator 盲测
3. reviewer 审核（评分 >= 4 通过）
"""
        result = agent.invoke({"messages": [{"role": "user", "content": user_message}]})

        # 提取结果
        final_sop = ""
        quality_score = 3.0
        
        if result and "messages" in result:
            for msg in result["messages"]:
                if hasattr(msg, 'content') and isinstance(msg.content, str):
                    content = msg.content
                    final_sop += content + "\n"
                    
                    if "评分" in content or "score" in content.lower():
                        import re
                        score_match = re.search(r'[评分:：]\s*(\d+)', content)
                        if score_match:
                            quality_score = float(score_match.group(1))

        # 记录审计日志 (MemoryManagerV4.log_audit 内部如果不是线程安全的，这里需要锁)
        # 假设 log_audit 是直接写文件，我们需要保护它
        with print_lock: # 复用打印锁作为简单的文件锁
            memory.log_audit({
                "experiment_type": "LC-MS_MS结构化验证",
                "section_title": section_title,
                "version": "V4_Concurrent",
                "sop_id": str(section.get("id", "")),
                "quality_assessment": {
                    "is_passed": quality_score >= 4,
                    "score": quality_score,
                    "feedback": "并发处理完成"
                }
            })

            # 保存 SOP 模板（如果通过）
            if quality_score >= 4:
                parsed_data = parse_sop_content(final_sop)
                memory.save_sop_template(section_title, {
                    "template": final_sop,
                    "core_principles": parsed_data["core_principles"],
                    "examples": parsed_data["examples"]
                })

        safe_print(f"✅ {section_title} 处理完成，评分: {quality_score}")
        return True

    except Exception as e:
        safe_print(f"❌ {section_title} 失败: {str(e)}")
        return False

def main():
    """主函数"""
    safe_print("\n" + "="*70)
    safe_print("🚀 SOP 生成系统 V4 - 并发处理模式")
    safe_print("="*70 + "\n")

    # 加载数据
    report_data = load_report_data("report_all.json")
    sections = filter_sections(report_data)
    safe_print(f"✓ 找到 {len(sections)} 个有效章节")

    # 创建 Agent
    agent = create_sop_agent()

    # 最大并发数
    MAX_WORKERS = 5
    safe_print(f"⚙️  配置并发线程数: {MAX_WORKERS}\n")

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(process_section_worker, agent, section): section for section in sections}
        
        for future in as_completed(futures):
            section = futures[future]
            try:
                future.result()
            except Exception as e:
                safe_print(f"⚠️  线程异常: {section.get('section_title')} -> {e}")

    safe_print("\n" + "="*70)
    safe_print("✅ 并发批量处理程序运行结束")
    safe_print("="*70)

if __name__ == "__main__":
    main()
