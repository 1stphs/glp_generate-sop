#!/usr/bin/env python3
"""
快速测试脚本 - 验证系统是否可以正常运行
"""

import sys
import os
from pathlib import Path


def check_system():
    """检查系统完整性"""
    print("\n" + "=" * 70)
    print("🔍 SOP 生成系统 V6 - 系统检查")
    print("=" * 70 + "\n")

    # 1. 检查核心文件
    print("1. 核心文件检查...")
    core_files = [
        "sop_deeplang/utils/config.py",
        "sop_deeplang/utils/memory_manager.py",
        "sop_deeplang/core/engine.py",
        "sop_deeplang/core/state.py",
        "sop_deeplang/main.py",
    ]

    for file in core_files:
        if Path(file).exists():
            print(f"   ✓ {file}")
        else:
            print(f"   ✗ {file}: 文件不存在")
            return False

    # 2. 检查 nodes
    print("\n2. 节点检查...")
    nodes = [
        "sop_deeplang/nodes/__init__.py",
        "sop_deeplang/nodes/master.py",
        "sop_deeplang/nodes/writer.py",
        "sop_deeplang/nodes/simulator.py",
        "sop_deeplang/nodes/reviewer.py",
        "sop_deeplang/nodes/curator.py",
    ]

    for node in nodes:
        if Path(node).exists():
            print(f"   ✓ {node}")
        else:
            print(f"   ✗ {node}: 文件不存在")
            return False

    # 3. 检查 skill 文件
    print("\n3. Skill 文件检查...")
    skills = [
        "sop_deeplang/memory/skills/master/complexity_analysis_skill_v1.md",
        "sop_deeplang/memory/skills/writing/writer_skill_v1.md",
        "sop_deeplang/memory/skills/simulation/simulator_skill_v1.md",
        "sop_deeplang/memory/skills/evaluation/reviewer_skill_v1.md",
        "sop_deeplang/memory/skills/curation/curator_skill_v1.md",
    ]

    for skill in skills:
        if Path(skill).exists():
            print(f"   ✓ {skill}")
        else:
            print(f"   ✗ {skill}: 文件不存在")
            return False

    # 4. 编译检查
    print("\n4. 编译检查...")
    all_files = core_files + nodes
    for file in all_files:
        try:
            with open(file, "r", encoding="utf-8") as f:
                compile(f.read(), file, "exec")
            print(f"   ✓ {file}: 编译成功")
        except SyntaxError as e:
            print(f"   ✗ {file}: 语法错误 - {e}")
            return False
        except Exception as e:
            print(f"   ⚠️  {file}: {e}")

    # 5. 检查 .env.example
    print("\n5. 配置文件检查...")
    env_example = Path("sop_deeplang/.env.example")
    if env_example.exists():
        print(f"   ✓ .env.example: 存在")
        print(f"   → cp sop_deeplang/.env.example sop_deeplang/.env 命令可用")
    else:
        print(f"   ✗ .env.example: 不存在")
        return False

    print("\n" + "=" * 70)
    print("✅ 所有检查通过！")
    print("=" * 70 + "\n")

    # 6. 检查数据文件
    print("6. 数据文件检查...")
    base_dir = Path(
        "/Users/pangshasha/Documents/github/glp_generate-sop/mockData/workflow-b"
    )
    protocol_file = base_dir / "protocol_content.json"
    report_file = base_dir / "report_content.json"

    if protocol_file.exists():
        print(f"   ✓ {protocol_file}: 存在")
        with open(protocol_file, "r", encoding="utf-8") as f:
            import json

            data = json.load(f)
            print(f"   → 包含 {len(data)} 条数据")
    else:
        print(f"   ✗ {protocol_file}: 不存在")
        return False

    if report_file.exists():
        print(f"   ✓ {report_file}: 存在")
        with open(report_file, "r", encoding="utf-8") as f:
            import json

            data = json.load(f)
            print(f"   → 包含 {len(data)} 条数据")
    else:
        print(f"   ✗ {report_file}: 不存在")
        return False

    print("\n" + "=" * 70)
    print("🚀 系统就绪！可以运行")
    print("=" * 70 + "\n")

    print("运行命令:")
    print("  python main.py")
    print()
    print("如遇 API 错误，请检查 .env 文件中的 API Keys 配置。")

    return True


if __name__ == "__main__":
    success = check_system()
    sys.exit(0 if success else 1)
