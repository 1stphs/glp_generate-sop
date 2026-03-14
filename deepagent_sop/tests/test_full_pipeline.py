import os
import sys
from pathlib import Path
import json

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.append(str(PROJECT_ROOT))

from deepagent_sop.core.config import Config
from deepagent_sop.core.main_agent import MainAgent


def test_full_pipeline():
    """测试整个记忆系统与大模型链路的导通"""
    
    print("=" * 60)
    print("DeepAgent SOP - 全链路记忆融合测试启动")
    print("=" * 60)

    # 1. 模拟业务环境约束
    experiment_type = "小分子模板"
    chapter_id = "16.2声明"
    
    # 2. 模拟真实传入内容
    user_query = f"为【{experiment_type}】实验类型中的『{chapter_id}』章节生成并验证标准SOP。"
    
    original_content = """
主要研究者：李四
测试机构：上海益诺思生物技术股份有限公司，上海浦东新区张江高科
签名日期：2026年3月14日
    """

    target_generate_content = """
------------------------------------------------------------------------------------------------------------------------------------------
|                            | 声明                                                                                                  |
------------------------------------------------------------------------------------------------------------------------------------------
| 本报告真实反映了实验原始数据。                                                                                                       |
|                                                                                                                                     |
|                                                                                                                                     |
|  主要研究者：    李四                                                                  日期： 2026年3月14日                             |
|                                                                                                                                     |
|                （上海益诺思生物技术股份有限公司）                                                                                      |
------------------------------------------------------------------------------------------------------------------------------------------
    """

    # 3. 构造下发给 Writer 的参数装配包
    params = {
        "original_content": original_content,
        "target_generate_content": target_generate_content,
        "section_title": chapter_id
    }

    print(f"当前配置 - 智能大脑模型: {Config.get_smart_llm_model()}")
    print(f"当前配置 - 极速校验模型: {Config.get_fast_llm_model()}")
    print("-" * 60)

    # 初始化主节点
    # 假装这是从前端自然语言解析出的结构。但由于我们需要强行注入 params 测试全流转，
    # 这里我们绕过用自然语言跑 main_agent.run，而是用类似白盒的打桩法：
    
    try:
        main_agent = MainAgent(
            llm_config={
                "api_provider": Config.get_llm_provider(),
                "temperature": 0.2,
                "max_tokens": 4096,
            },
            memory_path="deepagent_sop/memory"
        )
        
        # 为了展示真实学习过程，我们强行让主控台按如下路径调度：
        # Writer -> Simulator -> Reviewer
        current_state = {}
        
        # ----------------
        # 步骤 1：Writer 生成 SOP
        # ----------------
        print("\n[STEP 1] -> 激活 Writer Agent 进行 SOP 逆向抽取 (使用 Smart Model)")
        # 主查询，带出规则
        precise_memory = main_agent.memory_manager.query_rules(experiment_type, chapter_id)
        params["memory"] = "\n".join(precise_memory)
        params["experiment_type"] = experiment_type
        
        writer_result = main_agent._execute_subagent("writer", params)
        current_state.update(writer_result)
        
        print(f"📝 Writer 思考过程: {writer_result.get('reasoning', '无')[:100]}...")
        print("📝 Writer 提取的 Core Rules:")
        for r in writer_result.get("core_rules", []):
            print(f"  - {r}")
            
        # ----------------
        # 步骤 2：Simulator 盲测 SOP
        # ----------------
        print("\n[STEP 2] -> 激活 Simulator Agent 进行黑盒盲测 (使用 Fast Model)")
        params["current_sop"] = current_state.get("current_sop", "")
        sim_result = main_agent._execute_subagent("simulator", params)
        current_state.update(sim_result)
        
        print(f"🤖 Simulator 模拟作答:\n{sim_result.get('simulated_generate_content', '无')[:200]}...")
        
        # ----------------
        # 步骤 3：Reviewer 进行严密审查
        # ----------------
        print("\n[STEP 3] -> 激活 Reviewer Agent 进行差异排查 (使用 Fast Model)")
        params["simulated_generate_content"] = current_state.get("simulated_generate_content", "")
        rev_result = main_agent._execute_subagent("reviewer", params)
        current_state.update(rev_result)
        
        is_passed = rev_result.get("is_passed", False)
        print(f"✅ Reviewer 结论: {'通过' if is_passed else '打回重做'}")
        print(f"🔍 根因分析: {rev_result.get('root_cause_analysis', '无')}")
        print(f"🛠 修复建议: {rev_result.get('correct_approach', '无')}")

        # ----------------
        # 步骤 4：主干将结果落盘至 SOP Templates
        # ----------------
        print("\n[STEP 4] -> 如果通过，保存至独立的 SOP_Templates")
        if is_passed and current_state.get("current_sop"):
            sop_path = main_agent.memory_manager.save_sop(
                experiment_type=experiment_type,
                chapter_id=chapter_id,
                content=current_state.get("current_sop"),
                quality_score=current_state.get("score", 5.0)
            )
            print(f"💾 SOP 已保存至: {sop_path}")
        else:
            print("❌ SOP 考核未通过，暂不落盘。")

        # ----------------
        # 步骤 5：学习大脑提炼 Rules 并落盘
        # ----------------
        print("\n[STEP 5] -> 激活 Reflector & Curator 提炼深层防错规则 (使用 Smart Model)")
        # 强行塞入一个假的 trajectory 记录以便反射
        fake_trajectory = [
            {"step": 1, "agent": "writer", "type": "gen", "output": writer_result},
            {"step": 2, "agent": "simulator", "type": "sim", "output": sim_result},
            {"step": 3, "agent": "reviewer", "type": "rev", "output": rev_result}
        ]
        insights_res = main_agent.reflector.extract(fake_trajectory, experiment_type=experiment_type)
        insights = insights_res.get("insights", [])
        print(f"🧠 Reflector 提炼的 Insight: {insights_res.get('key_insight', 'None')}")
        
        current_playbook_block = "\n".join(main_agent.memory_manager.query_rules(experiment_type, chapter_id))
        curator_res = main_agent.curator.extract_operations(
           current_playbook=current_playbook_block,
           insights=insights,
           question_context=f"针对 {experiment_type} 类型的 {chapter_id} 标准化抽取中暴露的排版映射问题"
        )
        
        operations = curator_res.get("operations", [])
        if operations:
            print(f"✍ Curator 颁布的新版规则指令: {operations}")
            main_agent.memory_manager.apply_rules_operations(experiment_type, chapter_id, operations)
            print("💾 Rules 落盘完成。")
        else:
            print("ℹ️ Curator 判定无需增减新规则。")

        # ----------------
        # 步骤 6：审计日志落盘
        # ----------------
        print("\n[STEP 6] -> 写入当日系统审计日志 (Audit Log)")
        iteration_data = {
            "version": "TestVersion1",
            "sop_id": "test_sop_xyz",
            "experiment_type": experiment_type,
            "chapter_id": chapter_id,
            "quality_assessment": {"is_passed": is_passed, "feedback": rev_result.get("feedback")},
            "curation": {"operations_added": len(operations)}
        }
        log_path = main_agent.memory_manager.log_iteration(iteration_data)
        print(f"📜 审计日志写入完成: {log_path}")

        print("\n" + "=" * 60)
        print("✅ 全链路白盒流转测试结束")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ 测试链路发生异常: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_full_pipeline()
