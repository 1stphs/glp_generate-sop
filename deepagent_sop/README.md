# DeepAgent SOP - Complete Autonomous Multi-Agent System

## Overview

DeepAgent SOP is a fully autonomous multi-agent system for SOP (Standard Operating Procedure) generation and optimization. The system uses natural language-driven decision making to autonomously plan, execute, and learn from tasks.

## Architecture

### Core Design Principles

1. **Natural Language Driven**: Main Agent makes autonomous decisions based on task understanding - NO hardcoded workflows
2. **Autonomous Planning**: Each task is planned dynamically, not following fixed sequences
3. **Multi-Agent Collaboration**: Specialized sub-agents work together under Main Agent coordination
4. **Learning Loop**: Reflector extracts insights, Curator updates memory - continuous improvement
5. **Complete Trajectory Recording**: Every decision and execution is logged for auditability

### System Components

#### 1. Main Agent (`core/main_agent.py`)
**Role**: Autonomous orchestrator and decision maker

**Responsibilities**:
- Understand user tasks from natural language
- Autonomously plan execution steps (NOT fixed workflow)
- Dynamically select and coordinate sub-agents
- Record complete trajectory
- Handle learning loop if enabled

**Key Feature**: Completely autonomous - re-plans for every task

#### 2. Sub-Agents (`core/subagents/`)

##### Writer Agent (`writer_agent.py`)
- **Prompt**: Based on `sop_generation/prompts/registry.py`
- **Role**: Generate SOP from protocol and report
- **Input**: original_content, target_generate_content, section_title, memory
- **Output**: sop_type, current_sop (core rules + template + examples), reasoning

##### Simulator Agent (`simulator_agent.py`)
- **Prompt**: Based on `sop_generation/prompts/registry.py` concept
- **Role**: Blind test SOP effectiveness
- **Constraint**: NEVER sees target_generate_content
- **Input**: section_title, original_content, current_sop
- **Output**: simulated_generate_content, reasoning, steps_taken, compliance_check

##### Reviewer Agent (`reviewer_agent.py`)
- **Prompt**: Based on `sop_generation/prompts/registry.py`
- **Role**: Evaluate SOP quality
- **Scope**: Format, structure, template consistency only (NOT factual accuracy)
- **Input**: simulated_generate_content, target_generate_content, original_sop
- **Output**: is_passed, feedback (format_issues, content_issues, missing_elements), detailed_comparison

#### 3. Learning Agents (`core/learning/`)

##### Reflector Agent (`reflector_agent.py`)
- **Prompt**: Based on `ace/prompts/reflector.py`
- **Role**: Extract insights from trajectory
- **Input**: Complete trajectory
- **Output**: insights (with type, content, context, evidence, applicability), summary

##### Curator Agent (`curator_agent.py`)
- **Prompt**: Based on `ace/prompts/curator.py`
- **Role**: Maintain and optimize memory
- **Input**: current memory, new insights
- **Output**: updated_memory, changes_summary, recommendations

#### 4. Utilities (`core/utils/`)

##### Base Agent (`base_agent.py`)
- **Role**: Unified LLM framework
- **Features**: OpenAI/Anthropic support, retry logic, error handling

##### Prompt Manager (`prompt_manager.py`)
- **Role**: Centralized prompt storage
- **Contains**: All agent prompts (writer, simulator, reviewer, reflector, curator, main)

##### Memory Manager (`memory_manager.py`)
- **Role**: Manage memory.md file
- **Structure**: Audit Log + Rules + SOP Templates
- **Features**: Read/write, query rules, log iterations, save SOPs

##### Trajectory Logger (`trajectory_logger.py`)
- **Role**: Record execution trajectory
- **Features**: Log decisions and executions, summary statistics, JSON/Markdown export

## Usage

### Basic Usage

```python
from deepagent_sop import MainAgent

# 1. Configure LLM
llm_config = {
    "api_provider": "openai",
    "model": "gpt-4o",
    "temperature": 0.7,
    "max_tokens": 4096
}

# 2. Initialize Main Agent
main_agent = MainAgent(llm_config=llm_config)

# 3. Execute task
result = main_agent.run(
    user_query="为验证报告章节生成SOP，进行3轮迭代优化",
    enable_learning=True
)

# 4. Access results
print("Task understanding:", result["task_understanding"])
print("Plan:", result["plan"])
print("Final result:", result["final_result"])
print("Summary:", result["summary"])
```

### Advanced Usage

```python
# Custom memory path
main_agent = MainAgent(
    llm_config=llm_config,
    memory_path="path/to/custom/memory.md"
)

# Disable learning (for testing)
result = main_agent.run(
    user_query="Generate SOP",
    enable_learning=False
)

# Access trajectory
trajectory = result["trajectory"]
for step in trajectory:
    print(f"Step {step['step']}: {step['agent']} ({step['type']})")
```

### CLI Usage

The CLI uses configuration from environment variables automatically:

```bash
# Print current configuration
python deepagent_sop/main.py --config

# Run with default configuration
python deepagent_sop/main.py --task "Generate SOP for validation report"

# Run with custom parameters (overrides env config)
python deepagent_sop/main.py \
  --task "Generate SOP" \
  --model "gpt-4o-mini" \
  --temperature 0.5 \
  --no-learning

# Use different memory file
python deepagent_sop/main.py \
  --task "Generate SOP" \
  --memory-path "custom_memory.md"
```

## File Structure

```
deepagent_sop/
├── README.md                          # This file
├── main.py                            # Entry point
├── .env.example                       # Configuration template
├── core/
│   ├── __init__.py
│   ├── config.py                      # Configuration manager
│   ├── base_agent.py                   # DeepAgent base class
│   ├── main_agent.py                   # Main Agent (autonomous orchestrator)
│   ├── subagents/
│   │   ├── __init__.py
│   │   ├── writer_agent.py             # SOP generation
│   │   ├── simulator_agent.py           # Blind testing
│   │   └── reviewer_agent.py           # Quality evaluation
│   ├── learning/
│   │   ├── __init__.py
│   │   ├── reflector_agent.py          # Insight extraction
│   │   └── curator_agent.py           # Memory management
│   └── utils/
│       ├── __init__.py
│       ├── prompt_manager.py            # All prompts
│       ├── memory_manager.py            # Memory.md read/write
│       └── trajectory_logger.py        # Trajectory recording
└── memory/
    └── memory.md                       # Experience database
```

## Key Features

### 1. Autonomous Decision Making

Main Agent does NOT follow hardcoded workflows. Each task triggers autonomous planning:

- **Example 1**: "Generate SOP" → Plans: Writer → Simulator → Reviewer
- **Example 2**: "Check memory" → Plans: Direct memory query, no sub-agents
- **Example 3**: "Generate 5 chapters with iteration" → Plans: Multi-chapter with loops

### 2. Complete Prompt Integration

All prompts are centralized in `prompt_manager.py` and sourced from:

- **Writer/Simulator/Reviewer**: `sop_generation/prompts/registry.py`
- **Reflector/Curator**: `ace/prompts/reflector.py` and `ace/prompts/curator.py`
- **Main**: `agents/master_agent.py`

### 3. Full Self-Contained

All code, prompts, and configuration are in `deepagent_sop/` folder - no cross-referencing other parts of the project.

## Requirements

- Python >= 3.10
- openai >= 1.0.0
- anthropic >= 0.39.0 (optional, for Anthropic provider)
- python-dotenv >= 1.0.0
- httpx >= 0.24.0

## Configuration

DeepAgent SOP uses a centralized configuration system via environment variables.

### Quick Start

1. Copy the example configuration:
```bash
cp deepagent_sop/.env.example deepagent_sop/.env
```

2. Edit `deepagent_sop/.env` with your API keys:
```bash
# For OpenAI-compatible API (recommended)
OPENVIKING_LLM_API_KEY=your_api_key_here
OPENVIKING_LLM_MODEL=gpt-4o
OPENVIKING_LLM_API_BASE=https://aihubmix.com/v1

# Or for direct OpenAI
# OPENAI_API_KEY=your_openai_key
# DEEPAGENT_LLM_PROVIDER=openai

# Or for Anthropic
# ANTHROPIC_API_KEY=your_anthropic_key
# DEEPAGENT_LLM_PROVIDER=anthropic
```

### Configuration Options

| Environment Variable | Default | Description |
|-------------------|----------|-------------|
| `DEEPAGENT_LLM_PROVIDER` | `openai` | LLM provider: `openai` or `anthropic` |
| `OPENVIKING_LLM_MODEL` | `gpt-4o` | Model name for OpenAI-compatible API |
| `OPENVIKING_LLM_API_KEY` | - | API key for OpenAI-compatible API |
| `OPENVIKING_LLM_API_BASE` | `https://aihubmix.com/v1` | Base URL for OpenAI-compatible API |
| `DEEPAGENT_LLM_TEMPERATURE` | `0.7` | LLM generation temperature |
| `DEEPAGENT_LLM_MAX_TOKENS` | `4096` | Max tokens for LLM responses |
| `DEEPAGENT_MEMORY_PATH` | `deepagent_sop/memory/memory.md` | Path to memory file |
| `DEEPAGENT_LEARNING_ENABLED` | `true` | Enable/disable learning loop |
| `DEEPAGENT_DEBUG` | `false` | Enable debug mode |

For a complete list of configuration options, see `deepagent_sop/.env.example`.

## Development

### Running Tests

```bash
python -m pytest deepagent_sop/tests/
```

### Linting

```bash
black deepagent_sop/
mypy deepagent_sop/
```

## License

See project LICENSE file.

## Version

1.0.0 - Initial complete implementation
