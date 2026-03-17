"""
SOP生成系统 V5 - 方案B：4个Agent + SQLite + 多模型
"""

import json
import re
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from deepagents import create_deep_agent
from deepagents.backends import FilesystemBackend
from subagents_config_v5 import SUBAGENTS_LIST_V5
from memory_manager_v5 import MemoryManagerV5
from config import WRITER_MODEL

# 初始化
memory = MemoryManagerV5("./memory/sop_memory.db")
backend = FilesystemBackend(root_dir="./", virtual_mode=False)

# 主Agent提示词 - 负责调度
MAIN_SYSTEM_PROMPT = """你是SOP生成系统主控Agent。你的目标是通过迭代生成的SOP达到高质量标准(评分>=4)。

## 工作流程
1. 调用 `writer` 生成初始 SOP。
2. 调用 `simulator` 对生成的 SOP 进行盲测。
3. 调用 `super_reviewer` 对测试结果进行评分和根因诊断。
4. 如果 `super_reviewer` 的评分 < 4：
   - 调用 `curator` 提炼改进规则。
   - 携带新规则再次调用 `writer` 进行迭代生成。
5. 当评分 >= 4 或达到最大迭代次数（3次）时结束。

## 注意事项
- 仅通过子代理执行具体任务。
- 最终输出应包含最终修订后的 SOP 内容。
"""

def extract_json(text: str) -> dict:
    """提取 JSON 内容"""
    if not text: return {}
    try:
        return json.loads(text)
    except:
        match = re.search(r'```json\s*(\{.*?\})\s*```', text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except:
                pass
        return {}

def create_sop_agent():
    """创建主Agent"""
    return create_deep_agent(
        model=f"openai:{WRITER_MODEL}",
        system_prompt=MAIN_SYSTEM_PROMPT,
        subagents=SUBAGENTS_LIST_V5,
        backend=backend
    )

def load_report_data(json_path: str = "report_all.json") -> list:
    """加载report_all.json"""
    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)

def filter_sections(data: list) -> list:
    """过滤有效章节"""
    return [s for s in data if s.get("section_title") and 
            (s.get("original_content") or s.get("generate_content"))]

def process_section(agent, section: dict):
    """处理单个章节"""
    section_title = section.get("section_title", "")
    print(f"📝 启动章节处理: {section_title}")
    
    try:
        # 加载历史上下文
        history_rules = memory.load_rules(section_title)
        history_template = memory.load_sop_template(section_title)
        
        user_message = f"""
请开始为以下章节生成/优化 SOP：

【章节名称】：{section_title}
【验证方案 (Original Content)】：
{section.get("original_content", "无")[:2000]}

【GLP 报告参考 (Generate Content)】：
{section.get("generate_content", "无")[:2000]}

【当前历史规则】：
{json.dumps(history_rules, ensure_ascii=False, indent=2)}

【当前 SOP 模板】：
{history_template.get("template", "尚未生成")}

请按照工作流程执行：生成 -> 盲测 -> 评分诊断 -> (必要时)提炼规则并重试。
"""
        
        result = agent.invoke({"messages": [{"role": "user", "content": user_message}]})
        
        # 解析执行轨迹
        final_sop = ""
        current_score = 0.0
        final_rules = history_rules
        
        if result and "messages" in result:
            # 倒序查找最后一轮有效的环节
            for msg in reversed(result["messages"]):
                # 提取最终 SOP (来自 writer)
                if getattr(msg, "name", "") == "writer" and not final_sop:
                    final_sop = str(msg.content).strip()
                
                # 提取评分 (来自 super_reviewer)
                if getattr(msg, "name", "") == "super_reviewer" and current_score == 0.0:
                    review_data = extract_json(str(msg.content))
                    current_score = float(review_data.get("score", 0))
                    # 如果有新见解，可以记录，但在此流程中我们更关注 curator
                
                # 提取更新后的规则 (来自 curator)
                if getattr(msg, "name", "") == "curator":
                    curator_data = extract_json(str(msg.content))
                    new_rules = curator_data.get("rules", [])
                    if new_rules:
                        # 合并新旧规则（实际应根据 rule_id 或内容去重，此处简单追加）
                        final_rules = history_rules + new_rules
        
        # 如果没有明确找到 writer 的消息，则尝试从主 Agent 的回复中寻找
        if not final_sop and len(result["messages"]) > 0:
            final_sop = str(result["messages"][-1].content).strip()

        # 记录审计日志
        memory.log_audit({
            "experiment_type": "LC-MS_MS结构化验证",
            "section_title": section_title,
            "version": "V5_Optimized",
            "sop_id": str(section.get("id", "")),
            "quality_assessment": {
                "is_passed": current_score >= 4,
                "score": current_score,
                "feedback": f"最终得分: {current_score}"
            }
        })
        
        # 无论是否通过，都保存最新的规则（Curator 的产物）
        if final_rules != history_rules:
            memory.save_rules_bundle(section_title, final_rules)
            
        # 只有在评分达标时才更新最终模板文件
        if current_score >= 4:
            memory.save_sop_template(section_title, {
                "template": final_sop,
                "core_principles": [], # 可根据需要从 SOP 中正则提取原则
                "examples": []
            })
            print(f"✅ {section_title} 成功过审，评分: {current_score}")
        else:
            print(f"⚠️  {section_title} 未达标，最高评分: {current_score}")

        return True
        
    except Exception as e:
        import traceback
        print(f"❌ {section_title} 处理异常: {e}")
        traceback.print_exc()
        return False

def main():
    """驱动程序"""
    print("\n" + "="*70)
    print("🚀 SOP 生成系统 V5 - 并发优化版 (SQLite + File Storage)")
    print("="*70 + "\n")
    
    # 加载测试数据
    report_data = load_report_data("report_all.json")
    sections = filter_sections(report_data)
    print(f"✓ 已加载 {len(sections)} 个待处理章节\n")
    
    # 初始化主 Agent
    agent = create_sop_agent()
    
    # 限制并发以保证线程安全和 Rate Limit
    MAX_WORKERS = 3
    print(f"⚙️  并发执行中 (Workers: {MAX_WORKERS})...\n")
    
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(process_section, agent, s): s for s in sections}
        
        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                print(f"⚠️  核心处理异常: {e}")
    
    print("\n" + "="*70)
    print("✨ 所有任务处理完毕")
    print("="*70)

if __name__ == "__main__":
    main()
