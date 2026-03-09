"""Tests for md_evals execution engine."""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock

from md_evals.engine import ExecutionEngine
from md_evals.models import (
    EvalConfig, ExecutionResult, Defaults,
    Task, Treatment, RegexEvaluator, LLMResponse, ExecutionConfig
)


class TestExecutionEngine:
    """Test ExecutionEngine."""
    
    def test_init(self):
        """Test engine initialization."""
        config = EvalConfig(
            name="Test",
            defaults=Defaults(),
            treatments={"CONTROL": Treatment()},
            tests=[Task(name="test", prompt="test")]
        )
        
        from md_evals.llm import LLMAdapter
        adapter = LLMAdapter(model="gpt-4o")
        
        engine = ExecutionEngine(config=config, llm_adapter=adapter)
        
        assert engine.config == config
        assert engine.llm_adapter == adapter
    
    def test_get_semaphore(self):
        """Test semaphore creation."""
        config = EvalConfig(
            name="Test",
            execution__parallel_workers=2
        )
        
        engine = ExecutionEngine(config, MagicMock())
        
        assert engine._semaphore is None
        sem = engine._get_semaphore()
        assert sem is not None
        # Should return same semaphore
        assert engine._get_semaphore() is sem
    
    @pytest.mark.asyncio
    async def test_run_single(self):
        """Test single evaluation run."""
        config = EvalConfig(
            name="Test",
            defaults=Defaults(model="gpt-4o"),
            treatments={"CONTROL": Treatment(skill_path=None)},
            tests=[Task(
                name="test",
                prompt="Say {word}",
                variables={"word": "hello"},
                evaluators=[]
            )]
        )
        
        mock_adapter = MagicMock()
        # Return an actual LLMResponse instance
        mock_response = LLMResponse(
            content="Hello!",
            model="gpt-4o",
            provider="openai",
            tokens=5,
            duration_ms=1000,
            raw_response={}
        )
        
        mock_adapter.complete = AsyncMock(return_value=mock_response)
        
        engine = ExecutionEngine(config, mock_adapter)
        
        result = await engine.run_single(
            Treatment(skill_path=None),
            Task(name="test", prompt="Say {word}", variables={"word": "hello"}, evaluators=[]),
            "CONTROL"
        )
        
        assert result.treatment == "CONTROL"
        assert result.test == "test"
        assert result.response.content == "Hello!"


class TestEvalConfigDefaults:
    """Test EvalConfig with execution defaults."""
    
    def test_execution_defaults(self):
        """Test execution defaults."""
        config = EvalConfig(name="Test")
        
        assert config.execution.parallel_workers == 1
        assert config.execution.repetitions == 1
        assert config.execution.fail_fast is False
    
    def test_execution_override(self):
        """Test execution override."""
        config = EvalConfig(
            name="Test",
            execution=ExecutionConfig(parallel_workers=4, repetitions=3)
        )
        
        assert config.execution.parallel_workers == 4
        assert config.execution.repetitions == 3
    
    @pytest.mark.asyncio
    async def test_run_all_empty(self):
        """Test run_all with no treatments."""
        from md_evals.llm import LLMAdapter
        
        config = EvalConfig(
            name="Test",
            defaults=Defaults(model="gpt-4o"),
            treatments={},
            tests=[]
        )
        
        adapter = LLMAdapter(model="gpt-4o")
        engine = ExecutionEngine(config, adapter)
        
        results = await engine.run_all(["CONTROL"])
        
        # Should return empty or have CONTROL added
        assert isinstance(results, list)
    
    @pytest.mark.asyncio
    async def test_run_all_with_treatments(self):
        """Test run_all with multiple treatments."""
        from md_evals.llm import LLMAdapter
        
        config = EvalConfig(
            name="Test",
            defaults=Defaults(model="gpt-4o"),
            treatments={
                "CONTROL": Treatment(skill_path=None),
                "WITH_SKILL": Treatment(skill_path="./SKILL.md")
            },
            tests=[
                Task(name="test1", prompt="Hello", evaluators=[])
            ]
        )
        
        mock_adapter = MagicMock()
        mock_response = LLMResponse(
            content="Hi",
            model="gpt-4o",
            provider="openai",
            duration_ms=1000,
            raw_response={}
        )
        mock_adapter.complete = AsyncMock(return_value=mock_response)
        
        engine = ExecutionEngine(config, mock_adapter)
        
        results = await engine.run_all(["CONTROL", "WITH_SKILL"])
        
        # Should have results for both treatments
        assert len(results) >= 2
    
    @pytest.mark.asyncio
    async def test_run_all_with_repetitions(self):
        """Test run_all with multiple repetitions."""
        from md_evals.llm import LLMAdapter
        
        config = EvalConfig(
            name="Test",
            defaults=Defaults(model="gpt-4o"),
            treatments={"CONTROL": Treatment(skill_path=None)},
            tests=[Task(name="test1", prompt="Hello", evaluators=[])],
            execution=ExecutionConfig(repetitions=3)
        )
        
        mock_adapter = MagicMock()
        mock_response = LLMResponse(
            content="Hi",
            model="gpt-4o",
            provider="openai",
            duration_ms=1000,
            raw_response={}
        )
        mock_adapter.complete = AsyncMock(return_value=mock_response)
        
        engine = ExecutionEngine(config, mock_adapter)
        
        results = await engine.run_all(["CONTROL"])
        
        # Should have 3 results (one per repetition)
        assert len(results) == 3
    
    @pytest.mark.asyncio
    async def test_run_treatment(self):
        """Test run_treatment method."""
        from md_evals.llm import LLMAdapter
        
        config = EvalConfig(
            name="Test",
            defaults=Defaults(model="gpt-4o"),
            treatments={"CONTROL": Treatment(skill_path=None)},
            tests=[Task(name="test1", prompt="Hello", evaluators=[])]
        )
        
        mock_adapter = MagicMock()
        mock_response = LLMResponse(
            content="Hi",
            model="gpt-4o",
            provider="openai",
            duration_ms=1000,
            raw_response={}
        )
        mock_adapter.complete = AsyncMock(return_value=mock_response)
        
        engine = ExecutionEngine(config, mock_adapter)
        
        results = await engine.run_treatment("CONTROL")
        
        assert len(results) >= 1
        assert results[0].treatment == "CONTROL"
    
    @pytest.mark.asyncio
    async def test_run_single_with_variables(self):
        """Test run_single with prompt variables."""
        config = EvalConfig(
            name="Test",
            defaults=Defaults(model="gpt-4o"),
            treatments={"CONTROL": Treatment(skill_path=None)},
            tests=[Task(
                name="test",
                prompt="Hello {name}, you are {age} years old",
                variables={"name": "John", "age": "30"},
                evaluators=[]
            )]
        )
        
        mock_adapter = MagicMock()
        mock_response = LLMResponse(
            content="Hi John!",
            model="gpt-4o",
            provider="openai",
            tokens=5,
            duration_ms=1000,
            raw_response={}
        )
        
        mock_adapter.complete = AsyncMock(return_value=mock_response)
        
        engine = ExecutionEngine(config, mock_adapter)
        
        result = await engine.run_single(
            Treatment(skill_path=None),
            Task(
                name="test",
                prompt="Hello {name}, you are {age} years old",
                variables={"name": "John", "age": "30"},
                evaluators=[]
            ),
            "CONTROL"
        )
        
        # Verify variables were replaced in the prompt sent to LLM
        call_args = mock_adapter.complete.call_args
        actual_prompt = call_args[1]["prompt"] if "prompt" in call_args[1] else call_args[0][0]
        assert "{name}" not in actual_prompt
        assert "{age}" not in actual_prompt
    
    @pytest.mark.asyncio
    async def test_run_single_with_evaluator(self):
        """Test run_single with evaluator."""
        from md_evals.evaluator import EvaluatorEngine
        from md_evals.models import RegexEvaluator
        
        config = EvalConfig(
            name="Test",
            defaults=Defaults(model="gpt-4o"),
            treatments={"CONTROL": Treatment(skill_path=None)},
            tests=[Task(
                name="test",
                prompt="Say hello",
                evaluators=[RegexEvaluator(
                    name="has_hello",
                    pattern="hello",
                    pass_on_match=True
                )]
            )]
        )
        
        mock_adapter = MagicMock()
        mock_response = LLMResponse(
            content="Hello there!",
            model="gpt-4o",
            provider="openai",
            tokens=5,
            duration_ms=1000,
            raw_response={}
        )
        mock_adapter.complete = AsyncMock(return_value=mock_response)
        
        engine = ExecutionEngine(config, mock_adapter, EvaluatorEngine())
        
        result = await engine.run_single(
            Treatment(skill_path=None),
            Task(
                name="test",
                prompt="Say hello",
                evaluators=[RegexEvaluator(
                    name="has_hello",
                    pattern="hello",
                    pass_on_match=True
                )]
            ),
            "CONTROL"
        )
        
        assert result.passed is True
        assert len(result.evaluator_results) == 1
    
    @pytest.mark.asyncio
    async def test_run_single_with_llm_error(self):
        """Test run_single handles LLM error gracefully."""
        from md_evals.llm import LLMError
        
        config = EvalConfig(
            name="Test",
            defaults=Defaults(model="gpt-4o"),
            treatments={"CONTROL": Treatment(skill_path=None)},
            tests=[Task(name="test", prompt="Hello", evaluators=[])]
        )
        
        mock_adapter = MagicMock()
        mock_adapter.complete = AsyncMock(side_effect=LLMError("API Error"))
        
        engine = ExecutionEngine(config, mock_adapter)
        
        result = await engine.run_single(
            Treatment(skill_path=None),
            Task(name="test", prompt="Hello", evaluators=[]),
            "CONTROL"
        )
        
        # Should return error result with passed=False
        assert result.passed is False
        assert result.response.content == ""  # Empty content on error
    
    @pytest.mark.asyncio
    async def test_run_single_empty_variables(self):
        """Test run_single with empty variables dict."""
        config = EvalConfig(
            name="Test",
            defaults=Defaults(model="gpt-4o"),
            treatments={"CONTROL": Treatment(skill_path=None)},
            tests=[Task(name="test", prompt="Hello world", variables={}, evaluators=[])]
        )
        
        mock_adapter = MagicMock()
        mock_response = LLMResponse(
            content="Hi!",
            model="gpt-4o",
            provider="openai",
            duration_ms=1000,
            raw_response={}
        )
        mock_adapter.complete = AsyncMock(return_value=mock_response)
        
        engine = ExecutionEngine(config, mock_adapter)
        
        result = await engine.run_single(
            Treatment(skill_path=None),
            Task(name="test", prompt="Hello world", variables={}, evaluators=[]),
            "CONTROL"
        )
        
        # Should have called with unchanged prompt
        call_args = mock_adapter.complete.call_args
        actual_prompt = call_args[1]["prompt"] if "prompt" in call_args[1] else call_args[0][0]
        assert actual_prompt == "Hello world"
        assert result.treatment == "CONTROL"
        assert result.test == "test"
    
    @pytest.mark.asyncio
    async def test_run_single_multiple_variables(self):
        """Test run_single with multiple variables in prompt."""
        config = EvalConfig(
            name="Test",
            defaults=Defaults(model="gpt-4o"),
            treatments={"CONTROL": Treatment(skill_path=None)},
            tests=[Task(
                name="test",
                prompt="{greeting} {name}, you are {age} years old",
                variables={"greeting": "Hello", "name": "Alice", "age": "25"},
                evaluators=[]
            )]
        )
        
        mock_adapter = MagicMock()
        mock_response = LLMResponse(
            content="Hi Alice!",
            model="gpt-4o",
            provider="openai",
            duration_ms=1000,
            raw_response={}
        )
        mock_adapter.complete = AsyncMock(return_value=mock_response)
        
        engine = ExecutionEngine(config, mock_adapter)
        
        result = await engine.run_single(
            Treatment(skill_path=None),
            Task(
                name="test",
                prompt="{greeting} {name}, you are {age} years old",
                variables={"greeting": "Hello", "name": "Alice", "age": "25"},
                evaluators=[]
            ),
            "CONTROL"
        )
        
        # Verify all variables were replaced
        call_args = mock_adapter.complete.call_args
        actual_prompt = call_args[1]["prompt"] if "prompt" in call_args[1] else call_args[0][0]
        assert "{greeting}" not in actual_prompt
        assert "{name}" not in actual_prompt
        assert "{age}" not in actual_prompt
        assert "Hello" in actual_prompt
        assert "Alice" in actual_prompt
        assert "25" in actual_prompt
    
    @pytest.mark.asyncio
    async def test_run_single_special_chars_in_variables(self):
        """Test run_single with special characters in variable values."""
        config = EvalConfig(
            name="Test",
            defaults=Defaults(model="gpt-4o"),
            treatments={"CONTROL": Treatment(skill_path=None)},
            tests=[Task(
                name="test",
                prompt="Email: {email}",
                variables={"email": "user@example.com"},
                evaluators=[]
            )]
        )
        
        mock_adapter = MagicMock()
        mock_response = LLMResponse(
            content="Valid email",
            model="gpt-4o",
            provider="openai",
            duration_ms=1000,
            raw_response={}
        )
        mock_adapter.complete = AsyncMock(return_value=mock_response)
        
        engine = ExecutionEngine(config, mock_adapter)
        
        result = await engine.run_single(
            Treatment(skill_path=None),
            Task(
                name="test",
                prompt="Email: {email}",
                variables={"email": "user@example.com"},
                evaluators=[]
            ),
            "CONTROL"
        )
        
        # Verify special chars were preserved
        call_args = mock_adapter.complete.call_args
        actual_prompt = call_args[1]["prompt"] if "prompt" in call_args[1] else call_args[0][0]
        assert "user@example.com" in actual_prompt
    
    @pytest.mark.asyncio
    async def test_run_single_newlines_in_variables(self):
        """Test run_single with newlines in variable values."""
        config = EvalConfig(
            name="Test",
            defaults=Defaults(model="gpt-4o"),
            treatments={"CONTROL": Treatment(skill_path=None)},
            tests=[Task(
                name="test",
                prompt="Content:\n{content}",
                variables={"content": "Line 1\nLine 2\nLine 3"},
                evaluators=[]
            )]
        )
        
        mock_adapter = MagicMock()
        mock_response = LLMResponse(
            content="Processed",
            model="gpt-4o",
            provider="openai",
            duration_ms=1000,
            raw_response={}
        )
        mock_adapter.complete = AsyncMock(return_value=mock_response)
        
        engine = ExecutionEngine(config, mock_adapter)
        
        result = await engine.run_single(
            Treatment(skill_path=None),
            Task(
                name="test",
                prompt="Content:\n{content}",
                variables={"content": "Line 1\nLine 2\nLine 3"},
                evaluators=[]
            ),
            "CONTROL"
        )
        
        # Verify newlines preserved
        call_args = mock_adapter.complete.call_args
        actual_prompt = call_args[1]["prompt"] if "prompt" in call_args[1] else call_args[0][0]
        assert "Line 1" in actual_prompt
        assert "Line 2" in actual_prompt
        assert "Line 3" in actual_prompt
    
    @pytest.mark.asyncio
    async def test_run_single_variable_not_in_prompt(self):
        """Test run_single with variable defined but not used in prompt."""
        config = EvalConfig(
            name="Test",
            defaults=Defaults(model="gpt-4o"),
            treatments={"CONTROL": Treatment(skill_path=None)},
            tests=[Task(
                name="test",
                prompt="Hello world",
                variables={"unused": "value"},
                evaluators=[]
            )]
        )
        
        mock_adapter = MagicMock()
        mock_response = LLMResponse(
            content="Hi!",
            model="gpt-4o",
            provider="openai",
            duration_ms=1000,
            raw_response={}
        )
        mock_adapter.complete = AsyncMock(return_value=mock_response)
        
        engine = ExecutionEngine(config, mock_adapter)
        
        result = await engine.run_single(
            Treatment(skill_path=None),
            Task(
                name="test",
                prompt="Hello world",
                variables={"unused": "value"},
                evaluators=[]
            ),
            "CONTROL"
        )
        
        # Should work fine, just leave prompt unchanged
        call_args = mock_adapter.complete.call_args
        actual_prompt = call_args[1]["prompt"] if "prompt" in call_args[1] else call_args[0][0]
        assert actual_prompt == "Hello world"
    
    @pytest.mark.asyncio
    async def test_run_single_no_evaluators_always_passes(self):
        """Test run_single with no evaluators returns passed=True."""
        config = EvalConfig(
            name="Test",
            defaults=Defaults(model="gpt-4o"),
            treatments={"CONTROL": Treatment(skill_path=None)},
            tests=[Task(name="test", prompt="Hello", evaluators=[])]
        )
        
        mock_adapter = MagicMock()
        mock_response = LLMResponse(
            content="Response",
            model="gpt-4o",
            provider="openai",
            duration_ms=1000,
            raw_response={}
        )
        mock_adapter.complete = AsyncMock(return_value=mock_response)
        
        engine = ExecutionEngine(config, mock_adapter)
        
        result = await engine.run_single(
            Treatment(skill_path=None),
            Task(name="test", prompt="Hello", evaluators=[]),
            "CONTROL"
        )
        
        # No evaluators, so should pass by default
        assert result.passed is True
        assert len(result.evaluator_results) == 0
    
    @pytest.mark.asyncio
    async def test_run_single_evaluator_false_fails_result(self):
        """Test run_single fails if any evaluator fails."""
        from md_evals.evaluator import EvaluatorEngine
        
        config = EvalConfig(
            name="Test",
            defaults=Defaults(model="gpt-4o"),
            treatments={"CONTROL": Treatment(skill_path=None)},
            tests=[Task(
                name="test",
                prompt="Say goodbye",
                evaluators=[RegexEvaluator(
                    name="has_hello",
                    pattern="hello",
                    pass_on_match=True
                )]
            )]
        )
        
        mock_adapter = MagicMock()
        mock_response = LLMResponse(
            content="Goodbye!",
            model="gpt-4o",
            provider="openai",
            duration_ms=1000,
            raw_response={}
        )
        mock_adapter.complete = AsyncMock(return_value=mock_response)
        
        engine = ExecutionEngine(config, mock_adapter, EvaluatorEngine())
        
        result = await engine.run_single(
            Treatment(skill_path=None),
            Task(
                name="test",
                prompt="Say goodbye",
                evaluators=[RegexEvaluator(
                    name="has_hello",
                    pattern="hello",
                    pass_on_match=True
                )]
            ),
            "CONTROL"
        )
        
        # Evaluator should fail, so result.passed should be False
        assert result.passed is False
        assert len(result.evaluator_results) == 1
        assert result.evaluator_results[0].passed is False
    
    @pytest.mark.asyncio
    async def test_run_single_multiple_evaluators_all_pass(self):
        """Test run_single with multiple passing evaluators."""
        from md_evals.evaluator import EvaluatorEngine
        
        config = EvalConfig(
            name="Test",
            defaults=Defaults(model="gpt-4o"),
            treatments={"CONTROL": Treatment(skill_path=None)},
            tests=[Task(
                name="test",
                prompt="Say hello world",
                evaluators=[
                    RegexEvaluator(
                        name="has_hello",
                        pattern="hello",
                        pass_on_match=True
                    ),
                    RegexEvaluator(
                        name="has_world",
                        pattern="world",
                        pass_on_match=True
                    )
                ]
            )]
        )
        
        mock_adapter = MagicMock()
        mock_response = LLMResponse(
            content="Hello world!",
            model="gpt-4o",
            provider="openai",
            duration_ms=1000,
            raw_response={}
        )
        mock_adapter.complete = AsyncMock(return_value=mock_response)
        
        engine = ExecutionEngine(config, mock_adapter, EvaluatorEngine())
        
        result = await engine.run_single(
            Treatment(skill_path=None),
            Task(
                name="test",
                prompt="Say hello world",
                evaluators=[
                    RegexEvaluator(
                        name="has_hello",
                        pattern="hello",
                        pass_on_match=True
                    ),
                    RegexEvaluator(
                        name="has_world",
                        pattern="world",
                        pass_on_match=True
                    )
                ]
            ),
            "CONTROL"
        )
        
        # All evaluators pass, so result should pass
        assert result.passed is True
        assert len(result.evaluator_results) == 2
        assert all(r.passed for r in result.evaluator_results)
    
    @pytest.mark.asyncio
    async def test_run_single_multiple_evaluators_one_fails(self):
        """Test run_single with multiple evaluators where one fails."""
        from md_evals.evaluator import EvaluatorEngine
        
        config = EvalConfig(
            name="Test",
            defaults=Defaults(model="gpt-4o"),
            treatments={"CONTROL": Treatment(skill_path=None)},
            tests=[Task(
                name="test",
                prompt="Say hello",
                evaluators=[
                    RegexEvaluator(
                        name="has_hello",
                        pattern="hello",
                        pass_on_match=True
                    ),
                    RegexEvaluator(
                        name="has_world",
                        pattern="world",
                        pass_on_match=True
                    )
                ]
            )]
        )
        
        mock_adapter = MagicMock()
        mock_response = LLMResponse(
            content="Hello!",
            model="gpt-4o",
            provider="openai",
            duration_ms=1000,
            raw_response={}
        )
        mock_adapter.complete = AsyncMock(return_value=mock_response)
        
        engine = ExecutionEngine(config, mock_adapter, EvaluatorEngine())
        
        result = await engine.run_single(
            Treatment(skill_path=None),
            Task(
                name="test",
                prompt="Say hello",
                evaluators=[
                    RegexEvaluator(
                        name="has_hello",
                        pattern="hello",
                        pass_on_match=True
                    ),
                    RegexEvaluator(
                        name="has_world",
                        pattern="world",
                        pass_on_match=True
                    )
                ]
            ),
            "CONTROL"
        )
        
        # One evaluator fails, so overall result should fail
        assert result.passed is False
        assert len(result.evaluator_results) == 2
        assert sum(1 for r in result.evaluator_results if r.passed) == 1
    
    @pytest.mark.asyncio
    async def test_run_single_response_structure(self):
        """Test run_single returns proper ExecutionResult structure."""
        config = EvalConfig(
            name="Test",
            defaults=Defaults(model="gpt-4o"),
            treatments={"CONTROL": Treatment(skill_path=None)},
            tests=[Task(name="test", prompt="Hello", evaluators=[])]
        )
        
        mock_adapter = MagicMock()
        mock_response = LLMResponse(
            content="Hi!",
            model="gpt-4o",
            provider="openai",
            tokens=5,
            duration_ms=1000,
            raw_response={"id": "123"}
        )
        mock_adapter.complete = AsyncMock(return_value=mock_response)
        
        engine = ExecutionEngine(config, mock_adapter)
        
        result = await engine.run_single(
            Treatment(skill_path=None),
            Task(name="test", prompt="Hello", evaluators=[]),
            "CONTROL"
        )
        
        # Check all required fields
        assert hasattr(result, 'treatment')
        assert hasattr(result, 'test')
        assert hasattr(result, 'prompt')
        assert hasattr(result, 'response')
        assert hasattr(result, 'passed')
        assert hasattr(result, 'evaluator_results')
        assert hasattr(result, 'timestamp')
        assert result.treatment == "CONTROL"
        assert result.test == "test"
        assert result.response.content == "Hi!"
        assert result.response.tokens == 5
        assert isinstance(result.evaluator_results, list)
    
    @pytest.mark.asyncio
    async def test_run_single_system_prompt_passed(self):
        """Test run_single passes system_prompt to adapter."""
        config = EvalConfig(
            name="Test",
            defaults=Defaults(model="gpt-4o"),
            treatments={"CONTROL": Treatment(skill_path=None)},
            tests=[Task(name="test", prompt="Hello", evaluators=[])]
        )
        
        mock_adapter = MagicMock()
        mock_response = LLMResponse(
            content="Hi!",
            model="gpt-4o",
            provider="openai",
            duration_ms=1000,
            raw_response={}
        )
        mock_adapter.complete = AsyncMock(return_value=mock_response)
        
        engine = ExecutionEngine(config, mock_adapter)
        
        result = await engine.run_single(
            Treatment(skill_path=None),
            Task(name="test", prompt="Hello", evaluators=[]),
            "CONTROL"
        )
        
        # Verify system_prompt was passed to adapter.complete
        call_args = mock_adapter.complete.call_args
        assert "system_prompt" in call_args[1]
    
    @pytest.mark.asyncio
    async def test_run_single_timestamp_is_set(self):
        """Test run_single sets timestamp in result."""
        config = EvalConfig(
            name="Test",
            defaults=Defaults(model="gpt-4o"),
            treatments={"CONTROL": Treatment(skill_path=None)},
            tests=[Task(name="test", prompt="Hello", evaluators=[])]
        )
        
        mock_adapter = MagicMock()
        mock_response = LLMResponse(
            content="Hi!",
            model="gpt-4o",
            provider="openai",
            duration_ms=1000,
            raw_response={}
        )
        mock_adapter.complete = AsyncMock(return_value=mock_response)
        
        engine = ExecutionEngine(config, mock_adapter)
        
        result = await engine.run_single(
            Treatment(skill_path=None),
            Task(name="test", prompt="Hello", evaluators=[]),
            "CONTROL"
        )
        
        # Verify timestamp is ISO format
        assert result.timestamp
        assert "T" in result.timestamp  # ISO format includes T
