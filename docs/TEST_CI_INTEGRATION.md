# Test CI/CD Integration Guide

**Last Updated**: March 11, 2026  
**Coverage Enforcement**: 96%+ (configured but optional)  
**Parallel Execution**: 4 workers for 73% speedup  
**Total Test Time**: 6.63s (parallel) / 22.09s (serial)

## GitHub Actions Setup

### Quick Start: Using Provided Workflow

The project includes GitHub Actions workflow for automated testing:

```yaml
# .github/workflows/test.yml
name: Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ['3.12', '3.13']
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
      - run: pip install -e ".[dev]"
      - run: pytest -n 4 --cov=md_evals
```

### Enabling Parallel Execution in GitHub Actions

Update `.github/workflows/test.yml`:

```yaml
- name: Run Tests with Parallel Execution
  run: |
    pytest -n 4 \
      --cov=md_evals \
      --cov-report=xml \
      --cov-report=term-missing
```

**Performance Benefit**: Reduces test time from 22.09s to ~6.63s (73% speedup)

### Coverage Enforcement in CI

```yaml
# Option 1: Fail if coverage drops below threshold
- name: Check Coverage
  run: |
    pytest --cov=md_evals \
      --cov-fail-under=96 \
      --cov-report=xml

# Option 2: Report coverage without failing build
- name: Report Coverage
  run: |
    pytest --cov=md_evals \
      --cov-report=xml \
      --cov-report=html

# Option 3: Upload to coverage service
- name: Upload Coverage
  uses: codecov/codecov-action@v3
  with:
    files: ./coverage.xml
    flags: unittests
    name: codecov-umbrella
```

## Different CI Platforms

### Jenkins

```groovy
pipeline {
    agent any
    
    stages {
        stage('Install') {
            steps {
                sh 'pip install -e ".[dev]"'
            }
        }
        
        stage('Test') {
            steps {
                sh 'pytest -n 4 --cov=md_evals --cov-report=xml'
            }
        }
        
        stage('Archive Results') {
            steps {
                junit 'test-results.xml'
                publishHTML([
                    reportDir: 'htmlcov',
                    reportFiles: 'index.html',
                    reportName: 'Coverage Report'
                ])
            }
        }
    }
}
```

### GitLab CI

```yaml
# .gitlab-ci.yml
stages:
  - test

test:
  stage: test
  image: python:3.12
  script:
    - pip install -e ".[dev]"
    - pytest -n 4 --cov=md_evals --cov-report=xml --cov-report=html
  artifacts:
    reports:
      junit: test-results.xml
      coverage_report:
        coverage_format: cobertura
        path: coverage.xml
    paths:
      - htmlcov/
  coverage: '/TOTAL.*\s+(\d+%)$/'
```

### Azure Pipelines

```yaml
# azure-pipelines.yml
trigger:
  - main
  - develop

pool:
  vmImage: 'ubuntu-latest'

steps:
  - task: UsePythonVersion@0
    inputs:
      versionSpec: '3.12'

  - script: |
      pip install -e ".[dev]"
      pytest -n 4 --cov=md_evals --cov-report=xml
    displayName: 'Run Tests'

  - task: PublishCodeCoverageResults@1
    inputs:
      codeCoverageTool: cobertura
      summaryFileLocation: coverage.xml
      reportDirectory: htmlcov
```

### CircleCI

```yaml
# .circleci/config.yml
version: 2.1

jobs:
  test:
    docker:
      - image: cimg/python:3.12
    steps:
      - checkout
      - run:
          name: Install dependencies
          command: pip install -e ".[dev]"
      - run:
          name: Run tests
          command: pytest -n 4 --cov=md_evals --cov-report=xml
      - store_test_results:
          path: test-results
      - store_artifacts:
          path: htmlcov
          destination: coverage

workflows:
  test:
    jobs:
      - test
```

## Docker-Based CI

### Dockerfile for Testing

```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml setup.py ./
RUN pip install -e ".[dev]"

COPY . .

CMD ["pytest", "-n", "4", "--cov=md_evals"]
```

### Running Tests in Docker

```bash
# Build image
docker build -t md-evals-tests .

# Run tests
docker run md-evals-tests

# Run with coverage report
docker run -v $(pwd)/htmlcov:/app/htmlcov md-evals-tests \
  pytest -n 4 --cov=md_evals --cov-report=html
```

### Docker Compose for Multi-Service Testing

```yaml
version: '3.8'

services:
  test:
    build: .
    environment:
      - GITHUB_TOKEN=${GITHUB_TOKEN}
    volumes:
      - ./htmlcov:/app/htmlcov
      - ./test-results:/app/test-results
    command: pytest -n 4 --cov=md_evals --cov-report=html --junit-xml=test-results/results.xml
```

## Test Reporting and Artifacts

### Generating Test Reports

```bash
# JUnit XML format (for CI integration)
pytest --junit-xml=test-results.xml

# HTML coverage report
pytest --cov=md_evals --cov-report=html
# Opens at htmlcov/index.html

# JSON report for parsing
pytest --json-report --json-report-file=report.json

# Markdown report
pytest --html=report.html --self-contained-html

# Multiple formats at once
pytest -n 4 \
  --cov=md_evals \
  --cov-report=term-missing \
  --cov-report=html:htmlcov \
  --cov-report=xml:coverage.xml \
  --cov-report=json:coverage.json \
  --junit-xml=test-results.xml
```

### Storing Artifacts in CI

**GitHub Actions**:
```yaml
- uses: actions/upload-artifact@v3
  if: always()
  with:
    name: test-results
    path: |
      htmlcov/
      test-results.xml
      coverage.json
```

**GitLab CI**:
```yaml
artifacts:
  paths:
    - htmlcov/
    - coverage.xml
    - coverage.json
  reports:
    junit: test-results.xml
```

**Jenkins**:
```groovy
archiveArtifacts artifacts: 'htmlcov/**,test-results.xml,coverage.xml'
publishHTML([
    reportDir: 'htmlcov',
    reportFiles: 'index.html',
    reportName: 'Code Coverage'
])
```

## Coverage Enforcement Strategies

### Strategy 1: Strict Enforcement (Recommended)

Fail the build if coverage drops below threshold:

```bash
# In CI/CD pipeline
pytest --cov=md_evals --cov-fail-under=96
```

Configure in `pyproject.toml`:
```toml
[tool.coverage.report]
fail_under = 96
```

### Strategy 2: Gradual Enforcement

Increase coverage requirements over time:

```bash
# Phase 1: 90% requirement
pytest --cov=md_evals --cov-fail-under=90

# Phase 2: 93% requirement  
pytest --cov=md_evals --cov-fail-under=93

# Phase 3: 96% requirement (current)
pytest --cov=md_evals --cov-fail-under=96
```

### Strategy 3: Per-Module Enforcement

Different thresholds for different modules:

```toml
[tool.coverage.report]
# Overall requirement
fail_under = 90

[tool.coverage.report.omit_patterns]
"*/migrations/*" = 50  # Lower for generated code
"*/test_*.py" = 0      # Don't count test files
```

### Strategy 4: Soft Enforcement

Report coverage but don't fail the build:

```bash
# Generate report without failing
pytest --cov=md_evals --cov-report=html --cov-report=term-missing
# Don't use --cov-fail-under
```

## Parallel Execution in CI

### Recommended Configuration for CI

```bash
# Standard 4-worker setup (73% faster)
pytest -n 4 \
  --cov=md_evals \
  --cov-report=xml

# Or auto-detect available cores
pytest -n auto \
  --cov=md_evals
```

### GitHub Actions Example

```yaml
- name: Run Tests in Parallel
  run: |
    pip install pytest-xdist>=3.5.0
    pytest -n 4 \
      --cov=md_evals \
      --cov-report=xml \
      --junit-xml=test-results.xml
```

### Handling Flaky Tests in Parallel

```bash
# Retry failed tests once
pytest -n 4 --reruns 1

# Run serially if parallel fails
pytest -n 4 || pytest --tb=short
```

## Failed Test Debugging in CI

### 1. Capture Full Output

```bash
# Verbose output with all details
pytest -vvv --tb=long --capture=no

# Show print statements
pytest -s

# Show local variables in traceback
pytest -l
```

### 2. Download and Inspect Logs

In GitHub Actions:
1. Go to Actions tab
2. Click failed workflow
3. Download "logs" artifact
4. Search for specific test output

### 3. Reproduce Locally

```bash
# Run exact same command as CI
pytest -n 4 --cov=md_evals --tb=short

# Or run serially for debugging
pytest tests/test_file.py::test_name -vvv --tb=long

# With pdb debugger
pytest tests/test_file.py::test_name --pdb
```

### 4. Common Failure Causes in CI

**Problem**: Tests pass locally but fail in CI

**Solutions**:
```bash
# 1. Match CI environment
python -m pytest  # Use Python module syntax

# 2. Check for hardcoded paths
# Use tmp_path fixture instead of hardcoded /tmp

# 3. Mock external dependencies
# Tests should not rely on network or external services

# 4. Check timezone/locale
# Use UTC and avoid locale-specific formatting

# 5. Run in parallel locally
pytest -n 4  # Match CI parallelization
```

**Problem**: Flaky tests pass sometimes, fail other times

**Solutions**:
```bash
# 1. Run test multiple times
for i in {1..10}; do pytest tests/test_file.py::test_name || break; done

# 2. Remove timing dependencies
# Use mock timers instead of time.sleep()

# 3. Check for shared state
# Each test must be independent

# 4. Use explicit waits instead of sleep
# pytest.mark.timeout or pytest-asyncio with proper async

# 5. Run serially to identify ordering issues
pytest --tb=short -s
```

## Performance Monitoring in CI

### Track Test Performance Over Time

```bash
# Generate benchmark results
pytest -m performance --benchmark-json=benchmark.json

# Commit results to track trends
git add benchmark.json
git commit -m "benchmark: update performance metrics"
```

### Set Performance Budgets

```yaml
# GitHub Actions example
- name: Check Performance
  run: |
    pytest --durations=20  # Show slowest 20 tests
    # Alert if any test takes >1 second
    pytest --durations=20 | grep -E "^[0-9]+\.[0-9]{2}s" && exit 1
```

## CI/CD Best Practices

### 1. Always Run Tests Before Merge

```yaml
# Require CI to pass before merge
# GitHub: Settings → Branches → Require status checks to pass
```

### 2. Test on Multiple Python Versions

```yaml
strategy:
  matrix:
    python-version: ['3.12', '3.13', '3.14']
```

### 3. Run Tests on Every Branch

```yaml
on:
  push:
    branches: '*'  # All branches
  pull_request:
    branches: '*'  # All PRs
```

### 4. Cache Dependencies

```yaml
- uses: actions/setup-python@v5
  with:
    python-version: 3.12
    cache: 'pip'

- run: pip install -e ".[dev]"
```

### 5. Fail Fast on Critical Tests

```bash
# Stop on first failure
pytest -x

# Stop after N failures
pytest --maxfail=3
```

### 6. Notify on Failures

**GitHub Actions**:
```yaml
- name: Notify on Failure
  if: failure()
  run: |
    # Send Slack/email notification
    curl -X POST $SLACK_WEBHOOK_URL \
      -d "{\"text\": \"Tests failed on ${{ github.ref }}\"}"
```

## Secure CI/CD for Testing

### 1. Manage Secrets Safely

```yaml
# Don't log secrets
- name: Run Tests
  env:
    GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
  run: pytest --tb=short  # No -v to hide sensitive values
```

### 2. Validate Dependencies

```bash
# Check for vulnerabilities
pip install safety
safety check

# Or use pip-audit
pip-audit
```

### 3. Isolate Test Environments

```dockerfile
# Use minimal base image
FROM python:3.12-slim

# Don't run as root
RUN useradd -m pytest
USER pytest

# Install only needed dependencies
RUN pip install pytest
```

## Advanced CI/CD Patterns

### Pattern 1: Conditional Test Runs

```yaml
# Only run slow tests on schedule, not on every commit
name: Tests

on:
  push:
    branches: [main]
  pull_request:
  schedule:
    - cron: '0 3 * * *'  # 3 AM daily

jobs:
  fast:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: 3.12
      - run: pip install -e ".[dev]"
      - run: pytest -m "not slow" -n 4

  slow:
    if: github.event_name == 'schedule'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: 3.12
      - run: pip install -e ".[dev]"
      - run: pytest -m "slow"
```

### Pattern 2: Matrix Testing

```yaml
jobs:
  test:
    strategy:
      matrix:
        python-version: ['3.12', '3.13', '3.14']
        provider: ['github-models', 'openai', 'anthropic']
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
      - run: pip install -e ".[dev]"
      - run: pytest tests/test_providers.py -k "${{ matrix.provider }}"
```

### Pattern 3: Coverage Report Publishing

```yaml
- name: Publish Coverage Report
  if: always()
  uses: actions/upload-artifact@v3
  with:
    name: coverage-report-py${{ matrix.python-version }}
    path: htmlcov/

- name: Comment PR with Coverage
  if: github.event_name == 'pull_request'
  uses: py-cov-action/python-coverage-comment-action@v3
  with:
    GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
    MINIMUM_GREEN: 90
    MINIMUM_ORANGE: 70
```

## Troubleshooting CI/CD Issues

### Issue: "ModuleNotFoundError" in CI but not locally

```bash
# Ensure package is installed
pip install -e ".[dev]"  # Install with dev dependencies

# Check Python path
python -c "import sys; print(sys.path)"

# Use explicit module path
python -m pytest instead of pytest
```

### Issue: Tests timeout in CI

```bash
# Increase timeout for CI only
if [[ -n "$CI" ]]; then
  pytest --timeout=60
else
  pytest --timeout=10
fi
```

### Issue: Coverage drops on CI

```bash
# Ensure same conditions as local
python -m pytest --cov=md_evals \
  --cov-report=term-missing \
  --strict-markers
```

## Related Documentation

- [TESTING.md](TESTING.md) - User testing guide
- [TEST_DEVELOPMENT_GUIDE.md](TEST_DEVELOPMENT_GUIDE.md) - Writing tests
- [TEST_ARCHITECTURE.md](TEST_ARCHITECTURE.md) - Test organization
- [TEST_QUICK_REFERENCE.md](TEST_QUICK_REFERENCE.md) - Command cheat sheet
