# 数据结构重组完成

## 修改内容

### 1. 新建文件

**integrate_data.py** - 数据整合脚本
- 读取 `structure.json`, `protocol_content.json`, `report_content.json`
- 按章节结构提取上下文片段
- 生成整合后的数据文件 `integrated_data.json`

**integrated_data.json** - 整合数据文件（自动生成）
- 包含完整章节结构
- 每个数据集的完整 protocol 和 report 内容
- 每个章节的上下文片段（用于AI快速定位）

### 2. 修改文件

**config_v6.py**
- 新增配置项：`MAX_DATASETS = 1`
- 用法：设置为1测试第一份数据集，设为3测试前3份数据集

**main_v6.py**
- 新增函数：`load_integrated_data()` - 加载整合数据
- 新增函数：`prepare_sections_from_integrated()` - 从整合数据准备章节
- 修改 main 函数：使用新的数据加载逻辑
- 删除旧函数：`parse_sections_from_protocol()`, `load_real_data()`, `prepare_sections()`

## 数据结构对比

### 之前（混乱）
```
protocol_content.json:
{
  "protocol_content1": "很长的完整文本...",
  "protocol_content2": "另一段很长的文本..."
}

report_content.json:
{
  "report_content1": "很长的完整文本...",
  "report_content2": "另一段很长的文本..."
}

问题：
- 章节结构与文本内容分离
- 章节内容在长文本中，需要手动分割
- AI难以快速定位相关章节
```

### 现在（清晰）
```json
{
  "version": "1.0",
  "created_at": "2026-03-19",
  "structure": [...],  // 完整章节结构（65个章节）
  "datasets": [
    {
      "dataset_id": 1,
      "protocol_content": "完整验证方案文本（10589字符）",
      "report_content": "完整GLP报告文本（39426字符）",
      "sections": [
        {
          "section_title": "验证报告",
          "protocol_context": "...（章节上下文片段）...",
          "report_context": "...（章节上下文片段）..."
        },
        ...
      ]
    }
  ]
}
```

优势：
- 章节结构与内容统一
- 提供完整文本和上下文片段
- AI可以快速定位章节内容
- 易于扩展和维护

## 使用说明

### 生成整合数据
```bash
cd sop_deeplang
python3 integrate_data.py
```
会生成 `../mockData/workflow-b/integrated_data.json`

### 配置数据集数量
编辑 `config_v6.py`:
```python
MAX_DATASETS = 1  # 只测试第一份数据集
```

### 运行主程序
```bash
python3 main_v6.py
```

程序会：
1. 加载 `integrated_data.json`
2. 根据章节结构准备每个数据集的章节
3. 使用上下文片段作为AI输入
4. 处理最多 MAX_DATASETS 个数据集

## 章节示例（数据集1，前5个主要章节）

1. **验证报告** (protocol: 2004 chars, report: 1004 chars)
2. **GLP遵从性声明和签字页** (protocol: 0 chars, report: 1212 chars)
3. **质量保证声明** (protocol: 0 chars, report: 2006 chars)
4. **目录** (protocol: 2002 chars, report: 2002 chars)
5. **附表目录** (protocol: 0 chars, report: 2007 chars)

## 备注

- `structure.json` 包含所有65个章节的完整层级关系
- 当前只处理主要章节（parent_section_id 为 null），共21个
- 子章节可以通过扩展 `prepare_sections_from_integrated()` 函数来支持
- 如果 protocol 或 report 中找不到章节标题，对应上下文为空字符串（不影响AI，因为完整文本仍可用）
