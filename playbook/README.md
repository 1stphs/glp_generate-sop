# Playbook Directory

## Overview

This directory stores the persistent knowledge base (playbooks) used by the DeepAgent system.

## Files

### `playbooks.json`

The main playbook file storing all accumulated experience rules.

#### Data Structure

```json
{
  "version": "1.0",
  "created_at": "ISO-8601 timestamp",
  "updated_at": "ISO-8601 timestamp",
  "rules": {
    "<sop_type>": {
      "<chapter_id>": {
        "<rule_id>": {
          "id": "rule_xxx",
          "content": "Rule content",
          "tags": ["tag1", "tag2"],
          "applicability": {
            "sop_types": ["rule_template"],
            "chapters": ["验证报告"],
            "context": "适用场景描述"
          },
          "metrics": {
            "helpful": 10,
            "harmful": 0,
            "usage_count": 15
          },
          "created_at": "ISO-8601",
          "updated_at": "ISO-8601"
        }
      }
    }
  }
}
```

#### Schema

| Field | Type | Description |
|--------|------|-------------|
| `id` | string | Unique rule identifier (format: rule_xxxxxxxxxx) |
| `content` | string | Rule content (specific, actionable) |
| `tags` | array | Tags for rule classification and retrieval |
| `applicability.sop_types` | array | SOP types where this rule applies |
| `applicability.chapters` | array | Chapter titles where this rule applies |
| `applicability.context` | string | Description of when this rule is effective |
| `metrics.helpful` | integer | Count of times rule was helpful |
| `metrics.harmful` | integer | Count of times rule was harmful |
| `metrics.usage_count` | integer | Total times rule was used |
| `created_at` | string | ISO-8601 timestamp when rule was created |
| `updated_at` | string | ISO-8601 timestamp when rule was last updated |

## Operations

### Query

Performed by `PlaybookAgent.query()` to find rules relevant to a task.

### Update

Performed by `PlaybookAgent.update()` to integrate new insights from `InsightAgent`.

### Quality Maintenance

Rules with low effective metrics are periodically removed:
- `helpful == 0` and `harmful > 5` → Remove ineffective rules
- Duplicate content → Deduplicate based on content similarity

## Access Pattern

1. **Query**: When processing a chapter, query relevant rules
2. **Update**: After execution, update rule metrics
3. **Refine**: Periodically review and optimize rule organization
