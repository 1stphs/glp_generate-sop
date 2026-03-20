#!/usr/bin/env python3
"""
整合数据转换脚本
将 protocol_content.json, report_content.json 和 structure.json 整合成一个统一的数据文件
"""

import json
from pathlib import Path
from typing import Dict, List, Any


def extract_section_context(
    full_text: str, section_title: str, window: int = 2000
) -> str:
    """从完整文本中提取章节的上下文片段"""
    import re

    # 剥离 section_title 中可能自带的序号 (例如 "1. 目的" -> "目的")
    clean_title = re.sub(r"^[\d\.\s、]+", "", section_title).strip()
    if not clean_title:
        clean_title = section_title
        
    patterns = [
        # 精确匹配（带或不带前置编号）
        rf"(?:[\d\.\s、]+)?{re.escape(clean_title)}",
        rf"【\s*{re.escape(clean_title)}\s*】",
        rf"\[\s*{re.escape(clean_title)}\s*\]",
        # 宽容的 fallback
        rf"{re.escape(clean_title)}"
    ]

    for pattern in patterns:
        try:
            match = re.search(pattern, full_text)
            if match:
                # 提取章节标题前后的内容
                start = max(0, match.start() - window)
                end = min(len(full_text), match.end() + window)
                return full_text[start:end]
        except Exception:
            pass

    # 如果找不到标题，返回空字符串
    return ""


def build_section_map(structure: List[Dict]) -> Dict[str, Dict]:
    """建立章节映射（section_title -> section_info）"""
    section_map = {}
    for section in structure:
        section_map[section["section_title"]] = section
    return section_map


def main():
    # 基础路径
    base_dir = Path(__file__).parent.parent / "mockData" / "workflow-b"

    # 读取结构文件
    print("读取 structure.json...")
    with open(base_dir / "structure.json", "r", encoding="utf-8") as f:
        structure = json.load(f)

    # 读取 protocol 和 report
    print("读取 protocol_content.json 和 report_content.json...")
    with open(base_dir / "protocol_content.json", "r", encoding="utf-8") as f:
        protocol_data = json.load(f)

    with open(base_dir / "report_content.json", "r", encoding="utf-8") as f:
        report_data = json.load(f)

    # 获取数据集数量
    num_datasets = len(
        [k for k in protocol_data.keys() if k.startswith("protocol_content")]
    )
    print(f"发现 {num_datasets} 个数据集")

    # 构建整合数据
    integrated_data = {
        "version": "1.0",
        "created_at": "2026-03-19",
        "structure": structure,
        "datasets": [],
    }

    # 处理每个数据集
    for dataset_idx in range(1, num_datasets + 1):
        protocol_key = f"protocol_content{dataset_idx}"
        report_key = f"report_content{dataset_idx}"

        if protocol_key not in protocol_data or report_key not in report_data:
            print(f"警告: 数据集 {dataset_idx} 不完整，跳过")
            continue

        protocol_text = protocol_data[protocol_key]
        report_text = report_data[report_key]

        # 提取所有章节的上下文（移除仅过滤主要章节的限制）
        target_sections = structure

        sections_with_context = []
        for section in target_sections:
            section_title = section["section_title"]

            # 提取 protocol 和 report 的上下文片段
            protocol_context = extract_section_context(protocol_text, section_title)
            report_context = extract_section_context(report_text, section_title)

            sections_with_context.append(
                {
                    **section,
                    "protocol_context": protocol_context,
                    "report_context": report_context,
                }
            )

        # 构建数据集
        dataset = {
            "dataset_id": dataset_idx,
            "protocol_content": protocol_text,
            "report_content": report_text,
            "sections": sections_with_context,
            "metadata": {
                "protocol_length": len(protocol_text),
                "report_length": len(report_text),
                "num_sections": len(sections_with_context),
            },
        }

        integrated_data["datasets"].append(dataset)
        print(
            f"  ✓ 数据集 {dataset_idx}: {len(protocol_text)} + {len(report_text)} 字符"
        )

    # 保存整合数据
    output_file = base_dir / "integrated_data.json"
    print(f"\n保存整合数据到 {output_file}...")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(integrated_data, f, ensure_ascii=False, indent=2)

    print(f"✅ 完成！数据集数量: {len(integrated_data['datasets'])}")
    print(f"\n数据结构说明:")
    print(f"  - structure: 完整的章节结构（来自 structure.json）")
    print(f"  - datasets: 所有数据集列表")
    print(f"    - dataset_id: 数据集编号")
    print(f"    - protocol_content: 完整的验证方案文本")
    print(f"    - report_content: 完整的GLP报告文本")
    print(f"    - sections: 主要章节及上下文片段")
    print(f"      - protocol_context: 验证方案中的章节上下文")
    print(f"      - report_context: GLP报告中的章节上下文")


if __name__ == "__main__":
    main()
