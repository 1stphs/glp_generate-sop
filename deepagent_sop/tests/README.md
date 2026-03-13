# Tests for DeepAgent SOP

## Quick Start

Make sure you have configured your API keys:

```bash
# Copy and edit configuration
cp deepagent_sop/.env.example deepagent_sop/.env
# Edit deepagent_sop/.env with your API keys
```

## Test Files

### 1. test_writer_agent.py
Simple unit test for Writer Agent only.

**Purpose**: Test if Writer Agent can generate SOP from protocol and report.

**Run**:
```bash
python deepagent_sop/tests/test_writer_agent.py
```

**What it does**:
- Loads test data from `data/workflow-b/`
- Uses Writer Agent to generate SOP for "验证试验名称" section
- Tests the basic SOP generation flow

**Expected output**:
- SOP type (simple_insert, rule_template, complex_composite)
- Core rules extracted from the protocol/report pair
- Template text
- Reasoning process

### 2. test_integration.py
End-to-end integration test for the complete system.

**Purpose**: Test the full Main Agent workflow including planning and execution.

**Run**:
```bash
python deepagent_sop/tests/test_integration.py
```

**What it does**:
- Loads test data from `data/workflow-b/`
- Uses Main Agent to plan and execute SOP generation
- Tests autonomous planning and agent coordination
- (Optional) Runs learning loop

**Expected output**:
- Task understanding from Main Agent
- Execution plan (which agents to call and in what order)
- Final result (generated SOP)
- Trajectory log of all decisions and executions

## Troubleshooting

### "API key not found"
Make sure you've created and configured `deepagent_sop/.env`:
```bash
OPENVIKING_LLM_API_KEY=your_key_here
```

### "Import error"
Make sure you're running from the project root:
```bash
cd /Users/pangshasha/Documents/github/glp_generate-sop
python deepagent_sop/tests/test_writer_agent.py
```

### Timeout errors
If LLM calls timeout, increase the timeout in `.env`:
```bash
DEEPAGENT_LLM_TIMEOUT=120.0
```

## Test Data

Test data is located in `data/workflow-b/`:
- `protocol_content.json`: Two validation protocols
- `report_content.json`: Two validation reports
- `structure.json`: Report section structure

Current tests use the first dataset (protocol_content1, report_content1).
