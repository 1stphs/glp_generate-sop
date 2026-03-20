import asyncio
import json
import logging
import os
import sys
from typing import Any, List, Dict
from string import Template

# 尝试导入现有工具，如果失败则提供 Mock 逻辑
try:
    from tools.llm_client import chat_json
except ImportError:
    chat_json = None

# --- 配置区 ---
LLM_MODEL = os.getenv("GENERATE_CONTENT_LLM_MODEL", "grok-4-fast-non-reasoning")
MAX_ATTEMPTS = 3

# --- Prompt 模板 (源自 generate_content_registry.py) ---
SYSTEM_PROMPT_TEMPLATE = """你是一位资深的 GLP（良好实验室规范）临床前研究主任。请根据提供的章节结构、验证方案原文、Excel 数据、SOP 指导要求以及实验基本信息（project_info），撰写指定章节的验证报告内容。

**核心要求：**

1. **严格遵循 SOP**:
* 必须逐字研读提供的 [SOP] 指导流程。
* 如果 SOP 要求简略输出（如仅输出编号、日期、结论等），则直接输出结果，严禁废话。
* 如果 SOP 要求详细分析，则需结合提供的 Excel 数据进行专业科学的描述，确保结论有据可查。

2. **JSON 格式返回**:
* 字段要求：
* `section_id`: 必须与输入的章节 ID 完全一致。
* `generate_content`: 仅包含遵从 SOP 输出的章节具体的正文内容。

3. **统一要求**:
* `generate_content`不要输出章节标题，只输出正文内容
* 涉及数据时需要详细阅读 excel_parsed，不能只参考方案数据。
* 涉及的数学公式输出时，必须使用标准的 LaTeX 数学公式格式输出

**SOP要求: **
$sop_content"""

USER_PROMPT_TEMPLATE = """请根据以下内容生成报告章节正文：

【章节数据】
$section_json

【基本信息 project_info】
$project_info_json

请仅输出 JSON 对象，字段为 section_id 和 generate_content。"""

# --- 核心函数 ---

async def call_llm(messages: List[Dict[str, str]], model: str = LLM_MODEL):
    """封装 LLM 调用逻辑"""
    if chat_json:
        try:
            return await asyncio.to_thread(
                chat_json, 
                messages=messages, 
                model=model, 
                temperature=0.1,
                max_tokens=8000
            )
        except Exception as e:
            print(f"LLM Call Error: {e}")
            raise e
    else:
        # 如果环境不可用，打印提示
        print("Error: tools.llm_client.chat_json not available.")
        return {"section_id": "error", "generate_content": "LLM client missing."}

def normalize_llm_payload(payload: Any, expected_section_id: str) -> Dict[str, str]:
    """校验并格式化 LLM 返回值"""
    record = payload
    if isinstance(payload, dict):
        if "data" in payload: record = payload["data"]
        elif "result" in payload: record = payload["result"]
    
    section_id = str(record.get("section_id", "")).strip()
    if section_id != str(expected_section_id).strip():
        print(f"Warning: section_id mismatch! Expected {expected_section_id}, got {section_id}")
    
    return {
        "section_id": expected_section_id,
        "generate_content": str(record.get("generate_content", "")).strip()
    }

async def generate_single_section(project_info: Any, section_row: Dict[str, Any]) -> Dict[str, str]:
    """生成单个章节内容"""
    section_id = section_row.get("id")
    sop_content = section_row.get("sop", "")
    
    # 1. 准备 System Prompt (替换 SOP 内容)
    system_prompt = Template(SYSTEM_PROMPT_TEMPLATE).safe_substitute(sop_content=sop_content)
    
    # 2. 准备 User Prompt
    section_payload = {
        "id": section_id,
        "section_title": section_row.get("section_title", ""),
        "original_content": section_row.get("original_content", ""),
        "excel_parsed": section_row.get("excel_parsed", [])
    }
    
    user_prompt = Template(USER_PROMPT_TEMPLATE).safe_substitute(
        section_json=json.dumps(section_payload, ensure_ascii=False, indent=2),
        project_info_json=json.dumps(project_info, ensure_ascii=False, indent=2)
    )
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]
    
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            payload = await call_llm(messages)
            return normalize_llm_payload(payload, section_id)
        except Exception as e:
            if attempt == MAX_ATTEMPTS:
                return {
                    "section_id": section_id,
                    "generate_content": f"ERROR: Generation failed after {MAX_ATTEMPTS} attempts. {e}"
                }
            await asyncio.sleep(1)

async def run_batch_generation(project_info_path: str, sections_data_path: str, output_path: str):
    """批量处理"""
    # 加载数据
    try:
        with open(project_info_path, 'r', encoding='utf-8') as f:
            project_info = json.load(f)
        with open(sections_data_path, 'r', encoding='utf-8') as f:
            sections = json.load(f)
    except Exception as e:
        print(f"Load Data Error: {e}")
        return

    print(f"[*] Loaded {len(sections)} sections. Model: {LLM_MODEL}")
    
    # 因为 LLM 可能会有并发限制，建议分批或控制并发
    semaphore = asyncio.Semaphore(5) # 限制 5 个并发

    async def sem_task(row):
        async with semaphore:
            return await generate_single_section(project_info, row)

    tasks = [sem_task(s) for s in sections]
    results = await asyncio.gather(*tasks)
    
    # 保存结果
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"[+] All done! Results saved to: {output_path}")

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python generate_report.py <project_info.json> <sections_data.json> <output.json>")
        sys.exit(1)
    
    p_info = sys.argv[1]
    s_data = sys.argv[2]
    out = sys.argv[3]
    
    asyncio.run(run_batch_generation(p_info, s_data, out))
