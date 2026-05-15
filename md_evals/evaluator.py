"""Evaluator engine for regex and LLM-judge evaluation.

Supports per-evaluator judge models: if an LLMJudgeEvaluator specifies a
``judge_model`` different from the main adapter, a separate LLMAdapter is
created for that judge call. Inspired by ghagga's multi-model distribution.
"""

import json
import re
from typing import TYPE_CHECKING

from md_evals.models import (
    Evaluator, EvaluatorResult,
    RegexEvaluator, ExactMatchEvaluator, LLMJudgeEvaluator
)

if TYPE_CHECKING:
    from md_evals.llm import LLMAdapter


class EvaluatorEngine:
    """Evaluates outputs with regex and LLM-judge.

    If ``judge_api_key`` is provided, judge evaluators that specify a different
    ``judge_model`` will use their own LLMAdapter instead of the main one.
    This follows ghagga's pattern of supporting different models for different
    purposes (generation vs evaluation).
    """

    def __init__(
        self,
        llm_adapter: "LLMAdapter | None" = None,
        judge_api_key: str | None = None,
        judge_provider: str | None = None,
        judge_api_base: str | None = None,
    ):
        self.llm_adapter = llm_adapter
        self._judge_api_key = judge_api_key
        self._judge_provider = judge_provider
        self._judge_api_base = judge_api_base
        # Cache for judge adapters (keyed by model name)
        self._judge_adapters: dict[str, "LLMAdapter"] = {}
    
    async def evaluate(
        self,
        output: str,
        evaluators: list[Evaluator],
    ) -> list[EvaluatorResult]:
        """Evaluate output against evaluators.
        
        Args:
            output: LLM output to evaluate
            evaluators: List of evaluator configs
            
        Returns:
            List of EvaluatorResults
        """
        results = []
        
        for evaluator in evaluators:
            if isinstance(evaluator, RegexEvaluator):
                result = self._evaluate_regex(output, evaluator)
            elif isinstance(evaluator, ExactMatchEvaluator):
                result = self._evaluate_exact_match(output, evaluator)
            elif isinstance(evaluator, LLMJudgeEvaluator):
                if self.llm_adapter is None:
                    result = EvaluatorResult(
                        evaluator_name=evaluator.name,
                        passed=False,
                        score=0.0,
                        reason="LLM adapter not configured"
                    )
                else:
                    result = await self._evaluate_llm_judge(output, evaluator)
            else:
                result = EvaluatorResult(
                    evaluator_name=getattr(evaluator, "name", "unknown"),
                    passed=False,
                    score=0.0,
                    reason=f"Unknown evaluator type: {type(evaluator)}"
                )
            
            results.append(result)
        
        return results
    
    def _evaluate_regex(
        self,
        output: str,
        evaluator: RegexEvaluator
    ) -> EvaluatorResult:
        """Evaluate output with regex."""
        try:
            pattern = re.compile(evaluator.pattern, re.MULTILINE | re.IGNORECASE)
            match = pattern.search(output)
            
            passed = match is not None if evaluator.pass_on_match else match is None
            
            return EvaluatorResult(
                evaluator_name=evaluator.name,
                passed=passed,
                score=1.0 if passed else 0.0,
                reason=None if passed else evaluator.fail_message or "Pattern not found"
            )
        except re.error as e:
            return EvaluatorResult(
                evaluator_name=evaluator.name,
                passed=False,
                score=0.0,
                reason=f"Invalid regex: {e}"
            )
    
    def _evaluate_exact_match(
        self,
        output: str,
        evaluator: ExactMatchEvaluator
    ) -> EvaluatorResult:
        """Evaluate output with exact match."""
        if evaluator.case_sensitive:
            passed = evaluator.expected in output
        else:
            passed = evaluator.expected.lower() in output.lower()
        
        return EvaluatorResult(
            evaluator_name=evaluator.name,
            passed=passed,
            score=1.0 if passed else 0.0,
            reason=None if passed else "Exact match not found"
        )
    
    def _get_judge_adapter(self, evaluator: LLMJudgeEvaluator) -> "LLMAdapter":
        """Get or create an LLMAdapter for the judge model.

        If the evaluator's judge_model matches the main adapter's model,
        reuse it. Otherwise, create a dedicated adapter (ghagga pattern:
        each model purpose gets its own provider instance).
        """
        assert self.llm_adapter is not None  # Caller already checked

        # If judge_model matches the main adapter, reuse it
        main_model = getattr(self.llm_adapter, "model", None)
        main_litellm_model = getattr(self.llm_adapter, "_litellm_model", None)
        if (
            not evaluator.judge_model
            or evaluator.judge_model == main_model
            or evaluator.judge_model == main_litellm_model
        ):
            return self.llm_adapter

        # If no judge-specific credentials are configured, fall back to main
        # adapter (backward-compatible with existing tests/mocks)
        judge_api_key = self._judge_api_key
        judge_provider = self._judge_provider
        if not judge_api_key:
            raw_key = getattr(self.llm_adapter, "_api_key", None)
            judge_api_key = raw_key if isinstance(raw_key, str) else None
        if not judge_provider:
            raw_prov = getattr(self.llm_adapter, "provider", None)
            judge_provider = raw_prov if isinstance(raw_prov, str) else None
        if not judge_api_key and not judge_provider:
            return self.llm_adapter

        # Check cache
        if evaluator.judge_model in self._judge_adapters:
            return self._judge_adapters[evaluator.judge_model]

        # Create a dedicated adapter for this judge model
        from md_evals.llm import LLMAdapter as _LLMAdapter
        from md_evals.models import Defaults

        adapter = _LLMAdapter(
            model=evaluator.judge_model,
            provider=judge_provider or "openai",
            api_key=judge_api_key,
            api_base=self._judge_api_base,
            defaults=Defaults(
                model=evaluator.judge_model,
                provider=judge_provider or "openai",
                temperature=0.0,  # Judges should be deterministic
                max_tokens=1000,
                timeout=60,
                retry_attempts=2,
            ),
        )

        self._judge_adapters[evaluator.judge_model] = adapter
        return adapter

    async def _evaluate_llm_judge(
        self,
        output: str,
        evaluator: LLMJudgeEvaluator,
    ) -> EvaluatorResult:
        """Evaluate output with LLM judge.

        Uses a dedicated adapter if judge_model differs from the main model.
        """
        # Build judge prompt
        judge_prompt = self._build_judge_prompt(
            output,
            evaluator.criteria,
            evaluator.output_schema,
        )

        try:
            # Get the appropriate adapter for this judge
            judge_adapter = self._get_judge_adapter(evaluator)

            # Call LLM with JSON schema
            response = await judge_adapter.complete_with_json(
                prompt=judge_prompt,
                json_schema=evaluator.output_schema,
                temperature=0.0,  # Deterministic
                max_tokens=1000,
            )
            
            # Parse JSON response
            try:
                result_data = json.loads(response.content)
            except json.JSONDecodeError:
                return EvaluatorResult(
                    evaluator_name=evaluator.name,
                    passed=False,
                    score=0.0,
                    reason="Failed to parse judge response as JSON"
                )
            
            # Extract score and reasoning
            score = result_data.get("score", 0)
            if isinstance(score, str):
                try:
                    score = float(score)
                except ValueError:
                    score = 0
            
            # Normalize score to 0-1
            # Scores already in [0, 1] are passed through unchanged.
            # Scores > 1 are assumed to be on a 1-5 or 1-10 scale.
            if score > 1 and score <= 5:
                score = score / 5
            elif score > 5 and score <= 10:
                score = score / 10
            
            reasoning = result_data.get("reasoning", "")
            
            # Determine if passed based on threshold
            passed = score >= evaluator.pass_threshold
            
            return EvaluatorResult(
                evaluator_name=evaluator.name,
                passed=passed,
                score=score,
                reason=reasoning,
                details=result_data
            )
            
        except Exception as e:
            return EvaluatorResult(
                evaluator_name=evaluator.name,
                passed=False,
                score=0.0,
                reason=f"LLM judge error: {e}"
            )
    
    def _build_judge_prompt(
        self,
        output: str,
        criteria: str,
        output_schema: dict
    ) -> str:
        """Build prompt for LLM judge."""
        return f"""You are an expert evaluator. Your task is to evaluate the quality of an AI response.

## Output to Evaluate
---
{output}
---

## Evaluation Criteria
{criteria}

## Output Schema
Provide your evaluation as JSON matching this schema:
```json
{json.dumps(output_schema, indent=2)}
```

## Output
"""


# Factory function
def create_evaluator(evaluator_type: str, **kwargs) -> Evaluator:
    """Create evaluator from type."""
    if evaluator_type == "regex":
        return RegexEvaluator(**kwargs)
    elif evaluator_type == "exact-match":
        return ExactMatchEvaluator(**kwargs)
    elif evaluator_type == "llm-judge":
        return LLMJudgeEvaluator(**kwargs)
    else:
        raise ValueError(f"Unknown evaluator type: {evaluator_type}")
