"""Pytest configuration and shared fixtures for md-evals test suite.

This module provides:
- Session-level fixtures for expensive setup (LLMAdapter, mock providers)
- Autouse fixtures for common setup/teardown
- Fixture parameterization strategies
- Enhanced fixture caching
- Performance tracking and reporting
"""

import pytest
import tempfile
import os
import json
import time
from pathlib import Path
from typing import Dict, Any, Generator
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import datetime

from md_evals.models import (
    EvalConfig, Defaults, Treatment, Task, 
    RegexEvaluator, LLMJudgeEvaluator, ExecutionConfig
)
from md_evals.llm import LLMAdapter
from md_evals.engine import ExecutionEngine


# ============================================================================
# MARKERS - Define custom pytest markers for test categorization
# ============================================================================

def pytest_configure(config):
    """Register custom pytest markers."""
    config.addinivalue_line(
        "markers", "unit: Unit tests (fast, isolated, no external dependencies)"
    )
    config.addinivalue_line(
        "markers", "integration: Integration tests (may use fixtures, mocks, or test services)"
    )
    config.addinivalue_line(
        "markers", "e2e: End-to-end tests (full workflow execution)"
    )
    config.addinivalue_line(
        "markers", "slow: Slow-running tests (>1 second)"
    )
    config.addinivalue_line(
        "markers", "performance: Performance benchmark tests"
    )
    config.addinivalue_line(
        "markers", "xfail_known: Known failing tests (xfail with reason)"
    )
    config.addinivalue_line(
        "markers", "requires_provider: Tests requiring external provider (mocked in CI)"
    )


# ============================================================================
# SESSION-LEVEL FIXTURES - Expensive setup shared across all tests
# ============================================================================

@pytest.fixture(scope="session")
def session_temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for the entire test session.
    
    Yields:
        Path: Temporary directory path that persists for the session
    """
    with tempfile.TemporaryDirectory(prefix="md_evals_test_") as tmp_dir:
        yield Path(tmp_dir)


@pytest.fixture(scope="session")
def session_llm_adapter() -> LLMAdapter:
    """Create a session-level LLMAdapter with mock provider.
    
    This fixture is created once per session to avoid repeated initialization.
    All async tests use this adapter (mocked).
    
    Returns:
        LLMAdapter: Configured LLMAdapter with mock provider
    """
    adapter = LLMAdapter(model="gpt-4o", provider="mock")
    return adapter


@pytest.fixture(scope="session")
def mock_provider_registry():
    """Create mock provider registry for session-level use.
    
    Returns:
        Dict: Mock providers keyed by name
    """
    return {
        "mock": MagicMock(),
        "azure": MagicMock(),
        "github": MagicMock(),
    }


@pytest.fixture(scope="session")
def test_fixtures_dir() -> Path:
    """Get path to test fixtures directory.
    
    Returns:
        Path: Path to tests/fixtures directory
    """
    return Path(__file__).parent / "fixtures"


# ============================================================================
# FUNCTION-LEVEL FIXTURES - Reset between tests for isolation
# ============================================================================

@pytest.fixture
def tmp_path_session(session_temp_dir) -> Path:
    """Provide isolated temporary paths within session temp directory.
    
    Each test gets its own subdirectory within the session temp dir.
    This is faster than creating new temp directories for each test.
    
    Yields:
        Path: Isolated temporary directory for this test
    """
    test_dir = session_temp_dir / f"test_{id(pytest.current_test_node)}"
    test_dir.mkdir(parents=True, exist_ok=True)
    yield test_dir
    # Cleanup handled by session temp dir context manager


@pytest.fixture
def mock_eval_config() -> EvalConfig:
    """Create a minimal valid EvalConfig for testing.
    
    Returns:
        EvalConfig: Basic configuration with required fields
    """
    return EvalConfig(
        name="Test Evaluation",
        defaults=Defaults(
            provider="mock",
            model="gpt-4o",
        ),
        treatments={
            "CONTROL": Treatment(name="CONTROL", provider="mock"),
            "TREATMENT": Treatment(name="TREATMENT", provider="mock"),
        },
        tests=[
            Task(
                name="test_1",
                prompt="What is 2+2?",
                evaluators=[
                    RegexEvaluator(
                        name="contains_4",
                        pattern="4",
                        match_type="contains"
                    )
                ]
            )
        ]
    )


@pytest.fixture
def mock_eval_config_with_llm() -> EvalConfig:
    """Create EvalConfig with LLM judge evaluator for testing.
    
    Returns:
        EvalConfig: Configuration including LLMJudgeEvaluator
    """
    return EvalConfig(
        name="Test with LLM Judge",
        defaults=Defaults(
            provider="mock",
            model="gpt-4o",
        ),
        treatments={
            "CONTROL": Treatment(name="CONTROL"),
            "TREATMENT": Treatment(name="TREATMENT"),
        },
        tests=[
            Task(
                name="test_llm_judge",
                prompt="How creative is this response?",
                evaluators=[
                    LLMJudgeEvaluator(
                        name="creativity",
                        prompt="Rate the creativity of this response on a scale of 1-10.",
                        model="gpt-4o",
                    )
                ]
            )
        ]
    )


@pytest.fixture
def mock_llm_adapter() -> LLMAdapter:
    """Create a mock LLMAdapter for unit tests.
    
    This is mocked per-test (unlike session_llm_adapter).
    
    Returns:
        LLMAdapter: Mock adapter with stubbed provider
    """
    adapter = MagicMock(spec=LLMAdapter)
    adapter.model = "gpt-4o"
    adapter.provider_name = "mock"
    return adapter


@pytest.fixture
def mock_llm_response() -> Dict[str, Any]:
    """Create a mock LLM response for testing.
    
    Returns:
        Dict: Mock response with text and metadata
    """
    return {
        "text": "This is a mock LLM response.",
        "tokens_used": 15,
        "model": "gpt-4o",
        "provider": "mock",
    }


@pytest.fixture
def execution_engine(mock_eval_config, mock_llm_adapter) -> ExecutionEngine:
    """Create an ExecutionEngine for testing.
    
    Returns:
        ExecutionEngine: Configured engine with mock adapter
    """
    return ExecutionEngine(
        config=mock_eval_config,
        llm_adapter=mock_llm_adapter,
        execution_config=ExecutionConfig(
            parallel_workers=1,  # Single-threaded for tests
            timeout_seconds=30,
        )
    )


# ============================================================================
# AUTOUSE FIXTURES - Automatically applied to all tests
# ============================================================================

@pytest.fixture(autouse=True)
def reset_singletons():
    """Reset singleton instances between tests.
    
    Ensures test isolation by clearing any cached singletons.
    """
    # This would be used if there are module-level singletons
    # that need to be reset between tests
    yield
    # Cleanup/reset happens here if needed


@pytest.fixture(autouse=True)
def track_test_duration(request):
    """Track and report test execution duration.
    
    Adds performance metadata to test reports.
    """
    start_time = time.time()
    test_name = request.node.name
    
    yield
    
    duration = time.time() - start_time
    # Mark slow tests
    if duration > 1.0:
        request.node.add_marker(pytest.mark.slow)
    
    # Store duration for reporting
    request.node.duration = duration


@pytest.fixture(autouse=True)
def clear_environment_variables():
    """Clear environment variables before each test.
    
    Ensures tests don't inherit unwanted environment state.
    """
    # Save original environment
    original_env = os.environ.copy()
    
    # Clear test-sensitive variables
    test_vars = [
        "OPENAI_API_KEY",
        "AZURE_OPENAI_API_KEY",
        "GITHUB_TOKEN",
        "LLM_PROVIDER",
    ]
    for var in test_vars:
        os.environ.pop(var, None)
    
    yield
    
    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)


# ============================================================================
# PARAMETRIZATION FIXTURES - Support data-driven testing
# ============================================================================

@pytest.fixture(params=["gpt-4o", "gpt-4-turbo", "claude-3"])
def various_models(request):
    """Parametrized fixture providing different LLM models.
    
    Yields:
        str: Model name from parametrized list
    """
    return request.param


@pytest.fixture(params=["exact", "regex", "contains"])
def evaluator_types(request):
    """Parametrized fixture providing evaluator types.
    
    Yields:
        str: Evaluator type from parametrized list
    """
    return request.param


@pytest.fixture(params=[1, 2, 4, 8])
def parallel_worker_counts(request):
    """Parametrized fixture for parallel worker counts.
    
    Yields:
        int: Worker count from parametrized list
    """
    return request.param


# ============================================================================
# MOCK AND PATCH FIXTURES - Pre-configured mocks for common operations
# ============================================================================

@pytest.fixture
def mock_file_system(tmp_path):
    """Create mock file system for testing file operations.
    
    Args:
        tmp_path: pytest's built-in tmp_path fixture
        
    Returns:
        Dict: Mock file system with common test files
    """
    # Create test files
    eval_file = tmp_path / "eval.yaml"
    eval_file.write_text("""
name: Test Evaluation
defaults:
  provider: mock
  model: gpt-4o
treatments:
  CONTROL:
    name: CONTROL
  TREATMENT:
    name: TREATMENT
tests:
  - name: test_1
    prompt: What is 2+2?
""")
    
    skill_file = tmp_path / "SKILL.md"
    skill_file.write_text("# Test Skill\n\nDescription")
    
    return {
        "root": tmp_path,
        "eval_file": eval_file,
        "skill_file": skill_file,
        "results_dir": tmp_path / "results",
    }


@pytest.fixture
def mock_litellm_completion():
    """Create mock for litellm.completion calls.
    
    Returns:
        MagicMock: Mocked completion function
    """
    mock = AsyncMock()
    mock.return_value = {
        "choices": [
            {
                "message": {
                    "content": "This is a mock response from the LLM."
                }
            }
        ],
        "usage": {
            "prompt_tokens": 10,
            "completion_tokens": 15,
            "total_tokens": 25,
        }
    }
    return mock


@pytest.fixture
def mock_httpx_client(mocker):
    """Create mock httpx.AsyncClient for HTTP requests.
    
    Args:
        mocker: pytest-mock fixture
        
    Returns:
        MagicMock: Mocked AsyncClient
    """
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json = AsyncMock(return_value={"status": "success"})
    mock_response.text = "Success"
    
    mock_client.get = AsyncMock(return_value=mock_response)
    mock_client.post = AsyncMock(return_value=mock_response)
    
    return mock_client


# ============================================================================
# REPORT AND METADATA FIXTURES - For enhanced reporting
# ============================================================================

@pytest.fixture(scope="session")
def test_metadata() -> Dict[str, Any]:
    """Provide test metadata for reporting.
    
    Returns:
        Dict: Metadata about the test run
    """
    return {
        "test_suite": "md-evals",
        "test_date": datetime.now().isoformat(),
        "python_version": pytest.__version__,
        "markers_used": [],
        "slow_tests": [],
    }


# ============================================================================
# HOOKS FOR CUSTOM BEHAVIOR
# ============================================================================

def pytest_collection_modifyitems(config, items):
    """Automatically mark tests based on their location and name.
    
    Args:
        config: pytest config
        items: list of collected test items
    """
    for item in items:
        # Mark all tests in test_performance.py as performance
        if "test_performance" in item.nodeid:
            item.add_marker(pytest.mark.performance)
        
        # Mark all tests in test_e2e as e2e
        if "test_e2e" in item.nodeid:
            item.add_marker(pytest.mark.e2e)
        
        # Mark integration tests
        if "integration" in item.nodeid.lower() or "integration" in item.name.lower():
            item.add_marker(pytest.mark.integration)
        
        # Anything else is unit
        if not any(m.name in ["performance", "e2e", "integration"] for m in item.iter_markers()):
            item.add_marker(pytest.mark.unit)


def pytest_runtest_logreport(report):
    """Hook into test reports for custom reporting.
    
    Args:
        report: test report
    """
    # This could be extended for custom reporting
    pass


@pytest.fixture(scope="session", autouse=True)
def session_report(test_metadata):
    """Generate session-level test report.
    
    Args:
        test_metadata: session metadata
        
    Yields:
        Dict: Report metadata
    """
    yield test_metadata
    
    # Report generation could happen here
    # For now, just provide the metadata


# ============================================================================
# UTILITY FIXTURES
# ============================================================================

@pytest.fixture
def assert_contains():
    """Provide utility for asserting string containment with details.
    
    Returns:
        Callable: Function that asserts and provides detailed error
    """
    def _assert(haystack: str, needle: str, *, msg: str = ""):
        assert needle in haystack, (
            f"{msg}\n"
            f"Expected to find: {needle!r}\n"
            f"In: {haystack!r}"
        )
    return _assert


@pytest.fixture
def assert_matches():
    """Provide utility for regex matching assertions.
    
    Returns:
        Callable: Function that asserts regex match
    """
    import re
    
    def _assert(text: str, pattern: str, *, msg: str = ""):
        if not re.search(pattern, text):
            assert False, (
                f"{msg}\n"
                f"Pattern did not match: {pattern!r}\n"
                f"In text: {text!r}"
            )
    return _assert
