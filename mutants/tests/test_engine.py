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
