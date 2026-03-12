# Agents Directory

## Overview

This directory contains the core agents of the DeepAgent system.

## Components

### `MasterAgent` (`master_agent.py`)

**Role**: Core brain that autonomously plans and executes tasks.

**Key Features**:
- Natural language task understanding
- Autonomous decision making (NO hardcoded workflows)
- Dynamic agent selection and coordination
- Result aggregation

**Prompt Design**:
- Emphasizes autonomous decision making
- Requires reasoning output for auditability
- Explains decision rationale
- Lists available sub-agents

### `InsightAgent` (`insight_agent.py`)

**Role**: Extracts insights and lessons from execution trajectories.

**Key Features**:
- Evidence-driven extraction
- Context tagging for applicability
- Categorized insights (rule_success, rule_failure, problem_solution, pattern_discovery)

**Input**: Complete execution trajectory
**Output**: Insights with evidence and applicability metadata

### `PlaybookAgent` (`playbook_agent.py`)

**Role**: Manages persistent knowledge base (playbooks).

**Key Features**:
- LLM-driven query matching (not simple keyword search)
- LLM-driven updates (intelligent deduplication and cleanup)
- Quality maintenance (removes ineffective rules)

**Operations**:
- Query: Find relevant rules for current task
- Update: Integrate new insights
- Cleanup: Remove ineffective rules

## Utils

### `PromptTemplate` (`utils/prompt_template.py`)

**Role**: Manages prompt templates for all agents.

**Features**:
- Centralized template storage
- Variable substitution using `${variable_name}` syntax
- Multi-language support
- Version tracking

### `SharedMemory` (`utils/memory.py`)

**Role**: Provides shared context between agents.

**Features**:
- Key-value storage
- Context isolation by task ID
- Timestamp tracking
- Trajectory recording

## Agent Collaboration

### Two-Call Pattern

1. **First Call**: Master Agent → trajectory
2. **Second Call (Part 1)**: Insight Agent → insights (from trajectory)
3. **Second Call (Part 2)**: Playbook Agent → updated playbook (from insights)

### Communication Flow

```
User Task
    ↓
Master Agent (autonomous planning)
    ↓
Executes ACE System
    ↓
Builds Trajectory
    ↓
Insight Agent (extracts insights)
    ↓
Playbook Agent (updates playbook)
    ↓
Final Results
```

## Natural Language Driving

**Critical Principle**: All agents must make autonomous decisions based on natural language understanding.

**Master Agent**:
- Never assumes fixed workflow
- Each task is planned from scratch
- Decides which agents to call dynamically
- Explains reasoning in natural language

**Insight Agent**:
- Extracts based on evidence in trajectory
- Does not predefine insight categories
- Generalizes from specific to reusable

**Playbook Agent**:
- Matches based on semantic understanding, not keywords
- Updates based on intelligent deduplication
- Maintains quality without hardcoded rules

## Prompt Design

All agent prompts follow consistent structure:

1. **Role Definition**: Clear responsibility statement
2. **Task Description**: What to accomplish
3. **Output Format**: Structured JSON with clear schema
4. **Important Constraints**: Critical rules to follow
5. **Examples**: Demonstrating expected behavior

## Extension Points

### Adding New Agents

1. Create new agent file in `agents/`
2. Implement with natural language driving
3. Add to `__init__.py`
4. Update prompt templates if needed
5. Add to Master Agent's available agents list

### Modifying Agent Behavior

1. Update system prompt for new capabilities
2. Modify reasoning logic if needed
3. Update output schema
4. Test with integration tests
