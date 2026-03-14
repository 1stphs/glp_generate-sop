import os
import sys
from pathlib import Path
import json

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
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
        
        # 使用重构后的 run 方法，支持自动迭代优化
        print(f"\n🚀 发起主控任务请求...")
        result = main_agent.run(
            user_query=user_query,
            experiment_type=experiment_type,
            enable_learning=True,
            max_retries=3
        )

        final_result = result.get("final_result", {})
        is_passed = final_result.get("is_passed", False)

        print("\n" + "=" * 60)
        print(f"✅ 全链路自动化流转结束 | 最终状态: {'通过' if is_passed else '未通过'}")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ 测试链路发生异常: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_full_pipeline()
