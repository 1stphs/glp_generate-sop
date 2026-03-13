# Test Data Directory

## Overview

This directory contains test data for the DeepAgent system.

## Files

### `protocol_content.json`

Contains protocol (验证方案) content.

#### Schema

```json
{
  "protocol_content1": "First protocol content...",
  "protocol_content2": "Second protocol content...",
  ...
}
```

### `report_content.json`

Contains report (验证报告) content.

#### Schema

```json
{
  "report_content1": "First report content...",
  "report_content2": "Second report content...",
  ...
}
```

### `structure.json`

Contains chapter structure definitions.

#### Schema

```json
[
  {
    "id": "chapter_id",
    "section_title": "Chapter Title",
    "parent_section_id": "parent_id",
    "description": "Description..."
  },
  ...
]
```

## Data Usage

### Input

These files provide input data for:
1. **Protocol Content**: Original verification plan
2. **Report Content**: Target output format
3. **Structure**: Chapter organization

### Processing

The system processes this data to:
1. Generate SOPs for each chapter
2. Iterate and improve based on quality
3. Extract insights and update playbook

## Sample Data Format

Each protocol/report pair should contain:
- Full chapter structure
- All sections with their content
- Consistent formatting across sections

## Adding New Test Data

1. Copy new protocol to `protocol_content.json`
2. Copy corresponding report to `report_content.json`
3. Update structure in `structure.json`
4. Follow existing schema format

## Notes

- Ensure encoding is UTF-8
- Use consistent field naming
- Maintain structure integrity
- Validate JSON format before use
