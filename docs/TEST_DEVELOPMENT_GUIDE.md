# Test Development Guide for md-evals

**Last Updated**: March 11, 2026  
**Target Audience**: Developers writing new tests  
**Coverage Target**: 95%+ for each module

## Introduction

This guide teaches how to write effective tests for md-evals. We follow the **AAA pattern** (Arrange-Act-Assert) and emphasize meaningful coverage over metrics alone.

## Test Structure: AAA Pattern

All tests follow Arrange-Act-Assert pattern for clarity:

```python
def test_engine_runs_evaluation():
    # Arrange: Set up test data and dependencies
    config = EvalConfig(
        name="test",
        defaults=Defaults(model="gpt-4o", provider="mock"),
        treatments={"CONTROL": Treatment(skill_path=None)},
        tests=[Task(name="test1", prompt="Hello {name}", variables={"name": "Alice"})]
    )
    engine = ExecutionEngine(config)
    
    # Act: Execute the code being tested
    results = engine.run()
    
    # Assert: Verify the results
    assert results is not None
    assert len(results.treatments) == 1
    assert results.treatments["CONTROL"]["test1"]["passed"] > 0
```

## Writing Unit Tests

Unit tests are fast, isolated, and test single functions/methods.

### Basic Unit Test Example

```python
# tests/test_utils.py
import pytest
from md_evals.utils import format_duration, parse_yaml_safely

class TestFormatDuration:
    """Tests for duration formatting utility."""
    
    def test_format_seconds(self):
        """Test formatting durations in seconds."""
        # Arrange
        duration_ms = 1500
        
        # Act
        result = format_duration(duration_ms)
        
        # Assert
        assert result == "1.50s"
    
    def test_format_milliseconds(self):
        """Test formatting sub-second durations."""
        duration_ms = 250
        result = format_duration(duration_ms)
        assert result == "250ms"
    
    def test_format_large_duration(self):
        """Test formatting large durations."""
        duration_ms = 60000  # 60 seconds
        result = format_duration(duration_ms)
        assert result == "1m 0s"
```

### Using Fixtures for Setup

Fixtures provide reusable setup/teardown logic:

```python
# tests/conftest.py
@pytest.fixture
def sample_config():
    """Create a basic EvalConfig for testing."""
    return EvalConfig(
        name="test_eval",
        defaults=Defaults(
            model="gpt-4o",
            provider="mock",
            temperature=0.7,
            max_tokens=500
        ),
        treatments={"CONTROL": Treatment(skill_path=None)},
        tests=[
            Task(
                name="basic_test",
                prompt="Hello {name}",
                variables={"name": "Alice"},
                evaluators=[
                    RegexEvaluator(pattern="[Hh]ello", name="has_greeting")
                ]
            )
        ]
    )

# tests/test_engine.py
def test_engine_with_config(sample_config):
    """Test engine initialization with config."""
    engine = ExecutionEngine(sample_config)
    assert engine.config.name == "test_eval"
```

### Parameterized Tests for Multiple Cases

Test the same logic with different inputs:

```python
class TestRegexEvaluator:
    """Tests for regex evaluator."""
    
    @pytest.mark.parametrize("pattern,text,expected", [
        ("hello", "Hello World", True),      # Case-insensitive
        ("world", "hello world", True),      # Pattern exists
        ("xyz", "hello world", False),       # Pattern missing
        ("", "hello", True),                 # Empty pattern matches all
        (r"\d+", "no numbers here", False),  # No digits
        (r"\d+", "123 abc", True),           # Has digits
    ])
    def test_pattern_matching(self, pattern, text, expected):
        """Test various regex patterns."""
        evaluator = RegexEvaluator(pattern=pattern, name="test")
        result = evaluator.evaluate(text)
        assert result == expected
```

## Writing Integration Tests

Integration tests verify interactions between components:

```python
# tests/test_engine.py
@pytest.mark.integration
class TestEngineIntegration:
    """Integration tests for evaluation engine."""
    
    def test_full_evaluation_workflow(self, sample_config, mock_llm_provider):
        """Test complete evaluation from config to results."""
        # Arrange
        engine = ExecutionEngine(sample_config)
        engine.llm_provider = mock_llm_provider
        
        # Act
        results = engine.run()
        
        # Assert
        assert results.success
        assert "CONTROL" in results.treatments
        assert len(results.treatments["CONTROL"]) == len(sample_config.tests)
    
    def test_multiple_treatments_comparison(self, sample_config):
        """Test A/B testing with multiple treatments."""
        # Add another treatment
        sample_config.treatments["WITH_SKILL"] = Treatment(skill_path="./SKILL.md")
        
        engine = ExecutionEngine(sample_config)
        results = engine.run()
        
        # Both treatments should be present
        assert len(results.treatments) == 2
        assert "CONTROL" in results.treatments
        assert "WITH_SKILL" in results.treatments
```

## Writing E2E Tests

End-to-end tests verify complete workflows:

```python
# tests/test_e2e_workflow.py
@pytest.mark.e2e
class TestE2EWorkflow:
    """End-to-end tests for complete workflows."""
    
    def test_full_cli_workflow(self, tmp_path, mock_config_file):
        """Test complete CLI workflow: init → lint → run."""
        # Arrange
        config_path = tmp_path / "eval.yaml"
        
        # Act 1: Initialize
        subprocess.run(["md-evals", "init"], cwd=tmp_path, check=True)
        assert (tmp_path / "eval.yaml").exists()
        assert (tmp_path / "SKILL.md").exists()
        
        # Act 2: Lint
        result = subprocess.run(
            ["md-evals", "lint"],
            cwd=tmp_path,
            capture_output=True
        )
        assert result.returncode == 0
        
        # Act 3: Run
        result = subprocess.run(
            ["md-evals", "run", "--provider", "mock"],
            cwd=tmp_path,
            capture_output=True
        )
        assert result.returncode == 0
        assert b"passed" in result.stdout
```

## Test Patterns & Best Practices

### Pattern 1: Using Mocks for External Dependencies

```python
from unittest.mock import MagicMock, patch

def test_llm_call_with_mock():
    """Test LLM calls without hitting real API."""
    # Arrange
    mock_provider = MagicMock()
    mock_provider.complete.return_value = "Mock response"
    
    adapter = LLMAdapter(model="gpt-4o", provider="mock")
    adapter._provider = mock_provider
    
    # Act
    response = adapter.complete("Test prompt")
    
    # Assert
    assert response == "Mock response"
    mock_provider.complete.assert_called_once_with("Test prompt")
```

### Pattern 2: Testing Async Code

```python
import pytest

@pytest.mark.asyncio
async def test_async_evaluation():
    """Test async evaluation flow."""
    # Arrange
    evaluator = LLMJudgeEvaluator(
        criteria="Is response helpful?",
        name="test"
    )
    
    # Act
    result = await evaluator.evaluate_async("Test response")
    
    # Assert
    assert isinstance(result, bool)
```

### Pattern 3: Testing Error Handling

```python
def test_error_handling():
    """Test proper error handling."""
    # Arrange
    config = EvalConfig(
        name="test",
        defaults=Defaults(model="gpt-4o", provider="mock"),
        treatments={},  # Empty treatments - invalid
        tests=[]
    )
    
    # Act & Assert
    with pytest.raises(ValueError, match="treatments.*required"):
        EvalConfig(**config.dict())
```

### Pattern 4: Testing with Temporary Files

```python
def test_config_file_loading(tmp_path):
    """Test loading config from file."""
    # Arrange
    config_file = tmp_path / "eval.yaml"
    config_file.write_text("""
name: test
version: "1.0"
defaults:
  model: gpt-4o
  provider: mock
treatments:
  CONTROL:
    skill_path: null
tests:
  - name: test1
    prompt: Hello
""")
    
    # Act
    config = load_config(str(config_file))
    
    # Assert
    assert config.name == "test"
    assert "CONTROL" in config.treatments
```

## Fixture Usage Guide

### Fixture Scopes

```python
# Function scope: Created fresh for each test (default)
@pytest.fixture
def fresh_config():
    return EvalConfig(...)

# Class scope: Shared within a test class
@pytest.fixture(scope="class")
def class_shared_config():
    return EvalConfig(...)

# Session scope: Shared across entire test session
@pytest.fixture(scope="session")
def session_llm_adapter():
    return LLMAdapter(model="gpt-4o", provider="mock")
```

### Fixture Dependencies

Fixtures can depend on other fixtures:

```python
@pytest.fixture
def mock_provider():
    """Mock LLM provider."""
    provider = MagicMock()
    provider.complete.return_value = "Mock response"
    return provider

@pytest.fixture
def llm_adapter(mock_provider):
    """LLM adapter using mock provider."""
    adapter = LLMAdapter(model="gpt-4o", provider="mock")
    adapter._provider = mock_provider
    return adapter

def test_with_dependencies(llm_adapter):
    """Test using dependent fixture."""
    response = llm_adapter.complete("Test")
    assert response == "Mock response"
```

### Fixture Cleanup

Use `yield` for setup/teardown:

```python
@pytest.fixture
def temp_directory():
    """Create and clean up temporary directory."""
    tmp_dir = tempfile.mkdtemp()
    yield tmp_dir  # Test runs with this directory
    # Cleanup happens after test
    shutil.rmtree(tmp_dir)
```

## Mocking Strategies

### Strategy 1: Mock External APIs

```python
from unittest.mock import patch

@patch("md_evals.providers.github_models.requests.post")
def test_github_models_api(mock_post):
    """Test without hitting real GitHub API."""
    # Arrange
    mock_post.return_value.json.return_value = {
        "choices": [{"message": {"content": "Mocked response"}}]
    }
    
    # Act
    provider = GitHubModelsProvider(api_key="test_key")
    response = provider.complete("Test prompt")
    
    # Assert
    assert response == "Mocked response"
    mock_post.assert_called_once()
```

### Strategy 2: Mock File System

```python
from unittest.mock import patch, MagicMock

@patch("builtins.open", create=True)
def test_config_loading(mock_open):
    """Test file operations without real files."""
    # Arrange
    mock_open.return_value.__enter__.return_value.read.return_value = """
name: test
defaults:
  model: gpt-4o
  provider: mock
"""
    
    # Act
    config = load_config("eval.yaml")
    
    # Assert
    assert config.name == "test"
```

### Strategy 3: Wrap External Services

```python
class ExternalServiceWrapper:
    """Wrapper around external service for easier testing."""
    
    def __init__(self, service=None):
        self.service = service or ExternalService()
    
    def call_service(self, request):
        """Call wrapped service."""
        return self.service.call(request)

# In tests, inject mock
def test_with_wrapper():
    mock_service = MagicMock()
    wrapper = ExternalServiceWrapper(service=mock_service)
    wrapper.call_service("test")
    mock_service.call.assert_called_once_with("test")
```

## Common Pitfalls & Solutions

### Pitfall 1: Shared State Between Tests

❌ **Bad**: Tests depend on each other or share mutable state
```python
# DON'T DO THIS
test_data = []

def test_add_data():
    test_data.append(1)
    
def test_check_data():
    assert 1 in test_data  # Fails if run in different order
```

✅ **Good**: Each test is independent
```python
def test_add_data():
    data = []
    data.append(1)
    assert 1 in data

def test_check_other_data():
    data = []
    assert len(data) == 0
```

### Pitfall 2: Over-Mocking

❌ **Bad**: Mocking too much loses test value
```python
def test_evaluate():
    evaluator = MagicMock()  # Mocked the whole thing!
    evaluator.evaluate.return_value = True
    assert evaluator.evaluate("test") == True  # Tests the mock, not code
```

✅ **Good**: Mock only external dependencies
```python
def test_evaluate():
    evaluator = RegexEvaluator(pattern="test", name="test")
    # Mock only the external regex engine if needed
    result = evaluator.evaluate("test string")
    assert result == True
```

### Pitfall 3: Hardcoding Test Data

❌ **Bad**: Hardcoded values make tests brittle
```python
def test_format_result():
    result = format_result({"test": "data"})
    assert result == "{'test': 'data'}"  # Fails if format changes slightly
```

✅ **Good**: Test behavior, not exact output
```python
def test_format_result():
    result = format_result({"test": "data"})
    assert "test" in result
    assert "data" in result
    assert isinstance(result, str)
```

### Pitfall 4: Slow Tests

❌ **Bad**: Tests that are unnecessarily slow
```python
def test_evaluation():
    for i in range(1000000):  # Why?
        evaluate("test")
```

✅ **Good**: Test only what's needed
```python
def test_evaluation():
    # Test with meaningful data
    result = evaluate("test")
    assert result is not None
```

### Pitfall 5: Async Test Errors

❌ **Bad**: Forgetting async/await
```python
def test_async_function():
    result = async_function()  # Returns coroutine, not result
    assert result == expected
```

✅ **Good**: Properly handle async
```python
@pytest.mark.asyncio
async def test_async_function():
    result = await async_function()
    assert result == expected
```

## Test Naming Conventions

Follow clear naming that describes the test:

### Format: `test_[component]_[scenario]_[expected_outcome]`

```python
# Good names
def test_regex_evaluator_with_matching_pattern_returns_true():
    """Name describes: what, when, expect"""
    pass

def test_engine_with_empty_treatments_raises_error():
    """Clear what happens in error case"""
    pass

def test_cli_list_command_shows_treatments():
    """Describes the action and result"""
    pass

# Bad names
def test_1():
    """No context"""
    pass

def test_engine():
    """Too vague"""
    pass

def test_something_works():
    """Not specific"""
    pass
```

## Choosing Test Type: Decision Matrix

| Question | Answer | Test Type |
|----------|--------|-----------|
| Tests single function/method? | Yes | **Unit** |
| Calls other functions/services? | Yes | **Integration** |
| Tests entire workflow from user perspective? | Yes | **E2E** |
| Needs external API/file system? | Yes | **Integration/E2E** (with mocks) |
| Measures performance? | Yes | **Performance** |
| Runs in <100ms? | Yes | **Unit** |
| Takes >1 second? | Yes | **Slow** |
| Must run serially? | Yes | **Serial** |

## Performance Testing

Write performance tests to track regressions:

```python
# tests/test_performance.py
@pytest.mark.performance
class TestEvaluatorPerformance:
    """Performance benchmarks for evaluators."""
    
    @pytest.mark.benchmark
    def test_regex_performance(self, benchmark):
        """Benchmark regex evaluation."""
        evaluator = RegexEvaluator(pattern=r"\d+", name="test")
        
        # Run with benchmark decorator
        result = benchmark(evaluator.evaluate, "123 test 456")
        
        assert result == True
    
    def test_batch_evaluation_speed(self):
        """Test batch evaluation doesn't degrade."""
        evaluator = RegexEvaluator(pattern="test", name="test")
        
        start = time.time()
        for _ in range(1000):
            evaluator.evaluate("test string")
        duration = time.time() - start
        
        # Should complete in reasonable time
        assert duration < 1.0  # Less than 1 second for 1000 evaluations
```

## Debugging Tests

### Using pytest flags for debugging

```bash
# Show print statements
pytest tests/test_file.py -s

# Increase verbosity
pytest tests/test_file.py -vv

# Show local variables in tracebacks
pytest tests/test_file.py -l

# Use full traceback
pytest tests/test_file.py --tb=long

# Drop into debugger
pytest tests/test_file.py --pdb
```

### Adding debug output

```python
def test_with_debugging():
    """Test with debug output."""
    result = some_function()
    
    # This will show with pytest -s
    print(f"Debug: result = {result}")
    
    # Or use logging
    import logging
    logger = logging.getLogger(__name__)
    logger.debug(f"Result: {result}")
    
    assert result == expected
```

## Coverage-Driven Testing

### Check coverage for your code

```bash
# Generate coverage for specific module
pytest tests/test_evaluator.py --cov=md_evals.evaluator --cov-report=term-missing

# Find uncovered lines
pytest --cov=md_evals --cov-report=html
open htmlcov/md_evals/evaluator.html  # View in browser
```

### Cover important code paths

```python
def function_with_branches(value):
    if value > 0:
        return "positive"
    elif value < 0:
        return "negative"
    else:
        return "zero"

# Good: Tests all branches
def test_positive():
    assert function_with_branches(5) == "positive"

def test_negative():
    assert function_with_branches(-5) == "negative"

def test_zero():
    assert function_with_branches(0) == "zero"
```

## Next Steps

1. **Review** existing tests in `tests/test_*.py` for patterns
2. **Run** existing tests to understand behavior: `pytest -v`
3. **Write** tests following AAA pattern
4. **Check** coverage: `pytest --cov=md_evals --cov-report=html`
5. **Commit** tests with your changes

## Related Documentation

- [TESTING.md](TESTING.md) - Test running guide
- [TEST_ARCHITECTURE.md](TEST_ARCHITECTURE.md) - Test structure and patterns
- [TEST_QUICK_REFERENCE.md](TEST_QUICK_REFERENCE.md) - Command reference
- [TEST_CI_INTEGRATION.md](TEST_CI_INTEGRATION.md) - CI/CD setup
