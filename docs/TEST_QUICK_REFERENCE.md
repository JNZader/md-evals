# Test Quick Reference Guide

**Last Updated**: March 11, 2026  
**Purpose**: Quick commands and patterns for daily testing work

## Essential Commands

### Run Tests
```bash
# All tests (serial)
pytest

# All tests (parallel - recommended for CI)
pytest -n 4

# All tests (auto-detect cores)
pytest -n auto

# Specific file
pytest tests/test_engine.py

# Specific class
pytest tests/test_engine.py::TestExecutionEngine

# Specific test
pytest tests/test_engine.py::TestExecutionEngine::test_run_basic

# Pattern match
pytest -k "engine"
```

### View Coverage
```bash
# Terminal report
pytest --cov=md_evals --cov-report=term-missing

# HTML report
pytest --cov=md_evals --cov-report=html
open htmlcov/index.html

# XML report (for CI)
pytest --cov=md_evals --cov-report=xml
```

### Filter by Marker
```bash
# Unit tests only
pytest -m unit

# Integration tests
pytest -m integration

# E2E tests
pytest -m e2e

# Performance tests
pytest -m performance

# Not slow tests
pytest -m "not slow"

# Multiple markers
pytest -m "unit and not slow"
```

### Debugging
```bash
# Verbose output
pytest -vv

# Show print statements
pytest -s

# First failure stops run
pytest -x

# Drop into debugger
pytest --pdb

# Show local variables
pytest -l

# Full traceback
pytest --tb=long
```

## Pytest Markers Reference

| Marker | Command | Use Case |
|--------|---------|----------|
| `unit` | `pytest -m unit` | Fast unit tests |
| `integration` | `pytest -m integration` | Component tests |
| `e2e` | `pytest -m e2e` | Full workflows |
| `slow` | `pytest -m "not slow"` | Quick feedback |
| `performance` | `pytest -m performance` | Benchmarks |
| `serial` | `pytest -m "not serial" -n 4` | Parallel-safe tests |
| `asyncio` | `pytest -m asyncio` | Async tests |
| `xfail_known` | `pytest -m xfail_known` | Known failures |

## Fixture Quick Reference

### Session-Level (Expensive)
```python
@pytest.fixture(scope="session")
def session_llm_adapter() -> LLMAdapter:
    return LLMAdapter(model="gpt-4o", provider="mock")

@pytest.fixture(scope="session")
def session_temp_dir() -> Path:
    with tempfile.TemporaryDirectory() as tmp:
        yield Path(tmp)
```

### Function-Level (Cheap)
```python
@pytest.fixture
def sample_config() -> EvalConfig:
    return EvalConfig(...)

@pytest.fixture
def mock_provider() -> MagicMock:
    return MagicMock()

@pytest.fixture
def temp_config_file(tmp_path) -> Path:
    return tmp_path / "eval.yaml"
```

## Coverage Commands

| Goal | Command |
|------|---------|
| Check overall coverage | `pytest --cov=md_evals --cov-report=term-missing` |
| Module-specific | `pytest --cov=md_evals.engine` |
| See HTML report | `pytest --cov && open htmlcov/index.html` |
| Enforce minimum | `pytest --cov-fail-under=96` |
| JSON output | `pytest --cov-report=json:coverage.json` |
| XML for CI | `pytest --cov-report=xml:coverage.xml` |

## Parallel Execution Cheat Sheet

```bash
# 4 workers (recommended, 73% faster)
pytest -n 4

# Auto-detect CPU cores
pytest -n auto

# 2 workers (conservative, 61% faster)
pytest -n 2

# Scope-based distribution
pytest -n 4 -d loadscope

# Check for parallelization issues
pytest --co -q  # Count tests
pytest -n 4      # Run in parallel
```

## Report Generation

```bash
# All reports at once
pytest -n 4 \
  --cov=md_evals \
  --cov-report=term-missing \
  --cov-report=html:htmlcov \
  --cov-report=xml:coverage.xml \
  --cov-report=json:coverage.json \
  --junit-xml=test-results.xml

# JSON report for analysis
pytest --json-report --json-report-file=report.json

# HTML report with screenshots
pytest --html=report.html --self-contained-html

# Markdown report
pytest --html=report.md
```

## Common Test Patterns

### Basic Test
```python
def test_function_returns_expected_value():
    result = function_under_test()
    assert result == expected
```

### Test with Fixture
```python
def test_with_config(sample_config):
    engine = ExecutionEngine(sample_config)
    assert engine.config.name == "test_eval"
```

### Parameterized Test
```python
@pytest.mark.parametrize("input,expected", [
    ("test", True),
    ("other", False),
])
def test_multiple_cases(input, expected):
    assert evaluate(input) == expected
```

### Async Test
```python
@pytest.mark.asyncio
async def test_async_function():
    result = await async_function()
    assert result == expected
```

### Error Test
```python
def test_raises_error():
    with pytest.raises(ValueError, match="message"):
        function_that_raises()
```

### Mock Test
```python
def test_with_mock(mocker):
    mock = mocker.patch("module.function")
    mock.return_value = "mocked"
    assert function() == "mocked"
```

## Performance Benchmarks

### View slowest tests
```bash
pytest --durations=10
```

### Run only performance tests
```bash
pytest -m performance -v
```

### Benchmark-specific test
```bash
pytest tests/test_performance.py::TestRegexPerformance -v
```

## Troubleshooting Commands

| Problem | Solution |
|---------|----------|
| Module not found | `pip install -e ".[dev]"` |
| Tests hanging | `pytest --timeout=10` |
| Flaky test | `for i in {1..10}; do pytest tests/test.py::test_name || break; done` |
| Slow tests | `pytest -m "not slow"` |
| Import errors | `python -m pytest` (instead of just `pytest`) |
| Fixture not found | `pytest --fixtures` (see available fixtures) |

## Advanced Commands

### List available tests
```bash
pytest --co -q  # Quiet collection
pytest --co     # Detailed collection
```

### List available fixtures
```bash
pytest --fixtures tests/test_file.py
```

### Show test graph
```bash
pytest --setup-show tests/test_file.py::test_name
```

### Fail on first error
```bash
pytest -x  # Stop on first failure
pytest -x -v  # Verbose + stop first
```

### Run with warnings as errors
```bash
pytest -W error
```

### Cache tests in order
```bash
pytest --cache-clear  # Clear cache
pytest --lf           # Last failed
pytest --ff           # Failed first
```

## One-Liners for Common Tasks

```bash
# Quick check: run unit tests
pytest -m unit --tb=short

# Pre-commit: fast tests, coverage check
pytest -m "unit and not slow" --cov=md_evals --cov-fail-under=95

# CI pipeline: full tests with reports
pytest -n 4 --cov=md_evals --cov-report=xml --cov-report=html --junit-xml=results.xml

# Debug failing test
pytest tests/test_file.py::test_name -vvv --tb=long -s --pdb

# Performance regression check
pytest -m performance --benchmark-json=bench.json

# Find uncovered code
pytest --cov=md_evals --cov-report=html && open htmlcov/index.html

# Run tests that match pattern
pytest -k "github_models" -v

# Run all except slow
pytest -m "not slow" -n 4

# Parallel with coverage
pytest -n 4 --cov=md_evals --cov-report=term-missing

# Development: watch mode (requires pytest-watch)
ptw -- -n 4 -m "not slow"
```

## Configuration Quick Ref

### pytest.ini Key Settings
```ini
[pytest]
testpaths = tests              # Where to find tests
markers = unit, integration    # Available markers
addopts = --cov=md_evals      # Default options
```

### Enabling Parallel by Default
```ini
[pytest]
addopts = -n 4  # Use 4 workers for all runs
```

### Environment Variables
```bash
PYTHONPATH=.        # Include current dir
PYTEST_TIMEOUT=10   # 10 second timeout
CI=true            # Mark as CI environment
```

## Test File Templates

### Minimal Unit Test
```python
import pytest
from md_evals.module import Function

class TestFunction:
    def test_basic_case(self):
        result = Function()
        assert result == expected
    
    def test_error_case(self):
        with pytest.raises(ValueError):
            Function(invalid_input)
```

### Integration Test
```python
@pytest.mark.integration
class TestIntegration:
    def test_with_fixture(self, sample_config, mock_provider):
        engine = ExecutionEngine(sample_config)
        engine.provider = mock_provider
        
        result = engine.run()
        
        assert result.success
```

### E2E Test
```python
@pytest.mark.e2e
def test_full_workflow(tmp_path):
    # Setup
    config_file = tmp_path / "eval.yaml"
    
    # Act
    subprocess.run(["md-evals", "run"], cwd=tmp_path)
    
    # Verify
    assert (tmp_path / "results").exists()
```

## Report Artifacts

After running tests, you'll have:
- `htmlcov/index.html` - Coverage report (open in browser)
- `coverage.xml` - Cobertura format (for CI)
- `coverage.json` - JSON format (for parsing)
- `test-results.xml` - JUnit format (for CI)
- `test_run.log` - Detailed test logs

## Performance Baselines

| Configuration | Time | Tests |
|---------------|------|-------|
| Serial | 22.09s | 321 |
| Parallel (4w) | 6.63s | 321 |
| Unit only | ~5s | ~280 |
| Fast (no slow) | ~10s | ~290 |

## Key Shortcuts

```bash
# Commonly used combinations
alias pytest-fast='pytest -m "not slow" --tb=short'
alias pytest-parallel='pytest -n 4 --cov=md_evals'
alias pytest-debug='pytest -vvv -s --tb=long --pdb'

# Use them
pytest-fast    # Quick local run
pytest-parallel # Full test suite fast
pytest-debug   # Debug specific test
```

## Resources

- Full testing guide: [TESTING.md](TESTING.md)
- Development guide: [TEST_DEVELOPMENT_GUIDE.md](TEST_DEVELOPMENT_GUIDE.md)
- Architecture: [TEST_ARCHITECTURE.md](TEST_ARCHITECTURE.md)
- CI/CD setup: [TEST_CI_INTEGRATION.md](TEST_CI_INTEGRATION.md)
- Coverage details: [TEST_COVERAGE_ANALYSIS.md](TEST_COVERAGE_ANALYSIS.md)
