import json
import os
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.append(str(PROJECT_ROOT))

from deepagent_sop.core.main_agent import MainAgent
from deepagent_sop.core.config import Config

def cold_start_workflow(json_path: str, experiment_type: str, limit: int = 5):
    """
    通过 JSON 数据包进行冷启动引导
    """
    if not os.path.exists(json_path):
        print(f"Error: 找不到数据文件 {json_path}")
        return

    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 过滤掉无法处理的项目
    valid_items = [
        item for item in data 
        if item.get("is_process") and item.get("original_content") and item.get("generate_content")
    ]
    
    print(f"检测到有效章节: {len(valid_items)} 个。将处理前 {limit} 个进行冷启动注入...")

    main_agent = MainAgent(
        llm_config={
            "api_provider": Config.get_llm_provider(),
            "temperature": 0.2,
            "max_tokens": 4096,
        },
        memory_path="deepagent_sop/memory"
    )

    for i, item in enumerate(valid_items[:limit]):
        chapter_id = item.get("section_title", f"Unknown_{i}")
        original = item.get("original_content", "").strip()
        target = item.get("generate_content", "").strip()

        print(f"\n[任务 {i+1}/{limit}] 正在处理章节: {chapter_id}")
        
        # 构造执行参数
        params = {
            "original_content": original,
            "target_generate_content": target,
            "section_title": chapter_id,
            "experiment_type": experiment_type
        }

        try:
            # 1. 查询当前已存在的规则
            existing_rules = main_agent.memory_manager.query_rules(experiment_type, chapter_id)
            params["memory"] = "\n".join(existing_rules)

            # 2. 调用子 Agent 流转
            print(f" -> [Writer] 正在逆向提取 SOP...")
            writer_res = main_agent._execute_subagent("writer", params)
            current_sop = writer_res.get("current_sop", "")
            
            print(f" -> [Simulator/Reviewer] 正在盲测验收...")
            params["current_sop"] = current_sop
            sim_res = main_agent._execute_subagent("simulator", params)
            
            params["simulated_generate_content"] = sim_res.get("simulated_generate_content", "")
            rev_res = main_agent._execute_subagent("reviewer", params)
            
            is_passed = rev_res.get("is_passed", False)
            print(f" -> 验收结论: {'✅ 通过' if is_passed else '❌ 打回'}")

            # 3. 学习与沉淀
            if is_passed:
                print(f" -> [Storage] 正在将 SOP 存入专属模板库...")
                main_agent.memory_manager.save_sop(
                    experiment_type=experiment_type,
                    chapter_id=chapter_id,
                    sop_content=current_sop,
                    quality_score=5.0
                )
            
            # 始终尝试从本次运行中提炼规则 (Reflector -> Curator)
            print(f" -> [Learning] 正在提炼与更新 Rules...")
            trajectory = [
                {"step": 1, "agent": "writer", "type": "gen", "output": writer_res},
                {"step": 2, "agent": "simulator", "type": "sim", "output": sim_res},
                {"step": 3, "agent": "reviewer", "type": "rev", "output": rev_res}
            ]
            
            insights_res = main_agent.reflector.extract(trajectory, experiment_type=experiment_type)
            insights = insights_res.get("insights", [])
            print(f" -> [Insights] 提取到 {len(insights)} 条洞察项")
            if insights:
                print(f"    - 示例: {insights[0].get('bullet', '')[:50]}...")

            curator_res = main_agent.curator.extract_operations(
                current_playbook="\n".join(existing_rules),
                insights=insights,
                question_context=f"章节: {chapter_id} 的标准化映射逻辑"
            )
            
            ops = curator_res.get("operations", [])
            print(f" -> [Curator] 决策生成的 Operations: {len(ops)} 个")
            if ops:
                for op in ops:
                    print(f"    - {op.get('type')}: {op.get('content', '')[:50]}...")
            
            if ops:
                main_agent.memory_manager.apply_rules_operations(experiment_type, chapter_id, ops)
                print(f" -> 规则库已同步落盘")

            # 4. 记录审计
            main_agent.memory_manager.log_iteration({
                "experiment_type": experiment_type,
                "chapter_id": chapter_id,
                "version": "ColdStart_V1",
                "sop": current_sop if is_passed else "N/A (验收未通过)",
                "quality_assessment": {
                    "is_passed": is_passed,
                    "score": 5.0 if is_passed else 2.0,
                    "feedback": rev_res.get("feedback", "")
                },
                "curation": {"operations_added": len(ops)},
                "metrics": {"process_time": "N/A"}
            })

        except Exception as e:
            print(f" 处理章节 {chapter_id} 时发生错误: {e}")
            continue

    print("\n" + "="*50)
    print("冷启动注入任务执行完毕！")
    print("="*50)

if __name__ == "__main__":
    DATA_PATH = os.path.join("data", "report_all.json")
    # 虽然已在 MemoryManager 增加脱敏，但代码层也建议使用标准命名
    EXPERIMENT = "LC-MS_MS验证项目" 
    cold_start_workflow(DATA_PATH, EXPERIMENT, limit=3)
