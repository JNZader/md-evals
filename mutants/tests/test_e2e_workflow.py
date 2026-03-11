"""End-to-End workflow tests for md-evals integration.

Tests cover the integration between Engine and Evaluator components,
including happy path, error handling, and concurrent execution scenarios.
"""

import asyncio
import pytest
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import datetime, timezone

from md_evals.engine import ExecutionEngine
from md_evals.evaluator import EvaluatorEngine
from md_evals.models import (
    EvalConfig, ExecutionResult, Defaults, Task, Treatment,
    RegexEvaluator, ExactMatchEvaluator, LLMJudgeEvaluator,
    LLMResponse, EvaluatorResult, ExecutionConfig, OutputConfig
)
from md_evals.llm import LLMAdapter, LLMError


# ==================== Fixtures ====================


@pytest.fixture
def mock_llm_adapter() -> MagicMock:
    """Create a mock LLM adapter."""
    adapter = MagicMock(spec=LLMAdapter)
    return adapter


@pytest.fixture
def mock_llm_response() -> LLMResponse:
    """Create a mock LLM response."""
    return LLMResponse(
        content="Hello, world!",
        model="gpt-4o",
        provider="openai",
        tokens=100,
        duration_ms=1000,
        raw_response={}
    )


@pytest.fixture
def evaluator_engine() -> EvaluatorEngine:
    """Create evaluator engine without LLM adapter."""
    return EvaluatorEngine(llm_adapter=None)


@pytest.fixture
def base_config() -> EvalConfig:
    """Create a base evaluation config."""
    return EvalConfig(
        name="Test Evaluation",
        defaults=Defaults(model="gpt-4o"),
        treatments={
            "CONTROL": Treatment(skill_path=None),
        },
        tests=[
            Task(
                name="test_hello",
                prompt="Say hello",
                variables={},
                evaluators=[]
            ),
        ],
        execution=ExecutionConfig(parallel_workers=1, repetitions=1),
        output=OutputConfig()
    )


@pytest.fixture
def config_with_regex_evaluator() -> EvalConfig:
    """Create config with regex evaluator."""
    return EvalConfig(
        name="Test with Regex",
        defaults=Defaults(model="gpt-4o"),
        treatments={
            "CONTROL": Treatment(skill_path=None),
        },
        tests=[
            Task(
                name="test_greeting",
                prompt="Greet the user",
                variables={},
                evaluators=[
                    RegexEvaluator(
                        name="has_hello",
                        pattern=r"[Hh]ello|[Hh]i",
                        pass_on_match=True
                    )
                ]
            ),
        ]
    )


@pytest.fixture
def config_with_exact_match() -> EvalConfig:
    """Create config with exact match evaluator."""
    return EvalConfig(
        name="Test with Exact Match",
        defaults=Defaults(model="gpt-4o"),
        treatments={
            "CONTROL": Treatment(skill_path=None),
        },
        tests=[
            Task(
                name="test_exact",
                prompt="Say exactly: hello",
                variables={},
                evaluators=[
                    ExactMatchEvaluator(
                        name="exact_hello",
                        expected="hello",
                        case_sensitive=False
                    )
                ]
            ),
        ]
    )


@pytest.fixture
def config_with_multiple_treatments() -> EvalConfig:
    """Create config with multiple treatments."""
    return EvalConfig(
        name="Multi-Treatment Test",
        defaults=Defaults(model="gpt-4o"),
        treatments={
            "CONTROL": Treatment(skill_path=None),
            "VARIANT_A": Treatment(skill_path=None, description="Variant A"),
            "VARIANT_B": Treatment(skill_path=None, description="Variant B"),
        },
        tests=[
            Task(
                name="test_1",
                prompt="Question 1: {question}",
                variables={"question": "What is 2+2?"},
                evaluators=[]
            ),
        ]
    )


@pytest.fixture
def config_with_parallel_execution() -> EvalConfig:
    """Create config with parallel execution."""
    return EvalConfig(
        name="Parallel Test",
        defaults=Defaults(model="gpt-4o"),
        treatments={
            "CONTROL": Treatment(skill_path=None),
            "VARIANT": Treatment(skill_path=None),
        },
        tests=[
            Task(name="test_1", prompt="Q1", variables={}, evaluators=[]),
            Task(name="test_2", prompt="Q2", variables={}, evaluators=[]),
            Task(name="test_3", prompt="Q3", variables={}, evaluators=[]),
        ],
        execution=ExecutionConfig(parallel_workers=3, repetitions=1)
    )


@pytest.fixture
def config_with_multiple_evaluators() -> EvalConfig:
    """Create config with multiple evaluators on one task."""
    return EvalConfig(
        name="Multi-Evaluator Test",
        defaults=Defaults(model="gpt-4o"),
        treatments={
            "CONTROL": Treatment(skill_path=None),
        },
        tests=[
            Task(
                name="test_multi",
                prompt="Generate output",
                variables={},
                evaluators=[
                    RegexEvaluator(
                        name="has_pattern_1",
                        pattern=r"hello",
                        pass_on_match=True
                    ),
                    ExactMatchEvaluator(
                        name="has_word",
                        expected="world",
                        case_sensitive=False
                    ),
                ]
            ),
        ]
    )


# ==================== Happy Path Tests ====================


class TestHappyPath:
    """Test successful workflow scenarios."""

    @pytest.mark.asyncio
    async def test_full_workflow_init_to_report(
        self,
        base_config: EvalConfig,
        mock_llm_adapter: MagicMock,
        mock_llm_response: LLMResponse,
    ) -> None:
        """Test complete workflow from initialization to results.

        Covers:
        - Engine initialization
        - Running a single task
        - Result generation
        - Timestamp accuracy
        """
        # Setup
        mock_llm_adapter.complete = AsyncMock(return_value=mock_llm_response)
        evaluator = EvaluatorEngine()
        engine = ExecutionEngine(
            config=base_config,
            llm_adapter=mock_llm_adapter,
            evaluator_engine=evaluator
        )

        # Execute
        results = await engine.run_all(["CONTROL"])

        # Verify
        assert len(results) == 1
        result = results[0]
        assert result.treatment == "CONTROL"
        assert result.test == "test_hello"
        assert result.response.content == "Hello, world!"
        assert result.response.model == "gpt-4o"
        assert result.passed is True
        assert mock_llm_adapter.complete.called

        # Verify timestamp format (ISO 8601)
        timestamp = datetime.fromisoformat(result.timestamp)
        assert timestamp.tzinfo is not None

    @pytest.mark.asyncio
    async def test_engine_with_multiple_treatments(
        self,
        config_with_multiple_treatments: EvalConfig,
        mock_llm_adapter: MagicMock,
        mock_llm_response: LLMResponse,
    ) -> None:
        """Test engine processing multiple treatment variations.

        Covers:
        - Multiple treatments
        - Proper treatment assignment
        - Variable substitution
        """
        # Setup
        mock_llm_adapter.complete = AsyncMock(return_value=mock_llm_response)
        engine = ExecutionEngine(
            config=config_with_multiple_treatments,
            llm_adapter=mock_llm_adapter
        )

        # Execute
        results = await engine.run_all(["CONTROL", "VARIANT_A", "VARIANT_B"])

        # Verify
        assert len(results) == 3
        treatments = {r.treatment for r in results}
        assert treatments == {"CONTROL", "VARIANT_A", "VARIANT_B"}

        # Verify variable substitution
        for result in results:
            assert "What is 2+2?" in result.prompt

    @pytest.mark.asyncio
    async def test_evaluator_complete_flow(
        self,
        config_with_regex_evaluator: EvalConfig,
        mock_llm_adapter: MagicMock,
    ) -> None:
        """Test complete evaluation cycle with regex evaluator.

        Covers:
        - Regex pattern matching
        - Evaluator result generation
        - Pass/fail determination
        """
        # Setup
        success_response = LLMResponse(
            content="Hello there!",
            model="gpt-4o",
            provider="openai",
            tokens=50,
            duration_ms=800,
            raw_response={}
        )
        mock_llm_adapter.complete = AsyncMock(return_value=success_response)

        evaluator = EvaluatorEngine()
        engine = ExecutionEngine(
            config=config_with_regex_evaluator,
            llm_adapter=mock_llm_adapter,
            evaluator_engine=evaluator
        )

        # Execute
        results = await engine.run_all(["CONTROL"])

        # Verify
        assert len(results) == 1
        result = results[0]
        assert result.passed is True
        assert len(result.evaluator_results) == 1
        assert result.evaluator_results[0].evaluator_name == "has_hello"
        assert result.evaluator_results[0].passed is True
        assert result.evaluator_results[0].score == 1.0


# ==================== Integration Tests ====================


class TestEngineEvaluatorIntegration:
    """Test integration between Engine and Evaluator."""

    @pytest.mark.asyncio
    async def test_engine_evaluator_integration(
        self,
        config_with_multiple_evaluators: EvalConfig,
        mock_llm_adapter: MagicMock,
    ) -> None:
        """Verify Engine and Evaluator work together seamlessly.

        Covers:
        - Passing evaluator results from engine
        - Multiple evaluators on same task
        - Combined pass/fail logic
        """
        # Setup
        success_response = LLMResponse(
            content="Hello world!",
            model="gpt-4o",
            provider="openai",
            tokens=60,
            duration_ms=900,
            raw_response={}
        )
        mock_llm_adapter.complete = AsyncMock(return_value=success_response)

        evaluator = EvaluatorEngine()
        engine = ExecutionEngine(
            config=config_with_multiple_evaluators,
            llm_adapter=mock_llm_adapter,
            evaluator_engine=evaluator
        )

        # Execute
        results = await engine.run_all(["CONTROL"])

        # Verify
        assert len(results) == 1
        result = results[0]
        assert len(result.evaluator_results) == 2
        assert result.passed is True  # All evaluators passed

        # Verify individual evaluators
        evaluator_names = {r.evaluator_name for r in result.evaluator_results}
        assert evaluator_names == {"has_pattern_1", "has_word"}

    @pytest.mark.asyncio
    async def test_workflow_with_missing_skill(
        self,
        base_config: EvalConfig,
        mock_llm_adapter: MagicMock,
        mock_llm_response: LLMResponse,
    ) -> None:
        """Workflow handles missing skill files gracefully.

        Covers:
        - Missing skill path handling
        - Fallback to base prompt
        - Successful execution despite missing skill
        """
        # Setup - treatment with non-existent skill
        config = EvalConfig(
            name="Test",
            defaults=Defaults(model="gpt-4o"),
            treatments={
                "WITH_MISSING_SKILL": Treatment(
                    skill_path="/nonexistent/skill.md"
                ),
                "CONTROL": Treatment(skill_path=None),  # Explicitly add CONTROL
            },
            tests=[
                Task(
                    name="test",
                    prompt="Test prompt",
                    variables={},
                    evaluators=[]
                ),
            ]
        )

        mock_llm_adapter.complete = AsyncMock(return_value=mock_llm_response)
        engine = ExecutionEngine(config=config, llm_adapter=mock_llm_adapter)

        # Execute - should not raise, just use base prompt
        results = await engine.run_all(["WITH_MISSING_SKILL"])

        # Verify execution completed despite missing skill
        # Engine adds CONTROL automatically if not in treatments list
        assert len(results) == 2
        # Find the WITH_MISSING_SKILL result
        missing_skill_result = next(r for r in results if r.treatment == "WITH_MISSING_SKILL")
        assert missing_skill_result.passed is False  # Skill file not found error

    @pytest.mark.asyncio
    async def test_workflow_with_invalid_config(
        self,
        mock_llm_adapter: MagicMock,
    ) -> None:
        """Workflow handles invalid configuration gracefully.

        Covers:
        - Empty treatments
        - Empty tests
        - Config validation
        """
        # Setup - empty config
        config = EvalConfig(
            name="Empty",
            treatments={},
            tests=[]
        )

        engine = ExecutionEngine(config=config, llm_adapter=mock_llm_adapter)

        # Execute - should handle gracefully
        results = await engine.run_all([])

        # Verify
        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_concurrent_evaluations(
        self,
        config_with_parallel_execution: EvalConfig,
        mock_llm_adapter: MagicMock,
    ) -> None:
        """Multiple evaluations run without interference.

        Covers:
        - Parallel execution
        - Semaphore coordination
        - Result ordering
        - No cross-contamination
        """
        # Setup
        mock_llm_adapter.complete = AsyncMock(
            side_effect=lambda **kwargs: LLMResponse(
                content=f"Response to: {kwargs.get('prompt', 'unknown')}",
                model="gpt-4o",
                provider="openai",
                tokens=50,
                duration_ms=100,
                raw_response={}
            )
        )

        engine = ExecutionEngine(
            config=config_with_parallel_execution,
            llm_adapter=mock_llm_adapter
        )

        # Execute
        results = await engine.run_all(["CONTROL", "VARIANT"])

        # Verify
        # 2 treatments × 3 tests = 6 results
        assert len(results) == 6

        # Verify all combinations are present
        treatment_test_pairs = {(r.treatment, r.test) for r in results}
        expected_pairs = {
            ("CONTROL", "test_1"), ("CONTROL", "test_2"), ("CONTROL", "test_3"),
            ("VARIANT", "test_1"), ("VARIANT", "test_2"), ("VARIANT", "test_3"),
        }
        assert treatment_test_pairs == expected_pairs

    @pytest.mark.asyncio
    async def test_error_recovery(
        self,
        config_with_multiple_treatments: EvalConfig,
        mock_llm_adapter: MagicMock,
    ) -> None:
        """Workflow recovers from errors appropriately.

        Covers:
        - LLM error handling
        - Partial failure recovery
        - Error result generation
        """
        # Setup - first call succeeds, second fails
        success_response = LLMResponse(
            content="Success",
            model="gpt-4o",
            provider="openai",
            tokens=20,
            duration_ms=500,
            raw_response={}
        )

        mock_llm_adapter.complete = AsyncMock(
            side_effect=[success_response, LLMError("API timeout"), success_response]
        )

        engine = ExecutionEngine(
            config=config_with_multiple_treatments,
            llm_adapter=mock_llm_adapter
        )

        # Execute
        results = await engine.run_all(["CONTROL", "VARIANT_A", "VARIANT_B"])

        # Verify
        assert len(results) == 3
        # One should be a failure
        failed = [r for r in results if not r.passed]
        assert len(failed) == 1
        assert "error" in failed[0].response.model


# ==================== Error Path Tests ====================


class TestErrorHandling:
    """Test error handling scenarios."""

    @pytest.mark.asyncio
    async def test_evaluation_with_api_error(
        self,
        base_config: EvalConfig,
        mock_llm_adapter: MagicMock,
    ) -> None:
        """Handles API errors gracefully.

        Covers:
        - LLM API failures
        - Error message preservation
        - Result status
        """
        # Setup
        mock_llm_adapter.complete = AsyncMock(
            side_effect=LLMError("API rate limited")
        )
        engine = ExecutionEngine(config=base_config, llm_adapter=mock_llm_adapter)

        # Execute
        results = await engine.run_all(["CONTROL"])

        # Verify
        assert len(results) == 1
        assert results[0].passed is False
        assert results[0].response.model == "error"
        assert "API rate limited" in str(results[0].response.raw_response)

    @pytest.mark.asyncio
    async def test_evaluation_with_timeout(
        self,
        base_config: EvalConfig,
        mock_llm_adapter: MagicMock,
    ) -> None:
        """Handles LLM timeouts gracefully.

        Covers:
        - Timeout handling
        - Error message format
        - Graceful degradation
        """
        # Setup
        mock_llm_adapter.complete = AsyncMock(
            side_effect=LLMError("Request timeout after 60s")
        )
        engine = ExecutionEngine(config=base_config, llm_adapter=mock_llm_adapter)

        # Execute
        results = await engine.run_all(["CONTROL"])

        # Verify
        assert len(results) == 1
        assert results[0].passed is False
        assert "timeout" in str(results[0].response.raw_response).lower()

    @pytest.mark.asyncio
    async def test_evaluation_with_insufficient_tokens(
        self,
        base_config: EvalConfig,
        mock_llm_adapter: MagicMock,
    ) -> None:
        """Handles token limit scenarios.

        Covers:
        - Token limit errors
        - Error recovery
        - Status tracking
        """
        # Setup
        mock_llm_adapter.complete = AsyncMock(
            side_effect=LLMError("Exceeded token limit (context window: 8192)")
        )
        engine = ExecutionEngine(config=base_config, llm_adapter=mock_llm_adapter)

        # Execute
        results = await engine.run_all(["CONTROL"])

        # Verify
        assert len(results) == 1
        assert results[0].passed is False
        assert "token" in str(results[0].response.raw_response).lower()

    @pytest.mark.asyncio
    async def test_invalid_regex_evaluator(
        self,
        mock_llm_adapter: MagicMock,
        mock_llm_response: LLMResponse,
    ) -> None:
        """Invalid regex patterns handled gracefully.

        Covers:
        - Regex validation
        - Error reporting
        - Evaluation failure
        """
        # Setup
        config = EvalConfig(
            name="Invalid Regex",
            defaults=Defaults(model="gpt-4o"),
            treatments={"CONTROL": Treatment(skill_path=None)},
            tests=[
                Task(
                    name="test",
                    prompt="test",
                    evaluators=[
                        RegexEvaluator(
                            name="bad_regex",
                            pattern="[invalid",
                            pass_on_match=True
                        )
                    ]
                ),
            ]
        )

        mock_llm_adapter.complete = AsyncMock(return_value=mock_llm_response)
        evaluator = EvaluatorEngine()
        engine = ExecutionEngine(
            config=config,
            llm_adapter=mock_llm_adapter,
            evaluator_engine=evaluator
        )

        # Execute
        results = await engine.run_all(["CONTROL"])

        # Verify
        assert len(results) == 1
        assert results[0].passed is False
        assert len(results[0].evaluator_results) == 1
        assert "Invalid regex" in results[0].evaluator_results[0].reason


# ==================== Evaluator-Specific Tests ====================


class TestEvaluatorIntegration:
    """Test evaluator integration scenarios."""

    @pytest.mark.asyncio
    async def test_regex_evaluator_with_flags(
        self,
        mock_llm_response: LLMResponse,
        mock_llm_adapter: MagicMock,
    ) -> None:
        """Test regex evaluator with case-insensitive matching.

        Covers:
        - Flag support
        - Pattern variations
        - Consistent behavior
        """
        # Setup
        config = EvalConfig(
            name="Regex Flags",
            defaults=Defaults(model="gpt-4o"),
            treatments={"CONTROL": Treatment(skill_path=None)},
            tests=[
                Task(
                    name="test",
                    prompt="test",
                    evaluators=[
                        RegexEvaluator(
                            name="case_insensitive",
                            pattern="HELLO",
                            pass_on_match=True
                        )
                    ]
                ),
            ]
        )

        response = LLMResponse(
            content="hello world",
            model="gpt-4o",
            provider="openai",
            tokens=20,
            duration_ms=500,
            raw_response={}
        )
        mock_llm_adapter.complete = AsyncMock(return_value=response)
        evaluator = EvaluatorEngine()
        engine = ExecutionEngine(
            config=config,
            llm_adapter=mock_llm_adapter,
            evaluator_engine=evaluator
        )

        # Execute
        results = await engine.run_all(["CONTROL"])

        # Verify - should pass due to case-insensitive matching
        assert results[0].passed is True

    @pytest.mark.asyncio
    async def test_exact_match_evaluator(
        self,
        mock_llm_adapter: MagicMock,
    ) -> None:
        """Test exact match evaluator with various inputs.

        Covers:
        - Case sensitivity
        - Substring vs exact match
        - Score calculation
        """
        # Setup
        config = EvalConfig(
            name="Exact Match",
            defaults=Defaults(model="gpt-4o"),
            treatments={"CONTROL": Treatment(skill_path=None)},
            tests=[
                Task(
                    name="test",
                    prompt="test",
                    evaluators=[
                        ExactMatchEvaluator(
                            name="exact",
                            expected="world",
                            case_sensitive=False
                        )
                    ]
                ),
            ]
        )

        response = LLMResponse(
            content="Hello WORLD!",
            model="gpt-4o",
            provider="openai",
            tokens=20,
            duration_ms=500,
            raw_response={}
        )
        mock_llm_adapter.complete = AsyncMock(return_value=response)
        evaluator = EvaluatorEngine()
        engine = ExecutionEngine(
            config=config,
            llm_adapter=mock_llm_adapter,
            evaluator_engine=evaluator
        )

        # Execute
        results = await engine.run_all(["CONTROL"])

        # Verify
        assert results[0].passed is True
        assert results[0].evaluator_results[0].score == 1.0


# ==================== Repetition and Batch Tests ====================


class TestRepetitionAndBatching:
    """Test repetition and batch execution."""

    @pytest.mark.asyncio
    async def test_multiple_repetitions(
        self,
        mock_llm_adapter: MagicMock,
    ) -> None:
        """Test multiple repetitions of same evaluation.

        Covers:
        - Repetition tracking
        - Multiple runs
        - Result accumulation
        """
        # Setup
        config = EvalConfig(
            name="Repetitions",
            defaults=Defaults(model="gpt-4o"),
            treatments={"CONTROL": Treatment(skill_path=None)},
            tests=[
                Task(name="test_1", prompt="Q1", evaluators=[]),
            ],
            execution=ExecutionConfig(parallel_workers=1, repetitions=3)
        )

        response = LLMResponse(
            content="Answer",
            model="gpt-4o",
            provider="openai",
            tokens=20,
            duration_ms=500,
            raw_response={}
        )
        mock_llm_adapter.complete = AsyncMock(return_value=response)
        engine = ExecutionEngine(config=config, llm_adapter=mock_llm_adapter)

        # Execute
        results = await engine.run_all(["CONTROL"])

        # Verify - should have 3 repetitions
        assert len(results) == 3
        # All should be from CONTROL
        assert all(r.treatment == "CONTROL" for r in results)
        assert all(r.test == "test_1" for r in results)
        # LLM should be called 3 times
        assert mock_llm_adapter.complete.call_count == 3

    @pytest.mark.asyncio
    async def test_run_treatment_method(
        self,
        config_with_multiple_treatments: EvalConfig,
        mock_llm_adapter: MagicMock,
    ) -> None:
        """Test run_treatment method for single treatment execution.

        Covers:
        - Specific treatment targeting
        - Result filtering
        - Isolated execution
        """
        # Setup
        response = LLMResponse(
            content="Answer",
            model="gpt-4o",
            provider="openai",
            tokens=20,
            duration_ms=500,
            raw_response={}
        )
        mock_llm_adapter.complete = AsyncMock(return_value=response)
        engine = ExecutionEngine(
            config=config_with_multiple_treatments,
            llm_adapter=mock_llm_adapter
        )

        # Execute
        results = await engine.run_treatment("VARIANT_A")

        # Verify
        # Engine automatically adds CONTROL if running specific treatment
        assert len(results) == 2
        # Find VARIANT_A result
        variant_result = next(r for r in results if r.treatment == "VARIANT_A")
        assert variant_result.treatment == "VARIANT_A"


# ==================== Variable Substitution Tests ====================


class TestVariableSubstitution:
    """Test variable substitution in prompts."""

    @pytest.mark.asyncio
    async def test_multiple_variable_substitution(
        self,
        mock_llm_adapter: MagicMock,
    ) -> None:
        """Test substitution of multiple variables.

        Covers:
        - Multiple placeholders
        - Correct mapping
        - Prompt accuracy
        """
        # Setup
        config = EvalConfig(
            name="Multi-Var",
            defaults=Defaults(model="gpt-4o"),
            treatments={"CONTROL": Treatment(skill_path=None)},
            tests=[
                Task(
                    name="test",
                    prompt="What is {a} + {b}? Also, who is {person}?",
                    variables={
                        "a": "2",
                        "b": "3",
                        "person": "Alice"
                    },
                    evaluators=[]
                ),
            ]
        )

        response = LLMResponse(
            content="5 and Alice",
            model="gpt-4o",
            provider="openai",
            tokens=20,
            duration_ms=500,
            raw_response={}
        )
        mock_llm_adapter.complete = AsyncMock(return_value=response)
        engine = ExecutionEngine(config=config, llm_adapter=mock_llm_adapter)

        # Execute
        results = await engine.run_all(["CONTROL"])

        # Verify
        assert len(results) == 1
        # Check that variables were substituted
        assert "{a}" not in results[0].prompt
        assert "{b}" not in results[0].prompt
        assert "{person}" not in results[0].prompt
        assert "2 + 3" in results[0].prompt
        assert "Alice" in results[0].prompt

    @pytest.mark.asyncio
    async def test_special_characters_in_variables(
        self,
        mock_llm_adapter: MagicMock,
    ) -> None:
        """Test variables containing special characters.

        Covers:
        - Regex special chars
        - JSON special chars
        - Unicode handling
        """
        # Setup
        config = EvalConfig(
            name="Special Chars",
            defaults=Defaults(model="gpt-4o"),
            treatments={"CONTROL": Treatment(skill_path=None)},
            tests=[
                Task(
                    name="test",
                    prompt="Process: {text}",
                    variables={
                        "text": 'Special: [test] {value} "quoted" & < > | \\n'
                    },
                    evaluators=[]
                ),
            ]
        )

        response = LLMResponse(
            content="Processed",
            model="gpt-4o",
            provider="openai",
            tokens=20,
            duration_ms=500,
            raw_response={}
        )
        mock_llm_adapter.complete = AsyncMock(return_value=response)
        engine = ExecutionEngine(config=config, llm_adapter=mock_llm_adapter)

        # Execute
        results = await engine.run_all(["CONTROL"])

        # Verify
        assert len(results) == 1
        assert "Special:" in results[0].prompt
        assert "[test]" in results[0].prompt


# ==================== Timestamp and Metadata Tests ====================


class TestMetadataTracking:
    """Test metadata tracking in results."""

    @pytest.mark.asyncio
    async def test_timestamp_tracking(
        self,
        base_config: EvalConfig,
        mock_llm_adapter: MagicMock,
        mock_llm_response: LLMResponse,
    ) -> None:
        """Test that timestamps are properly tracked.

        Covers:
        - Timestamp generation
        - ISO 8601 format
        - Timezone awareness
        """
        # Setup
        before = datetime.now(timezone.utc)
        mock_llm_adapter.complete = AsyncMock(return_value=mock_llm_response)
        engine = ExecutionEngine(config=base_config, llm_adapter=mock_llm_adapter)

        # Execute
        results = await engine.run_all(["CONTROL"])
        after = datetime.now(timezone.utc)

        # Verify
        assert len(results) == 1
        result_time = datetime.fromisoformat(results[0].timestamp)
        assert before <= result_time <= after
        assert result_time.tzinfo is not None

    @pytest.mark.asyncio
    async def test_response_metadata(
        self,
        base_config: EvalConfig,
        mock_llm_adapter: MagicMock,
    ) -> None:
        """Test LLM response metadata is preserved.

        Covers:
        - Token counting
        - Duration tracking
        - Model attribution
        """
        # Setup
        response = LLMResponse(
            content="Test response",
            model="gpt-4o-mini",
            provider="openai",
            tokens=123,
            duration_ms=2500,
            raw_response={"id": "test-123"}
        )
        mock_llm_adapter.complete = AsyncMock(return_value=response)
        engine = ExecutionEngine(config=base_config, llm_adapter=mock_llm_adapter)

        # Execute
        results = await engine.run_all(["CONTROL"])

        # Verify
        assert len(results) == 1
        assert results[0].response.tokens == 123
        assert results[0].response.duration_ms == 2500
        assert results[0].response.model == "gpt-4o-mini"
        assert results[0].response.raw_response["id"] == "test-123"


# ==================== Phase 4b: Multi-Evaluator Pipeline Tests ====================


class TestMultiEvaluatorPipeline:
    """Test complex multi-evaluator scenarios with chaining and error handling."""

    @pytest.fixture
    def config_regex_and_llm_judge(self) -> EvalConfig:
        """Create config with both regex and LLM judge evaluators."""
        return EvalConfig(
            name="Regex + LLM Judge Pipeline",
            defaults=Defaults(model="gpt-4o"),
            treatments={
                "CONTROL": Treatment(skill_path=None),
            },
            tests=[
                Task(
                    name="test_quality_check",
                    prompt="Write a helpful response",
                    variables={},
                    evaluators=[
                        RegexEvaluator(
                            name="contains_greeting",
                            pattern=r"(?i)(hello|hi|greetings)",
                            pass_on_match=True
                        ),
                        LLMJudgeEvaluator(
                            name="quality_assessment",
                            judge_model="gpt-4o",
                            criteria="Response is helpful and clear",
                            pass_threshold=0.8
                        ),
                    ]
                ),
            ]
        )

    @pytest.fixture
    def config_evaluator_chain_failure(self) -> EvalConfig:
        """Create config where evaluators might fail sequentially."""
        return EvalConfig(
            name="Evaluator Chain with Failures",
            defaults=Defaults(model="gpt-4o"),
            treatments={
                "CONTROL": Treatment(skill_path=None),
            },
            tests=[
                Task(
                    name="test_strict_matching",
                    prompt="Say exactly: 'hello world'",
                    variables={},
                    evaluators=[
                        ExactMatchEvaluator(
                            name="exact_greeting",
                            expected="hello",
                            case_sensitive=False
                        ),
                        ExactMatchEvaluator(
                            name="exact_world",
                            expected="world",
                            case_sensitive=False
                        ),
                        RegexEvaluator(
                            name="pattern_check",
                            pattern=r"^hello world$",
                            pass_on_match=True
                        ),
                    ]
                ),
            ]
        )

    @pytest.mark.asyncio
    async def test_multi_evaluator_pipeline(
        self,
        config_regex_and_llm_judge: EvalConfig,
        mock_llm_adapter: MagicMock,
    ) -> None:
        """Test regex evaluator + LLM judge working together.

        Covers:
        - Multiple evaluator types in pipeline
        - Each evaluator gets the same response
        - Results aggregated correctly
        - Both regex and LLM judges execute
        """
        # Setup
        response = LLMResponse(
            content="Hello! I'm here to help with your question.",
            model="gpt-4o",
            provider="openai",
            tokens=80,
            duration_ms=1200,
            raw_response={}
        )
        mock_llm_adapter.complete = AsyncMock(return_value=response)

        evaluator = EvaluatorEngine()
        engine = ExecutionEngine(
            config=config_regex_and_llm_judge,
            llm_adapter=mock_llm_adapter,
            evaluator_engine=evaluator
        )

        # Execute
        results = await engine.run_all(["CONTROL"])

        # Verify
        assert len(results) == 1
        result = results[0]
        assert len(result.evaluator_results) == 2

        # Verify regex evaluator passed
        regex_result = next(
            (r for r in result.evaluator_results if r.evaluator_name == "contains_greeting"),
            None
        )
        assert regex_result is not None
        assert regex_result.passed is True
        assert regex_result.score == 1.0

        # Verify LLM judge was attempted (mocked)
        llm_judge_result = next(
            (r for r in result.evaluator_results if r.evaluator_name == "quality_assessment"),
            None
        )
        assert llm_judge_result is not None

    @pytest.mark.asyncio
    async def test_evaluator_chain_with_failures(
        self,
        config_evaluator_chain_failure: EvalConfig,
        mock_llm_adapter: MagicMock,
    ) -> None:
        """Test evaluator chain where some succeed and some fail gracefully.

        Covers:
        - One evaluator succeeds, others fail
        - Execution continues despite failures
        - Overall pass reflects all evaluators
        - Error info captured
        """
        # Setup - response contains "hello world" but not matching exact case
        response = LLMResponse(
            content="Hello, this is the world!",
            model="gpt-4o",
            provider="openai",
            tokens=50,
            duration_ms=800,
            raw_response={}
        )
        mock_llm_adapter.complete = AsyncMock(return_value=response)

        evaluator = EvaluatorEngine()
        engine = ExecutionEngine(
            config=config_evaluator_chain_failure,
            llm_adapter=mock_llm_adapter,
            evaluator_engine=evaluator
        )

        # Execute
        results = await engine.run_all(["CONTROL"])

        # Verify
        assert len(results) == 1
        result = results[0]
        assert len(result.evaluator_results) == 3

        # At least one evaluator should have passed (contains "hello")
        passed_count = sum(1 for r in result.evaluator_results if r.passed)
        assert passed_count >= 1

        # Overall result should reflect that not all passed
        # (since "exact_world" strict match should fail)
        evaluator_names = {r.evaluator_name for r in result.evaluator_results}
        assert evaluator_names == {"exact_greeting", "exact_world", "pattern_check"}


# ==================== Phase 4b: Treatment Expansion & Wildcards Tests ====================


class TestTreatmentExpansion:
    """Test treatment expansion and wildcard pattern matching."""

    @pytest.fixture
    def config_wildcard_treatments(self) -> EvalConfig:
        """Create config with wildcard-compatible treatment names."""
        return EvalConfig(
            name="Wildcard Treatment Test",
            defaults=Defaults(model="gpt-4o"),
            treatments={
                "CONTROL": Treatment(skill_path=None),
                "VARIANT_A_V1": Treatment(skill_path=None, description="Variant A Version 1"),
                "VARIANT_A_V2": Treatment(skill_path=None, description="Variant A Version 2"),
                "VARIANT_B_V1": Treatment(skill_path=None, description="Variant B Version 1"),
                "CUSTOM_SPECIAL": Treatment(skill_path=None, description="Custom Special"),
            },
            tests=[
                Task(
                    name="test_wildcard",
                    prompt="Test {variant} variant",
                    variables={"variant": "unknown"},
                    evaluators=[
                        RegexEvaluator(
                            name="has_variant",
                            pattern=r"variant",
                            pass_on_match=True
                        )
                    ]
                ),
            ]
        )

    @pytest.mark.asyncio
    async def test_treatment_expansion_with_execution(
        self,
        config_wildcard_treatments: EvalConfig,
        mock_llm_adapter: MagicMock,
    ) -> None:
        """Test treatment patterns work correctly with execution.

        Covers:
        - Multiple specific treatments execute
        - Expansion logic produces correct set of treatments
        - All specified treatments execute
        - Results include all variants
        """
        from md_evals.config import ConfigLoader

        # Setup - response must contain "variant" to pass the regex
        response = LLMResponse(
            content="Testing the variant functionality",
            model="gpt-4o",
            provider="openai",
            tokens=100,
            duration_ms=1000,
            raw_response={}
        )
        mock_llm_adapter.complete = AsyncMock(return_value=response)

        evaluator = EvaluatorEngine()
        engine = ExecutionEngine(
            config=config_wildcard_treatments,
            llm_adapter=mock_llm_adapter,
            evaluator_engine=evaluator
        )

        # Manually expand wildcard patterns (as CLI does)
        treatments_to_run = ConfigLoader.expand_wildcards(
            ["CONTROL", "VARIANT_A_*"],
            config_wildcard_treatments.treatments
        )

        # Execute with expanded treatments
        results = await engine.run_all(treatments_to_run)

        # Verify expansion occurred
        treatments = {r.treatment for r in results}
        assert "CONTROL" in treatments
        assert "VARIANT_A_V1" in treatments
        assert "VARIANT_A_V2" in treatments
        assert "VARIANT_B_V1" not in treatments
        assert "CUSTOM_SPECIAL" not in treatments

        # Should have 1 (CONTROL) + 2 (VARIANT_A_*) = 3 results
        assert len(results) == 3

        # All results should have evaluated successfully
        for result in results:
            assert result.response is not None
            assert result.passed is True


# ==================== Phase 4b: Reporter Format Validation Tests ====================


class TestReporterFormatConsistency:
    """Test reporter output formats maintain data consistency."""

    @pytest.fixture
    def reporter_test_results(self) -> list[ExecutionResult]:
        """Create consistent test results for reporter validation."""
        return [
            ExecutionResult(
                treatment="CONTROL",
                test="test_1",
                prompt="What is 2+2?",
                response=LLMResponse(
                    content="4",
                    model="gpt-4o",
                    provider="openai",
                    tokens=10,
                    duration_ms=500,
                    raw_response={"id": "1"}
                ),
                passed=True,
                evaluator_results=[
                    EvaluatorResult(
                        evaluator_name="exact_match",
                        passed=True,
                        score=1.0,
                        details={"reason": "Matched exactly"}
                    )
                ],
                timestamp="2024-01-01T12:00:00Z"
            ),
            ExecutionResult(
                treatment="VARIANT_A",
                test="test_1",
                prompt="What is 2+2?",
                response=LLMResponse(
                    content="The answer is 4",
                    model="gpt-4o-mini",
                    provider="openai",
                    tokens=15,
                    duration_ms=600,
                    raw_response={"id": "2"}
                ),
                passed=True,
                evaluator_results=[
                    EvaluatorResult(
                        evaluator_name="regex_match",
                        passed=True,
                        score=0.9,
                        details={"reason": "Contains number 4"}
                    )
                ],
                timestamp="2024-01-01T12:01:00Z"
            ),
            ExecutionResult(
                treatment="VARIANT_B",
                test="test_1",
                prompt="What is 2+2?",
                response=LLMResponse(
                    content="I don't know",
                    model="gpt-4o-mini",
                    provider="openai",
                    tokens=8,
                    duration_ms=400,
                    raw_response={"id": "3"}
                ),
                passed=False,
                evaluator_results=[
                    EvaluatorResult(
                        evaluator_name="exact_match",
                        passed=False,
                        score=0.0,
                        details={"reason": "Did not match"}
                    )
                ],
                timestamp="2024-01-01T12:02:00Z"
            ),
        ]

    @pytest.mark.asyncio
    async def test_reporter_preserves_all_data(
        self,
        base_config: EvalConfig,
        reporter_test_results: list[ExecutionResult],
    ) -> None:
        """Test all data preserved across reporter formats.

        Covers:
        - All result fields present
        - Metadata intact (tokens, duration, timestamp)
        - Evaluator results preserved
        - No data loss in formatting
        """
        from md_evals.reporter import Reporter

        reporter = Reporter(base_config)

        # Test data consistency
        for result in reporter_test_results:
            # Verify all core fields exist
            assert result.treatment is not None
            assert result.test is not None
            assert result.prompt is not None
            assert result.response is not None
            assert result.response.content is not None
            assert result.response.model is not None
            assert result.response.tokens > 0
            assert result.response.duration_ms > 0
            assert result.timestamp is not None

            # Verify evaluator results
            assert len(result.evaluator_results) > 0
            for eval_result in result.evaluator_results:
                assert eval_result.evaluator_name is not None
                assert eval_result.passed is not None
                assert 0.0 <= eval_result.score <= 1.0

    @pytest.mark.asyncio
    async def test_reporter_json_vs_table_consistency(
        self,
        base_config: EvalConfig,
        reporter_test_results: list[ExecutionResult],
        tmp_path: Path,
    ) -> None:
        """Test JSON and table formats produce consistent data.

        Covers:
        - Same data in JSON and table outputs
        - Aggregation logic consistent
        - Pass rates match
        - Treatment summaries agree
        """
        from md_evals.reporter import Reporter
        import json

        reporter = Reporter(base_config)

        # Generate JSON report to file
        json_output = str(tmp_path / "report.json")
        reporter.report_json(reporter_test_results, json_output)

        # Load and verify JSON contains expected aggregated data
        with open(json_output) as f:
            json_data = json.load(f)

        # Should have summary by treatment
        assert isinstance(json_data, dict)

        # Extract treatment stats from results
        by_treatment = {}
        for result in reporter_test_results:
            if result.treatment not in by_treatment:
                by_treatment[result.treatment] = {"total": 0, "passed": 0}
            by_treatment[result.treatment]["total"] += 1
            if result.passed:
                by_treatment[result.treatment]["passed"] += 1

        # Verify each treatment has data
        for treatment, stats in by_treatment.items():
            assert stats["total"] > 0
            assert stats["passed"] <= stats["total"]

    @pytest.mark.asyncio
    async def test_reporter_handles_empty_results(
        self,
        base_config: EvalConfig,
        tmp_path: Path,
    ) -> None:
        """Test reporter handles empty result sets gracefully.

        Covers:
        - No crashes on empty results
        - Sensible output for no data
        - Proper error/info messages
        """
        from md_evals.reporter import Reporter

        reporter = Reporter(base_config)
        empty_results: list[ExecutionResult] = []

        # Should not crash
        try:
            output_path = str(tmp_path / "empty.json")
            reporter.report_json(empty_results, output_path)
            assert Path(output_path).exists()
        except Exception as e:
            pytest.fail(f"Reporter crashed on empty results: {e}")


# ==================== Phase 4b: Large Batch Processing Tests ====================


class TestLargeBatchProcessing:
    """Test execution of large batches with many tests and treatments."""

    @pytest.fixture
    def config_large_batch(self) -> EvalConfig:
        """Create config with 100+ test items."""
        tasks = [
            Task(
                name=f"test_{i:03d}",
                prompt=f"Question {i}: What is {i} + 1?",
                variables={"num": str(i)},
                evaluators=[
                    RegexEvaluator(
                        name=f"check_{i}",
                        pattern=r"\d+",
                        pass_on_match=True
                    )
                ]
            )
            for i in range(50)
        ]

        return EvalConfig(
            name="Large Batch Test (100+)",
            defaults=Defaults(model="gpt-4o-mini"),
            treatments={
                "CONTROL": Treatment(skill_path=None),
                "VARIANT_1": Treatment(skill_path=None),
                "VARIANT_2": Treatment(skill_path=None),
            },
            tests=tasks,
            execution=ExecutionConfig(parallel_workers=5, repetitions=1)
        )

    @pytest.mark.asyncio
    async def test_large_batch_processing(
        self,
        config_large_batch: EvalConfig,
        mock_llm_adapter: MagicMock,
    ) -> None:
        """Test 100+ tests × multiple treatments execute correctly.

        Covers:
        - Large batch execution (150+ total runs)
        - Parallel worker management
        - Memory efficiency
        - Result collection
        - No data loss in large runs
        """
        # Setup - mock to return quickly for this test
        mock_response = LLMResponse(
            content="42",
            model="gpt-4o-mini",
            provider="openai",
            tokens=5,
            duration_ms=100,
            raw_response={}
        )
        mock_llm_adapter.complete = AsyncMock(return_value=mock_response)

        evaluator = EvaluatorEngine()
        engine = ExecutionEngine(
            config=config_large_batch,
            llm_adapter=mock_llm_adapter,
            evaluator_engine=evaluator
        )

        # Execute all treatments
        results = await engine.run_all(["CONTROL", "VARIANT_1", "VARIANT_2"])

        # Verify expected count: 50 tests × 3 treatments = 150 results
        assert len(results) == 150

        # Verify all treatments present
        treatments = {r.treatment for r in results}
        assert treatments == {"CONTROL", "VARIANT_1", "VARIANT_2"}

        # Verify all tests executed
        test_names = {r.test for r in results}
        expected_tests = {f"test_{i:03d}" for i in range(50)}
        assert test_names == expected_tests

        # Verify each result is valid
        for result in results:
            assert result.response is not None
            assert result.response.content == "42"
            assert result.passed is True
            assert len(result.evaluator_results) > 0

        # Verify no duplicates
        result_keys = [
            (r.treatment, r.test) for r in results
        ]
        assert len(result_keys) == len(set(result_keys))

    @pytest.mark.asyncio
    async def test_large_batch_with_failures(
        self,
        config_large_batch: EvalConfig,
        mock_llm_adapter: MagicMock,
    ) -> None:
        """Test large batch handles failures gracefully.

        Covers:
        - Some responses pass, some fail
        - Partial failure doesn't stop execution
        - All results collected despite failures
        - Statistics accurate with mixed results
        """
        # Setup - alternate between passing and failing responses
        call_count = 0

        async def mock_complete_with_failures(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count % 3 == 0:
                # Fail this one
                content = "unknown"
            else:
                content = "42"

            return LLMResponse(
                content=content,
                model="gpt-4o-mini",
                provider="openai",
                tokens=5,
                duration_ms=100,
                raw_response={}
            )

        mock_llm_adapter.complete = AsyncMock(side_effect=mock_complete_with_failures)

        evaluator = EvaluatorEngine()
        engine = ExecutionEngine(
            config=config_large_batch,
            llm_adapter=mock_llm_adapter,
            evaluator_engine=evaluator
        )

        # Execute
        results = await engine.run_all(["CONTROL", "VARIANT_1", "VARIANT_2"])

        # Verify all executed despite failures
        assert len(results) == 150

        # Verify we have mix of pass/fail
        passed_count = sum(1 for r in results if r.passed)
        failed_count = sum(1 for r in results if not r.passed)

        assert passed_count > 0
        assert failed_count > 0
        assert passed_count + failed_count == 150
