# ACE (Agent-Curator-Environment) Subsystem

## Overview

The ACE subsystem implements experience generation and management through two-call pattern.

## Components

### `AuditLog` (`audit_log.py`)

**Role**: Records all execution details as audit log.

**Data Fields**:
- `timestamp`: When iteration occurred
- `version`: Version identifier (Version1/2/3)
- `sop`: Generated SOP content
- `sop_id`: Unique SOP identifier
- `sop_type`: SOP type (rule_template, simple_insert, complex_composite)
- `curation`: Modification records from Curator
- `metrics`: Token usage, latency, model
- `quality_assessment`: Quality score and feedback

**Data Structure**: Organized by chapter_id → iterations

### `RulesManager` (`rules_manager.py`)

**Role**: Manages rules by SOP type and chapter.

**Data Structure**:
```
<sop_type>
  └── <chapter_id>
      └── <rule_id>
            ├── id: Unique identifier
            ├── content: Rule content
            ├── tags: Classification tags
            ├── applicability: Where rule applies
            └── metrics: helpful/harmful counts
```

**Key Methods**:
- `get_rules()`: Query by type and chapter
- `add_rule()`: Add new rule
- `update_rule_metrics()`: Track helpful/harmful counts

### `SOPTemplates` (`sop_templates.py`)

**Role**: Manages SOP templates and chapter-specific SOPs.

**Data Structure**:
```
templates
  └── <sop_type>
        ├── template_content: Template definition
        ├── created_at: Creation timestamp
        └── updated_at: Last update timestamp

chapter_sops
  └── <chapter_id>
        ├── chapter_title: Chapter name
        ├── sops
        │   └── <sop_type>
        │       ├── sop_content: SOP text
        │       ├── version: Version identifier
        │       ├── quality_score: Quality rating
        │       ├── created_at: Creation timestamp
        │       └── updated_at: Last update timestamp
        └── <more sop_types>
```

### `Reflector` (`reflector.py`)

**Role**: Analyzes SOP quality and evaluates rule effectiveness.

**Tasks**:
1. Evaluate SOP quality (1-5 score)
2. Tag rules as helpful/harmful/neutral
3. Provide specific feedback
4. Suggest improvements

**Input**: Generated SOP, target report, original protocol, used rules
**Output**: Quality score, assessment, rule tags, improvement suggestions

### `Curator` (`curator.py`)

**Role**: Extracts and refines rules from successful executions.

**Tasks**:
1. Analyze high-quality SOPs (quality >= threshold)
2. Extract reusable rules
3. Generalize for other chapters
4. Tag with metadata
5. Identify patterns

**Input**: High-quality SOP, reflection results, execution context
**Output**: New rules, refined rules, patterns, summary

## Two-Call Pattern

### First Call: Master Agent → Trajectory

```
User Task
    ↓
Master Agent (autonomous planning & execution)
    ↓
ACE System executes
    ↓
Builds complete trajectory (steps, metrics, used rules)
```

### Second Call: Trajectory → Insights → Playbook

```
Trajectory (from first call)
    ↓
Insight Agent extracts insights
    ↓
Insights (experience + applicability)
    ↓
Playbook Agent updates playbook
    ↓
Updated playbook with new/modified rules
```

## Data Flow

### Input Data

1. **Protocol**: From `data/protocol_content.json`
2. **Report**: From `data/report_content.json`
3. **Structure**: From `data/structure.json`

### Execution Flow

1. **SOP Generation**: Uses RulesManager to query rules
2. **Quality Assessment**: Reflector evaluates generated SOP
3. **Rule Extraction**: Curator extracts rules from high-quality SOPs
4. **Audit Logging**: AuditLog records all details
5. **Template Storage**: SOPTemplates saves final SOPs

### Output Data

1. **Audit Log**: `agent_memory/audit_log/audit_log.json`
2. **Rules**: `agent_memory/rules/rules.json`
3. **SOPs**: `agent_memory/sop_templates/sop_templates.json`
4. **Playbook**: `playbook/playbooks.json`

## Integration with Agents

### Master Agent Integration

- ACE is called as a sub-agent by Master Agent
- Master Agent provides trajectory to Insight Agent
- Master Agent provides insights to Playbook Agent

### Quality Threshold

Curator only extracts rules when quality >= threshold (default: 4.0)

This ensures:
- Only successful executions contribute to playbook
- Quality-driven rule management
- Prevention of rule pollution

## Metrics Tracking

### Rule Metrics

Each rule tracks:
- `helpful`: Count of times rule was helpful
- `harmful`: Count of times rule was harmful
- `usage_count`: Total times rule was used

### Cleanup Rules

Rules with poor metrics are removed:
- `helpful == 0` and `harmful > 5` → Ineffective
- Duplicate content (similarity-based) → Deduplicated

## Extension Points

### Adding New SOP Types

1. Update `RulesManager` to support new type
2. Update `SOPTemplates` with template for new type
3. Update prompts in `Reflector` if needed
4. Test with sample data

### Modifying Curation Logic

1. Adjust quality threshold in `Curator.__init__()`
2. Modify extraction logic in `curate()` method
3. Update prompt templates if needed
