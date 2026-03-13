# Tests Directory

## Overview

This directory contains test entry points for the DeepAgent system.

## Test Files

### `test_master_agent.py`

Tests Master Agent's autonomous decision-making capabilities.

#### Test Cases
- Natural language task understanding
- Autonomous planning and decomposition
- Dynamic agent selection
- Execution coordination
- Result aggregation

### `test_ace_flow.py`

Tests the complete ACE subsystem flow.

#### Test Cases
- Audit log recording
- Rules management
- SOP template management
- Reflection quality assessment
- Curation rule extraction

### `test_integration.py`

Tests the complete end-to-end workflow.

#### Test Cases
- Two-call pattern (trajectory → insights → playbook)
- Agent coordination
- Data persistence
- Quality tracking

## Running Tests

### Setup

```bash
# Ensure Python environment is set up
python --version  # Python 3.10+

# Install dependencies
pip install -r requirements.txt
```

### Execute

```bash
# Run all tests
python tests/test_integration.py

# Run specific test
python tests/test_master_agent.py
```

## Expected Output

### Success Criteria
- All tests pass without errors
- Output files are generated correctly
- Data formats match schema
- Quality metrics are tracked

### Verification

After running tests:
1. Check `agent_memory/` directories for generated files
2. Verify JSON format with `jq . <file>` or similar
3. Review log outputs for any warnings
4. Validate data integrity

## Test Data

Tests use data from `data/` directory:
- `protocol_content.json`
- `report_content.json`
- `structure.json`

Ensure test data is available before running tests.

## Debugging

### Enable Verbose Logging

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Check Intermediate Results

Each test should:
1. Print task understanding
2. Print execution plan
3. Print agent outputs
4. Print final summary

## Continuous Integration

Tests can be integrated with CI/CD:
- GitHub Actions
- GitLab CI
- Jenkins

Example workflow:
1. Run tests on every push
2. Run tests on every PR
3. Report coverage metrics
