# Testing Guide for md-evals

**Last Updated**: March 11, 2026  
**Coverage**: 94.95%  
**Test Suite**: 321 tests passing, 2 skipped  
**Execution Time**: 22.09s (serial) / 6.63s (parallel with 4 workers, 73% improvement)

## Quick Start: Running Tests

### Run All Tests
```bash
# Serial execution (default, good for debugging)
pytest

# Parallel execution with 4 workers (recommended for CI)
pytest -n 4

# Parallel execution auto-detect CPU cores
pytest -n auto
```

### Run Specific Tests
```bash
# Run single test file
pytest tests/test_engine.py -v

# Run specific test class
pytest tests/test_engine.py::TestExecutionEngine -v

# Run specific test function
pytest tests/test_engine.py::TestExecutionEngine::test_run_basic -v

# Run tests matching pattern
pytest -k "github_models" -v

# Run tests with specific marker
pytest -m "unit" -v          # Unit tests only
pytest -m "integration" -v   # Integration tests only
pytest -m "e2e" -v          # End-to-end tests only
pytest -m "performance" -v  # Performance tests only
```

### View Coverage Report
```bash
# Generate HTML coverage report
pytest --cov=md_evals --cov-report=html

# View report in browser
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html  # Windows

# Terminal coverage summary
pytest --cov=md_evals --cov-report=term-missing
```

### Run Tests by Category
```bash
# Fast unit tests only (good for TDD)
pytest -m "unit" --durations=0

# Slow tests only
pytest -m "slow"

# Performance benchmarks
pytest -m "performance" -v

# Known failures (documented xfail)
pytest -m "xfail_known" -v

# Tests requiring external providers (mocked in CI)
pytest -m "requires_provider"
```

## Test Organization

### Directory Structure
```
tests/
├── conftest.py                    # Shared fixtures and configuration
├── fixtures/                      # Custom fixture modules
│   └── __init__.py
├── test_cli.py                    # CLI command tests (18 test classes, 100+ tests)
├── test_config.py                 # Configuration parsing tests (16+ tests)
├── test_e2e_workflow.py          # End-to-end workflow tests (45+ tests)
├── test_engine.py                 # Core evaluation engine tests (32+ tests)
├── test_evaluator.py             # Regex & LLM evaluator tests (50+ tests)
├── test_github_models_provider.py # GitHub Models API tests (43 tests)
├── test_linter.py                # SKILL.md linting tests (20+ tests)
├── test_llm.py                   # LLM adapter tests (18+ tests)
├── test_performance.py           # Performance benchmarks (30+ tests)
├── test_provider_registry.py     # Provider registry tests (11 tests)
├── test_reporter.py              # Report generation tests (50+ tests)
└── test_utils.py                 # Utility function tests (5+ tests)
```

### Coverage by Module

| Module | Coverage | Key Tests |
|--------|----------|-----------|
| `md_evals/cli.py` | 92% | CLI commands, option parsing, user interaction |
| `md_evals/engine.py` | 96% | Core evaluation logic, A/B testing, result aggregation |
| `md_evals/evaluators/` | 98% | Regex patterns, LLM judge evaluation, error handling |
| `md_evals/providers/` | 94% | GitHub Models, OpenAI, Anthropic, token handling |
| `md_evals/config.py` | 96% | YAML parsing, validation, defaults |
| `md_evals/linter.py` | 97% | SKILL.md validation, length checks, best practices |
| `md_evals/reporter.py` | 95% | Table, JSON, Markdown output formatting |
| `md_evals/llm.py` | 93% | LLM adapter, provider routing, error handling |
| `md_evals/models.py` | 99% | Pydantic models, validation (high coverage) |
| `md_evals/utils.py` | 100% | Utilities (small module, fully covered) |

## Custom Pytest Markers

Markers help organize and filter tests by type and characteristics.

### Available Markers

#### Test Type Markers
- **`@pytest.mark.unit`** - Fast, isolated tests with no external dependencies
  ```bash
  pytest -m unit  # Run only unit tests
  ```

- **`@pytest.mark.integration`** - Tests using fixtures, mocks, or test services
  ```bash
  pytest -m integration  # Run only integration tests
  ```

- **`@pytest.mark.e2e`** - Full workflow execution (end-to-end tests)
  ```bash
  pytest -m e2e  # Run only E2E tests
  ```

#### Characteristic Markers
- **`@pytest.mark.slow`** - Tests that take >1 second to execute
  ```bash
  pytest -m "not slow"  # Skip slow tests for faster feedback
  ```

- **`@pytest.mark.performance`** - Performance benchmark tests
  ```bash
  pytest -m performance  # Run all benchmarks
  ```

- **`@pytest.mark.xfail_known`** - Known failing tests with documented reasons
  ```bash
  pytest -m xfail_known  # Run known failures to track progress
  ```

- **`@pytest.mark.requires_provider`** - Tests requiring external provider (mocked in CI)
  ```bash
  pytest -m requires_provider  # Run provider-specific tests
  ```

- **`@pytest.mark.asyncio`** - Async tests (pytest-asyncio)
  ```bash
  pytest -m asyncio  # Run async tests
  ```

- **`@pytest.mark.serial`** - Tests that must run serially (not parallelizable)
  ```bash
  pytest -m serial  # Run tests that can't be parallelized
  ```

- **`@pytest.mark.isolated`** - Fully isolated tests (safe for parallel execution)
  ```bash
  pytest -m isolated  # Run only parallelizable tests
  ```

### Combining Markers
```bash
# Run unit tests that are not slow
pytest -m "unit and not slow"

# Run integration or E2E tests
pytest -m "integration or e2e"

# Run all tests except known failures
pytest -m "not xfail_known"
```

## Parallel Execution with pytest-xdist

Parallel test execution dramatically improves feedback speed.

### Configuration Recommendations

| Scenario | Command | Speed | Notes |
|----------|---------|-------|-------|
| **Local development** | `pytest` | 22.09s | Serial (easiest debugging) |
| **CI/CD pipeline** | `pytest -n 4` | 6.63s | **Recommended** (73% faster) |
| **Resource-constrained** | `pytest -n 2` | 9.44s | Conservative (61% faster) |
| **All CPU cores** | `pytest -n auto` | 10.04s | Uses all cores (59% faster) |
| **Scope-based grouping** | `pytest -n 4 -d loadscope` | 7.23s | Groups tests by class/module |

### Enable in CI/CD

Update `.github/workflows/test.yml`:
```yaml
- name: Run Tests
  run: |
    source venv/bin/activate
    pytest -n 4  # Use 4 workers for 73% speedup
```

Or add to `pyproject.toml`:
```toml
[tool.pytest.ini_options]
addopts = ["-n", "4"]  # Enable by default
```

## Common Testing Scenarios

### Scenario 1: Developing a New Feature

1. **Write unit tests first**
   ```bash
   pytest tests/test_new_feature.py -v --durations=0
   ```

2. **Run with minimal overhead**
   ```bash
   pytest tests/test_new_feature.py -m unit --tb=short
   ```

3. **Check coverage for your code**
   ```bash
   pytest tests/test_new_feature.py --cov=md_evals.new_module --cov-report=term-missing
   ```

### Scenario 2: Debugging a Failing Test

1. **Run the specific test with detailed output**
   ```bash
   pytest tests/test_engine.py::TestExecutionEngine::test_run_basic -vvv
   ```

2. **Add print statements (captured output shows with -s)**
   ```bash
   pytest tests/test_engine.py::TestExecutionEngine::test_run_basic -s
   ```

3. **Enable full traceback**
   ```bash
   pytest tests/test_engine.py::TestExecutionEngine::test_run_basic --tb=long
   ```

4. **Use PDB debugger**
   ```bash
   pytest tests/test_engine.py::TestExecutionEngine::test_run_basic --pdb
   ```

### Scenario 3: Testing Against External Provider

```bash
# Mock provider (default, no credentials needed)
pytest tests/test_github_models_provider.py -v

# With real credentials (requires setup)
export GITHUB_TOKEN="your_token"
pytest tests/test_github_models_provider.py --provider-real -v
```

### Scenario 4: Performance Regression Testing

1. **Run all benchmarks**
   ```bash
   pytest -m performance -v
   ```

2. **Generate benchmark report**
   ```bash
   pytest -m performance -v --benchmark-json=benchmark.json
   ```

3. **Compare with baseline**
   ```bash
   # pytest-benchmark can compare runs automatically
   ```

### Scenario 5: Pre-commit Testing

```bash
# Fast unit tests only (for pre-commit)
pytest -m "unit and not slow" --co -q | wc -l  # Count tests

# Run them
pytest -m "unit and not slow"
```

## Troubleshooting Guide

### Problem: "ModuleNotFoundError: No module named 'md_evals'"

**Solution**: Ensure project is installed in development mode
```bash
pip install -e .
# or
pip install -e ".[dev]"
```

### Problem: "fixture 'sample_config' not found"

**Solution**: Fixtures are defined in `conftest.py`. Ensure it's in test directory:
```bash
# Should exist
ls tests/conftest.py

# Check it defines the fixture
grep "def sample_config" tests/conftest.py
```

### Problem: Tests hanging or timing out

**Solutions**:
```bash
# Set timeout (10 seconds)
pytest --timeout=10

# Run with verbose output to see which test hangs
pytest -v --tb=short

# Run serially to identify the problematic test
pytest -n 0  # or just 'pytest'
```

### Problem: Flaky tests (inconsistent pass/fail)

**Common causes and solutions**:
```bash
# Run test multiple times to confirm flakiness
for i in {1..10}; do pytest tests/test_file.py::test_name; done

# Check for:
# 1. Timing issues - use async fixtures properly
# 2. Shared state - check fixture scope
# 3. External dependencies - mock them
```

### Problem: High memory usage during tests

**Solutions**:
```bash
# Run serially instead of parallel
pytest  # not -n 4

# Run only fast unit tests
pytest -m "unit and not slow"

# Monitor memory
pytest --benchmark-only --benchmark-disable-gc
```

### Problem: "Permission denied" errors in temporary directories

**Solution**: Check permissions
```bash
# Ensure venv has correct permissions
chmod -R u+x venv/

# Run with proper environment
source venv/bin/activate
pytest
```

### Problem: GitHub Models provider tests fail with auth error

**Solutions**:
```bash
# Tests mock the provider by default (no token needed)
pytest tests/test_github_models_provider.py

# For real provider tests, set token
export GITHUB_TOKEN="github_pat_..."
pytest tests/test_github_models_provider.py
```

## Performance Tips

### For Local Development
```bash
# 1. Run only unit tests (fastest feedback)
pytest -m unit

# 2. Run only changed test file
pytest tests/test_changed.py

# 3. Use -x to stop at first failure (faster)
pytest -x

# 4. Increase verbosity to understand progress
pytest -vv
```

### For Continuous Integration
```bash
# 1. Parallel execution with 4 workers
pytest -n 4

# 2. Parallel with scope distribution
pytest -n 4 -d loadscope

# 3. Skip slow tests in fast pipeline
pytest -m "not slow" -n 4

# 4. Separate fast and slow test runs
# Fast (in pipeline)
pytest -m "not slow" -n 4

# Slow (separate job)
pytest -m "slow" --timeout=30
```

### Cache Pytest Artifacts
```bash
# pytest creates .pytest_cache
# Keep it between runs for faster startup
# .gitignore includes it by default

# To force clear cache
rm -rf .pytest_cache/
```

## Configuration Files

### pytest.ini
Located in project root. Defines:
- Test discovery patterns (`test_*.py`)
- Custom markers
- Coverage settings
- Output format (JUnit XML, HTML)
- Warning filters

Key settings:
```ini
[pytest]
testpaths = tests          # Where to find tests
python_files = test_*.py   # File naming pattern
python_classes = Test*     # Class naming pattern
python_functions = test_*  # Function naming pattern

addopts =
    --cov=md_evals                    # Coverage target
    --cov-report=html:htmlcov         # HTML report
    --cov-report=xml:coverage.xml     # XML (for CI)
    --strict-markers                  # Fail on unknown markers
    -v                                # Verbose output
```

### pyproject.toml
Contains additional configuration:
```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"  # Auto mode for async tests
testpaths = ["tests"]

# Coverage settings
[tool.coverage.run]
branch = true  # Measure branch coverage
omit = ["*/tests/*"]

[tool.coverage.report]
fail_under = 96  # Enforce minimum coverage (in CI)
```

## Continuous Integration

All test runs are tracked in CI/CD pipeline. See [TEST_CI_INTEGRATION.md](TEST_CI_INTEGRATION.md) for:
- GitHub Actions setup
- Running tests in Docker
- Reporting and artifacts
- Coverage enforcement
- Parallel execution in CI

## Architecture & Advanced Topics

For deeper understanding of how tests are structured, see [TEST_ARCHITECTURE.md](TEST_ARCHITECTURE.md):
- Test file organization
- Fixture hierarchy and dependencies
- Mock strategy overview
- Test isolation patterns
- Concurrency approach

## Next Steps

1. **Read** [TEST_DEVELOPMENT_GUIDE.md](TEST_DEVELOPMENT_GUIDE.md) to learn how to write new tests
2. **Review** [TEST_QUICK_REFERENCE.md](TEST_QUICK_REFERENCE.md) for command cheat sheet
3. **Check** [TEST_COVERAGE_ANALYSIS.md](TEST_COVERAGE_ANALYSIS.md) for module coverage details
4. **Explore** test files in `tests/` directory to see patterns in action

## Related Documentation

- [README.md](../README.md) - Project overview
- [CONTRIBUTING.md](../CONTRIBUTING.md) - Contributing guidelines
- [docs/](../) - Full documentation
