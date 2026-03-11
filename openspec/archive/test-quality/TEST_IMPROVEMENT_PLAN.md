# Test Improvement Action Plan

**Based on Test Audit Report**  
**Target:** Improve coverage from 87% → 92% and fix deprecation warnings

---

## Phase 1: Critical Fixes (Week 1)

### 1.1 Register Pytest Marks in pytest.ini

**Current Issue:** Unknown pytest mark warning  
**Fix:** Add custom marks to pytest.ini

```ini
[pytest]
markers =
    integration: marks tests as integration tests
    unit: marks tests as unit tests
    slow: marks tests as slow running
```

**Time:** 15 minutes

---

### 1.2 Fix Deprecation Warnings

**Issue:** `datetime.utcnow()` deprecated in Python 3.12+  
**Impact:** 37 warnings in test output

#### File: `md_evals/engine.py`

**Lines to fix:** 86, 107, 178

```python
# BEFORE
timestamp=datetime.utcnow().isoformat()

# AFTER
timestamp=datetime.now(datetime.UTC).isoformat()
```

#### File: `md_evals/reporter.py`

**Lines to fix:** 194, 195, 230

```python
# BEFORE
"experiment_id": f"eval_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
"timestamp": datetime.utcnow().isoformat(),

# AFTER
"experiment_id": f"eval_{datetime.now(datetime.UTC).strftime('%Y%m%d_%H%M%S')}",
"timestamp": datetime.now(datetime.UTC).isoformat(),
```

**Time:** 30 minutes  
**Test:** Run full test suite to verify no regressions

---

## Phase 2: Expand CLI Tests (Week 1-2)

### Target: Increase cli.py coverage from 71% → 92%

**Missing coverage:**
- Line 37: --debug flag edge case
- Lines 161-165: Help text formatting
- Lines 231-317: Advanced shell completion
- Lines 335, 344, 349: Error message formatting
- Lines 380-382: Performance profiling hooks
- Lines 387-388: Logging configuration
- Lines 473, 477: Custom exception handling

### 2.1 Debug Flag Tests

```python
def test_run_with_debug_enabled():
    """Test --debug flag enables verbose logging"""
    runner = CliRunner()
    result = runner.invoke(cli, ["run", "--debug"])
    # Assert debug output appears in logs

def test_debug_flag_with_invalid_config():
    """Test debug output with invalid config file"""
    runner = CliRunner()
    result = runner.invoke(cli, ["run", "--debug", "--config", "nonexistent.yaml"])
    # Assert error details are verbose
```

**Time:** 30 minutes

### 2.2 Help Message Tests

```python
def test_help_formatting():
    """Test help messages are properly formatted"""
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])
    assert "Usage:" in result.output
    assert "Options:" in result.output

def test_command_help_messages():
    """Test individual command help messages"""
    for cmd in ["init", "run", "lint", "list"]:
        result = runner.invoke(cli, [cmd, "--help"])
        assert result.exit_code == 0
```

**Time:** 30 minutes

### 2.3 Shell Completion Tests

```python
def test_shell_completion_bash():
    """Test bash completion generation"""
    # Test _get_completion_for_parameter()

def test_shell_completion_zsh():
    """Test zsh completion generation"""
    # Similar to bash
```

**Time:** 1 hour

### 2.4 Error Message Formatting

```python
def test_error_message_format_missing_config():
    """Test error message is clear and actionable"""
    # Assert suggests creating with init

def test_error_message_format_invalid_yaml():
    """Test YAML parse error is helpful"""
    # Assert shows line number and problem
```

**Time:** 45 minutes

### 2.5 Logging Configuration

```python
def test_logging_level_configuration():
    """Test log level can be configured"""
    # Test verbose, debug, quiet modes

def test_log_output_to_file():
    """Test logs can be written to file"""
    # Test --log-file option
```

**Time:** 1 hour

---

## Phase 3: Expand GitHub Models Tests (Week 2)

### Target: Increase github_models.py coverage from 78% → 90%

**Missing coverage:**
- Lines 224-230: Specific error recovery
- Lines 288-312: Complex retry logic
- Lines 343-354: Rate limit handling
- Lines 375, 385, 390-396: API response parsing
- Lines 461-462: Error context

### 3.1 Error Recovery Tests

```python
def test_network_error_recovery():
    """Test provider recovers from network errors"""
    # Mock network timeout, expect retry

def test_malformed_response_handling():
    """Test handling of malformed API responses"""
    # Mock invalid JSON response

def test_partial_token_deduction():
    """Test correct token deduction on partial failures"""
    # Verify token accounting with retries
```

**Time:** 1 hour

### 3.2 Rate Limit Tests

```python
def test_rate_limit_backoff():
    """Test exponential backoff on rate limits"""
    # Mock 429 response, verify backoff timing

def test_rate_limit_header_parsing():
    """Test correct parsing of rate limit headers"""
    # Verify X-RateLimit-Remaining parsing

def test_rate_limit_context():
    """Test error includes rate limit context"""
    # Verify error message mentions when limits reset
```

**Time:** 1 hour

### 3.3 API Response Parsing

```python
def test_streaming_response_parsing():
    """Test parsing of streaming responses"""
    # Handle chunked responses

def test_response_with_null_fields():
    """Test handling of null/missing fields"""
    # Graceful handling

def test_response_with_extra_fields():
    """Test ignoring unexpected fields"""
    # Forward compatibility
```

**Time:** 1 hour

---

## Phase 4: Add E2E Tests (Week 2-3)

### 4.1 Full Workflow Test

**Create:** `tests/test_e2e_workflow.py`

```python
def test_full_evaluation_workflow(tmp_path):
    """Test complete workflow: init → config → run → report"""
    # 1. Initialize project
    runner = CliRunner()
    result = runner.invoke(cli, ["init"], input="n")
    assert result.exit_code == 0
    
    # 2. Run evaluation
    result = runner.invoke(cli, ["run"])
    assert result.exit_code == 0
    
    # 3. Verify output files
    assert (tmp_path / "results.json").exists()
    
    # 4. Verify report generation
    assert "Control" in output
    assert "Treatment" in output

def test_multiple_provider_evaluation():
    """Test evaluation with different providers"""
    # Test with github-models, openai, etc.

def test_evaluation_with_multiple_treatments():
    """Test A/B testing with multiple treatments"""
    # Run with CONTROL + WITH_SKILL + WITH_SKILL_V2

def test_result_export_all_formats():
    """Test exporting results in all formats"""
    # JSON, Markdown, Table
```

**Time:** 1.5 hours

### 4.2 Integration Tests

**Mark with:** `@pytest.mark.integration`

```python
@pytest.mark.integration
def test_github_models_real_api_call():
    """Test real API call to GitHub Models (requires token)"""
    # Only runs with GITHUB_TOKEN set
    # Uses skip if token not available

@pytest.mark.integration
def test_openai_real_api_call():
    """Test real API call to OpenAI"""
```

**Time:** 1 hour

---

## Phase 5: Add Performance Tests (Week 3)

### 5.1 Performance Benchmarks

**Create:** `tests/test_performance.py`

```python
import pytest

@pytest.mark.slow
@pytest.mark.benchmark
def test_evaluation_performance(benchmark):
    """Benchmark evaluation execution speed"""
    # Should complete 100 tests in < 2 seconds

@pytest.mark.benchmark
def test_config_loading_performance(benchmark):
    """Benchmark YAML config loading"""
    # Should load in < 100ms

@pytest.mark.benchmark
def test_report_generation_performance(benchmark):
    """Benchmark report generation"""
    # Should generate report in < 500ms
```

**Time:** 1.5 hours

---

## Phase 6: Add pytest Configuration (Week 3)

### 6.1 pytest.ini Enhancement

```ini
[pytest]
# Marker definitions
markers =
    integration: Integration tests requiring external services
    unit: Unit tests (fast, isolated)
    slow: Slow-running tests
    benchmark: Performance benchmark tests

# Test discovery
python_files = test_*.py
python_classes = Test*
python_functions = test_*

# Coverage options
addopts = 
    --cov=md_evals
    --cov-report=term-missing
    --cov-report=html
    --cov-report=xml
    --strict-markers
    -v

# Ignore warnings we can't control
filterwarnings =
    ignore::DeprecationWarning:jsonschema
    ignore::PytestUnknownMarkWarning

# Output options
junit_family = xunit2
```

**Time:** 30 minutes

---

## Phase 7: Add Parallel Test Execution (Week 3)

### 7.1 Install pytest-xdist

```bash
pip install pytest-xdist
```

### 7.2 Update pytest.ini

```ini
[pytest]
addopts = -n auto  # Use all CPU cores
```

### 7.3 Expected Results

- Current: ~4.9 seconds
- With parallelization: ~2.5 seconds (50% faster)

**Time:** 30 minutes

---

## Phase 8: Test Documentation (Week 4)

### 8.1 Add Test Docstrings

For each test file, add comprehensive docstrings explaining:
- What is being tested
- Why it matters
- What scenarios are covered
- Expected behavior

**Example:**

```python
class TestRegexEvaluator:
    """
    Test regex evaluation logic.
    
    Covers:
    - Simple pattern matching
    - Complex regex patterns
    - Case sensitivity
    - Unicode/special characters
    - Edge cases (empty strings, long strings)
    """
    
    def test_simple_pattern_match(self):
        """Test matching simple literal patterns"""
        # Test body...
```

**Time:** 2-3 hours

---

## Summary Timeline

| Phase | Focus | Effort | Estimated Days |
|-------|-------|--------|-----------------|
| 1 | Deprecation warnings + pytest.ini | 45 min | 0.5 |
| 2 | CLI coverage expansion | 4-5 hrs | 2-3 |
| 3 | GitHub Models expansion | 3-4 hrs | 2 |
| 4 | E2E workflow tests | 2.5 hrs | 1-2 |
| 5 | Performance benchmarks | 1.5 hrs | 1 |
| 6 | pytest configuration | 30 min | 0.5 |
| 7 | Parallel execution | 30 min | 0.5 |
| 8 | Documentation | 2-3 hrs | 2 |
| **TOTAL** | | **14-17 hrs** | **9-11 days** |

---

## Coverage Target Progression

```
Current:  87% overall
                │
Phase 1:  87% (warnings fixed, no code change)
                │
Phase 2:  89% (+2% CLI coverage)
                │
Phase 3:  91% (+2% GitHub Models)
                │
Phase 4:  93% (+2% E2E tests)
                │
Target:   92%+ (all phases)
```

---

## Success Criteria

- ✅ 0 deprecation warnings
- ✅ All custom pytest marks registered
- ✅ CLI coverage ≥ 90%
- ✅ GitHub Models coverage ≥ 90%
- ✅ E2E test suite created
- ✅ Performance benchmarks in place
- ✅ Parallel test execution enabled
- ✅ All tests documented
- ✅ Overall coverage ≥ 92%

---

## Quick Start Commands

```bash
# Phase 1: Run after fixes
pytest --tb=short -v

# Phase 2-3: Test CLI and providers
pytest tests/test_cli.py tests/test_github_models_provider.py -v

# Phase 4: Run E2E tests
pytest tests/test_e2e_workflow.py -v

# Phase 5: Run benchmarks
pytest -m benchmark -v

# All with parallelization
pytest -n auto -v

# Coverage report
pytest --cov=md_evals --cov-report=html
# Open htmlcov/index.html
```

---

## Maintenance

**After improvements:**
- Run full test suite in CI before each merge
- Track coverage trends quarterly
- Update performance benchmarks as code evolves
- Keep test documentation in sync with code

