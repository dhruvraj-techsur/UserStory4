# Automated Test-Generation Pipeline

A fully automated, end-to-end test-generation pipeline that can take any user story (in a README.md) plus its code files and produce working tests.

## Architecture

The pipeline consists of 6 main steps:

0. **Fetch code & user story via MCP GitHub** - Clone target repo and extract code + README
1. **Parse acceptance criteria → Gherkin** - Convert markdown acceptance criteria to Gherkin scenarios
2. **Generate test specs** - Create test files based on configuration
3. **Setup test dependencies & fixtures** - Configure mock servers and test data
4. **Update project config** - Modify package.json and test runner configs
5. **Run a smoke test** - Execute generated tests in sandbox
6. **Feedback loop** - Report results back to MCP pipeline

## Requirements

- Python 3.8+
- MCP GitHub server integration
- Node.js (for test runners)
- Docker (for sandbox testing)

## Setup

```bash
pip install -r requirements.txt
npm install -g cucumber-js jest selenium-webdriver
```

## Usage

```bash
python main.py --repo-url <github-repo-url> --config pipeline.config.json
```

## Configuration

See `pipeline.config.json` for pipeline configuration options. 