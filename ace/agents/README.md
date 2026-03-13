# ACE Agents - SOP Generation & Quality Control

## Overview

This directory contains the core agents for SOP generation and quality control.

## Components

### SOP Generation Agents

#### `SOPWriter` (`sop_writer.py`)

**Role**: Generates standardized SOPs (Core Rules, Template, Examples)

**Responsibilities**:
- Generate SOP based on chapter content
- Output fixed three-section structure
- Support three SOP types: simple_insert, rule_template, complex_composite

**Output Format**:
\`\`\`markdown
## 一、核心填写规则
1. Rule 1
2. Rule 2

## 二、通用模板
[Template Content]

## 三、示例
[Example Content]
\`\`\`

#### `SOPSimulator` (`sop_simulator.py`)

**Role**: Simulates SOP execution

**Responsibilities**:
- Execute SOP based on original_content and current_sop
- Anti-cheat: Never reads target_generate_content
- Output simulated report content

**Important Constraint**: STRICTLY only uses original_content as input

**Output Format**: Simulated report content matching SOP template format

#### `SOPReviewer` (`sop_reviewer.py`)

**Role**: Three-party quality review

**Responsibilities**:
- Compare three inputs:
  1. target_generate_content (actual report)
  2. current_sop (generated SOP)
  3. simulated_generate_content (simulation result)
- Review only: structure, format, template consistency
- Output: is_passed + feedback

**Review Scope**: Limited to form/template consistency, NOT numerical accuracy

## ACE System Components

### `AuditLog` (`audit_log.py`)
Records all execution details (time, version, sop, id, type, curation, metrics, quality_assessment)

### `RulesManager` (`rules_manager.py`)
Manages rules by SOP type and chapter

### `SOPTemplates` (`sop_templates.py`)
Manages SOP templates and chapter-specific SOPs

### `Reflector` (`reflector.py`)
Analyzes SOP quality and provides feedback

### `Curator` (`curator.py`)
Extracts and refines rules from successful executions

## Integration with Master Agent

Master Agent can coordinate these agents:

\`\`\`
User Task
    ↓
Master Agent (autonomous planning)
    ↓
1. SOP Writer (generate SOP)
    ↓
2. SOP Simulator (simulate execution)
    ↓
3. SOP Reviewer (quality check)
    ↓
Master Agent (decide based on is_passed)
    ↓
If failed: Retry with feedback
If passed: Save SOP and continue
\`\`\`

## Key Design Decisions

1. **Simplified Implementation**: Removed unnecessary complexity from original agents
2. **Clean Prompts**: Focused on core responsibilities
3. **Mock Data**: Agents return mock data until LLM integration
4. **Clear Separation**: Each agent has single, well-defined responsibility

## Next Steps

1. Implement LLM client integration
2. Add JSON parsing for all agent responses
3. Create integration tests
4. Connect to AuditLog, RulesManager for persistence
