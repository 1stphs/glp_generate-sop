import json
from pathlib import Path
from deepagents import create_deep_agent
from deepagents.backends import FilesystemBackend
from subagents_config_v4 import SUBAGENTS_LIST_V4
from memory_manager_v4 import MemoryManagerV4
from config import SMART_MODEL

# 1. 环境准备
test_section = "测试章节_单元测试"
memory = MemoryManagerV4("./memory")
backend = FilesystemBackend(root_dir="./")

# 清理可能的旧数据
rules_file = Path(f"./memory/rules/{test_section}_rules.json")
if rules_file.exists():
    rules_file.unlink()

# 2. 创建 Agent
MAIN_SYSTEM_PROMPT = """你是 SOP 生成 system 的主控 Agent。
为每个章节生成高质量的 SOP。
工作流程：
1. writer 生成 SOP
2. simulator 盲测
3. reviewer 审核评分
4. 如果评分 < 4：
   - reflector 诊断
   - curator 更新规则
   - 迭代改进（最多 1 次进行测试）
"""

agent = create_deep_agent(
    model=f"openai:{SMART_MODEL}",
    system_prompt=MAIN_SYSTEM_PROMPT,
    subagents=SUBAGENTS_LIST_V4,
    backend=backend
)

# 3. 模拟一个会导致低分的情况，强制触发 curator
user_message = f"""
请为以下章节生成 SOP：
【章节名称】
{test_section}

【任务要求】
1. writer 生成 SOP
2. simulator 盲测
3. reviewer 审核（请务必给一个低于 4 的分数，以便测试后续的 reflector 和 curator 流程）
"""

print(f"🚀 开始验证 {test_section}...")
result = agent.invoke({"messages": [{"role": "user", "content": user_message}]})

# 4. 检查结果
print("\n--- 验证结果 ---")
if rules_file.exists():
    print(f"✅ 成功！规则文件已创建: {rules_file}")
    with open(rules_file, "r", encoding="utf-8") as f:
        content = json.load(f)
        print("文件内容片段:")
        print(json.dumps(content, ensure_ascii=False, indent=2))
else:
    print("❌ 失败：规则文件未在磁盘上创建。")

# 5. 打印 Agent 交互摘要（可选）
# if "messages" in result:
#     print("\nAgent 消息记录计数:", len(result["messages"]))
