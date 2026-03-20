# 报告内容生成程序 (Report Generation Utility)

本工具用于根据 GLP 研究的章节 SOP、实验结果（Excel 解析内容）以及项目基础信息，自动生成连贯、专业的报告各章节正文内容。

## 目录结构说明

- `generate_report.py`: 核心执行脚本，负责 Prompt 渲染及 LLM 交互。
- `requirements.txt`: Python 依赖库列表。
- `README.md`: 使用说明（本文件）。

## 环境准备

1.  **Python 版本**: 建议使用 Python 3.8 或更高版本。
2.  **安装依赖**:
    ```bash
    pip install -r requirements.txt
    ```
3.  **配置 LLM 环境变量**:
    脚本默认使用 `grok-4-fast-non-reasoning` 模型。请确保配置了相应的 API Key 和域名：
    ```bash
    export OPENAI_API_KEY="您的密钥"
    export OPENAI_BASE_URL="您的 API 代理地址（如有）"
    ```

## 快速使用

### 1. 准备输入数据 (JSON)

你需要准备两个 JSON 文件：

#### `project_info.json` (项目全局信息)
```json
{
  "study_no": "NS2023001",
  "test_item": "供试品 A"
}
```

#### `sections_data.json` (各章节明细)
```json
[
  {
    "id": "1.1",
    "section_title": "供试品信息",
    "sop": "请总结供试品的批号和有效期。",
    "excel_parsed": [
      { "sheet_name": "BatchInfo", "extracted_content": "批号: 20230101, 有效期: 2025-01-01" }
    ]
  }
]
```

### 2. 运行脚本

```bash
python3 generate_report.py project_info.json sections_data.json report_output.json
```

生成的报告正文将保存在 `report_output.json` 中。

## 开发与集成建议

- **LLM 调用**: 脚本内置了基础的异步调用逻辑。如果您的新项目中已有成熟的 `llm_client` 工具，建议在 `generate_report.py` 的 `call_llm` 函数中进行简单适配。
- **SOP 来源**: 生成效果高度依赖于 `sop` 字段的质量，请确保该字段包含明确的撰写规则。
