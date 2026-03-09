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
from typing import Annotated
from typing import Callable
from typing import ClassVar

MutantDict = Annotated[dict[str, Callable], "Mutant"] # type: ignore


def _mutmut_trampoline(orig, mutants, call_args, call_kwargs, self_arg = None): # type: ignore
    """Forward call to original or mutated function, depending on the environment"""
    import os # type: ignore
    mutant_under_test = os.environ['MUTANT_UNDER_TEST'] # type: ignore
    if mutant_under_test == 'fail': # type: ignore
        from mutmut.__main__ import MutmutProgrammaticFailException # type: ignore
        raise MutmutProgrammaticFailException('Failed programmatically')       # type: ignore
    elif mutant_under_test == 'stats': # type: ignore
        from mutmut.__main__ import record_trampoline_hit # type: ignore
        record_trampoline_hit(orig.__module__ + '.' + orig.__name__) # type: ignore
        # (for class methods, orig is bound and thus does not need the explicit self argument)
        result = orig(*call_args, **call_kwargs) # type: ignore
        return result # type: ignore
    prefix = orig.__module__ + '.' + orig.__name__ + '__mutmut_' # type: ignore
    if not mutant_under_test.startswith(prefix): # type: ignore
        result = orig(*call_args, **call_kwargs) # type: ignore
        return result # type: ignore
    mutant_name = mutant_under_test.rpartition('.')[-1] # type: ignore
    if self_arg is not None: # type: ignore
        # call to a class method where self is not bound
        result = mutants[mutant_name](self_arg, *call_args, **call_kwargs) # type: ignore
    else:
        result = mutants[mutant_name](*call_args, **call_kwargs) # type: ignore
    return result # type: ignore


class EvaluatorEngine:
    """Evaluates outputs with regex and LLM-judge."""
    
    def __init__(self, llm_adapter: "LLMAdapter | None" = None):
        args = [llm_adapter]# type: ignore
        kwargs = {}# type: ignore
        return _mutmut_trampoline(object.__getattribute__(self, 'xǁEvaluatorEngineǁ__init____mutmut_orig'), object.__getattribute__(self, 'xǁEvaluatorEngineǁ__init____mutmut_mutants'), args, kwargs, self)
    
    def xǁEvaluatorEngineǁ__init____mutmut_orig(self, llm_adapter: "LLMAdapter | None" = None):
        self.llm_adapter = llm_adapter
    
    def xǁEvaluatorEngineǁ__init____mutmut_1(self, llm_adapter: "LLMAdapter | None" = None):
        self.llm_adapter = None
    
    xǁEvaluatorEngineǁ__init____mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
    'xǁEvaluatorEngineǁ__init____mutmut_1': xǁEvaluatorEngineǁ__init____mutmut_1
    }
    xǁEvaluatorEngineǁ__init____mutmut_orig.__name__ = 'xǁEvaluatorEngineǁ__init__'
    
    async def evaluate(
        self,
        output: str,
        evaluators: list[Evaluator],
    ) -> list[EvaluatorResult]:
        args = [output, evaluators]# type: ignore
        kwargs = {}# type: ignore
        return await _mutmut_trampoline(object.__getattribute__(self, 'xǁEvaluatorEngineǁevaluate__mutmut_orig'), object.__getattribute__(self, 'xǁEvaluatorEngineǁevaluate__mutmut_mutants'), args, kwargs, self)
    
    async def xǁEvaluatorEngineǁevaluate__mutmut_orig(
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
    
    async def xǁEvaluatorEngineǁevaluate__mutmut_1(
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
        results = None
        
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
    
    async def xǁEvaluatorEngineǁevaluate__mutmut_2(
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
                result = None
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
    
    async def xǁEvaluatorEngineǁevaluate__mutmut_3(
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
                result = self._evaluate_regex(None, evaluator)
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
    
    async def xǁEvaluatorEngineǁevaluate__mutmut_4(
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
                result = self._evaluate_regex(output, None)
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
    
    async def xǁEvaluatorEngineǁevaluate__mutmut_5(
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
                result = self._evaluate_regex(evaluator)
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
    
    async def xǁEvaluatorEngineǁevaluate__mutmut_6(
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
                result = self._evaluate_regex(output, )
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
    
    async def xǁEvaluatorEngineǁevaluate__mutmut_7(
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
                result = None
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
    
    async def xǁEvaluatorEngineǁevaluate__mutmut_8(
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
                result = self._evaluate_exact_match(None, evaluator)
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
    
    async def xǁEvaluatorEngineǁevaluate__mutmut_9(
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
                result = self._evaluate_exact_match(output, None)
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
    
    async def xǁEvaluatorEngineǁevaluate__mutmut_10(
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
                result = self._evaluate_exact_match(evaluator)
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
    
    async def xǁEvaluatorEngineǁevaluate__mutmut_11(
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
                result = self._evaluate_exact_match(output, )
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
    
    async def xǁEvaluatorEngineǁevaluate__mutmut_12(
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
                if self.llm_adapter is not None:
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
    
    async def xǁEvaluatorEngineǁevaluate__mutmut_13(
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
                    result = None
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
    
    async def xǁEvaluatorEngineǁevaluate__mutmut_14(
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
                        evaluator_name=None,
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
    
    async def xǁEvaluatorEngineǁevaluate__mutmut_15(
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
                        passed=None,
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
    
    async def xǁEvaluatorEngineǁevaluate__mutmut_16(
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
                        score=None,
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
    
    async def xǁEvaluatorEngineǁevaluate__mutmut_17(
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
                        reason=None
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
    
    async def xǁEvaluatorEngineǁevaluate__mutmut_18(
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
    
    async def xǁEvaluatorEngineǁevaluate__mutmut_19(
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
    
    async def xǁEvaluatorEngineǁevaluate__mutmut_20(
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
    
    async def xǁEvaluatorEngineǁevaluate__mutmut_21(
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
    
    async def xǁEvaluatorEngineǁevaluate__mutmut_22(
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
                        passed=True,
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
    
    async def xǁEvaluatorEngineǁevaluate__mutmut_23(
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
                        score=1.0,
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
    
    async def xǁEvaluatorEngineǁevaluate__mutmut_24(
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
                        reason="XXLLM adapter not configuredXX"
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
    
    async def xǁEvaluatorEngineǁevaluate__mutmut_25(
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
                        reason="llm adapter not configured"
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
    
    async def xǁEvaluatorEngineǁevaluate__mutmut_26(
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
                        reason="LLM ADAPTER NOT CONFIGURED"
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
    
    async def xǁEvaluatorEngineǁevaluate__mutmut_27(
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
                    result = None
            else:
                result = EvaluatorResult(
                    evaluator_name=getattr(evaluator, "name", "unknown"),
                    passed=False,
                    score=0.0,
                    reason=f"Unknown evaluator type: {type(evaluator)}"
                )
            
            results.append(result)
        
        return results
    
    async def xǁEvaluatorEngineǁevaluate__mutmut_28(
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
                    result = await self._evaluate_llm_judge(None, evaluator)
            else:
                result = EvaluatorResult(
                    evaluator_name=getattr(evaluator, "name", "unknown"),
                    passed=False,
                    score=0.0,
                    reason=f"Unknown evaluator type: {type(evaluator)}"
                )
            
            results.append(result)
        
        return results
    
    async def xǁEvaluatorEngineǁevaluate__mutmut_29(
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
                    result = await self._evaluate_llm_judge(output, None)
            else:
                result = EvaluatorResult(
                    evaluator_name=getattr(evaluator, "name", "unknown"),
                    passed=False,
                    score=0.0,
                    reason=f"Unknown evaluator type: {type(evaluator)}"
                )
            
            results.append(result)
        
        return results
    
    async def xǁEvaluatorEngineǁevaluate__mutmut_30(
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
                    result = await self._evaluate_llm_judge(evaluator)
            else:
                result = EvaluatorResult(
                    evaluator_name=getattr(evaluator, "name", "unknown"),
                    passed=False,
                    score=0.0,
                    reason=f"Unknown evaluator type: {type(evaluator)}"
                )
            
            results.append(result)
        
        return results
    
    async def xǁEvaluatorEngineǁevaluate__mutmut_31(
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
                    result = await self._evaluate_llm_judge(output, )
            else:
                result = EvaluatorResult(
                    evaluator_name=getattr(evaluator, "name", "unknown"),
                    passed=False,
                    score=0.0,
                    reason=f"Unknown evaluator type: {type(evaluator)}"
                )
            
            results.append(result)
        
        return results
    
    async def xǁEvaluatorEngineǁevaluate__mutmut_32(
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
                result = None
            
            results.append(result)
        
        return results
    
    async def xǁEvaluatorEngineǁevaluate__mutmut_33(
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
                    evaluator_name=None,
                    passed=False,
                    score=0.0,
                    reason=f"Unknown evaluator type: {type(evaluator)}"
                )
            
            results.append(result)
        
        return results
    
    async def xǁEvaluatorEngineǁevaluate__mutmut_34(
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
                    passed=None,
                    score=0.0,
                    reason=f"Unknown evaluator type: {type(evaluator)}"
                )
            
            results.append(result)
        
        return results
    
    async def xǁEvaluatorEngineǁevaluate__mutmut_35(
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
                    score=None,
                    reason=f"Unknown evaluator type: {type(evaluator)}"
                )
            
            results.append(result)
        
        return results
    
    async def xǁEvaluatorEngineǁevaluate__mutmut_36(
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
                    reason=None
                )
            
            results.append(result)
        
        return results
    
    async def xǁEvaluatorEngineǁevaluate__mutmut_37(
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
                    passed=False,
                    score=0.0,
                    reason=f"Unknown evaluator type: {type(evaluator)}"
                )
            
            results.append(result)
        
        return results
    
    async def xǁEvaluatorEngineǁevaluate__mutmut_38(
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
                    score=0.0,
                    reason=f"Unknown evaluator type: {type(evaluator)}"
                )
            
            results.append(result)
        
        return results
    
    async def xǁEvaluatorEngineǁevaluate__mutmut_39(
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
                    reason=f"Unknown evaluator type: {type(evaluator)}"
                )
            
            results.append(result)
        
        return results
    
    async def xǁEvaluatorEngineǁevaluate__mutmut_40(
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
                    )
            
            results.append(result)
        
        return results
    
    async def xǁEvaluatorEngineǁevaluate__mutmut_41(
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
                    evaluator_name=getattr(None, "name", "unknown"),
                    passed=False,
                    score=0.0,
                    reason=f"Unknown evaluator type: {type(evaluator)}"
                )
            
            results.append(result)
        
        return results
    
    async def xǁEvaluatorEngineǁevaluate__mutmut_42(
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
                    evaluator_name=getattr(evaluator, None, "unknown"),
                    passed=False,
                    score=0.0,
                    reason=f"Unknown evaluator type: {type(evaluator)}"
                )
            
            results.append(result)
        
        return results
    
    async def xǁEvaluatorEngineǁevaluate__mutmut_43(
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
                    evaluator_name=getattr(evaluator, "name", None),
                    passed=False,
                    score=0.0,
                    reason=f"Unknown evaluator type: {type(evaluator)}"
                )
            
            results.append(result)
        
        return results
    
    async def xǁEvaluatorEngineǁevaluate__mutmut_44(
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
                    evaluator_name=getattr("name", "unknown"),
                    passed=False,
                    score=0.0,
                    reason=f"Unknown evaluator type: {type(evaluator)}"
                )
            
            results.append(result)
        
        return results
    
    async def xǁEvaluatorEngineǁevaluate__mutmut_45(
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
                    evaluator_name=getattr(evaluator, "unknown"),
                    passed=False,
                    score=0.0,
                    reason=f"Unknown evaluator type: {type(evaluator)}"
                )
            
            results.append(result)
        
        return results
    
    async def xǁEvaluatorEngineǁevaluate__mutmut_46(
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
                    evaluator_name=getattr(evaluator, "name", ),
                    passed=False,
                    score=0.0,
                    reason=f"Unknown evaluator type: {type(evaluator)}"
                )
            
            results.append(result)
        
        return results
    
    async def xǁEvaluatorEngineǁevaluate__mutmut_47(
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
                    evaluator_name=getattr(evaluator, "XXnameXX", "unknown"),
                    passed=False,
                    score=0.0,
                    reason=f"Unknown evaluator type: {type(evaluator)}"
                )
            
            results.append(result)
        
        return results
    
    async def xǁEvaluatorEngineǁevaluate__mutmut_48(
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
                    evaluator_name=getattr(evaluator, "NAME", "unknown"),
                    passed=False,
                    score=0.0,
                    reason=f"Unknown evaluator type: {type(evaluator)}"
                )
            
            results.append(result)
        
        return results
    
    async def xǁEvaluatorEngineǁevaluate__mutmut_49(
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
                    evaluator_name=getattr(evaluator, "name", "XXunknownXX"),
                    passed=False,
                    score=0.0,
                    reason=f"Unknown evaluator type: {type(evaluator)}"
                )
            
            results.append(result)
        
        return results
    
    async def xǁEvaluatorEngineǁevaluate__mutmut_50(
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
                    evaluator_name=getattr(evaluator, "name", "UNKNOWN"),
                    passed=False,
                    score=0.0,
                    reason=f"Unknown evaluator type: {type(evaluator)}"
                )
            
            results.append(result)
        
        return results
    
    async def xǁEvaluatorEngineǁevaluate__mutmut_51(
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
                    passed=True,
                    score=0.0,
                    reason=f"Unknown evaluator type: {type(evaluator)}"
                )
            
            results.append(result)
        
        return results
    
    async def xǁEvaluatorEngineǁevaluate__mutmut_52(
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
                    score=1.0,
                    reason=f"Unknown evaluator type: {type(evaluator)}"
                )
            
            results.append(result)
        
        return results
    
    async def xǁEvaluatorEngineǁevaluate__mutmut_53(
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
                    reason=f"Unknown evaluator type: {type(None)}"
                )
            
            results.append(result)
        
        return results
    
    async def xǁEvaluatorEngineǁevaluate__mutmut_54(
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
            
            results.append(None)
        
        return results
    
    xǁEvaluatorEngineǁevaluate__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
    'xǁEvaluatorEngineǁevaluate__mutmut_1': xǁEvaluatorEngineǁevaluate__mutmut_1, 
        'xǁEvaluatorEngineǁevaluate__mutmut_2': xǁEvaluatorEngineǁevaluate__mutmut_2, 
        'xǁEvaluatorEngineǁevaluate__mutmut_3': xǁEvaluatorEngineǁevaluate__mutmut_3, 
        'xǁEvaluatorEngineǁevaluate__mutmut_4': xǁEvaluatorEngineǁevaluate__mutmut_4, 
        'xǁEvaluatorEngineǁevaluate__mutmut_5': xǁEvaluatorEngineǁevaluate__mutmut_5, 
        'xǁEvaluatorEngineǁevaluate__mutmut_6': xǁEvaluatorEngineǁevaluate__mutmut_6, 
        'xǁEvaluatorEngineǁevaluate__mutmut_7': xǁEvaluatorEngineǁevaluate__mutmut_7, 
        'xǁEvaluatorEngineǁevaluate__mutmut_8': xǁEvaluatorEngineǁevaluate__mutmut_8, 
        'xǁEvaluatorEngineǁevaluate__mutmut_9': xǁEvaluatorEngineǁevaluate__mutmut_9, 
        'xǁEvaluatorEngineǁevaluate__mutmut_10': xǁEvaluatorEngineǁevaluate__mutmut_10, 
        'xǁEvaluatorEngineǁevaluate__mutmut_11': xǁEvaluatorEngineǁevaluate__mutmut_11, 
        'xǁEvaluatorEngineǁevaluate__mutmut_12': xǁEvaluatorEngineǁevaluate__mutmut_12, 
        'xǁEvaluatorEngineǁevaluate__mutmut_13': xǁEvaluatorEngineǁevaluate__mutmut_13, 
        'xǁEvaluatorEngineǁevaluate__mutmut_14': xǁEvaluatorEngineǁevaluate__mutmut_14, 
        'xǁEvaluatorEngineǁevaluate__mutmut_15': xǁEvaluatorEngineǁevaluate__mutmut_15, 
        'xǁEvaluatorEngineǁevaluate__mutmut_16': xǁEvaluatorEngineǁevaluate__mutmut_16, 
        'xǁEvaluatorEngineǁevaluate__mutmut_17': xǁEvaluatorEngineǁevaluate__mutmut_17, 
        'xǁEvaluatorEngineǁevaluate__mutmut_18': xǁEvaluatorEngineǁevaluate__mutmut_18, 
        'xǁEvaluatorEngineǁevaluate__mutmut_19': xǁEvaluatorEngineǁevaluate__mutmut_19, 
        'xǁEvaluatorEngineǁevaluate__mutmut_20': xǁEvaluatorEngineǁevaluate__mutmut_20, 
        'xǁEvaluatorEngineǁevaluate__mutmut_21': xǁEvaluatorEngineǁevaluate__mutmut_21, 
        'xǁEvaluatorEngineǁevaluate__mutmut_22': xǁEvaluatorEngineǁevaluate__mutmut_22, 
        'xǁEvaluatorEngineǁevaluate__mutmut_23': xǁEvaluatorEngineǁevaluate__mutmut_23, 
        'xǁEvaluatorEngineǁevaluate__mutmut_24': xǁEvaluatorEngineǁevaluate__mutmut_24, 
        'xǁEvaluatorEngineǁevaluate__mutmut_25': xǁEvaluatorEngineǁevaluate__mutmut_25, 
        'xǁEvaluatorEngineǁevaluate__mutmut_26': xǁEvaluatorEngineǁevaluate__mutmut_26, 
        'xǁEvaluatorEngineǁevaluate__mutmut_27': xǁEvaluatorEngineǁevaluate__mutmut_27, 
        'xǁEvaluatorEngineǁevaluate__mutmut_28': xǁEvaluatorEngineǁevaluate__mutmut_28, 
        'xǁEvaluatorEngineǁevaluate__mutmut_29': xǁEvaluatorEngineǁevaluate__mutmut_29, 
        'xǁEvaluatorEngineǁevaluate__mutmut_30': xǁEvaluatorEngineǁevaluate__mutmut_30, 
        'xǁEvaluatorEngineǁevaluate__mutmut_31': xǁEvaluatorEngineǁevaluate__mutmut_31, 
        'xǁEvaluatorEngineǁevaluate__mutmut_32': xǁEvaluatorEngineǁevaluate__mutmut_32, 
        'xǁEvaluatorEngineǁevaluate__mutmut_33': xǁEvaluatorEngineǁevaluate__mutmut_33, 
        'xǁEvaluatorEngineǁevaluate__mutmut_34': xǁEvaluatorEngineǁevaluate__mutmut_34, 
        'xǁEvaluatorEngineǁevaluate__mutmut_35': xǁEvaluatorEngineǁevaluate__mutmut_35, 
        'xǁEvaluatorEngineǁevaluate__mutmut_36': xǁEvaluatorEngineǁevaluate__mutmut_36, 
        'xǁEvaluatorEngineǁevaluate__mutmut_37': xǁEvaluatorEngineǁevaluate__mutmut_37, 
        'xǁEvaluatorEngineǁevaluate__mutmut_38': xǁEvaluatorEngineǁevaluate__mutmut_38, 
        'xǁEvaluatorEngineǁevaluate__mutmut_39': xǁEvaluatorEngineǁevaluate__mutmut_39, 
        'xǁEvaluatorEngineǁevaluate__mutmut_40': xǁEvaluatorEngineǁevaluate__mutmut_40, 
        'xǁEvaluatorEngineǁevaluate__mutmut_41': xǁEvaluatorEngineǁevaluate__mutmut_41, 
        'xǁEvaluatorEngineǁevaluate__mutmut_42': xǁEvaluatorEngineǁevaluate__mutmut_42, 
        'xǁEvaluatorEngineǁevaluate__mutmut_43': xǁEvaluatorEngineǁevaluate__mutmut_43, 
        'xǁEvaluatorEngineǁevaluate__mutmut_44': xǁEvaluatorEngineǁevaluate__mutmut_44, 
        'xǁEvaluatorEngineǁevaluate__mutmut_45': xǁEvaluatorEngineǁevaluate__mutmut_45, 
        'xǁEvaluatorEngineǁevaluate__mutmut_46': xǁEvaluatorEngineǁevaluate__mutmut_46, 
        'xǁEvaluatorEngineǁevaluate__mutmut_47': xǁEvaluatorEngineǁevaluate__mutmut_47, 
        'xǁEvaluatorEngineǁevaluate__mutmut_48': xǁEvaluatorEngineǁevaluate__mutmut_48, 
        'xǁEvaluatorEngineǁevaluate__mutmut_49': xǁEvaluatorEngineǁevaluate__mutmut_49, 
        'xǁEvaluatorEngineǁevaluate__mutmut_50': xǁEvaluatorEngineǁevaluate__mutmut_50, 
        'xǁEvaluatorEngineǁevaluate__mutmut_51': xǁEvaluatorEngineǁevaluate__mutmut_51, 
        'xǁEvaluatorEngineǁevaluate__mutmut_52': xǁEvaluatorEngineǁevaluate__mutmut_52, 
        'xǁEvaluatorEngineǁevaluate__mutmut_53': xǁEvaluatorEngineǁevaluate__mutmut_53, 
        'xǁEvaluatorEngineǁevaluate__mutmut_54': xǁEvaluatorEngineǁevaluate__mutmut_54
    }
    xǁEvaluatorEngineǁevaluate__mutmut_orig.__name__ = 'xǁEvaluatorEngineǁevaluate'
    
    def _evaluate_regex(
        self,
        output: str,
        evaluator: RegexEvaluator
    ) -> EvaluatorResult:
        args = [output, evaluator]# type: ignore
        kwargs = {}# type: ignore
        return _mutmut_trampoline(object.__getattribute__(self, 'xǁEvaluatorEngineǁ_evaluate_regex__mutmut_orig'), object.__getattribute__(self, 'xǁEvaluatorEngineǁ_evaluate_regex__mutmut_mutants'), args, kwargs, self)
    
    def xǁEvaluatorEngineǁ_evaluate_regex__mutmut_orig(
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
    
    def xǁEvaluatorEngineǁ_evaluate_regex__mutmut_1(
        self,
        output: str,
        evaluator: RegexEvaluator
    ) -> EvaluatorResult:
        """Evaluate output with regex."""
        try:
            pattern = None
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
    
    def xǁEvaluatorEngineǁ_evaluate_regex__mutmut_2(
        self,
        output: str,
        evaluator: RegexEvaluator
    ) -> EvaluatorResult:
        """Evaluate output with regex."""
        try:
            pattern = re.compile(None, re.MULTILINE | re.IGNORECASE)
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
    
    def xǁEvaluatorEngineǁ_evaluate_regex__mutmut_3(
        self,
        output: str,
        evaluator: RegexEvaluator
    ) -> EvaluatorResult:
        """Evaluate output with regex."""
        try:
            pattern = re.compile(evaluator.pattern, None)
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
    
    def xǁEvaluatorEngineǁ_evaluate_regex__mutmut_4(
        self,
        output: str,
        evaluator: RegexEvaluator
    ) -> EvaluatorResult:
        """Evaluate output with regex."""
        try:
            pattern = re.compile(re.MULTILINE | re.IGNORECASE)
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
    
    def xǁEvaluatorEngineǁ_evaluate_regex__mutmut_5(
        self,
        output: str,
        evaluator: RegexEvaluator
    ) -> EvaluatorResult:
        """Evaluate output with regex."""
        try:
            pattern = re.compile(evaluator.pattern, )
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
    
    def xǁEvaluatorEngineǁ_evaluate_regex__mutmut_6(
        self,
        output: str,
        evaluator: RegexEvaluator
    ) -> EvaluatorResult:
        """Evaluate output with regex."""
        try:
            pattern = re.compile(evaluator.pattern, re.MULTILINE & re.IGNORECASE)
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
    
    def xǁEvaluatorEngineǁ_evaluate_regex__mutmut_7(
        self,
        output: str,
        evaluator: RegexEvaluator
    ) -> EvaluatorResult:
        """Evaluate output with regex."""
        try:
            pattern = re.compile(evaluator.pattern, re.MULTILINE | re.IGNORECASE)
            match = None
            
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
    
    def xǁEvaluatorEngineǁ_evaluate_regex__mutmut_8(
        self,
        output: str,
        evaluator: RegexEvaluator
    ) -> EvaluatorResult:
        """Evaluate output with regex."""
        try:
            pattern = re.compile(evaluator.pattern, re.MULTILINE | re.IGNORECASE)
            match = pattern.search(None)
            
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
    
    def xǁEvaluatorEngineǁ_evaluate_regex__mutmut_9(
        self,
        output: str,
        evaluator: RegexEvaluator
    ) -> EvaluatorResult:
        """Evaluate output with regex."""
        try:
            pattern = re.compile(evaluator.pattern, re.MULTILINE | re.IGNORECASE)
            match = pattern.search(output)
            
            passed = None
            
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
    
    def xǁEvaluatorEngineǁ_evaluate_regex__mutmut_10(
        self,
        output: str,
        evaluator: RegexEvaluator
    ) -> EvaluatorResult:
        """Evaluate output with regex."""
        try:
            pattern = re.compile(evaluator.pattern, re.MULTILINE | re.IGNORECASE)
            match = pattern.search(output)
            
            passed = match is None if evaluator.pass_on_match else match is None
            
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
    
    def xǁEvaluatorEngineǁ_evaluate_regex__mutmut_11(
        self,
        output: str,
        evaluator: RegexEvaluator
    ) -> EvaluatorResult:
        """Evaluate output with regex."""
        try:
            pattern = re.compile(evaluator.pattern, re.MULTILINE | re.IGNORECASE)
            match = pattern.search(output)
            
            passed = match is not None if evaluator.pass_on_match else match is not None
            
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
    
    def xǁEvaluatorEngineǁ_evaluate_regex__mutmut_12(
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
                evaluator_name=None,
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
    
    def xǁEvaluatorEngineǁ_evaluate_regex__mutmut_13(
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
                passed=None,
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
    
    def xǁEvaluatorEngineǁ_evaluate_regex__mutmut_14(
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
                score=None,
                reason=None if passed else evaluator.fail_message or "Pattern not found"
            )
        except re.error as e:
            return EvaluatorResult(
                evaluator_name=evaluator.name,
                passed=False,
                score=0.0,
                reason=f"Invalid regex: {e}"
            )
    
    def xǁEvaluatorEngineǁ_evaluate_regex__mutmut_15(
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
                reason=None
            )
        except re.error as e:
            return EvaluatorResult(
                evaluator_name=evaluator.name,
                passed=False,
                score=0.0,
                reason=f"Invalid regex: {e}"
            )
    
    def xǁEvaluatorEngineǁ_evaluate_regex__mutmut_16(
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
    
    def xǁEvaluatorEngineǁ_evaluate_regex__mutmut_17(
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
    
    def xǁEvaluatorEngineǁ_evaluate_regex__mutmut_18(
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
                reason=None if passed else evaluator.fail_message or "Pattern not found"
            )
        except re.error as e:
            return EvaluatorResult(
                evaluator_name=evaluator.name,
                passed=False,
                score=0.0,
                reason=f"Invalid regex: {e}"
            )
    
    def xǁEvaluatorEngineǁ_evaluate_regex__mutmut_19(
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
                )
        except re.error as e:
            return EvaluatorResult(
                evaluator_name=evaluator.name,
                passed=False,
                score=0.0,
                reason=f"Invalid regex: {e}"
            )
    
    def xǁEvaluatorEngineǁ_evaluate_regex__mutmut_20(
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
                score=2.0 if passed else 0.0,
                reason=None if passed else evaluator.fail_message or "Pattern not found"
            )
        except re.error as e:
            return EvaluatorResult(
                evaluator_name=evaluator.name,
                passed=False,
                score=0.0,
                reason=f"Invalid regex: {e}"
            )
    
    def xǁEvaluatorEngineǁ_evaluate_regex__mutmut_21(
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
                score=1.0 if passed else 1.0,
                reason=None if passed else evaluator.fail_message or "Pattern not found"
            )
        except re.error as e:
            return EvaluatorResult(
                evaluator_name=evaluator.name,
                passed=False,
                score=0.0,
                reason=f"Invalid regex: {e}"
            )
    
    def xǁEvaluatorEngineǁ_evaluate_regex__mutmut_22(
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
                reason=None if passed else evaluator.fail_message and "Pattern not found"
            )
        except re.error as e:
            return EvaluatorResult(
                evaluator_name=evaluator.name,
                passed=False,
                score=0.0,
                reason=f"Invalid regex: {e}"
            )
    
    def xǁEvaluatorEngineǁ_evaluate_regex__mutmut_23(
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
                reason=None if passed else evaluator.fail_message or "XXPattern not foundXX"
            )
        except re.error as e:
            return EvaluatorResult(
                evaluator_name=evaluator.name,
                passed=False,
                score=0.0,
                reason=f"Invalid regex: {e}"
            )
    
    def xǁEvaluatorEngineǁ_evaluate_regex__mutmut_24(
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
                reason=None if passed else evaluator.fail_message or "pattern not found"
            )
        except re.error as e:
            return EvaluatorResult(
                evaluator_name=evaluator.name,
                passed=False,
                score=0.0,
                reason=f"Invalid regex: {e}"
            )
    
    def xǁEvaluatorEngineǁ_evaluate_regex__mutmut_25(
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
                reason=None if passed else evaluator.fail_message or "PATTERN NOT FOUND"
            )
        except re.error as e:
            return EvaluatorResult(
                evaluator_name=evaluator.name,
                passed=False,
                score=0.0,
                reason=f"Invalid regex: {e}"
            )
    
    def xǁEvaluatorEngineǁ_evaluate_regex__mutmut_26(
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
                evaluator_name=None,
                passed=False,
                score=0.0,
                reason=f"Invalid regex: {e}"
            )
    
    def xǁEvaluatorEngineǁ_evaluate_regex__mutmut_27(
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
                passed=None,
                score=0.0,
                reason=f"Invalid regex: {e}"
            )
    
    def xǁEvaluatorEngineǁ_evaluate_regex__mutmut_28(
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
                score=None,
                reason=f"Invalid regex: {e}"
            )
    
    def xǁEvaluatorEngineǁ_evaluate_regex__mutmut_29(
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
                reason=None
            )
    
    def xǁEvaluatorEngineǁ_evaluate_regex__mutmut_30(
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
                passed=False,
                score=0.0,
                reason=f"Invalid regex: {e}"
            )
    
    def xǁEvaluatorEngineǁ_evaluate_regex__mutmut_31(
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
                score=0.0,
                reason=f"Invalid regex: {e}"
            )
    
    def xǁEvaluatorEngineǁ_evaluate_regex__mutmut_32(
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
                reason=f"Invalid regex: {e}"
            )
    
    def xǁEvaluatorEngineǁ_evaluate_regex__mutmut_33(
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
                )
    
    def xǁEvaluatorEngineǁ_evaluate_regex__mutmut_34(
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
                passed=True,
                score=0.0,
                reason=f"Invalid regex: {e}"
            )
    
    def xǁEvaluatorEngineǁ_evaluate_regex__mutmut_35(
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
                score=1.0,
                reason=f"Invalid regex: {e}"
            )
    
    xǁEvaluatorEngineǁ_evaluate_regex__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
    'xǁEvaluatorEngineǁ_evaluate_regex__mutmut_1': xǁEvaluatorEngineǁ_evaluate_regex__mutmut_1, 
        'xǁEvaluatorEngineǁ_evaluate_regex__mutmut_2': xǁEvaluatorEngineǁ_evaluate_regex__mutmut_2, 
        'xǁEvaluatorEngineǁ_evaluate_regex__mutmut_3': xǁEvaluatorEngineǁ_evaluate_regex__mutmut_3, 
        'xǁEvaluatorEngineǁ_evaluate_regex__mutmut_4': xǁEvaluatorEngineǁ_evaluate_regex__mutmut_4, 
        'xǁEvaluatorEngineǁ_evaluate_regex__mutmut_5': xǁEvaluatorEngineǁ_evaluate_regex__mutmut_5, 
        'xǁEvaluatorEngineǁ_evaluate_regex__mutmut_6': xǁEvaluatorEngineǁ_evaluate_regex__mutmut_6, 
        'xǁEvaluatorEngineǁ_evaluate_regex__mutmut_7': xǁEvaluatorEngineǁ_evaluate_regex__mutmut_7, 
        'xǁEvaluatorEngineǁ_evaluate_regex__mutmut_8': xǁEvaluatorEngineǁ_evaluate_regex__mutmut_8, 
        'xǁEvaluatorEngineǁ_evaluate_regex__mutmut_9': xǁEvaluatorEngineǁ_evaluate_regex__mutmut_9, 
        'xǁEvaluatorEngineǁ_evaluate_regex__mutmut_10': xǁEvaluatorEngineǁ_evaluate_regex__mutmut_10, 
        'xǁEvaluatorEngineǁ_evaluate_regex__mutmut_11': xǁEvaluatorEngineǁ_evaluate_regex__mutmut_11, 
        'xǁEvaluatorEngineǁ_evaluate_regex__mutmut_12': xǁEvaluatorEngineǁ_evaluate_regex__mutmut_12, 
        'xǁEvaluatorEngineǁ_evaluate_regex__mutmut_13': xǁEvaluatorEngineǁ_evaluate_regex__mutmut_13, 
        'xǁEvaluatorEngineǁ_evaluate_regex__mutmut_14': xǁEvaluatorEngineǁ_evaluate_regex__mutmut_14, 
        'xǁEvaluatorEngineǁ_evaluate_regex__mutmut_15': xǁEvaluatorEngineǁ_evaluate_regex__mutmut_15, 
        'xǁEvaluatorEngineǁ_evaluate_regex__mutmut_16': xǁEvaluatorEngineǁ_evaluate_regex__mutmut_16, 
        'xǁEvaluatorEngineǁ_evaluate_regex__mutmut_17': xǁEvaluatorEngineǁ_evaluate_regex__mutmut_17, 
        'xǁEvaluatorEngineǁ_evaluate_regex__mutmut_18': xǁEvaluatorEngineǁ_evaluate_regex__mutmut_18, 
        'xǁEvaluatorEngineǁ_evaluate_regex__mutmut_19': xǁEvaluatorEngineǁ_evaluate_regex__mutmut_19, 
        'xǁEvaluatorEngineǁ_evaluate_regex__mutmut_20': xǁEvaluatorEngineǁ_evaluate_regex__mutmut_20, 
        'xǁEvaluatorEngineǁ_evaluate_regex__mutmut_21': xǁEvaluatorEngineǁ_evaluate_regex__mutmut_21, 
        'xǁEvaluatorEngineǁ_evaluate_regex__mutmut_22': xǁEvaluatorEngineǁ_evaluate_regex__mutmut_22, 
        'xǁEvaluatorEngineǁ_evaluate_regex__mutmut_23': xǁEvaluatorEngineǁ_evaluate_regex__mutmut_23, 
        'xǁEvaluatorEngineǁ_evaluate_regex__mutmut_24': xǁEvaluatorEngineǁ_evaluate_regex__mutmut_24, 
        'xǁEvaluatorEngineǁ_evaluate_regex__mutmut_25': xǁEvaluatorEngineǁ_evaluate_regex__mutmut_25, 
        'xǁEvaluatorEngineǁ_evaluate_regex__mutmut_26': xǁEvaluatorEngineǁ_evaluate_regex__mutmut_26, 
        'xǁEvaluatorEngineǁ_evaluate_regex__mutmut_27': xǁEvaluatorEngineǁ_evaluate_regex__mutmut_27, 
        'xǁEvaluatorEngineǁ_evaluate_regex__mutmut_28': xǁEvaluatorEngineǁ_evaluate_regex__mutmut_28, 
        'xǁEvaluatorEngineǁ_evaluate_regex__mutmut_29': xǁEvaluatorEngineǁ_evaluate_regex__mutmut_29, 
        'xǁEvaluatorEngineǁ_evaluate_regex__mutmut_30': xǁEvaluatorEngineǁ_evaluate_regex__mutmut_30, 
        'xǁEvaluatorEngineǁ_evaluate_regex__mutmut_31': xǁEvaluatorEngineǁ_evaluate_regex__mutmut_31, 
        'xǁEvaluatorEngineǁ_evaluate_regex__mutmut_32': xǁEvaluatorEngineǁ_evaluate_regex__mutmut_32, 
        'xǁEvaluatorEngineǁ_evaluate_regex__mutmut_33': xǁEvaluatorEngineǁ_evaluate_regex__mutmut_33, 
        'xǁEvaluatorEngineǁ_evaluate_regex__mutmut_34': xǁEvaluatorEngineǁ_evaluate_regex__mutmut_34, 
        'xǁEvaluatorEngineǁ_evaluate_regex__mutmut_35': xǁEvaluatorEngineǁ_evaluate_regex__mutmut_35
    }
    xǁEvaluatorEngineǁ_evaluate_regex__mutmut_orig.__name__ = 'xǁEvaluatorEngineǁ_evaluate_regex'
    
    def _evaluate_exact_match(
        self,
        output: str,
        evaluator: ExactMatchEvaluator
    ) -> EvaluatorResult:
        args = [output, evaluator]# type: ignore
        kwargs = {}# type: ignore
        return _mutmut_trampoline(object.__getattribute__(self, 'xǁEvaluatorEngineǁ_evaluate_exact_match__mutmut_orig'), object.__getattribute__(self, 'xǁEvaluatorEngineǁ_evaluate_exact_match__mutmut_mutants'), args, kwargs, self)
    
    def xǁEvaluatorEngineǁ_evaluate_exact_match__mutmut_orig(
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
    
    def xǁEvaluatorEngineǁ_evaluate_exact_match__mutmut_1(
        self,
        output: str,
        evaluator: ExactMatchEvaluator
    ) -> EvaluatorResult:
        """Evaluate output with exact match."""
        if evaluator.case_sensitive:
            passed = None
        else:
            passed = evaluator.expected.lower() in output.lower()
        
        return EvaluatorResult(
            evaluator_name=evaluator.name,
            passed=passed,
            score=1.0 if passed else 0.0,
            reason=None if passed else "Exact match not found"
        )
    
    def xǁEvaluatorEngineǁ_evaluate_exact_match__mutmut_2(
        self,
        output: str,
        evaluator: ExactMatchEvaluator
    ) -> EvaluatorResult:
        """Evaluate output with exact match."""
        if evaluator.case_sensitive:
            passed = evaluator.expected not in output
        else:
            passed = evaluator.expected.lower() in output.lower()
        
        return EvaluatorResult(
            evaluator_name=evaluator.name,
            passed=passed,
            score=1.0 if passed else 0.0,
            reason=None if passed else "Exact match not found"
        )
    
    def xǁEvaluatorEngineǁ_evaluate_exact_match__mutmut_3(
        self,
        output: str,
        evaluator: ExactMatchEvaluator
    ) -> EvaluatorResult:
        """Evaluate output with exact match."""
        if evaluator.case_sensitive:
            passed = evaluator.expected in output
        else:
            passed = None
        
        return EvaluatorResult(
            evaluator_name=evaluator.name,
            passed=passed,
            score=1.0 if passed else 0.0,
            reason=None if passed else "Exact match not found"
        )
    
    def xǁEvaluatorEngineǁ_evaluate_exact_match__mutmut_4(
        self,
        output: str,
        evaluator: ExactMatchEvaluator
    ) -> EvaluatorResult:
        """Evaluate output with exact match."""
        if evaluator.case_sensitive:
            passed = evaluator.expected in output
        else:
            passed = evaluator.expected.upper() in output.lower()
        
        return EvaluatorResult(
            evaluator_name=evaluator.name,
            passed=passed,
            score=1.0 if passed else 0.0,
            reason=None if passed else "Exact match not found"
        )
    
    def xǁEvaluatorEngineǁ_evaluate_exact_match__mutmut_5(
        self,
        output: str,
        evaluator: ExactMatchEvaluator
    ) -> EvaluatorResult:
        """Evaluate output with exact match."""
        if evaluator.case_sensitive:
            passed = evaluator.expected in output
        else:
            passed = evaluator.expected.lower() not in output.lower()
        
        return EvaluatorResult(
            evaluator_name=evaluator.name,
            passed=passed,
            score=1.0 if passed else 0.0,
            reason=None if passed else "Exact match not found"
        )
    
    def xǁEvaluatorEngineǁ_evaluate_exact_match__mutmut_6(
        self,
        output: str,
        evaluator: ExactMatchEvaluator
    ) -> EvaluatorResult:
        """Evaluate output with exact match."""
        if evaluator.case_sensitive:
            passed = evaluator.expected in output
        else:
            passed = evaluator.expected.lower() in output.upper()
        
        return EvaluatorResult(
            evaluator_name=evaluator.name,
            passed=passed,
            score=1.0 if passed else 0.0,
            reason=None if passed else "Exact match not found"
        )
    
    def xǁEvaluatorEngineǁ_evaluate_exact_match__mutmut_7(
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
            evaluator_name=None,
            passed=passed,
            score=1.0 if passed else 0.0,
            reason=None if passed else "Exact match not found"
        )
    
    def xǁEvaluatorEngineǁ_evaluate_exact_match__mutmut_8(
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
            passed=None,
            score=1.0 if passed else 0.0,
            reason=None if passed else "Exact match not found"
        )
    
    def xǁEvaluatorEngineǁ_evaluate_exact_match__mutmut_9(
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
            score=None,
            reason=None if passed else "Exact match not found"
        )
    
    def xǁEvaluatorEngineǁ_evaluate_exact_match__mutmut_10(
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
            reason=None
        )
    
    def xǁEvaluatorEngineǁ_evaluate_exact_match__mutmut_11(
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
            passed=passed,
            score=1.0 if passed else 0.0,
            reason=None if passed else "Exact match not found"
        )
    
    def xǁEvaluatorEngineǁ_evaluate_exact_match__mutmut_12(
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
            score=1.0 if passed else 0.0,
            reason=None if passed else "Exact match not found"
        )
    
    def xǁEvaluatorEngineǁ_evaluate_exact_match__mutmut_13(
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
            reason=None if passed else "Exact match not found"
        )
    
    def xǁEvaluatorEngineǁ_evaluate_exact_match__mutmut_14(
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
            )
    
    def xǁEvaluatorEngineǁ_evaluate_exact_match__mutmut_15(
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
            score=2.0 if passed else 0.0,
            reason=None if passed else "Exact match not found"
        )
    
    def xǁEvaluatorEngineǁ_evaluate_exact_match__mutmut_16(
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
            score=1.0 if passed else 1.0,
            reason=None if passed else "Exact match not found"
        )
    
    def xǁEvaluatorEngineǁ_evaluate_exact_match__mutmut_17(
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
            reason=None if passed else "XXExact match not foundXX"
        )
    
    def xǁEvaluatorEngineǁ_evaluate_exact_match__mutmut_18(
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
            reason=None if passed else "exact match not found"
        )
    
    def xǁEvaluatorEngineǁ_evaluate_exact_match__mutmut_19(
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
            reason=None if passed else "EXACT MATCH NOT FOUND"
        )
    
    xǁEvaluatorEngineǁ_evaluate_exact_match__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
    'xǁEvaluatorEngineǁ_evaluate_exact_match__mutmut_1': xǁEvaluatorEngineǁ_evaluate_exact_match__mutmut_1, 
        'xǁEvaluatorEngineǁ_evaluate_exact_match__mutmut_2': xǁEvaluatorEngineǁ_evaluate_exact_match__mutmut_2, 
        'xǁEvaluatorEngineǁ_evaluate_exact_match__mutmut_3': xǁEvaluatorEngineǁ_evaluate_exact_match__mutmut_3, 
        'xǁEvaluatorEngineǁ_evaluate_exact_match__mutmut_4': xǁEvaluatorEngineǁ_evaluate_exact_match__mutmut_4, 
        'xǁEvaluatorEngineǁ_evaluate_exact_match__mutmut_5': xǁEvaluatorEngineǁ_evaluate_exact_match__mutmut_5, 
        'xǁEvaluatorEngineǁ_evaluate_exact_match__mutmut_6': xǁEvaluatorEngineǁ_evaluate_exact_match__mutmut_6, 
        'xǁEvaluatorEngineǁ_evaluate_exact_match__mutmut_7': xǁEvaluatorEngineǁ_evaluate_exact_match__mutmut_7, 
        'xǁEvaluatorEngineǁ_evaluate_exact_match__mutmut_8': xǁEvaluatorEngineǁ_evaluate_exact_match__mutmut_8, 
        'xǁEvaluatorEngineǁ_evaluate_exact_match__mutmut_9': xǁEvaluatorEngineǁ_evaluate_exact_match__mutmut_9, 
        'xǁEvaluatorEngineǁ_evaluate_exact_match__mutmut_10': xǁEvaluatorEngineǁ_evaluate_exact_match__mutmut_10, 
        'xǁEvaluatorEngineǁ_evaluate_exact_match__mutmut_11': xǁEvaluatorEngineǁ_evaluate_exact_match__mutmut_11, 
        'xǁEvaluatorEngineǁ_evaluate_exact_match__mutmut_12': xǁEvaluatorEngineǁ_evaluate_exact_match__mutmut_12, 
        'xǁEvaluatorEngineǁ_evaluate_exact_match__mutmut_13': xǁEvaluatorEngineǁ_evaluate_exact_match__mutmut_13, 
        'xǁEvaluatorEngineǁ_evaluate_exact_match__mutmut_14': xǁEvaluatorEngineǁ_evaluate_exact_match__mutmut_14, 
        'xǁEvaluatorEngineǁ_evaluate_exact_match__mutmut_15': xǁEvaluatorEngineǁ_evaluate_exact_match__mutmut_15, 
        'xǁEvaluatorEngineǁ_evaluate_exact_match__mutmut_16': xǁEvaluatorEngineǁ_evaluate_exact_match__mutmut_16, 
        'xǁEvaluatorEngineǁ_evaluate_exact_match__mutmut_17': xǁEvaluatorEngineǁ_evaluate_exact_match__mutmut_17, 
        'xǁEvaluatorEngineǁ_evaluate_exact_match__mutmut_18': xǁEvaluatorEngineǁ_evaluate_exact_match__mutmut_18, 
        'xǁEvaluatorEngineǁ_evaluate_exact_match__mutmut_19': xǁEvaluatorEngineǁ_evaluate_exact_match__mutmut_19
    }
    xǁEvaluatorEngineǁ_evaluate_exact_match__mutmut_orig.__name__ = 'xǁEvaluatorEngineǁ_evaluate_exact_match'
    
    async def _evaluate_llm_judge(
        self,
        output: str,
        evaluator: LLMJudgeEvaluator
    ) -> EvaluatorResult:
        args = [output, evaluator]# type: ignore
        kwargs = {}# type: ignore
        return await _mutmut_trampoline(object.__getattribute__(self, 'xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_orig'), object.__getattribute__(self, 'xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_mutants'), args, kwargs, self)
    
    async def xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_orig(
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
    
    async def xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_1(
        self,
        output: str,
        evaluator: LLMJudgeEvaluator
    ) -> EvaluatorResult:
        """Evaluate output with LLM judge."""
        # Build judge prompt
        judge_prompt = None
        
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
    
    async def xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_2(
        self,
        output: str,
        evaluator: LLMJudgeEvaluator
    ) -> EvaluatorResult:
        """Evaluate output with LLM judge."""
        # Build judge prompt
        judge_prompt = self._build_judge_prompt(
            None,
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
    
    async def xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_3(
        self,
        output: str,
        evaluator: LLMJudgeEvaluator
    ) -> EvaluatorResult:
        """Evaluate output with LLM judge."""
        # Build judge prompt
        judge_prompt = self._build_judge_prompt(
            output,
            None,
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
    
    async def xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_4(
        self,
        output: str,
        evaluator: LLMJudgeEvaluator
    ) -> EvaluatorResult:
        """Evaluate output with LLM judge."""
        # Build judge prompt
        judge_prompt = self._build_judge_prompt(
            output,
            evaluator.criteria,
            None
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
    
    async def xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_5(
        self,
        output: str,
        evaluator: LLMJudgeEvaluator
    ) -> EvaluatorResult:
        """Evaluate output with LLM judge."""
        # Build judge prompt
        judge_prompt = self._build_judge_prompt(
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
    
    async def xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_6(
        self,
        output: str,
        evaluator: LLMJudgeEvaluator
    ) -> EvaluatorResult:
        """Evaluate output with LLM judge."""
        # Build judge prompt
        judge_prompt = self._build_judge_prompt(
            output,
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
    
    async def xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_7(
        self,
        output: str,
        evaluator: LLMJudgeEvaluator
    ) -> EvaluatorResult:
        """Evaluate output with LLM judge."""
        # Build judge prompt
        judge_prompt = self._build_judge_prompt(
            output,
            evaluator.criteria,
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
    
    async def xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_8(
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
            response = None
            
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
    
    async def xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_9(
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
                prompt=None,
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
    
    async def xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_10(
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
                json_schema=None,
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
    
    async def xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_11(
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
                temperature=None,  # Deterministic
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
    
    async def xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_12(
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
                max_tokens=None,
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
    
    async def xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_13(
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
    
    async def xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_14(
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
    
    async def xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_15(
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
    
    async def xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_16(
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
    
    async def xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_17(
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
                temperature=1.0,  # Deterministic
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
    
    async def xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_18(
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
                max_tokens=1001,
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
    
    async def xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_19(
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
                result_data = None
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
    
    async def xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_20(
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
                result_data = json.loads(None)
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
    
    async def xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_21(
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
                    evaluator_name=None,
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
    
    async def xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_22(
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
                    passed=None,
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
    
    async def xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_23(
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
                    score=None,
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
    
    async def xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_24(
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
                    reason=None
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
    
    async def xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_25(
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
    
    async def xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_26(
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
    
    async def xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_27(
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
    
    async def xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_28(
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
    
    async def xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_29(
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
                    passed=True,
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
    
    async def xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_30(
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
                    score=1.0,
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
    
    async def xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_31(
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
                    reason="XXFailed to parse judge response as JSONXX"
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
    
    async def xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_32(
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
                    reason="failed to parse judge response as json"
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
    
    async def xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_33(
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
                    reason="FAILED TO PARSE JUDGE RESPONSE AS JSON"
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
    
    async def xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_34(
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
            score = None
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
    
    async def xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_35(
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
            score = result_data.get(None, 0)
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
    
    async def xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_36(
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
            score = result_data.get("score", None)
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
    
    async def xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_37(
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
            score = result_data.get(0)
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
    
    async def xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_38(
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
            score = result_data.get("score", )
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
    
    async def xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_39(
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
            score = result_data.get("XXscoreXX", 0)
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
    
    async def xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_40(
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
            score = result_data.get("SCORE", 0)
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
    
    async def xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_41(
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
            score = result_data.get("score", 1)
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
    
    async def xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_42(
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
                    score = None
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
    
    async def xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_43(
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
                    score = float(None)
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
    
    async def xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_44(
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
                    score = None
            
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
    
    async def xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_45(
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
                    score = 1
            
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
    
    async def xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_46(
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
            if 2 <= score <= 5:
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
    
    async def xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_47(
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
            if 1 < score <= 5:
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
    
    async def xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_48(
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
            if 1 <= score < 5:
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
    
    async def xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_49(
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
            if 1 <= score <= 6:
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
    
    async def xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_50(
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
                score = None
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
    
    async def xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_51(
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
                score = score * 5
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
    
    async def xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_52(
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
                score = score / 6
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
    
    async def xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_53(
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
            elif 2 <= score <= 10:
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
    
    async def xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_54(
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
            elif 1 < score <= 10:
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
    
    async def xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_55(
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
            elif 1 <= score < 10:
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
    
    async def xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_56(
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
            elif 1 <= score <= 11:
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
    
    async def xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_57(
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
                score = None
            
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
    
    async def xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_58(
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
                score = score * 10
            
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
    
    async def xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_59(
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
                score = score / 11
            
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
    
    async def xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_60(
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
            
            reasoning = None
            
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
    
    async def xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_61(
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
            
            reasoning = result_data.get(None, "")
            
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
    
    async def xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_62(
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
            
            reasoning = result_data.get("reasoning", None)
            
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
    
    async def xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_63(
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
            
            reasoning = result_data.get("")
            
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
    
    async def xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_64(
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
            
            reasoning = result_data.get("reasoning", )
            
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
    
    async def xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_65(
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
            
            reasoning = result_data.get("XXreasoningXX", "")
            
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
    
    async def xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_66(
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
            
            reasoning = result_data.get("REASONING", "")
            
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
    
    async def xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_67(
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
            
            reasoning = result_data.get("reasoning", "XXXX")
            
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
    
    async def xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_68(
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
            passed = None
            
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
    
    async def xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_69(
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
            passed = score > evaluator.pass_threshold
            
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
    
    async def xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_70(
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
                evaluator_name=None,
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
    
    async def xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_71(
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
                passed=None,
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
    
    async def xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_72(
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
                score=None,
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
    
    async def xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_73(
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
                reason=None,
                details=result_data
            )
            
        except Exception as e:
            return EvaluatorResult(
                evaluator_name=evaluator.name,
                passed=False,
                score=0.0,
                reason=f"LLM judge error: {e}"
            )
    
    async def xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_74(
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
                details=None
            )
            
        except Exception as e:
            return EvaluatorResult(
                evaluator_name=evaluator.name,
                passed=False,
                score=0.0,
                reason=f"LLM judge error: {e}"
            )
    
    async def xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_75(
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
    
    async def xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_76(
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
    
    async def xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_77(
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
    
    async def xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_78(
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
                details=result_data
            )
            
        except Exception as e:
            return EvaluatorResult(
                evaluator_name=evaluator.name,
                passed=False,
                score=0.0,
                reason=f"LLM judge error: {e}"
            )
    
    async def xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_79(
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
                )
            
        except Exception as e:
            return EvaluatorResult(
                evaluator_name=evaluator.name,
                passed=False,
                score=0.0,
                reason=f"LLM judge error: {e}"
            )
    
    async def xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_80(
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
                evaluator_name=None,
                passed=False,
                score=0.0,
                reason=f"LLM judge error: {e}"
            )
    
    async def xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_81(
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
                passed=None,
                score=0.0,
                reason=f"LLM judge error: {e}"
            )
    
    async def xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_82(
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
                score=None,
                reason=f"LLM judge error: {e}"
            )
    
    async def xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_83(
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
                reason=None
            )
    
    async def xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_84(
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
                passed=False,
                score=0.0,
                reason=f"LLM judge error: {e}"
            )
    
    async def xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_85(
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
                score=0.0,
                reason=f"LLM judge error: {e}"
            )
    
    async def xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_86(
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
                reason=f"LLM judge error: {e}"
            )
    
    async def xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_87(
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
                )
    
    async def xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_88(
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
                passed=True,
                score=0.0,
                reason=f"LLM judge error: {e}"
            )
    
    async def xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_89(
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
                score=1.0,
                reason=f"LLM judge error: {e}"
            )
    
    xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
    'xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_1': xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_1, 
        'xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_2': xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_2, 
        'xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_3': xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_3, 
        'xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_4': xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_4, 
        'xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_5': xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_5, 
        'xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_6': xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_6, 
        'xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_7': xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_7, 
        'xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_8': xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_8, 
        'xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_9': xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_9, 
        'xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_10': xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_10, 
        'xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_11': xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_11, 
        'xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_12': xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_12, 
        'xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_13': xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_13, 
        'xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_14': xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_14, 
        'xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_15': xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_15, 
        'xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_16': xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_16, 
        'xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_17': xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_17, 
        'xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_18': xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_18, 
        'xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_19': xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_19, 
        'xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_20': xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_20, 
        'xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_21': xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_21, 
        'xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_22': xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_22, 
        'xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_23': xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_23, 
        'xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_24': xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_24, 
        'xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_25': xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_25, 
        'xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_26': xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_26, 
        'xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_27': xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_27, 
        'xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_28': xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_28, 
        'xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_29': xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_29, 
        'xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_30': xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_30, 
        'xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_31': xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_31, 
        'xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_32': xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_32, 
        'xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_33': xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_33, 
        'xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_34': xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_34, 
        'xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_35': xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_35, 
        'xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_36': xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_36, 
        'xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_37': xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_37, 
        'xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_38': xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_38, 
        'xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_39': xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_39, 
        'xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_40': xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_40, 
        'xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_41': xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_41, 
        'xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_42': xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_42, 
        'xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_43': xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_43, 
        'xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_44': xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_44, 
        'xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_45': xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_45, 
        'xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_46': xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_46, 
        'xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_47': xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_47, 
        'xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_48': xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_48, 
        'xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_49': xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_49, 
        'xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_50': xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_50, 
        'xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_51': xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_51, 
        'xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_52': xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_52, 
        'xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_53': xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_53, 
        'xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_54': xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_54, 
        'xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_55': xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_55, 
        'xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_56': xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_56, 
        'xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_57': xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_57, 
        'xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_58': xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_58, 
        'xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_59': xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_59, 
        'xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_60': xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_60, 
        'xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_61': xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_61, 
        'xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_62': xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_62, 
        'xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_63': xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_63, 
        'xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_64': xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_64, 
        'xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_65': xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_65, 
        'xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_66': xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_66, 
        'xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_67': xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_67, 
        'xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_68': xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_68, 
        'xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_69': xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_69, 
        'xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_70': xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_70, 
        'xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_71': xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_71, 
        'xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_72': xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_72, 
        'xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_73': xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_73, 
        'xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_74': xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_74, 
        'xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_75': xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_75, 
        'xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_76': xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_76, 
        'xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_77': xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_77, 
        'xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_78': xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_78, 
        'xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_79': xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_79, 
        'xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_80': xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_80, 
        'xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_81': xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_81, 
        'xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_82': xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_82, 
        'xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_83': xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_83, 
        'xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_84': xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_84, 
        'xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_85': xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_85, 
        'xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_86': xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_86, 
        'xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_87': xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_87, 
        'xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_88': xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_88, 
        'xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_89': xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_89
    }
    xǁEvaluatorEngineǁ_evaluate_llm_judge__mutmut_orig.__name__ = 'xǁEvaluatorEngineǁ_evaluate_llm_judge'
    
    def _build_judge_prompt(
        self,
        output: str,
        criteria: str,
        output_schema: dict
    ) -> str:
        args = [output, criteria, output_schema]# type: ignore
        kwargs = {}# type: ignore
        return _mutmut_trampoline(object.__getattribute__(self, 'xǁEvaluatorEngineǁ_build_judge_prompt__mutmut_orig'), object.__getattribute__(self, 'xǁEvaluatorEngineǁ_build_judge_prompt__mutmut_mutants'), args, kwargs, self)
    
    def xǁEvaluatorEngineǁ_build_judge_prompt__mutmut_orig(
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
    
    def xǁEvaluatorEngineǁ_build_judge_prompt__mutmut_1(
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
{json.dumps(None, indent=2)}
```

## Output
"""
    
    def xǁEvaluatorEngineǁ_build_judge_prompt__mutmut_2(
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
{json.dumps(output_schema, indent=None)}
```

## Output
"""
    
    def xǁEvaluatorEngineǁ_build_judge_prompt__mutmut_3(
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
{json.dumps(indent=2)}
```

## Output
"""
    
    def xǁEvaluatorEngineǁ_build_judge_prompt__mutmut_4(
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
{json.dumps(output_schema, )}
```

## Output
"""
    
    def xǁEvaluatorEngineǁ_build_judge_prompt__mutmut_5(
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
{json.dumps(output_schema, indent=3)}
```

## Output
"""
    
    xǁEvaluatorEngineǁ_build_judge_prompt__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
    'xǁEvaluatorEngineǁ_build_judge_prompt__mutmut_1': xǁEvaluatorEngineǁ_build_judge_prompt__mutmut_1, 
        'xǁEvaluatorEngineǁ_build_judge_prompt__mutmut_2': xǁEvaluatorEngineǁ_build_judge_prompt__mutmut_2, 
        'xǁEvaluatorEngineǁ_build_judge_prompt__mutmut_3': xǁEvaluatorEngineǁ_build_judge_prompt__mutmut_3, 
        'xǁEvaluatorEngineǁ_build_judge_prompt__mutmut_4': xǁEvaluatorEngineǁ_build_judge_prompt__mutmut_4, 
        'xǁEvaluatorEngineǁ_build_judge_prompt__mutmut_5': xǁEvaluatorEngineǁ_build_judge_prompt__mutmut_5
    }
    xǁEvaluatorEngineǁ_build_judge_prompt__mutmut_orig.__name__ = 'xǁEvaluatorEngineǁ_build_judge_prompt'


# Factory function
def create_evaluator(evaluator_type: str, **kwargs) -> Evaluator:
    args = [evaluator_type]# type: ignore
    kwargs = {**kwargs}# type: ignore
    return _mutmut_trampoline(x_create_evaluator__mutmut_orig, x_create_evaluator__mutmut_mutants, args, kwargs, None)


# Factory function
def x_create_evaluator__mutmut_orig(evaluator_type: str, **kwargs) -> Evaluator:
    """Create evaluator from type."""
    if evaluator_type == "regex":
        return RegexEvaluator(**kwargs)
    elif evaluator_type == "exact-match":
        return ExactMatchEvaluator(**kwargs)
    elif evaluator_type == "llm-judge":
        return LLMJudgeEvaluator(**kwargs)
    else:
        raise ValueError(f"Unknown evaluator type: {evaluator_type}")


# Factory function
def x_create_evaluator__mutmut_1(evaluator_type: str, **kwargs) -> Evaluator:
    """Create evaluator from type."""
    if evaluator_type != "regex":
        return RegexEvaluator(**kwargs)
    elif evaluator_type == "exact-match":
        return ExactMatchEvaluator(**kwargs)
    elif evaluator_type == "llm-judge":
        return LLMJudgeEvaluator(**kwargs)
    else:
        raise ValueError(f"Unknown evaluator type: {evaluator_type}")


# Factory function
def x_create_evaluator__mutmut_2(evaluator_type: str, **kwargs) -> Evaluator:
    """Create evaluator from type."""
    if evaluator_type == "XXregexXX":
        return RegexEvaluator(**kwargs)
    elif evaluator_type == "exact-match":
        return ExactMatchEvaluator(**kwargs)
    elif evaluator_type == "llm-judge":
        return LLMJudgeEvaluator(**kwargs)
    else:
        raise ValueError(f"Unknown evaluator type: {evaluator_type}")


# Factory function
def x_create_evaluator__mutmut_3(evaluator_type: str, **kwargs) -> Evaluator:
    """Create evaluator from type."""
    if evaluator_type == "REGEX":
        return RegexEvaluator(**kwargs)
    elif evaluator_type == "exact-match":
        return ExactMatchEvaluator(**kwargs)
    elif evaluator_type == "llm-judge":
        return LLMJudgeEvaluator(**kwargs)
    else:
        raise ValueError(f"Unknown evaluator type: {evaluator_type}")


# Factory function
def x_create_evaluator__mutmut_4(evaluator_type: str, **kwargs) -> Evaluator:
    """Create evaluator from type."""
    if evaluator_type == "regex":
        return RegexEvaluator(**kwargs)
    elif evaluator_type != "exact-match":
        return ExactMatchEvaluator(**kwargs)
    elif evaluator_type == "llm-judge":
        return LLMJudgeEvaluator(**kwargs)
    else:
        raise ValueError(f"Unknown evaluator type: {evaluator_type}")


# Factory function
def x_create_evaluator__mutmut_5(evaluator_type: str, **kwargs) -> Evaluator:
    """Create evaluator from type."""
    if evaluator_type == "regex":
        return RegexEvaluator(**kwargs)
    elif evaluator_type == "XXexact-matchXX":
        return ExactMatchEvaluator(**kwargs)
    elif evaluator_type == "llm-judge":
        return LLMJudgeEvaluator(**kwargs)
    else:
        raise ValueError(f"Unknown evaluator type: {evaluator_type}")


# Factory function
def x_create_evaluator__mutmut_6(evaluator_type: str, **kwargs) -> Evaluator:
    """Create evaluator from type."""
    if evaluator_type == "regex":
        return RegexEvaluator(**kwargs)
    elif evaluator_type == "EXACT-MATCH":
        return ExactMatchEvaluator(**kwargs)
    elif evaluator_type == "llm-judge":
        return LLMJudgeEvaluator(**kwargs)
    else:
        raise ValueError(f"Unknown evaluator type: {evaluator_type}")


# Factory function
def x_create_evaluator__mutmut_7(evaluator_type: str, **kwargs) -> Evaluator:
    """Create evaluator from type."""
    if evaluator_type == "regex":
        return RegexEvaluator(**kwargs)
    elif evaluator_type == "exact-match":
        return ExactMatchEvaluator(**kwargs)
    elif evaluator_type != "llm-judge":
        return LLMJudgeEvaluator(**kwargs)
    else:
        raise ValueError(f"Unknown evaluator type: {evaluator_type}")


# Factory function
def x_create_evaluator__mutmut_8(evaluator_type: str, **kwargs) -> Evaluator:
    """Create evaluator from type."""
    if evaluator_type == "regex":
        return RegexEvaluator(**kwargs)
    elif evaluator_type == "exact-match":
        return ExactMatchEvaluator(**kwargs)
    elif evaluator_type == "XXllm-judgeXX":
        return LLMJudgeEvaluator(**kwargs)
    else:
        raise ValueError(f"Unknown evaluator type: {evaluator_type}")


# Factory function
def x_create_evaluator__mutmut_9(evaluator_type: str, **kwargs) -> Evaluator:
    """Create evaluator from type."""
    if evaluator_type == "regex":
        return RegexEvaluator(**kwargs)
    elif evaluator_type == "exact-match":
        return ExactMatchEvaluator(**kwargs)
    elif evaluator_type == "LLM-JUDGE":
        return LLMJudgeEvaluator(**kwargs)
    else:
        raise ValueError(f"Unknown evaluator type: {evaluator_type}")


# Factory function
def x_create_evaluator__mutmut_10(evaluator_type: str, **kwargs) -> Evaluator:
    """Create evaluator from type."""
    if evaluator_type == "regex":
        return RegexEvaluator(**kwargs)
    elif evaluator_type == "exact-match":
        return ExactMatchEvaluator(**kwargs)
    elif evaluator_type == "llm-judge":
        return LLMJudgeEvaluator(**kwargs)
    else:
        raise ValueError(None)

x_create_evaluator__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
'x_create_evaluator__mutmut_1': x_create_evaluator__mutmut_1, 
    'x_create_evaluator__mutmut_2': x_create_evaluator__mutmut_2, 
    'x_create_evaluator__mutmut_3': x_create_evaluator__mutmut_3, 
    'x_create_evaluator__mutmut_4': x_create_evaluator__mutmut_4, 
    'x_create_evaluator__mutmut_5': x_create_evaluator__mutmut_5, 
    'x_create_evaluator__mutmut_6': x_create_evaluator__mutmut_6, 
    'x_create_evaluator__mutmut_7': x_create_evaluator__mutmut_7, 
    'x_create_evaluator__mutmut_8': x_create_evaluator__mutmut_8, 
    'x_create_evaluator__mutmut_9': x_create_evaluator__mutmut_9, 
    'x_create_evaluator__mutmut_10': x_create_evaluator__mutmut_10
}
x_create_evaluator__mutmut_orig.__name__ = 'x_create_evaluator'
