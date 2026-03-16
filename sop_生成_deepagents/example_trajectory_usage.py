"""
完整示例：如何使用轨迹存储和洞察提取
展示 Reflector + Curator 的正确用法
"""

from memory_manager_v3 import MemoryManagerV3
from deepagents import create_deep_agent

# 初始化
memory = MemoryManagerV3("./memory")

# ============================================================
# 场景：Main Agent 执行完一个任务后的完整对话历史
# ============================================================

task_id = "task_20240316_001"

# 模拟完整对话轨迹（Main Agent 的执行结果）
conversation_history = [
    {"role": "user", "content": "生成小分子模板的 GLP 报告 SOP"},
    {"role": "assistant", "content": "我将调用 writer 生成 SOP"},
    {"role": "tool", "tool_name": "writer", "content": "生成的 SOP 内容..."},
    {"role": "assistant", "content": "现在调用 simulator 盲测"},
    {"role": "tool", "tool_name": "simulator", "content": "执行过程中发现问题：步骤 3 缺少具体温度参数"},
    {"role": "assistant", "content": "调用 reviewer 审核"},
    {"role": "tool", "tool_name": "reviewer", "content": "评分：2/5，问题：缺少温度参数"},
    {"role": "assistant", "content": "评分过低，调用 reflector 诊断"},
]

# ============================================================
# 步骤 1：保存完整轨迹
# ============================================================
print("📝 保存对话轨迹...")
trajectory_path = memory.save_trajectory(task_id, conversation_history)
print(f"✓ 轨迹已保存: {trajectory_path}\n")

# ============================================================
# 步骤 2：Reflector 从轨迹中提取洞察
# ============================================================
print("🔍 Reflector 分析轨迹...")

reflector_agent = create_deep_agent(
    model="openai:claude-opus-4-6",
    system_prompt="""你是系统诊断专家。

分析完整的对话轨迹，提取失败的根本原因和可泛化的洞察。

输出格式：
### 问题根源
[分析]

### 可泛化的洞察
[方法论，不含具体数值]
"""
)

# 将轨迹转换为文本
trajectory_text = "\n\n".join([
    f"[{msg['role']}]: {msg.get('content', '')}"
    for msg in conversation_history
])

# Reflector 分析
result = reflector_agent.invoke({
    "messages": [{"role": "user", "content": f"分析以下对话轨迹：\n\n{trajectory_text}"}]
})

insight = result["messages"][-1].content
print(f"✓ 提取的洞察:\n{insight}\n")

# ============================================================
# 步骤 3：保存洞察
# ============================================================
print("💾 保存洞察...")
insight_path = memory.save_insight("小分子模板", insight)
print(f"✓ 洞察已保存: {insight_path}\n")

# ============================================================
# 步骤 4：Curator 基于洞察更新规则
# ============================================================
print("📚 Curator 更新规则...")

curator_agent = create_deep_agent(
    model="openai:claude-opus-4-6",
    system_prompt="""你是规则库管理员。

根据提取的洞察，生成可添加到规则库的内容。

输出格式（Markdown）：
## [章节名]
[规则内容]
"""
)

# 加载现有规则
old_rules = memory.load_rules("小分子模板")

# Curator 生成新规则
result = curator_agent.invoke({
    "messages": [{
        "role": "user",
        "content": f"现有规则：\n{old_rules}\n\n新洞察：\n{insight}\n\n请生成要添加的规则。"
    }]
})

new_rule = result["messages"][-1].content
print(f"✓ 生成的新规则:\n{new_rule}\n")

# 更新规则库
rule_path = memory.append_rule("小分子模板", "参数规范", new_rule)
print(f"✓ 规则已更新: {rule_path}\n")

# ============================================================
# 步骤 5：记录审计日志
# ============================================================
print("📊 记录审计日志...")
memory.log_execution({
    "task_id": task_id,
    "experiment_type": "小分子模板",
    "section": "GLP报告",
    "status": "failed_then_learned",
    "quality_score": 2,
    "iterations": 1,
    "insight_extracted": True
})
print("✓ 审计日志已记录\n")

# ============================================================
# 总结
# ============================================================
print("="*70)
print("✅ 完整流程演示完成")
print("="*70)
print("""
记忆存储结构：
memory/
├── trajectories/
│   └── task_20240316_001.json      # 完整对话轨迹
├── insights/
│   └── 小分子模板_2024-03.md       # 提取的洞察
├── rules/
│   └── 小分子模板.md                # 更新的规则
└── audit_log/
    └── audit_2024-03.jsonl          # 统计数据

关键点：
1. 保存完整轨迹（不只是结果）
2. Reflector 分析轨迹提取洞察
3. Curator 基于洞察更新规则
4. 下次执行自动复用新规则
""")
