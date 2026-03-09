"""Evaluator engine for regex and LLM-judge evaluation."""

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
    """Evaluates outputs with regex and LLM-judge."""
    
    def __init__(self, llm_adapter: "LLMAdapter | None" = None):
        self.llm_adapter = llm_adapter
    
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
            pattern = re.compile(evaluator.pattern, re.MULTILINE)
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
    
    async def _evaluate_llm_judge(
        self,
        output: str,
        evaluator: LLMJudgeEvaluator
    ) -> EvaluatorResult:
        """Evaluate output with LLM judge."""
        # Build judge prompt
        judge_prompt = self._build_judge_prompt(
            output,
            evaluator.criteria,
            evaluator.output_schema
        )
        
        try:
            # Call LLM with JSON schema
            response = await self.llm_adapter.complete_with_json(
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
            if 1 <= score <= 5:
                score = score / 5
            elif 1 <= score <= 10:
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
