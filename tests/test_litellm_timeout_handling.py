"""Tests for LiteLLM timeout classification, normalization, and reporting."""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from md_evals.engine import ExecutionEngine
from md_evals.llm import (
    LLMAdapter,
    LLMError,
    LLMTimeoutError,
    classify_litellm_timeout,
    normalize_timeout_error,
)
from md_evals.models import Defaults, EvalConfig, ExecutionResult, LLMResponse, Task, Treatment
from md_evals.reporter import Reporter


def _mock_response(content: str = "ok") -> Mock:
    response = Mock()
    response.choices = [Mock(message=Mock(content=content))]
    response.usage = None
    response.model_dump = Mock(return_value={})
    return response


class TestTimeoutClassifier:
    """Unit tests for timeout classifier rules and guardrails."""

    def test_classifies_known_timeout_type(self):
        is_timeout, reason, confidence = classify_litellm_timeout(TimeoutError("timed out"))
        assert is_timeout is True
        assert reason == "known_type"
        assert confidence == "high"

    def test_classifies_timeout_in_cause_chain(self):
        try:
            raise TimeoutError("inner timeout")
        except TimeoutError as timeout_exc:
            outer = RuntimeError("wrapper failure")
            outer.__cause__ = timeout_exc

        is_timeout, reason, confidence = classify_litellm_timeout(outer)
        assert is_timeout is True
        assert reason in {"known_type", "cause_chain"}
        assert confidence == "high"

    def test_classifies_timeout_from_fallback_message(self):
        exc = Exception("request timeout while waiting for provider response")
        is_timeout, reason, confidence = classify_litellm_timeout(exc)
        assert is_timeout is True
        assert reason == "message_fallback"
        assert confidence == "low"

    def test_does_not_misclassify_ambiguous_non_timeout_error(self):
        exc = Exception("authentication timeout token invalid")
        is_timeout, reason, _ = classify_litellm_timeout(exc)
        assert is_timeout is False
        assert reason == "not_timeout"


class TestTimeoutNormalizer:
    """Unit tests for normalized timeout contract fields."""

    def test_normalized_payload_contains_required_fields(self):
        payload = normalize_timeout_error(
            TimeoutError("network timed out"),
            provider="openai",
            model="gpt-4o",
            stage="single_pass",
            attempt=2,
            max_attempts=3,
        )
        assert payload["error_type"] == "llm_timeout"
        assert payload["error_code"] == "LITELLM_TIMEOUT"
        assert payload["provider"] == "openai"
        assert payload["model"] == "gpt-4o"
        assert payload["stage"] == "single_pass"
        assert payload["is_retryable"] is True
        assert payload["attempt"] == 2
        assert payload["max_attempts"] == 3
        assert payload["raw_exception"]

    def test_normalized_payload_falls_back_to_unknown_metadata(self):
        payload = normalize_timeout_error(
            TimeoutError("timed out"),
            provider=None,
            model=None,
            stage=None,
            attempt=None,
            max_attempts=None,
        )
        assert payload["provider"] == "unknown"
        assert payload["model"] == "unknown"
        assert payload["stage"] == "single_pass"
        assert payload["attempt"] is None
        assert payload["max_attempts"] is None


class TestRetryIntegration:
    """Integration tests for timeout + retry behavior."""

    @pytest.mark.asyncio
    async def test_timeout_then_success_before_retry_limit(self):
        adapter = LLMAdapter(
            model="gpt-4o",
            provider="openai",
            defaults=Defaults(retry_attempts=3, retry_delay=0),
        )
        with patch("md_evals.llm.litellm.acompletion", new_callable=AsyncMock) as mocked_completion:
            mocked_completion.side_effect = [TimeoutError("first timeout"), _mock_response("success")]
            response = await adapter.complete(prompt="hello")
        assert response.content == "success"
        assert mocked_completion.await_count == 2

    @pytest.mark.asyncio
    async def test_timeout_exhausts_retries_with_normalized_error(self):
        adapter = LLMAdapter(
            model="gpt-4o",
            provider="openai",
            defaults=Defaults(retry_attempts=2, retry_delay=0),
        )
        with patch("md_evals.llm.litellm.acompletion", new_callable=AsyncMock) as mocked_completion:
            mocked_completion.side_effect = [TimeoutError("t1"), TimeoutError("t2")]
            with pytest.raises(LLMTimeoutError) as exc_info:
                await adapter.complete(prompt="hello")
        payload = exc_info.value.to_error_payload()
        assert payload["error_code"] == "LITELLM_TIMEOUT"
        assert payload["attempt"] == 2
        assert payload["max_attempts"] == 2

    @pytest.mark.asyncio
    async def test_zero_retry_policy_attempts_once(self):
        adapter = LLMAdapter(
            model="gpt-4o",
            provider="openai",
            defaults=Defaults(retry_attempts=0, retry_delay=0),
        )
        with patch("md_evals.llm.litellm.acompletion", new_callable=AsyncMock) as mocked_completion:
            mocked_completion.side_effect = TimeoutError("single timeout")
            with pytest.raises(LLMTimeoutError):
                await adapter.complete(prompt="hello")
        assert mocked_completion.await_count == 1

    @pytest.mark.asyncio
    async def test_mixed_retry_outcome_uses_terminal_non_timeout_error(self):
        adapter = LLMAdapter(
            model="gpt-4o",
            provider="openai",
            defaults=Defaults(retry_attempts=2, retry_delay=0),
        )
        with patch("md_evals.llm.litellm.acompletion", new_callable=AsyncMock) as mocked_completion:
            mocked_completion.side_effect = [TimeoutError("timeout"), ValueError("bad request")]
            with pytest.raises(LLMError) as exc_info:
                await adapter.complete(prompt="hello")
        assert "bad request" in str(exc_info.value).lower()
        assert mocked_completion.await_count == 2


class TestEngineAndOutputIntegration:
    """Integration tests for engine payload and reporter outputs."""

    @pytest.mark.asyncio
    async def test_engine_keeps_normalized_timeout_payload(self):
        config = EvalConfig(
            name="Timeout Eval",
            defaults=Defaults(),
            treatments={"CONTROL": Treatment(skill_path=None)},
            tests=[Task(name="t1", prompt="hello")],
        )
        mock_adapter = Mock()
        normalized_error = LLMTimeoutError(
            {
                "error_type": "llm_timeout",
                "error_code": "LITELLM_TIMEOUT",
                "message": "timeout happened",
                "provider": "openai",
                "model": "gpt-4o",
                "stage": "single_pass",
                "is_retryable": True,
                "attempt": 2,
                "max_attempts": 2,
                "raw_exception": "Request timed out",
            }
        )
        mock_adapter.complete = AsyncMock(side_effect=normalized_error)

        engine = ExecutionEngine(config=config, llm_adapter=mock_adapter)
        result = await engine.run_single(
            Treatment(skill_path=None),
            Task(name="t1", prompt="hello"),
            "CONTROL",
        )

        assert result.passed is False
        assert result.response.raw_response["error_code"] == "LITELLM_TIMEOUT"
        assert result.response.raw_response["error_type"] == "llm_timeout"

    def test_reporter_json_contains_normalized_timeout_fields(self):
        config = EvalConfig(name="Timeout Eval")
        reporter = Reporter(config)
        timeout_payload = {
            "error": "timeout happened",
            "error_type": "llm_timeout",
            "error_code": "LITELLM_TIMEOUT",
            "message": "timeout happened",
            "provider": "openai",
            "model": "gpt-4o",
            "stage": "single_pass",
            "is_retryable": True,
            "attempt": 2,
            "max_attempts": 2,
            "raw_exception": "Request timed out",
        }
        result = ExecutionResult(
            treatment="CONTROL",
            test="timeout-case",
            prompt="hello",
            response=LLMResponse(
                content="",
                model="error",
                provider="error",
                duration_ms=0,
                raw_response=timeout_payload,
            ),
            passed=False,
            evaluator_results=[],
            timestamp="2026-03-17T00:00:00+00:00",
        )
        output = reporter._build_output_data([result])
        row = output["results"][0]

        assert row["error_code"] == "LITELLM_TIMEOUT"
        assert row["error_type"] == "llm_timeout"
        assert row["is_retryable"] is True
        assert row["attempt"] == 2
        assert row["max_attempts"] == 2
        assert row["tokens"] == 0

    def test_reporter_terminal_shows_timeout_hint(self, capsys):
        config = EvalConfig(name="Timeout Eval")
        reporter = Reporter(config)
        result = ExecutionResult(
            treatment="CONTROL",
            test="timeout-case",
            prompt="hello",
            response=LLMResponse(
                content="",
                model="error",
                provider="error",
                duration_ms=0,
                raw_response={"error_code": "LITELLM_TIMEOUT", "error_type": "llm_timeout"},
            ),
            passed=False,
            evaluator_results=[],
            timestamp="2026-03-17T00:00:00+00:00",
        )
        reporter.report_terminal([result], verbose=False)
        captured = capsys.readouterr()
        assert "Timeout failures detected" in captured.out
