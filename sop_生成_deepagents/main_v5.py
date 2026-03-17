"""
SOP生成系统 V5 - 方案B：4个Agent + SQLite + 多模型
"""

import json
import asyncio
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

# 主Agent提示词
MAIN_SYSTEM_PROMPT = """你是SOP生成系统主控Agent。

## 工作流程
1. writer生成SOP
2. simulator盲测
3. super_reviewer评分+诊断（评分>=4通过）
4. 如果不通过：curator更新规则，迭代改进（最多3次）

## 输出要求
- 记录审计日志
- 更新规则库
- 保存SOP模板
"""

def extract_json(text: str) -> dict:
    """简单JSON提取（备用）"""
    try:
        # 尝试直接解析
        return json.loads(text)
    except:
        # 提取```json代码块
        import re
        match = re.search(r'```json\s*(\{.*?\})\s*```', text, re.DOTALL)
        if match:
            return json.loads(match.group(1))
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
    print(f"📝 处理: {section_title}")
    
    try:
        rules = memory.load_rules(section_title)
        sop_template = memory.load_sop_template(section_title)
        
        user_message = f"""
请为以下章节生成SOP：

【章节】{section_title}
【验证方案】{section.get("original_content", "")[:1500]}
【GLP参考】{section.get("generate_content", "")[:1500]}
【历史规则】{json.dumps(rules, ensure_ascii=False)}
【历史模板】{json.dumps(sop_template, ensure_ascii=False)}

要求：writer生成 → simulator盲测 → super_reviewer评分（>=4通过）
"""
        
        result = agent.invoke({"messages": [{"role": "user", "content": user_message}]})
        
        # 提取结果
        final_sop = ""
        score = 3.0
        
        if result and "messages" in result:
            for msg in result["messages"]:
                if hasattr(msg, 'content'):
                    content = str(msg.content)
                    final_sop += content + "\n"
                    
                    # 提取评分
                    if "score" in content.lower():
                        import re
                        m = re.search(r'[评分:：score]\s*[:\s]*(\d+)', content, re.I)
                        if m:
                            score = float(m.group(1))
        
        # 记录审计
        memory.log_audit({
            "experiment_type": "LC-MS_MS",
            "section_title": section_title,
            "version": "V5",
            "sop_id": str(section.get("id", "")),
            "quality_assessment": {"is_passed": score >= 4, "score": score}
        })
        
        # 保存模板
        if score >= 4:
            memory.save_sop_template(section_title, {
                "template": final_sop,
                "core_principles": [],
                "examples": []
            })
        
        print(f"✅ {section_title} 完成，评分: {score}")
        return True
        
    except Exception as e:
        print(f"❌ {section_title} 失败: {e}")
        return False

def main():
    """主函数"""
    print("\n" + "="*70)
    print("🚀 SOP生成系统 V5 - 4个Agent + SQLite + 多模型")
    print("="*70 + "\n")
    
    # 加载数据
    report_data = load_report_data("report_all.json")
    sections = filter_sections(report_data)
    print(f"✓ 找到 {len(sections)} 个有效章节\n")
    
    # 创建Agent
    agent = create_sop_agent()
    
    # 并发处理
    MAX_WORKERS = 3
    print(f"⚙️  并发线程数: {MAX_WORKERS}\n")
    
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(process_section, agent, s): s for s in sections}
        
        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                print(f"⚠️  线程异常: {e}")
    
    print("\n" + "="*70)
    print("✅ V5处理完成")
    print("="*70)

if __name__ == "__main__":
    main()
