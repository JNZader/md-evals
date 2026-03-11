# Test Architecture Documentation

**Last Updated**: March 11, 2026  
**Test Suite**: 321 tests, 94.95% coverage  
**Architecture**: Layered with fixtures, mocks, and isolation patterns  
**Parallelization**: Safe for parallel execution with pytest-xdist

## Test File Organization

### Directory Structure and Responsibilities

```
tests/
├── conftest.py                    # [Core] Shared fixtures, markers, configuration
│                                   └─ Session fixtures: llm_adapter, providers
│                                   └─ Function fixtures: sample_config, temp directories
│                                   └─ Marker definitions: unit, integration, e2e, etc.
│
├── fixtures/                      # [Organization] Custom fixture modules
│   └── __init__.py               # Exported fixture utilities
│
├── test_*.py                      # [Test Modules] Organized by component
│   ├── test_cli.py               # CLI command testing (18 test classes)
│   ├── test_config.py            # Config parsing and validation
│   ├── test_e2e_workflow.py      # End-to-end workflow tests
│   ├── test_engine.py            # Core evaluation engine logic
│   ├── test_evaluator.py         # Regex & LLM evaluators
│   ├── test_github_models_provider.py  # Provider implementation
│   ├── test_linter.py            # SKILL.md validation
│   ├── test_llm.py               # LLM adapter interface
│   ├── test_performance.py       # Performance benchmarks
│   ├── test_provider_registry.py # Provider registry
│   ├── test_reporter.py          # Report generation
│   └── test_utils.py             # Utility functions
│
└── __init__.py                    # Package marker
```

## Fixture Hierarchy and Dependencies

### Session-Level Fixtures (Expensive, Shared)

These fixtures are created once per test session and shared across all tests:

```python
# tests/conftest.py - Session scope fixtures

@pytest.fixture(scope="session")
def session_temp_dir() -> Generator[Path, None, None]:
    """Temporary directory for entire session.
    
    Scope: Session (created once, used by all tests)
    Cleanup: Automatic after all tests complete
    Usage: Store test files that don't change
    """
    with tempfile.TemporaryDirectory(prefix="md_evals_test_") as tmp_dir:
        yield Path(tmp_dir)

@pytest.fixture(scope="session")
def session_llm_adapter() -> LLMAdapter:
    """Session-level LLM adapter with mock provider.
    
    Scope: Session (expensive, reused)
    Purpose: Avoid repeated LLMAdapter initialization
    Note: All async tests use this adapter
    """
    adapter = LLMAdapter(model="gpt-4o", provider="mock")
    return adapter

@pytest.fixture(scope="session")
def mock_provider_registry() -> Dict[str, Any]:
    """Mock provider implementations.
    
    Scope: Session
    Provides: Mock implementations for all providers
    Note: Mocked to avoid external API calls
    """
    return {
        "github-models": MagicMock(),
        "openai": MagicMock(),
        "anthropic": MagicMock(),
    }
```

### Function-Level Fixtures (Cheap, Isolated)

These fixtures are created fresh for each test function:

```python
# tests/conftest.py - Function scope fixtures

@pytest.fixture
def sample_config() -> EvalConfig:
    """Basic EvalConfig for testing.
    
    Scope: Function (default, fresh for each test)
    Guarantees: Each test gets uncontaminated data
    Use for: Standard test configuration
    """
    return EvalConfig(
        name="test_eval",
        defaults=Defaults(model="gpt-4o", provider="mock"),
        treatments={"CONTROL": Treatment(skill_path=None)},
        tests=[
            Task(
                name="basic_test",
                prompt="Hello {name}",
                variables={"name": "Alice"},
            )
        ]
    )

@pytest.fixture
def temp_config_file(tmp_path) -> Path:
    """Create temporary config file.
    
    Scope: Function
    Parameter: tmp_path (pytest built-in)
    Returns: Path to temporary YAML file
    """
    config_file = tmp_path / "eval.yaml"
    config_file.write_text("""
name: test
defaults:
  model: gpt-4o
  provider: mock
""")
    return config_file

@pytest.fixture
def mock_llm_provider() -> MagicMock:
    """Mock LLM provider for isolated testing.
    
    Scope: Function
    Purpose: Isolate from real API calls
    Returns: MagicMock with .complete() method
    """
    provider = MagicMock()
    provider.complete.return_value = "Mock LLM response"
    return provider
```

### Fixture Dependency Graph

```
┌─────────────────────────────────────────┐
│  Session-Level Fixtures (Expensive)     │
│  ├─ session_temp_dir                    │
│  ├─ session_llm_adapter                 │
│  └─ mock_provider_registry              │
└────────────┬────────────────────────────┘
             │ (depends on)
             ↓
┌─────────────────────────────────────────┐
│  Function-Level Fixtures (Cheap)        │
│  ├─ sample_config                       │
│  ├─ temp_config_file (uses tmp_path)   │
│  ├─ mock_llm_provider                   │
│  └─ Other test data                     │
└────────────┬────────────────────────────┘
             │ (used in)
             ↓
┌─────────────────────────────────────────┐
│  Individual Test Functions              │
│  test_example_case(fixture_name):       │
│      # Test code here                   │
└─────────────────────────────────────────┘
```

## Mock Strategy Overview

### 1. External API Mocking

Mock calls to external services to avoid network dependency:

```python
# Mock GitHub Models API
@patch("md_evals.providers.github_models.requests.post")
def test_github_models_call(mock_post):
    """Test without hitting real API."""
    mock_post.return_value.json.return_value = {
        "choices": [{"message": {"content": "Mocked response"}}]
    }
    
    provider = GitHubModelsProvider(api_key="test")
    result = provider.complete("Test prompt")
    
    assert result == "Mocked response"
    mock_post.assert_called_once()
```

### 2. File System Mocking

Mock file I/O for deterministic testing:

```python
# Mock file operations
@patch("builtins.open", create=True)
def test_config_from_file(mock_open):
    """Test file loading without real files."""
    mock_open.return_value.__enter__.return_value.read.return_value = (
        "name: test\ndefaults:\n  model: gpt-4o"
    )
    
    config = load_config("eval.yaml")
    assert config.name == "test"
```

### 3. Provider Wrapper Pattern

Instead of mocking the provider directly, wrap it:

```python
class LLMProviderWrapper:
    """Wrapper for easier testing."""
    
    def __init__(self, provider=None):
        self._provider = provider or RealProvider()
    
    def complete(self, prompt):
        """Call wrapped provider."""
        return self._provider.complete(prompt)

# In tests
def test_with_wrapper():
    mock_provider = MagicMock()
    wrapper = LLMProviderWrapper(provider=mock_provider)
    wrapper.complete("test")
    mock_provider.complete.assert_called_with("test")
```

### 4. Spy Pattern (Partial Mocking)

Call real implementation but track calls:

```python
from unittest.mock import patch

original_evaluate = RegexEvaluator.evaluate

def test_evaluate_called_correctly(mocker):
    """Spy on real function without replacing it."""
    spy = mocker.spy(RegexEvaluator, 'evaluate')
    
    evaluator = RegexEvaluator(pattern="test", name="test")
    result = evaluator.evaluate("test string")
    
    assert result == True
    spy.assert_called_once()  # Verify it was called
```

## Test Isolation Patterns

### Pattern 1: Test-Local State

Each test manages its own state:

```python
def test_case_1():
    """Test with local state."""
    config = create_test_config()  # Fresh config for this test
    engine = ExecutionEngine(config)
    
    result = engine.run()
    
    assert result.success
    # State is garbage collected after test

def test_case_2():
    """Completely independent test."""
    config = create_test_config()  # Fresh config, not affected by test_case_1
    engine = ExecutionEngine(config)
    
    result = engine.run()
```

### Pattern 2: Fixture Scope Management

Use appropriate fixture scopes for isolation:

```python
@pytest.fixture(scope="function")  # Fresh for each test
def isolated_config():
    return EvalConfig(...)

@pytest.fixture(scope="class")     # Shared within class
def class_config():
    return EvalConfig(...)

@pytest.fixture(scope="session")   # Shared across session
def session_config():
    return EvalConfig(...)

# Tests automatically get proper isolation
class TestSuite:
    def test_1(self, isolated_config):
        # Gets fresh config
        pass
    
    def test_2(self, isolated_config):
        # Gets different fresh config
        pass
```

### Pattern 3: Cleanup and Teardown

Fixtures with cleanup:

```python
@pytest.fixture
def temp_directory():
    """Create temp directory and clean up after test."""
    tmp_dir = tempfile.mkdtemp()
    yield tmp_dir  # Test runs with this directory
    # Automatic cleanup after test
    shutil.rmtree(tmp_dir)

@pytest.fixture
def database_connection():
    """Connect to test database and cleanup."""
    conn = create_test_connection()
    yield conn
    conn.close()  # Cleanup
```

### Pattern 4: Autouse Fixtures for Common Setup

Fixtures that automatically run for all tests in a scope:

```python
@pytest.fixture(autouse=True)
def reset_environment():
    """Reset environment variables before each test."""
    original_env = os.environ.copy()
    yield
    # Restore environment
    os.environ.clear()
    os.environ.update(original_env)

@pytest.fixture(autouse=True)
def clear_cache():
    """Clear any global caches."""
    yield
    # Reset caches after test
    import md_evals.cache
    md_evals.cache.clear_all()
```

## Concurrency and Parallelization Approach

### Test Parallelization Strategy

Tests are organized to be safely parallelizable:

```
┌─────────────────────────────────────┐
│  pytest-xdist Distribution          │
├─────────────────────────────────────┤
│ Worker 1: tests/test_cli.py         │
│ Worker 2: tests/test_config.py      │
│ Worker 3: tests/test_e2e_workflow.py│
│ Worker 4: tests/test_engine.py      │
│ (Distributed with -n 4)             │
└─────────────────────────────────────┘
```

### Safe Parallelization Principles

1. **No Shared State**: Each test is completely independent
   ```python
   # ✅ Good: Each test has its own config
   def test_1(sample_config):
       pass
   
   def test_2(sample_config):  # Fresh copy
       pass
   
   # ❌ Bad: Shared global state
   GLOBAL_STATE = {}
   
   def test_1():
       GLOBAL_STATE["value"] = 1
   
   def test_2():
       assert GLOBAL_STATE["value"] == 1  # Fails if run in different order
   ```

2. **Isolated Resources**: No resource contention
   ```python
   # ✅ Good: Separate temp directories per test
   def test_1(tmp_path):
       file1 = tmp_path / "test1.txt"
   
   def test_2(tmp_path):  # Different tmp_path
       file2 = tmp_path / "test2.txt"
   
   # ❌ Bad: Shared file path
   def test_1():
       with open("/tmp/shared.txt", "w") as f:
           f.write("test1")
   
   def test_2():
       # Race condition: file might not exist or have wrong content
       with open("/tmp/shared.txt", "r") as f:
           content = f.read()
   ```

3. **Marked Serial Tests**: Tests that can't be parallelized
   ```python
   @pytest.mark.serial  # Must run sequentially
   def test_system_state_mutation():
       """Changes global system state."""
       pass
   
   # Run with: pytest -m "not serial" -n 4  # Skip serial tests in parallel
   ```

### Parallel Execution Configuration

```ini
# pytest.ini
[pytest]
# Use with: pytest -n 4
# Or enable by default:
# addopts = -n 4
```

### Load Distribution Strategies

```bash
# Default (eager): Load-balanced distribution
pytest -n 4

# Loadscope: Group tests by scope (class/module)
pytest -n 4 -d loadscope

# Loadfile: Group tests by file
pytest -n 4 -d loadfile

# Performance: 4 workers is optimal (73% speedup)
# 2 workers: 61% speedup
# 8+ workers: Diminishing returns
```

## Module Coverage Map

### Coverage by Component

| Module | File | Coverage | Key Tests | Notes |
|--------|------|----------|-----------|-------|
| **CLI** | `cli.py` | 92% | test_cli.py (100+ tests) | User commands, options |
| **Engine** | `engine.py` | 96% | test_engine.py (32+ tests) | A/B testing logic |
| **Evaluators** | `evaluator.py` | 98% | test_evaluator.py (50+ tests) | Regex & LLM judge |
| **Providers** | `providers/` | 94% | test_*_provider.py (43+ tests) | API integration |
| **Config** | `config.py` | 96% | test_config.py (16+ tests) | YAML parsing |
| **LLM Adapter** | `llm.py` | 93% | test_llm.py (18+ tests) | Provider routing |
| **Linter** | `linter.py` | 97% | test_linter.py (20+ tests) | SKILL.md validation |
| **Reporter** | `reporter.py` | 95% | test_reporter.py (50+ tests) | Output formatting |
| **Models** | `models.py` | 99% | (implicit coverage) | Pydantic models |
| **Utils** | `utils.py` | 100% | test_utils.py (5+ tests) | Utility functions |

### Gap Analysis

**Areas with Good Coverage (>95%)**:
- Core engine logic
- Evaluator implementations
- Configuration parsing
- Linting rules

**Areas Needing Enhancement (<90%)**:
- CLI error paths (difficult to test all edge cases)
- Provider error handling (mocked, limited coverage of real errors)

## Test Configuration Files

### pytest.ini
Defines test discovery, markers, and output format:

```ini
[pytest]
# Test discovery
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*

# Markers
markers =
    unit: Fast tests, no external deps
    integration: Uses fixtures/mocks
    e2e: Full workflow tests
    slow: >1 second duration
    performance: Benchmark tests
    serial: Must run serially

# Coverage
addopts =
    --cov=md_evals
    --cov-report=html
    --cov-report=xml
    -v
```

### pyproject.toml
Additional configuration:

```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"  # Auto mode for async
testpaths = ["tests"]

# Coverage thresholds (optional)
[tool.coverage.report]
fail_under = 96  # Enforce minimum
```

## Running Tests by Component

### Component-Specific Test Runs

```bash
# Test just the evaluator module
pytest tests/test_evaluator.py -v --cov=md_evals.evaluator

# Test just the CLI
pytest tests/test_cli.py -v --cov=md_evals.cli

# Test providers only
pytest tests/test_*_provider.py -v --cov=md_evals.providers

# Test with specific marker
pytest -m unit -v  # Just unit tests
pytest -m integration -v  # Just integration tests
```

## Architecture Design Decisions

### Decision 1: Session-Level vs Function-Level Fixtures

**Choice**: Session-level for expensive resources, function-level for test data

**Rationale**:
- **Session fixtures** (LLMAdapter, mock providers): Initialization is expensive, reusing is fine
- **Function fixtures** (configs, test data): Fresh data ensures test isolation

### Decision 2: Fixture Parameterization

**Choice**: Use `@pytest.mark.parametrize` for multiple test cases

**Rationale**:
- Reduces code duplication
- Clear mapping of inputs to expected outputs
- Easy to add more test cases

### Decision 3: Mock vs Real Implementations

**Choice**: Mock external APIs, use real implementations for internal logic

**Rationale**:
- **Mock**: External APIs (GitHub, OpenAI) - avoids network calls
- **Real**: Internal logic (evaluators, config parsing) - tests actual behavior

### Decision 4: Test Organization

**Choice**: One test file per production module

**Rationale**:
- Easy to find tests for a component
- Tests stay in sync with code
- Clear test-to-production mapping

## Performance Considerations

### Test Execution Time Profile

```
Total: 22.09s (serial) / 6.63s (parallel)

Slowest tests:
├─ Timeout tests (3.01s + 3.00s) - Intentional delays
├─ Performance benchmarks (~1.1s each)
└─ Other tests (<100ms typically)
```

### Optimization Strategies

1. **Skip Slow Tests Locally**: `pytest -m "not slow"`
2. **Run in Parallel**: `pytest -n 4` (73% faster)
3. **Fail Fast**: `pytest -x` (stop on first failure)
4. **Filter Tests**: `pytest -k "pattern"` (run matching tests only)

## Related Documentation

- [TESTING.md](TESTING.md) - How to run tests
- [TEST_DEVELOPMENT_GUIDE.md](TEST_DEVELOPMENT_GUIDE.md) - Writing tests
- [TEST_QUICK_REFERENCE.md](TEST_QUICK_REFERENCE.md) - Command reference
- [TEST_CI_INTEGRATION.md](TEST_CI_INTEGRATION.md) - CI/CD setup
