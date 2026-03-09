"""Execution engine for running evaluations."""

import asyncio
from datetime import datetime
from typing import TYPE_CHECKING

from md_evals.models import (
    EvalConfig, ExecutionResult, Defaults,
    Task, Treatment, LLMResponse
)
from md_evals.llm import LLMAdapter, inject_skill, LLMError

if TYPE_CHECKING:
    from md_evals.evaluator import EvaluatorEngine as EvaluatorEngineType
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


class ExecutionEngine:
    """Orchestrates evaluation runs."""
    
    def __init__(
        self,
        config: EvalConfig,
        llm_adapter: LLMAdapter,
        evaluator_engine: "EvaluatorEngineType | None" = None
    ):
        args = [config, llm_adapter, evaluator_engine]# type: ignore
        kwargs = {}# type: ignore
        return _mutmut_trampoline(object.__getattribute__(self, 'xǁExecutionEngineǁ__init____mutmut_orig'), object.__getattribute__(self, 'xǁExecutionEngineǁ__init____mutmut_mutants'), args, kwargs, self)
    
    def xǁExecutionEngineǁ__init____mutmut_orig(
        self,
        config: EvalConfig,
        llm_adapter: LLMAdapter,
        evaluator_engine: "EvaluatorEngineType | None" = None
    ):
        self.config = config
        self.llm_adapter = llm_adapter
        self.evaluator_engine = evaluator_engine
        self._semaphore: asyncio.Semaphore | None = None
    
    def xǁExecutionEngineǁ__init____mutmut_1(
        self,
        config: EvalConfig,
        llm_adapter: LLMAdapter,
        evaluator_engine: "EvaluatorEngineType | None" = None
    ):
        self.config = None
        self.llm_adapter = llm_adapter
        self.evaluator_engine = evaluator_engine
        self._semaphore: asyncio.Semaphore | None = None
    
    def xǁExecutionEngineǁ__init____mutmut_2(
        self,
        config: EvalConfig,
        llm_adapter: LLMAdapter,
        evaluator_engine: "EvaluatorEngineType | None" = None
    ):
        self.config = config
        self.llm_adapter = None
        self.evaluator_engine = evaluator_engine
        self._semaphore: asyncio.Semaphore | None = None
    
    def xǁExecutionEngineǁ__init____mutmut_3(
        self,
        config: EvalConfig,
        llm_adapter: LLMAdapter,
        evaluator_engine: "EvaluatorEngineType | None" = None
    ):
        self.config = config
        self.llm_adapter = llm_adapter
        self.evaluator_engine = None
        self._semaphore: asyncio.Semaphore | None = None
    
    def xǁExecutionEngineǁ__init____mutmut_4(
        self,
        config: EvalConfig,
        llm_adapter: LLMAdapter,
        evaluator_engine: "EvaluatorEngineType | None" = None
    ):
        self.config = config
        self.llm_adapter = llm_adapter
        self.evaluator_engine = evaluator_engine
        self._semaphore: asyncio.Semaphore | None = ""
    
    xǁExecutionEngineǁ__init____mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
    'xǁExecutionEngineǁ__init____mutmut_1': xǁExecutionEngineǁ__init____mutmut_1, 
        'xǁExecutionEngineǁ__init____mutmut_2': xǁExecutionEngineǁ__init____mutmut_2, 
        'xǁExecutionEngineǁ__init____mutmut_3': xǁExecutionEngineǁ__init____mutmut_3, 
        'xǁExecutionEngineǁ__init____mutmut_4': xǁExecutionEngineǁ__init____mutmut_4
    }
    xǁExecutionEngineǁ__init____mutmut_orig.__name__ = 'xǁExecutionEngineǁ__init__'
    
    def _get_semaphore(self) -> asyncio.Semaphore:
        args = []# type: ignore
        kwargs = {}# type: ignore
        return _mutmut_trampoline(object.__getattribute__(self, 'xǁExecutionEngineǁ_get_semaphore__mutmut_orig'), object.__getattribute__(self, 'xǁExecutionEngineǁ_get_semaphore__mutmut_mutants'), args, kwargs, self)
    
    def xǁExecutionEngineǁ_get_semaphore__mutmut_orig(self) -> asyncio.Semaphore:
        """Get or create semaphore for concurrency control."""
        if self._semaphore is None:
            self._semaphore = asyncio.Semaphore(self.config.execution.parallel_workers)
        return self._semaphore
    
    def xǁExecutionEngineǁ_get_semaphore__mutmut_1(self) -> asyncio.Semaphore:
        """Get or create semaphore for concurrency control."""
        if self._semaphore is not None:
            self._semaphore = asyncio.Semaphore(self.config.execution.parallel_workers)
        return self._semaphore
    
    def xǁExecutionEngineǁ_get_semaphore__mutmut_2(self) -> asyncio.Semaphore:
        """Get or create semaphore for concurrency control."""
        if self._semaphore is None:
            self._semaphore = None
        return self._semaphore
    
    def xǁExecutionEngineǁ_get_semaphore__mutmut_3(self) -> asyncio.Semaphore:
        """Get or create semaphore for concurrency control."""
        if self._semaphore is None:
            self._semaphore = asyncio.Semaphore(None)
        return self._semaphore
    
    xǁExecutionEngineǁ_get_semaphore__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
    'xǁExecutionEngineǁ_get_semaphore__mutmut_1': xǁExecutionEngineǁ_get_semaphore__mutmut_1, 
        'xǁExecutionEngineǁ_get_semaphore__mutmut_2': xǁExecutionEngineǁ_get_semaphore__mutmut_2, 
        'xǁExecutionEngineǁ_get_semaphore__mutmut_3': xǁExecutionEngineǁ_get_semaphore__mutmut_3
    }
    xǁExecutionEngineǁ_get_semaphore__mutmut_orig.__name__ = 'xǁExecutionEngineǁ_get_semaphore'
    
    async def run_single(
        self,
        treatment: Treatment,
        task: Task,
        treatment_name: str,
    ) -> ExecutionResult:
        args = [treatment, task, treatment_name]# type: ignore
        kwargs = {}# type: ignore
        return await _mutmut_trampoline(object.__getattribute__(self, 'xǁExecutionEngineǁrun_single__mutmut_orig'), object.__getattribute__(self, 'xǁExecutionEngineǁrun_single__mutmut_mutants'), args, kwargs, self)
    
    async def xǁExecutionEngineǁrun_single__mutmut_orig(
        self,
        treatment: Treatment,
        task: Task,
        treatment_name: str,
    ) -> ExecutionResult:
        """Run a single evaluation.
        
        Args:
            treatment: Treatment configuration
            task: Task configuration
            treatment_name: Name of treatment
            
        Returns:
            ExecutionResult
        """
        async with self._get_semaphore():
            # Inject skill if present
            final_prompt, system_prompt = inject_skill(
                task.prompt,
                treatment.skill_path
            )
            
            # Replace variables in prompt
            for key, value in task.variables.items():
                placeholder = f"{{{key}}}"
                final_prompt = final_prompt.replace(placeholder, value)
            
            # Call LLM
            try:
                response = await self.llm_adapter.complete(
                    prompt=final_prompt,
                    system_prompt=system_prompt,
                )
            except LLMError as e:
                # Return error result
                return ExecutionResult(
                    treatment=treatment_name,
                    test=task.name,
                    prompt=final_prompt,
                    response=None,
                    passed=False,
                    evaluator_results=[],
                    timestamp=datetime.utcnow().isoformat()
                )
            
            # Evaluate if evaluator engine is available
            evaluator_results = []
            if self.evaluator_engine and task.evaluators:
                evaluator_results = await self.evaluator_engine.evaluate(
                    response.content,
                    task.evaluators
                )
            
            # Determine if passed
            passed = all(r.passed for r in evaluator_results) if evaluator_results else True
            
            return ExecutionResult(
                treatment=treatment_name,
                test=task.name,
                prompt=final_prompt,
                response=response,
                passed=passed,
                evaluator_results=evaluator_results,
                timestamp=datetime.utcnow().isoformat()
            )
    
    async def xǁExecutionEngineǁrun_single__mutmut_1(
        self,
        treatment: Treatment,
        task: Task,
        treatment_name: str,
    ) -> ExecutionResult:
        """Run a single evaluation.
        
        Args:
            treatment: Treatment configuration
            task: Task configuration
            treatment_name: Name of treatment
            
        Returns:
            ExecutionResult
        """
        async with self._get_semaphore():
            # Inject skill if present
            final_prompt, system_prompt = None
            
            # Replace variables in prompt
            for key, value in task.variables.items():
                placeholder = f"{{{key}}}"
                final_prompt = final_prompt.replace(placeholder, value)
            
            # Call LLM
            try:
                response = await self.llm_adapter.complete(
                    prompt=final_prompt,
                    system_prompt=system_prompt,
                )
            except LLMError as e:
                # Return error result
                return ExecutionResult(
                    treatment=treatment_name,
                    test=task.name,
                    prompt=final_prompt,
                    response=None,
                    passed=False,
                    evaluator_results=[],
                    timestamp=datetime.utcnow().isoformat()
                )
            
            # Evaluate if evaluator engine is available
            evaluator_results = []
            if self.evaluator_engine and task.evaluators:
                evaluator_results = await self.evaluator_engine.evaluate(
                    response.content,
                    task.evaluators
                )
            
            # Determine if passed
            passed = all(r.passed for r in evaluator_results) if evaluator_results else True
            
            return ExecutionResult(
                treatment=treatment_name,
                test=task.name,
                prompt=final_prompt,
                response=response,
                passed=passed,
                evaluator_results=evaluator_results,
                timestamp=datetime.utcnow().isoformat()
            )
    
    async def xǁExecutionEngineǁrun_single__mutmut_2(
        self,
        treatment: Treatment,
        task: Task,
        treatment_name: str,
    ) -> ExecutionResult:
        """Run a single evaluation.
        
        Args:
            treatment: Treatment configuration
            task: Task configuration
            treatment_name: Name of treatment
            
        Returns:
            ExecutionResult
        """
        async with self._get_semaphore():
            # Inject skill if present
            final_prompt, system_prompt = inject_skill(
                None,
                treatment.skill_path
            )
            
            # Replace variables in prompt
            for key, value in task.variables.items():
                placeholder = f"{{{key}}}"
                final_prompt = final_prompt.replace(placeholder, value)
            
            # Call LLM
            try:
                response = await self.llm_adapter.complete(
                    prompt=final_prompt,
                    system_prompt=system_prompt,
                )
            except LLMError as e:
                # Return error result
                return ExecutionResult(
                    treatment=treatment_name,
                    test=task.name,
                    prompt=final_prompt,
                    response=None,
                    passed=False,
                    evaluator_results=[],
                    timestamp=datetime.utcnow().isoformat()
                )
            
            # Evaluate if evaluator engine is available
            evaluator_results = []
            if self.evaluator_engine and task.evaluators:
                evaluator_results = await self.evaluator_engine.evaluate(
                    response.content,
                    task.evaluators
                )
            
            # Determine if passed
            passed = all(r.passed for r in evaluator_results) if evaluator_results else True
            
            return ExecutionResult(
                treatment=treatment_name,
                test=task.name,
                prompt=final_prompt,
                response=response,
                passed=passed,
                evaluator_results=evaluator_results,
                timestamp=datetime.utcnow().isoformat()
            )
    
    async def xǁExecutionEngineǁrun_single__mutmut_3(
        self,
        treatment: Treatment,
        task: Task,
        treatment_name: str,
    ) -> ExecutionResult:
        """Run a single evaluation.
        
        Args:
            treatment: Treatment configuration
            task: Task configuration
            treatment_name: Name of treatment
            
        Returns:
            ExecutionResult
        """
        async with self._get_semaphore():
            # Inject skill if present
            final_prompt, system_prompt = inject_skill(
                task.prompt,
                None
            )
            
            # Replace variables in prompt
            for key, value in task.variables.items():
                placeholder = f"{{{key}}}"
                final_prompt = final_prompt.replace(placeholder, value)
            
            # Call LLM
            try:
                response = await self.llm_adapter.complete(
                    prompt=final_prompt,
                    system_prompt=system_prompt,
                )
            except LLMError as e:
                # Return error result
                return ExecutionResult(
                    treatment=treatment_name,
                    test=task.name,
                    prompt=final_prompt,
                    response=None,
                    passed=False,
                    evaluator_results=[],
                    timestamp=datetime.utcnow().isoformat()
                )
            
            # Evaluate if evaluator engine is available
            evaluator_results = []
            if self.evaluator_engine and task.evaluators:
                evaluator_results = await self.evaluator_engine.evaluate(
                    response.content,
                    task.evaluators
                )
            
            # Determine if passed
            passed = all(r.passed for r in evaluator_results) if evaluator_results else True
            
            return ExecutionResult(
                treatment=treatment_name,
                test=task.name,
                prompt=final_prompt,
                response=response,
                passed=passed,
                evaluator_results=evaluator_results,
                timestamp=datetime.utcnow().isoformat()
            )
    
    async def xǁExecutionEngineǁrun_single__mutmut_4(
        self,
        treatment: Treatment,
        task: Task,
        treatment_name: str,
    ) -> ExecutionResult:
        """Run a single evaluation.
        
        Args:
            treatment: Treatment configuration
            task: Task configuration
            treatment_name: Name of treatment
            
        Returns:
            ExecutionResult
        """
        async with self._get_semaphore():
            # Inject skill if present
            final_prompt, system_prompt = inject_skill(
                treatment.skill_path
            )
            
            # Replace variables in prompt
            for key, value in task.variables.items():
                placeholder = f"{{{key}}}"
                final_prompt = final_prompt.replace(placeholder, value)
            
            # Call LLM
            try:
                response = await self.llm_adapter.complete(
                    prompt=final_prompt,
                    system_prompt=system_prompt,
                )
            except LLMError as e:
                # Return error result
                return ExecutionResult(
                    treatment=treatment_name,
                    test=task.name,
                    prompt=final_prompt,
                    response=None,
                    passed=False,
                    evaluator_results=[],
                    timestamp=datetime.utcnow().isoformat()
                )
            
            # Evaluate if evaluator engine is available
            evaluator_results = []
            if self.evaluator_engine and task.evaluators:
                evaluator_results = await self.evaluator_engine.evaluate(
                    response.content,
                    task.evaluators
                )
            
            # Determine if passed
            passed = all(r.passed for r in evaluator_results) if evaluator_results else True
            
            return ExecutionResult(
                treatment=treatment_name,
                test=task.name,
                prompt=final_prompt,
                response=response,
                passed=passed,
                evaluator_results=evaluator_results,
                timestamp=datetime.utcnow().isoformat()
            )
    
    async def xǁExecutionEngineǁrun_single__mutmut_5(
        self,
        treatment: Treatment,
        task: Task,
        treatment_name: str,
    ) -> ExecutionResult:
        """Run a single evaluation.
        
        Args:
            treatment: Treatment configuration
            task: Task configuration
            treatment_name: Name of treatment
            
        Returns:
            ExecutionResult
        """
        async with self._get_semaphore():
            # Inject skill if present
            final_prompt, system_prompt = inject_skill(
                task.prompt,
                )
            
            # Replace variables in prompt
            for key, value in task.variables.items():
                placeholder = f"{{{key}}}"
                final_prompt = final_prompt.replace(placeholder, value)
            
            # Call LLM
            try:
                response = await self.llm_adapter.complete(
                    prompt=final_prompt,
                    system_prompt=system_prompt,
                )
            except LLMError as e:
                # Return error result
                return ExecutionResult(
                    treatment=treatment_name,
                    test=task.name,
                    prompt=final_prompt,
                    response=None,
                    passed=False,
                    evaluator_results=[],
                    timestamp=datetime.utcnow().isoformat()
                )
            
            # Evaluate if evaluator engine is available
            evaluator_results = []
            if self.evaluator_engine and task.evaluators:
                evaluator_results = await self.evaluator_engine.evaluate(
                    response.content,
                    task.evaluators
                )
            
            # Determine if passed
            passed = all(r.passed for r in evaluator_results) if evaluator_results else True
            
            return ExecutionResult(
                treatment=treatment_name,
                test=task.name,
                prompt=final_prompt,
                response=response,
                passed=passed,
                evaluator_results=evaluator_results,
                timestamp=datetime.utcnow().isoformat()
            )
    
    async def xǁExecutionEngineǁrun_single__mutmut_6(
        self,
        treatment: Treatment,
        task: Task,
        treatment_name: str,
    ) -> ExecutionResult:
        """Run a single evaluation.
        
        Args:
            treatment: Treatment configuration
            task: Task configuration
            treatment_name: Name of treatment
            
        Returns:
            ExecutionResult
        """
        async with self._get_semaphore():
            # Inject skill if present
            final_prompt, system_prompt = inject_skill(
                task.prompt,
                treatment.skill_path
            )
            
            # Replace variables in prompt
            for key, value in task.variables.items():
                placeholder = None
                final_prompt = final_prompt.replace(placeholder, value)
            
            # Call LLM
            try:
                response = await self.llm_adapter.complete(
                    prompt=final_prompt,
                    system_prompt=system_prompt,
                )
            except LLMError as e:
                # Return error result
                return ExecutionResult(
                    treatment=treatment_name,
                    test=task.name,
                    prompt=final_prompt,
                    response=None,
                    passed=False,
                    evaluator_results=[],
                    timestamp=datetime.utcnow().isoformat()
                )
            
            # Evaluate if evaluator engine is available
            evaluator_results = []
            if self.evaluator_engine and task.evaluators:
                evaluator_results = await self.evaluator_engine.evaluate(
                    response.content,
                    task.evaluators
                )
            
            # Determine if passed
            passed = all(r.passed for r in evaluator_results) if evaluator_results else True
            
            return ExecutionResult(
                treatment=treatment_name,
                test=task.name,
                prompt=final_prompt,
                response=response,
                passed=passed,
                evaluator_results=evaluator_results,
                timestamp=datetime.utcnow().isoformat()
            )
    
    async def xǁExecutionEngineǁrun_single__mutmut_7(
        self,
        treatment: Treatment,
        task: Task,
        treatment_name: str,
    ) -> ExecutionResult:
        """Run a single evaluation.
        
        Args:
            treatment: Treatment configuration
            task: Task configuration
            treatment_name: Name of treatment
            
        Returns:
            ExecutionResult
        """
        async with self._get_semaphore():
            # Inject skill if present
            final_prompt, system_prompt = inject_skill(
                task.prompt,
                treatment.skill_path
            )
            
            # Replace variables in prompt
            for key, value in task.variables.items():
                placeholder = f"{{{key}}}"
                final_prompt = None
            
            # Call LLM
            try:
                response = await self.llm_adapter.complete(
                    prompt=final_prompt,
                    system_prompt=system_prompt,
                )
            except LLMError as e:
                # Return error result
                return ExecutionResult(
                    treatment=treatment_name,
                    test=task.name,
                    prompt=final_prompt,
                    response=None,
                    passed=False,
                    evaluator_results=[],
                    timestamp=datetime.utcnow().isoformat()
                )
            
            # Evaluate if evaluator engine is available
            evaluator_results = []
            if self.evaluator_engine and task.evaluators:
                evaluator_results = await self.evaluator_engine.evaluate(
                    response.content,
                    task.evaluators
                )
            
            # Determine if passed
            passed = all(r.passed for r in evaluator_results) if evaluator_results else True
            
            return ExecutionResult(
                treatment=treatment_name,
                test=task.name,
                prompt=final_prompt,
                response=response,
                passed=passed,
                evaluator_results=evaluator_results,
                timestamp=datetime.utcnow().isoformat()
            )
    
    async def xǁExecutionEngineǁrun_single__mutmut_8(
        self,
        treatment: Treatment,
        task: Task,
        treatment_name: str,
    ) -> ExecutionResult:
        """Run a single evaluation.
        
        Args:
            treatment: Treatment configuration
            task: Task configuration
            treatment_name: Name of treatment
            
        Returns:
            ExecutionResult
        """
        async with self._get_semaphore():
            # Inject skill if present
            final_prompt, system_prompt = inject_skill(
                task.prompt,
                treatment.skill_path
            )
            
            # Replace variables in prompt
            for key, value in task.variables.items():
                placeholder = f"{{{key}}}"
                final_prompt = final_prompt.replace(None, value)
            
            # Call LLM
            try:
                response = await self.llm_adapter.complete(
                    prompt=final_prompt,
                    system_prompt=system_prompt,
                )
            except LLMError as e:
                # Return error result
                return ExecutionResult(
                    treatment=treatment_name,
                    test=task.name,
                    prompt=final_prompt,
                    response=None,
                    passed=False,
                    evaluator_results=[],
                    timestamp=datetime.utcnow().isoformat()
                )
            
            # Evaluate if evaluator engine is available
            evaluator_results = []
            if self.evaluator_engine and task.evaluators:
                evaluator_results = await self.evaluator_engine.evaluate(
                    response.content,
                    task.evaluators
                )
            
            # Determine if passed
            passed = all(r.passed for r in evaluator_results) if evaluator_results else True
            
            return ExecutionResult(
                treatment=treatment_name,
                test=task.name,
                prompt=final_prompt,
                response=response,
                passed=passed,
                evaluator_results=evaluator_results,
                timestamp=datetime.utcnow().isoformat()
            )
    
    async def xǁExecutionEngineǁrun_single__mutmut_9(
        self,
        treatment: Treatment,
        task: Task,
        treatment_name: str,
    ) -> ExecutionResult:
        """Run a single evaluation.
        
        Args:
            treatment: Treatment configuration
            task: Task configuration
            treatment_name: Name of treatment
            
        Returns:
            ExecutionResult
        """
        async with self._get_semaphore():
            # Inject skill if present
            final_prompt, system_prompt = inject_skill(
                task.prompt,
                treatment.skill_path
            )
            
            # Replace variables in prompt
            for key, value in task.variables.items():
                placeholder = f"{{{key}}}"
                final_prompt = final_prompt.replace(placeholder, None)
            
            # Call LLM
            try:
                response = await self.llm_adapter.complete(
                    prompt=final_prompt,
                    system_prompt=system_prompt,
                )
            except LLMError as e:
                # Return error result
                return ExecutionResult(
                    treatment=treatment_name,
                    test=task.name,
                    prompt=final_prompt,
                    response=None,
                    passed=False,
                    evaluator_results=[],
                    timestamp=datetime.utcnow().isoformat()
                )
            
            # Evaluate if evaluator engine is available
            evaluator_results = []
            if self.evaluator_engine and task.evaluators:
                evaluator_results = await self.evaluator_engine.evaluate(
                    response.content,
                    task.evaluators
                )
            
            # Determine if passed
            passed = all(r.passed for r in evaluator_results) if evaluator_results else True
            
            return ExecutionResult(
                treatment=treatment_name,
                test=task.name,
                prompt=final_prompt,
                response=response,
                passed=passed,
                evaluator_results=evaluator_results,
                timestamp=datetime.utcnow().isoformat()
            )
    
    async def xǁExecutionEngineǁrun_single__mutmut_10(
        self,
        treatment: Treatment,
        task: Task,
        treatment_name: str,
    ) -> ExecutionResult:
        """Run a single evaluation.
        
        Args:
            treatment: Treatment configuration
            task: Task configuration
            treatment_name: Name of treatment
            
        Returns:
            ExecutionResult
        """
        async with self._get_semaphore():
            # Inject skill if present
            final_prompt, system_prompt = inject_skill(
                task.prompt,
                treatment.skill_path
            )
            
            # Replace variables in prompt
            for key, value in task.variables.items():
                placeholder = f"{{{key}}}"
                final_prompt = final_prompt.replace(value)
            
            # Call LLM
            try:
                response = await self.llm_adapter.complete(
                    prompt=final_prompt,
                    system_prompt=system_prompt,
                )
            except LLMError as e:
                # Return error result
                return ExecutionResult(
                    treatment=treatment_name,
                    test=task.name,
                    prompt=final_prompt,
                    response=None,
                    passed=False,
                    evaluator_results=[],
                    timestamp=datetime.utcnow().isoformat()
                )
            
            # Evaluate if evaluator engine is available
            evaluator_results = []
            if self.evaluator_engine and task.evaluators:
                evaluator_results = await self.evaluator_engine.evaluate(
                    response.content,
                    task.evaluators
                )
            
            # Determine if passed
            passed = all(r.passed for r in evaluator_results) if evaluator_results else True
            
            return ExecutionResult(
                treatment=treatment_name,
                test=task.name,
                prompt=final_prompt,
                response=response,
                passed=passed,
                evaluator_results=evaluator_results,
                timestamp=datetime.utcnow().isoformat()
            )
    
    async def xǁExecutionEngineǁrun_single__mutmut_11(
        self,
        treatment: Treatment,
        task: Task,
        treatment_name: str,
    ) -> ExecutionResult:
        """Run a single evaluation.
        
        Args:
            treatment: Treatment configuration
            task: Task configuration
            treatment_name: Name of treatment
            
        Returns:
            ExecutionResult
        """
        async with self._get_semaphore():
            # Inject skill if present
            final_prompt, system_prompt = inject_skill(
                task.prompt,
                treatment.skill_path
            )
            
            # Replace variables in prompt
            for key, value in task.variables.items():
                placeholder = f"{{{key}}}"
                final_prompt = final_prompt.replace(placeholder, )
            
            # Call LLM
            try:
                response = await self.llm_adapter.complete(
                    prompt=final_prompt,
                    system_prompt=system_prompt,
                )
            except LLMError as e:
                # Return error result
                return ExecutionResult(
                    treatment=treatment_name,
                    test=task.name,
                    prompt=final_prompt,
                    response=None,
                    passed=False,
                    evaluator_results=[],
                    timestamp=datetime.utcnow().isoformat()
                )
            
            # Evaluate if evaluator engine is available
            evaluator_results = []
            if self.evaluator_engine and task.evaluators:
                evaluator_results = await self.evaluator_engine.evaluate(
                    response.content,
                    task.evaluators
                )
            
            # Determine if passed
            passed = all(r.passed for r in evaluator_results) if evaluator_results else True
            
            return ExecutionResult(
                treatment=treatment_name,
                test=task.name,
                prompt=final_prompt,
                response=response,
                passed=passed,
                evaluator_results=evaluator_results,
                timestamp=datetime.utcnow().isoformat()
            )
    
    async def xǁExecutionEngineǁrun_single__mutmut_12(
        self,
        treatment: Treatment,
        task: Task,
        treatment_name: str,
    ) -> ExecutionResult:
        """Run a single evaluation.
        
        Args:
            treatment: Treatment configuration
            task: Task configuration
            treatment_name: Name of treatment
            
        Returns:
            ExecutionResult
        """
        async with self._get_semaphore():
            # Inject skill if present
            final_prompt, system_prompt = inject_skill(
                task.prompt,
                treatment.skill_path
            )
            
            # Replace variables in prompt
            for key, value in task.variables.items():
                placeholder = f"{{{key}}}"
                final_prompt = final_prompt.replace(placeholder, value)
            
            # Call LLM
            try:
                response = None
            except LLMError as e:
                # Return error result
                return ExecutionResult(
                    treatment=treatment_name,
                    test=task.name,
                    prompt=final_prompt,
                    response=None,
                    passed=False,
                    evaluator_results=[],
                    timestamp=datetime.utcnow().isoformat()
                )
            
            # Evaluate if evaluator engine is available
            evaluator_results = []
            if self.evaluator_engine and task.evaluators:
                evaluator_results = await self.evaluator_engine.evaluate(
                    response.content,
                    task.evaluators
                )
            
            # Determine if passed
            passed = all(r.passed for r in evaluator_results) if evaluator_results else True
            
            return ExecutionResult(
                treatment=treatment_name,
                test=task.name,
                prompt=final_prompt,
                response=response,
                passed=passed,
                evaluator_results=evaluator_results,
                timestamp=datetime.utcnow().isoformat()
            )
    
    async def xǁExecutionEngineǁrun_single__mutmut_13(
        self,
        treatment: Treatment,
        task: Task,
        treatment_name: str,
    ) -> ExecutionResult:
        """Run a single evaluation.
        
        Args:
            treatment: Treatment configuration
            task: Task configuration
            treatment_name: Name of treatment
            
        Returns:
            ExecutionResult
        """
        async with self._get_semaphore():
            # Inject skill if present
            final_prompt, system_prompt = inject_skill(
                task.prompt,
                treatment.skill_path
            )
            
            # Replace variables in prompt
            for key, value in task.variables.items():
                placeholder = f"{{{key}}}"
                final_prompt = final_prompt.replace(placeholder, value)
            
            # Call LLM
            try:
                response = await self.llm_adapter.complete(
                    prompt=None,
                    system_prompt=system_prompt,
                )
            except LLMError as e:
                # Return error result
                return ExecutionResult(
                    treatment=treatment_name,
                    test=task.name,
                    prompt=final_prompt,
                    response=None,
                    passed=False,
                    evaluator_results=[],
                    timestamp=datetime.utcnow().isoformat()
                )
            
            # Evaluate if evaluator engine is available
            evaluator_results = []
            if self.evaluator_engine and task.evaluators:
                evaluator_results = await self.evaluator_engine.evaluate(
                    response.content,
                    task.evaluators
                )
            
            # Determine if passed
            passed = all(r.passed for r in evaluator_results) if evaluator_results else True
            
            return ExecutionResult(
                treatment=treatment_name,
                test=task.name,
                prompt=final_prompt,
                response=response,
                passed=passed,
                evaluator_results=evaluator_results,
                timestamp=datetime.utcnow().isoformat()
            )
    
    async def xǁExecutionEngineǁrun_single__mutmut_14(
        self,
        treatment: Treatment,
        task: Task,
        treatment_name: str,
    ) -> ExecutionResult:
        """Run a single evaluation.
        
        Args:
            treatment: Treatment configuration
            task: Task configuration
            treatment_name: Name of treatment
            
        Returns:
            ExecutionResult
        """
        async with self._get_semaphore():
            # Inject skill if present
            final_prompt, system_prompt = inject_skill(
                task.prompt,
                treatment.skill_path
            )
            
            # Replace variables in prompt
            for key, value in task.variables.items():
                placeholder = f"{{{key}}}"
                final_prompt = final_prompt.replace(placeholder, value)
            
            # Call LLM
            try:
                response = await self.llm_adapter.complete(
                    prompt=final_prompt,
                    system_prompt=None,
                )
            except LLMError as e:
                # Return error result
                return ExecutionResult(
                    treatment=treatment_name,
                    test=task.name,
                    prompt=final_prompt,
                    response=None,
                    passed=False,
                    evaluator_results=[],
                    timestamp=datetime.utcnow().isoformat()
                )
            
            # Evaluate if evaluator engine is available
            evaluator_results = []
            if self.evaluator_engine and task.evaluators:
                evaluator_results = await self.evaluator_engine.evaluate(
                    response.content,
                    task.evaluators
                )
            
            # Determine if passed
            passed = all(r.passed for r in evaluator_results) if evaluator_results else True
            
            return ExecutionResult(
                treatment=treatment_name,
                test=task.name,
                prompt=final_prompt,
                response=response,
                passed=passed,
                evaluator_results=evaluator_results,
                timestamp=datetime.utcnow().isoformat()
            )
    
    async def xǁExecutionEngineǁrun_single__mutmut_15(
        self,
        treatment: Treatment,
        task: Task,
        treatment_name: str,
    ) -> ExecutionResult:
        """Run a single evaluation.
        
        Args:
            treatment: Treatment configuration
            task: Task configuration
            treatment_name: Name of treatment
            
        Returns:
            ExecutionResult
        """
        async with self._get_semaphore():
            # Inject skill if present
            final_prompt, system_prompt = inject_skill(
                task.prompt,
                treatment.skill_path
            )
            
            # Replace variables in prompt
            for key, value in task.variables.items():
                placeholder = f"{{{key}}}"
                final_prompt = final_prompt.replace(placeholder, value)
            
            # Call LLM
            try:
                response = await self.llm_adapter.complete(
                    system_prompt=system_prompt,
                )
            except LLMError as e:
                # Return error result
                return ExecutionResult(
                    treatment=treatment_name,
                    test=task.name,
                    prompt=final_prompt,
                    response=None,
                    passed=False,
                    evaluator_results=[],
                    timestamp=datetime.utcnow().isoformat()
                )
            
            # Evaluate if evaluator engine is available
            evaluator_results = []
            if self.evaluator_engine and task.evaluators:
                evaluator_results = await self.evaluator_engine.evaluate(
                    response.content,
                    task.evaluators
                )
            
            # Determine if passed
            passed = all(r.passed for r in evaluator_results) if evaluator_results else True
            
            return ExecutionResult(
                treatment=treatment_name,
                test=task.name,
                prompt=final_prompt,
                response=response,
                passed=passed,
                evaluator_results=evaluator_results,
                timestamp=datetime.utcnow().isoformat()
            )
    
    async def xǁExecutionEngineǁrun_single__mutmut_16(
        self,
        treatment: Treatment,
        task: Task,
        treatment_name: str,
    ) -> ExecutionResult:
        """Run a single evaluation.
        
        Args:
            treatment: Treatment configuration
            task: Task configuration
            treatment_name: Name of treatment
            
        Returns:
            ExecutionResult
        """
        async with self._get_semaphore():
            # Inject skill if present
            final_prompt, system_prompt = inject_skill(
                task.prompt,
                treatment.skill_path
            )
            
            # Replace variables in prompt
            for key, value in task.variables.items():
                placeholder = f"{{{key}}}"
                final_prompt = final_prompt.replace(placeholder, value)
            
            # Call LLM
            try:
                response = await self.llm_adapter.complete(
                    prompt=final_prompt,
                    )
            except LLMError as e:
                # Return error result
                return ExecutionResult(
                    treatment=treatment_name,
                    test=task.name,
                    prompt=final_prompt,
                    response=None,
                    passed=False,
                    evaluator_results=[],
                    timestamp=datetime.utcnow().isoformat()
                )
            
            # Evaluate if evaluator engine is available
            evaluator_results = []
            if self.evaluator_engine and task.evaluators:
                evaluator_results = await self.evaluator_engine.evaluate(
                    response.content,
                    task.evaluators
                )
            
            # Determine if passed
            passed = all(r.passed for r in evaluator_results) if evaluator_results else True
            
            return ExecutionResult(
                treatment=treatment_name,
                test=task.name,
                prompt=final_prompt,
                response=response,
                passed=passed,
                evaluator_results=evaluator_results,
                timestamp=datetime.utcnow().isoformat()
            )
    
    async def xǁExecutionEngineǁrun_single__mutmut_17(
        self,
        treatment: Treatment,
        task: Task,
        treatment_name: str,
    ) -> ExecutionResult:
        """Run a single evaluation.
        
        Args:
            treatment: Treatment configuration
            task: Task configuration
            treatment_name: Name of treatment
            
        Returns:
            ExecutionResult
        """
        async with self._get_semaphore():
            # Inject skill if present
            final_prompt, system_prompt = inject_skill(
                task.prompt,
                treatment.skill_path
            )
            
            # Replace variables in prompt
            for key, value in task.variables.items():
                placeholder = f"{{{key}}}"
                final_prompt = final_prompt.replace(placeholder, value)
            
            # Call LLM
            try:
                response = await self.llm_adapter.complete(
                    prompt=final_prompt,
                    system_prompt=system_prompt,
                )
            except LLMError as e:
                # Return error result
                return ExecutionResult(
                    treatment=None,
                    test=task.name,
                    prompt=final_prompt,
                    response=None,
                    passed=False,
                    evaluator_results=[],
                    timestamp=datetime.utcnow().isoformat()
                )
            
            # Evaluate if evaluator engine is available
            evaluator_results = []
            if self.evaluator_engine and task.evaluators:
                evaluator_results = await self.evaluator_engine.evaluate(
                    response.content,
                    task.evaluators
                )
            
            # Determine if passed
            passed = all(r.passed for r in evaluator_results) if evaluator_results else True
            
            return ExecutionResult(
                treatment=treatment_name,
                test=task.name,
                prompt=final_prompt,
                response=response,
                passed=passed,
                evaluator_results=evaluator_results,
                timestamp=datetime.utcnow().isoformat()
            )
    
    async def xǁExecutionEngineǁrun_single__mutmut_18(
        self,
        treatment: Treatment,
        task: Task,
        treatment_name: str,
    ) -> ExecutionResult:
        """Run a single evaluation.
        
        Args:
            treatment: Treatment configuration
            task: Task configuration
            treatment_name: Name of treatment
            
        Returns:
            ExecutionResult
        """
        async with self._get_semaphore():
            # Inject skill if present
            final_prompt, system_prompt = inject_skill(
                task.prompt,
                treatment.skill_path
            )
            
            # Replace variables in prompt
            for key, value in task.variables.items():
                placeholder = f"{{{key}}}"
                final_prompt = final_prompt.replace(placeholder, value)
            
            # Call LLM
            try:
                response = await self.llm_adapter.complete(
                    prompt=final_prompt,
                    system_prompt=system_prompt,
                )
            except LLMError as e:
                # Return error result
                return ExecutionResult(
                    treatment=treatment_name,
                    test=None,
                    prompt=final_prompt,
                    response=None,
                    passed=False,
                    evaluator_results=[],
                    timestamp=datetime.utcnow().isoformat()
                )
            
            # Evaluate if evaluator engine is available
            evaluator_results = []
            if self.evaluator_engine and task.evaluators:
                evaluator_results = await self.evaluator_engine.evaluate(
                    response.content,
                    task.evaluators
                )
            
            # Determine if passed
            passed = all(r.passed for r in evaluator_results) if evaluator_results else True
            
            return ExecutionResult(
                treatment=treatment_name,
                test=task.name,
                prompt=final_prompt,
                response=response,
                passed=passed,
                evaluator_results=evaluator_results,
                timestamp=datetime.utcnow().isoformat()
            )
    
    async def xǁExecutionEngineǁrun_single__mutmut_19(
        self,
        treatment: Treatment,
        task: Task,
        treatment_name: str,
    ) -> ExecutionResult:
        """Run a single evaluation.
        
        Args:
            treatment: Treatment configuration
            task: Task configuration
            treatment_name: Name of treatment
            
        Returns:
            ExecutionResult
        """
        async with self._get_semaphore():
            # Inject skill if present
            final_prompt, system_prompt = inject_skill(
                task.prompt,
                treatment.skill_path
            )
            
            # Replace variables in prompt
            for key, value in task.variables.items():
                placeholder = f"{{{key}}}"
                final_prompt = final_prompt.replace(placeholder, value)
            
            # Call LLM
            try:
                response = await self.llm_adapter.complete(
                    prompt=final_prompt,
                    system_prompt=system_prompt,
                )
            except LLMError as e:
                # Return error result
                return ExecutionResult(
                    treatment=treatment_name,
                    test=task.name,
                    prompt=None,
                    response=None,
                    passed=False,
                    evaluator_results=[],
                    timestamp=datetime.utcnow().isoformat()
                )
            
            # Evaluate if evaluator engine is available
            evaluator_results = []
            if self.evaluator_engine and task.evaluators:
                evaluator_results = await self.evaluator_engine.evaluate(
                    response.content,
                    task.evaluators
                )
            
            # Determine if passed
            passed = all(r.passed for r in evaluator_results) if evaluator_results else True
            
            return ExecutionResult(
                treatment=treatment_name,
                test=task.name,
                prompt=final_prompt,
                response=response,
                passed=passed,
                evaluator_results=evaluator_results,
                timestamp=datetime.utcnow().isoformat()
            )
    
    async def xǁExecutionEngineǁrun_single__mutmut_20(
        self,
        treatment: Treatment,
        task: Task,
        treatment_name: str,
    ) -> ExecutionResult:
        """Run a single evaluation.
        
        Args:
            treatment: Treatment configuration
            task: Task configuration
            treatment_name: Name of treatment
            
        Returns:
            ExecutionResult
        """
        async with self._get_semaphore():
            # Inject skill if present
            final_prompt, system_prompt = inject_skill(
                task.prompt,
                treatment.skill_path
            )
            
            # Replace variables in prompt
            for key, value in task.variables.items():
                placeholder = f"{{{key}}}"
                final_prompt = final_prompt.replace(placeholder, value)
            
            # Call LLM
            try:
                response = await self.llm_adapter.complete(
                    prompt=final_prompt,
                    system_prompt=system_prompt,
                )
            except LLMError as e:
                # Return error result
                return ExecutionResult(
                    treatment=treatment_name,
                    test=task.name,
                    prompt=final_prompt,
                    response=None,
                    passed=None,
                    evaluator_results=[],
                    timestamp=datetime.utcnow().isoformat()
                )
            
            # Evaluate if evaluator engine is available
            evaluator_results = []
            if self.evaluator_engine and task.evaluators:
                evaluator_results = await self.evaluator_engine.evaluate(
                    response.content,
                    task.evaluators
                )
            
            # Determine if passed
            passed = all(r.passed for r in evaluator_results) if evaluator_results else True
            
            return ExecutionResult(
                treatment=treatment_name,
                test=task.name,
                prompt=final_prompt,
                response=response,
                passed=passed,
                evaluator_results=evaluator_results,
                timestamp=datetime.utcnow().isoformat()
            )
    
    async def xǁExecutionEngineǁrun_single__mutmut_21(
        self,
        treatment: Treatment,
        task: Task,
        treatment_name: str,
    ) -> ExecutionResult:
        """Run a single evaluation.
        
        Args:
            treatment: Treatment configuration
            task: Task configuration
            treatment_name: Name of treatment
            
        Returns:
            ExecutionResult
        """
        async with self._get_semaphore():
            # Inject skill if present
            final_prompt, system_prompt = inject_skill(
                task.prompt,
                treatment.skill_path
            )
            
            # Replace variables in prompt
            for key, value in task.variables.items():
                placeholder = f"{{{key}}}"
                final_prompt = final_prompt.replace(placeholder, value)
            
            # Call LLM
            try:
                response = await self.llm_adapter.complete(
                    prompt=final_prompt,
                    system_prompt=system_prompt,
                )
            except LLMError as e:
                # Return error result
                return ExecutionResult(
                    treatment=treatment_name,
                    test=task.name,
                    prompt=final_prompt,
                    response=None,
                    passed=False,
                    evaluator_results=None,
                    timestamp=datetime.utcnow().isoformat()
                )
            
            # Evaluate if evaluator engine is available
            evaluator_results = []
            if self.evaluator_engine and task.evaluators:
                evaluator_results = await self.evaluator_engine.evaluate(
                    response.content,
                    task.evaluators
                )
            
            # Determine if passed
            passed = all(r.passed for r in evaluator_results) if evaluator_results else True
            
            return ExecutionResult(
                treatment=treatment_name,
                test=task.name,
                prompt=final_prompt,
                response=response,
                passed=passed,
                evaluator_results=evaluator_results,
                timestamp=datetime.utcnow().isoformat()
            )
    
    async def xǁExecutionEngineǁrun_single__mutmut_22(
        self,
        treatment: Treatment,
        task: Task,
        treatment_name: str,
    ) -> ExecutionResult:
        """Run a single evaluation.
        
        Args:
            treatment: Treatment configuration
            task: Task configuration
            treatment_name: Name of treatment
            
        Returns:
            ExecutionResult
        """
        async with self._get_semaphore():
            # Inject skill if present
            final_prompt, system_prompt = inject_skill(
                task.prompt,
                treatment.skill_path
            )
            
            # Replace variables in prompt
            for key, value in task.variables.items():
                placeholder = f"{{{key}}}"
                final_prompt = final_prompt.replace(placeholder, value)
            
            # Call LLM
            try:
                response = await self.llm_adapter.complete(
                    prompt=final_prompt,
                    system_prompt=system_prompt,
                )
            except LLMError as e:
                # Return error result
                return ExecutionResult(
                    treatment=treatment_name,
                    test=task.name,
                    prompt=final_prompt,
                    response=None,
                    passed=False,
                    evaluator_results=[],
                    timestamp=None
                )
            
            # Evaluate if evaluator engine is available
            evaluator_results = []
            if self.evaluator_engine and task.evaluators:
                evaluator_results = await self.evaluator_engine.evaluate(
                    response.content,
                    task.evaluators
                )
            
            # Determine if passed
            passed = all(r.passed for r in evaluator_results) if evaluator_results else True
            
            return ExecutionResult(
                treatment=treatment_name,
                test=task.name,
                prompt=final_prompt,
                response=response,
                passed=passed,
                evaluator_results=evaluator_results,
                timestamp=datetime.utcnow().isoformat()
            )
    
    async def xǁExecutionEngineǁrun_single__mutmut_23(
        self,
        treatment: Treatment,
        task: Task,
        treatment_name: str,
    ) -> ExecutionResult:
        """Run a single evaluation.
        
        Args:
            treatment: Treatment configuration
            task: Task configuration
            treatment_name: Name of treatment
            
        Returns:
            ExecutionResult
        """
        async with self._get_semaphore():
            # Inject skill if present
            final_prompt, system_prompt = inject_skill(
                task.prompt,
                treatment.skill_path
            )
            
            # Replace variables in prompt
            for key, value in task.variables.items():
                placeholder = f"{{{key}}}"
                final_prompt = final_prompt.replace(placeholder, value)
            
            # Call LLM
            try:
                response = await self.llm_adapter.complete(
                    prompt=final_prompt,
                    system_prompt=system_prompt,
                )
            except LLMError as e:
                # Return error result
                return ExecutionResult(
                    test=task.name,
                    prompt=final_prompt,
                    response=None,
                    passed=False,
                    evaluator_results=[],
                    timestamp=datetime.utcnow().isoformat()
                )
            
            # Evaluate if evaluator engine is available
            evaluator_results = []
            if self.evaluator_engine and task.evaluators:
                evaluator_results = await self.evaluator_engine.evaluate(
                    response.content,
                    task.evaluators
                )
            
            # Determine if passed
            passed = all(r.passed for r in evaluator_results) if evaluator_results else True
            
            return ExecutionResult(
                treatment=treatment_name,
                test=task.name,
                prompt=final_prompt,
                response=response,
                passed=passed,
                evaluator_results=evaluator_results,
                timestamp=datetime.utcnow().isoformat()
            )
    
    async def xǁExecutionEngineǁrun_single__mutmut_24(
        self,
        treatment: Treatment,
        task: Task,
        treatment_name: str,
    ) -> ExecutionResult:
        """Run a single evaluation.
        
        Args:
            treatment: Treatment configuration
            task: Task configuration
            treatment_name: Name of treatment
            
        Returns:
            ExecutionResult
        """
        async with self._get_semaphore():
            # Inject skill if present
            final_prompt, system_prompt = inject_skill(
                task.prompt,
                treatment.skill_path
            )
            
            # Replace variables in prompt
            for key, value in task.variables.items():
                placeholder = f"{{{key}}}"
                final_prompt = final_prompt.replace(placeholder, value)
            
            # Call LLM
            try:
                response = await self.llm_adapter.complete(
                    prompt=final_prompt,
                    system_prompt=system_prompt,
                )
            except LLMError as e:
                # Return error result
                return ExecutionResult(
                    treatment=treatment_name,
                    prompt=final_prompt,
                    response=None,
                    passed=False,
                    evaluator_results=[],
                    timestamp=datetime.utcnow().isoformat()
                )
            
            # Evaluate if evaluator engine is available
            evaluator_results = []
            if self.evaluator_engine and task.evaluators:
                evaluator_results = await self.evaluator_engine.evaluate(
                    response.content,
                    task.evaluators
                )
            
            # Determine if passed
            passed = all(r.passed for r in evaluator_results) if evaluator_results else True
            
            return ExecutionResult(
                treatment=treatment_name,
                test=task.name,
                prompt=final_prompt,
                response=response,
                passed=passed,
                evaluator_results=evaluator_results,
                timestamp=datetime.utcnow().isoformat()
            )
    
    async def xǁExecutionEngineǁrun_single__mutmut_25(
        self,
        treatment: Treatment,
        task: Task,
        treatment_name: str,
    ) -> ExecutionResult:
        """Run a single evaluation.
        
        Args:
            treatment: Treatment configuration
            task: Task configuration
            treatment_name: Name of treatment
            
        Returns:
            ExecutionResult
        """
        async with self._get_semaphore():
            # Inject skill if present
            final_prompt, system_prompt = inject_skill(
                task.prompt,
                treatment.skill_path
            )
            
            # Replace variables in prompt
            for key, value in task.variables.items():
                placeholder = f"{{{key}}}"
                final_prompt = final_prompt.replace(placeholder, value)
            
            # Call LLM
            try:
                response = await self.llm_adapter.complete(
                    prompt=final_prompt,
                    system_prompt=system_prompt,
                )
            except LLMError as e:
                # Return error result
                return ExecutionResult(
                    treatment=treatment_name,
                    test=task.name,
                    response=None,
                    passed=False,
                    evaluator_results=[],
                    timestamp=datetime.utcnow().isoformat()
                )
            
            # Evaluate if evaluator engine is available
            evaluator_results = []
            if self.evaluator_engine and task.evaluators:
                evaluator_results = await self.evaluator_engine.evaluate(
                    response.content,
                    task.evaluators
                )
            
            # Determine if passed
            passed = all(r.passed for r in evaluator_results) if evaluator_results else True
            
            return ExecutionResult(
                treatment=treatment_name,
                test=task.name,
                prompt=final_prompt,
                response=response,
                passed=passed,
                evaluator_results=evaluator_results,
                timestamp=datetime.utcnow().isoformat()
            )
    
    async def xǁExecutionEngineǁrun_single__mutmut_26(
        self,
        treatment: Treatment,
        task: Task,
        treatment_name: str,
    ) -> ExecutionResult:
        """Run a single evaluation.
        
        Args:
            treatment: Treatment configuration
            task: Task configuration
            treatment_name: Name of treatment
            
        Returns:
            ExecutionResult
        """
        async with self._get_semaphore():
            # Inject skill if present
            final_prompt, system_prompt = inject_skill(
                task.prompt,
                treatment.skill_path
            )
            
            # Replace variables in prompt
            for key, value in task.variables.items():
                placeholder = f"{{{key}}}"
                final_prompt = final_prompt.replace(placeholder, value)
            
            # Call LLM
            try:
                response = await self.llm_adapter.complete(
                    prompt=final_prompt,
                    system_prompt=system_prompt,
                )
            except LLMError as e:
                # Return error result
                return ExecutionResult(
                    treatment=treatment_name,
                    test=task.name,
                    prompt=final_prompt,
                    passed=False,
                    evaluator_results=[],
                    timestamp=datetime.utcnow().isoformat()
                )
            
            # Evaluate if evaluator engine is available
            evaluator_results = []
            if self.evaluator_engine and task.evaluators:
                evaluator_results = await self.evaluator_engine.evaluate(
                    response.content,
                    task.evaluators
                )
            
            # Determine if passed
            passed = all(r.passed for r in evaluator_results) if evaluator_results else True
            
            return ExecutionResult(
                treatment=treatment_name,
                test=task.name,
                prompt=final_prompt,
                response=response,
                passed=passed,
                evaluator_results=evaluator_results,
                timestamp=datetime.utcnow().isoformat()
            )
    
    async def xǁExecutionEngineǁrun_single__mutmut_27(
        self,
        treatment: Treatment,
        task: Task,
        treatment_name: str,
    ) -> ExecutionResult:
        """Run a single evaluation.
        
        Args:
            treatment: Treatment configuration
            task: Task configuration
            treatment_name: Name of treatment
            
        Returns:
            ExecutionResult
        """
        async with self._get_semaphore():
            # Inject skill if present
            final_prompt, system_prompt = inject_skill(
                task.prompt,
                treatment.skill_path
            )
            
            # Replace variables in prompt
            for key, value in task.variables.items():
                placeholder = f"{{{key}}}"
                final_prompt = final_prompt.replace(placeholder, value)
            
            # Call LLM
            try:
                response = await self.llm_adapter.complete(
                    prompt=final_prompt,
                    system_prompt=system_prompt,
                )
            except LLMError as e:
                # Return error result
                return ExecutionResult(
                    treatment=treatment_name,
                    test=task.name,
                    prompt=final_prompt,
                    response=None,
                    evaluator_results=[],
                    timestamp=datetime.utcnow().isoformat()
                )
            
            # Evaluate if evaluator engine is available
            evaluator_results = []
            if self.evaluator_engine and task.evaluators:
                evaluator_results = await self.evaluator_engine.evaluate(
                    response.content,
                    task.evaluators
                )
            
            # Determine if passed
            passed = all(r.passed for r in evaluator_results) if evaluator_results else True
            
            return ExecutionResult(
                treatment=treatment_name,
                test=task.name,
                prompt=final_prompt,
                response=response,
                passed=passed,
                evaluator_results=evaluator_results,
                timestamp=datetime.utcnow().isoformat()
            )
    
    async def xǁExecutionEngineǁrun_single__mutmut_28(
        self,
        treatment: Treatment,
        task: Task,
        treatment_name: str,
    ) -> ExecutionResult:
        """Run a single evaluation.
        
        Args:
            treatment: Treatment configuration
            task: Task configuration
            treatment_name: Name of treatment
            
        Returns:
            ExecutionResult
        """
        async with self._get_semaphore():
            # Inject skill if present
            final_prompt, system_prompt = inject_skill(
                task.prompt,
                treatment.skill_path
            )
            
            # Replace variables in prompt
            for key, value in task.variables.items():
                placeholder = f"{{{key}}}"
                final_prompt = final_prompt.replace(placeholder, value)
            
            # Call LLM
            try:
                response = await self.llm_adapter.complete(
                    prompt=final_prompt,
                    system_prompt=system_prompt,
                )
            except LLMError as e:
                # Return error result
                return ExecutionResult(
                    treatment=treatment_name,
                    test=task.name,
                    prompt=final_prompt,
                    response=None,
                    passed=False,
                    timestamp=datetime.utcnow().isoformat()
                )
            
            # Evaluate if evaluator engine is available
            evaluator_results = []
            if self.evaluator_engine and task.evaluators:
                evaluator_results = await self.evaluator_engine.evaluate(
                    response.content,
                    task.evaluators
                )
            
            # Determine if passed
            passed = all(r.passed for r in evaluator_results) if evaluator_results else True
            
            return ExecutionResult(
                treatment=treatment_name,
                test=task.name,
                prompt=final_prompt,
                response=response,
                passed=passed,
                evaluator_results=evaluator_results,
                timestamp=datetime.utcnow().isoformat()
            )
    
    async def xǁExecutionEngineǁrun_single__mutmut_29(
        self,
        treatment: Treatment,
        task: Task,
        treatment_name: str,
    ) -> ExecutionResult:
        """Run a single evaluation.
        
        Args:
            treatment: Treatment configuration
            task: Task configuration
            treatment_name: Name of treatment
            
        Returns:
            ExecutionResult
        """
        async with self._get_semaphore():
            # Inject skill if present
            final_prompt, system_prompt = inject_skill(
                task.prompt,
                treatment.skill_path
            )
            
            # Replace variables in prompt
            for key, value in task.variables.items():
                placeholder = f"{{{key}}}"
                final_prompt = final_prompt.replace(placeholder, value)
            
            # Call LLM
            try:
                response = await self.llm_adapter.complete(
                    prompt=final_prompt,
                    system_prompt=system_prompt,
                )
            except LLMError as e:
                # Return error result
                return ExecutionResult(
                    treatment=treatment_name,
                    test=task.name,
                    prompt=final_prompt,
                    response=None,
                    passed=False,
                    evaluator_results=[],
                    )
            
            # Evaluate if evaluator engine is available
            evaluator_results = []
            if self.evaluator_engine and task.evaluators:
                evaluator_results = await self.evaluator_engine.evaluate(
                    response.content,
                    task.evaluators
                )
            
            # Determine if passed
            passed = all(r.passed for r in evaluator_results) if evaluator_results else True
            
            return ExecutionResult(
                treatment=treatment_name,
                test=task.name,
                prompt=final_prompt,
                response=response,
                passed=passed,
                evaluator_results=evaluator_results,
                timestamp=datetime.utcnow().isoformat()
            )
    
    async def xǁExecutionEngineǁrun_single__mutmut_30(
        self,
        treatment: Treatment,
        task: Task,
        treatment_name: str,
    ) -> ExecutionResult:
        """Run a single evaluation.
        
        Args:
            treatment: Treatment configuration
            task: Task configuration
            treatment_name: Name of treatment
            
        Returns:
            ExecutionResult
        """
        async with self._get_semaphore():
            # Inject skill if present
            final_prompt, system_prompt = inject_skill(
                task.prompt,
                treatment.skill_path
            )
            
            # Replace variables in prompt
            for key, value in task.variables.items():
                placeholder = f"{{{key}}}"
                final_prompt = final_prompt.replace(placeholder, value)
            
            # Call LLM
            try:
                response = await self.llm_adapter.complete(
                    prompt=final_prompt,
                    system_prompt=system_prompt,
                )
            except LLMError as e:
                # Return error result
                return ExecutionResult(
                    treatment=treatment_name,
                    test=task.name,
                    prompt=final_prompt,
                    response=None,
                    passed=True,
                    evaluator_results=[],
                    timestamp=datetime.utcnow().isoformat()
                )
            
            # Evaluate if evaluator engine is available
            evaluator_results = []
            if self.evaluator_engine and task.evaluators:
                evaluator_results = await self.evaluator_engine.evaluate(
                    response.content,
                    task.evaluators
                )
            
            # Determine if passed
            passed = all(r.passed for r in evaluator_results) if evaluator_results else True
            
            return ExecutionResult(
                treatment=treatment_name,
                test=task.name,
                prompt=final_prompt,
                response=response,
                passed=passed,
                evaluator_results=evaluator_results,
                timestamp=datetime.utcnow().isoformat()
            )
    
    async def xǁExecutionEngineǁrun_single__mutmut_31(
        self,
        treatment: Treatment,
        task: Task,
        treatment_name: str,
    ) -> ExecutionResult:
        """Run a single evaluation.
        
        Args:
            treatment: Treatment configuration
            task: Task configuration
            treatment_name: Name of treatment
            
        Returns:
            ExecutionResult
        """
        async with self._get_semaphore():
            # Inject skill if present
            final_prompt, system_prompt = inject_skill(
                task.prompt,
                treatment.skill_path
            )
            
            # Replace variables in prompt
            for key, value in task.variables.items():
                placeholder = f"{{{key}}}"
                final_prompt = final_prompt.replace(placeholder, value)
            
            # Call LLM
            try:
                response = await self.llm_adapter.complete(
                    prompt=final_prompt,
                    system_prompt=system_prompt,
                )
            except LLMError as e:
                # Return error result
                return ExecutionResult(
                    treatment=treatment_name,
                    test=task.name,
                    prompt=final_prompt,
                    response=None,
                    passed=False,
                    evaluator_results=[],
                    timestamp=datetime.utcnow().isoformat()
                )
            
            # Evaluate if evaluator engine is available
            evaluator_results = None
            if self.evaluator_engine and task.evaluators:
                evaluator_results = await self.evaluator_engine.evaluate(
                    response.content,
                    task.evaluators
                )
            
            # Determine if passed
            passed = all(r.passed for r in evaluator_results) if evaluator_results else True
            
            return ExecutionResult(
                treatment=treatment_name,
                test=task.name,
                prompt=final_prompt,
                response=response,
                passed=passed,
                evaluator_results=evaluator_results,
                timestamp=datetime.utcnow().isoformat()
            )
    
    async def xǁExecutionEngineǁrun_single__mutmut_32(
        self,
        treatment: Treatment,
        task: Task,
        treatment_name: str,
    ) -> ExecutionResult:
        """Run a single evaluation.
        
        Args:
            treatment: Treatment configuration
            task: Task configuration
            treatment_name: Name of treatment
            
        Returns:
            ExecutionResult
        """
        async with self._get_semaphore():
            # Inject skill if present
            final_prompt, system_prompt = inject_skill(
                task.prompt,
                treatment.skill_path
            )
            
            # Replace variables in prompt
            for key, value in task.variables.items():
                placeholder = f"{{{key}}}"
                final_prompt = final_prompt.replace(placeholder, value)
            
            # Call LLM
            try:
                response = await self.llm_adapter.complete(
                    prompt=final_prompt,
                    system_prompt=system_prompt,
                )
            except LLMError as e:
                # Return error result
                return ExecutionResult(
                    treatment=treatment_name,
                    test=task.name,
                    prompt=final_prompt,
                    response=None,
                    passed=False,
                    evaluator_results=[],
                    timestamp=datetime.utcnow().isoformat()
                )
            
            # Evaluate if evaluator engine is available
            evaluator_results = []
            if self.evaluator_engine or task.evaluators:
                evaluator_results = await self.evaluator_engine.evaluate(
                    response.content,
                    task.evaluators
                )
            
            # Determine if passed
            passed = all(r.passed for r in evaluator_results) if evaluator_results else True
            
            return ExecutionResult(
                treatment=treatment_name,
                test=task.name,
                prompt=final_prompt,
                response=response,
                passed=passed,
                evaluator_results=evaluator_results,
                timestamp=datetime.utcnow().isoformat()
            )
    
    async def xǁExecutionEngineǁrun_single__mutmut_33(
        self,
        treatment: Treatment,
        task: Task,
        treatment_name: str,
    ) -> ExecutionResult:
        """Run a single evaluation.
        
        Args:
            treatment: Treatment configuration
            task: Task configuration
            treatment_name: Name of treatment
            
        Returns:
            ExecutionResult
        """
        async with self._get_semaphore():
            # Inject skill if present
            final_prompt, system_prompt = inject_skill(
                task.prompt,
                treatment.skill_path
            )
            
            # Replace variables in prompt
            for key, value in task.variables.items():
                placeholder = f"{{{key}}}"
                final_prompt = final_prompt.replace(placeholder, value)
            
            # Call LLM
            try:
                response = await self.llm_adapter.complete(
                    prompt=final_prompt,
                    system_prompt=system_prompt,
                )
            except LLMError as e:
                # Return error result
                return ExecutionResult(
                    treatment=treatment_name,
                    test=task.name,
                    prompt=final_prompt,
                    response=None,
                    passed=False,
                    evaluator_results=[],
                    timestamp=datetime.utcnow().isoformat()
                )
            
            # Evaluate if evaluator engine is available
            evaluator_results = []
            if self.evaluator_engine and task.evaluators:
                evaluator_results = None
            
            # Determine if passed
            passed = all(r.passed for r in evaluator_results) if evaluator_results else True
            
            return ExecutionResult(
                treatment=treatment_name,
                test=task.name,
                prompt=final_prompt,
                response=response,
                passed=passed,
                evaluator_results=evaluator_results,
                timestamp=datetime.utcnow().isoformat()
            )
    
    async def xǁExecutionEngineǁrun_single__mutmut_34(
        self,
        treatment: Treatment,
        task: Task,
        treatment_name: str,
    ) -> ExecutionResult:
        """Run a single evaluation.
        
        Args:
            treatment: Treatment configuration
            task: Task configuration
            treatment_name: Name of treatment
            
        Returns:
            ExecutionResult
        """
        async with self._get_semaphore():
            # Inject skill if present
            final_prompt, system_prompt = inject_skill(
                task.prompt,
                treatment.skill_path
            )
            
            # Replace variables in prompt
            for key, value in task.variables.items():
                placeholder = f"{{{key}}}"
                final_prompt = final_prompt.replace(placeholder, value)
            
            # Call LLM
            try:
                response = await self.llm_adapter.complete(
                    prompt=final_prompt,
                    system_prompt=system_prompt,
                )
            except LLMError as e:
                # Return error result
                return ExecutionResult(
                    treatment=treatment_name,
                    test=task.name,
                    prompt=final_prompt,
                    response=None,
                    passed=False,
                    evaluator_results=[],
                    timestamp=datetime.utcnow().isoformat()
                )
            
            # Evaluate if evaluator engine is available
            evaluator_results = []
            if self.evaluator_engine and task.evaluators:
                evaluator_results = await self.evaluator_engine.evaluate(
                    None,
                    task.evaluators
                )
            
            # Determine if passed
            passed = all(r.passed for r in evaluator_results) if evaluator_results else True
            
            return ExecutionResult(
                treatment=treatment_name,
                test=task.name,
                prompt=final_prompt,
                response=response,
                passed=passed,
                evaluator_results=evaluator_results,
                timestamp=datetime.utcnow().isoformat()
            )
    
    async def xǁExecutionEngineǁrun_single__mutmut_35(
        self,
        treatment: Treatment,
        task: Task,
        treatment_name: str,
    ) -> ExecutionResult:
        """Run a single evaluation.
        
        Args:
            treatment: Treatment configuration
            task: Task configuration
            treatment_name: Name of treatment
            
        Returns:
            ExecutionResult
        """
        async with self._get_semaphore():
            # Inject skill if present
            final_prompt, system_prompt = inject_skill(
                task.prompt,
                treatment.skill_path
            )
            
            # Replace variables in prompt
            for key, value in task.variables.items():
                placeholder = f"{{{key}}}"
                final_prompt = final_prompt.replace(placeholder, value)
            
            # Call LLM
            try:
                response = await self.llm_adapter.complete(
                    prompt=final_prompt,
                    system_prompt=system_prompt,
                )
            except LLMError as e:
                # Return error result
                return ExecutionResult(
                    treatment=treatment_name,
                    test=task.name,
                    prompt=final_prompt,
                    response=None,
                    passed=False,
                    evaluator_results=[],
                    timestamp=datetime.utcnow().isoformat()
                )
            
            # Evaluate if evaluator engine is available
            evaluator_results = []
            if self.evaluator_engine and task.evaluators:
                evaluator_results = await self.evaluator_engine.evaluate(
                    response.content,
                    None
                )
            
            # Determine if passed
            passed = all(r.passed for r in evaluator_results) if evaluator_results else True
            
            return ExecutionResult(
                treatment=treatment_name,
                test=task.name,
                prompt=final_prompt,
                response=response,
                passed=passed,
                evaluator_results=evaluator_results,
                timestamp=datetime.utcnow().isoformat()
            )
    
    async def xǁExecutionEngineǁrun_single__mutmut_36(
        self,
        treatment: Treatment,
        task: Task,
        treatment_name: str,
    ) -> ExecutionResult:
        """Run a single evaluation.
        
        Args:
            treatment: Treatment configuration
            task: Task configuration
            treatment_name: Name of treatment
            
        Returns:
            ExecutionResult
        """
        async with self._get_semaphore():
            # Inject skill if present
            final_prompt, system_prompt = inject_skill(
                task.prompt,
                treatment.skill_path
            )
            
            # Replace variables in prompt
            for key, value in task.variables.items():
                placeholder = f"{{{key}}}"
                final_prompt = final_prompt.replace(placeholder, value)
            
            # Call LLM
            try:
                response = await self.llm_adapter.complete(
                    prompt=final_prompt,
                    system_prompt=system_prompt,
                )
            except LLMError as e:
                # Return error result
                return ExecutionResult(
                    treatment=treatment_name,
                    test=task.name,
                    prompt=final_prompt,
                    response=None,
                    passed=False,
                    evaluator_results=[],
                    timestamp=datetime.utcnow().isoformat()
                )
            
            # Evaluate if evaluator engine is available
            evaluator_results = []
            if self.evaluator_engine and task.evaluators:
                evaluator_results = await self.evaluator_engine.evaluate(
                    task.evaluators
                )
            
            # Determine if passed
            passed = all(r.passed for r in evaluator_results) if evaluator_results else True
            
            return ExecutionResult(
                treatment=treatment_name,
                test=task.name,
                prompt=final_prompt,
                response=response,
                passed=passed,
                evaluator_results=evaluator_results,
                timestamp=datetime.utcnow().isoformat()
            )
    
    async def xǁExecutionEngineǁrun_single__mutmut_37(
        self,
        treatment: Treatment,
        task: Task,
        treatment_name: str,
    ) -> ExecutionResult:
        """Run a single evaluation.
        
        Args:
            treatment: Treatment configuration
            task: Task configuration
            treatment_name: Name of treatment
            
        Returns:
            ExecutionResult
        """
        async with self._get_semaphore():
            # Inject skill if present
            final_prompt, system_prompt = inject_skill(
                task.prompt,
                treatment.skill_path
            )
            
            # Replace variables in prompt
            for key, value in task.variables.items():
                placeholder = f"{{{key}}}"
                final_prompt = final_prompt.replace(placeholder, value)
            
            # Call LLM
            try:
                response = await self.llm_adapter.complete(
                    prompt=final_prompt,
                    system_prompt=system_prompt,
                )
            except LLMError as e:
                # Return error result
                return ExecutionResult(
                    treatment=treatment_name,
                    test=task.name,
                    prompt=final_prompt,
                    response=None,
                    passed=False,
                    evaluator_results=[],
                    timestamp=datetime.utcnow().isoformat()
                )
            
            # Evaluate if evaluator engine is available
            evaluator_results = []
            if self.evaluator_engine and task.evaluators:
                evaluator_results = await self.evaluator_engine.evaluate(
                    response.content,
                    )
            
            # Determine if passed
            passed = all(r.passed for r in evaluator_results) if evaluator_results else True
            
            return ExecutionResult(
                treatment=treatment_name,
                test=task.name,
                prompt=final_prompt,
                response=response,
                passed=passed,
                evaluator_results=evaluator_results,
                timestamp=datetime.utcnow().isoformat()
            )
    
    async def xǁExecutionEngineǁrun_single__mutmut_38(
        self,
        treatment: Treatment,
        task: Task,
        treatment_name: str,
    ) -> ExecutionResult:
        """Run a single evaluation.
        
        Args:
            treatment: Treatment configuration
            task: Task configuration
            treatment_name: Name of treatment
            
        Returns:
            ExecutionResult
        """
        async with self._get_semaphore():
            # Inject skill if present
            final_prompt, system_prompt = inject_skill(
                task.prompt,
                treatment.skill_path
            )
            
            # Replace variables in prompt
            for key, value in task.variables.items():
                placeholder = f"{{{key}}}"
                final_prompt = final_prompt.replace(placeholder, value)
            
            # Call LLM
            try:
                response = await self.llm_adapter.complete(
                    prompt=final_prompt,
                    system_prompt=system_prompt,
                )
            except LLMError as e:
                # Return error result
                return ExecutionResult(
                    treatment=treatment_name,
                    test=task.name,
                    prompt=final_prompt,
                    response=None,
                    passed=False,
                    evaluator_results=[],
                    timestamp=datetime.utcnow().isoformat()
                )
            
            # Evaluate if evaluator engine is available
            evaluator_results = []
            if self.evaluator_engine and task.evaluators:
                evaluator_results = await self.evaluator_engine.evaluate(
                    response.content,
                    task.evaluators
                )
            
            # Determine if passed
            passed = None
            
            return ExecutionResult(
                treatment=treatment_name,
                test=task.name,
                prompt=final_prompt,
                response=response,
                passed=passed,
                evaluator_results=evaluator_results,
                timestamp=datetime.utcnow().isoformat()
            )
    
    async def xǁExecutionEngineǁrun_single__mutmut_39(
        self,
        treatment: Treatment,
        task: Task,
        treatment_name: str,
    ) -> ExecutionResult:
        """Run a single evaluation.
        
        Args:
            treatment: Treatment configuration
            task: Task configuration
            treatment_name: Name of treatment
            
        Returns:
            ExecutionResult
        """
        async with self._get_semaphore():
            # Inject skill if present
            final_prompt, system_prompt = inject_skill(
                task.prompt,
                treatment.skill_path
            )
            
            # Replace variables in prompt
            for key, value in task.variables.items():
                placeholder = f"{{{key}}}"
                final_prompt = final_prompt.replace(placeholder, value)
            
            # Call LLM
            try:
                response = await self.llm_adapter.complete(
                    prompt=final_prompt,
                    system_prompt=system_prompt,
                )
            except LLMError as e:
                # Return error result
                return ExecutionResult(
                    treatment=treatment_name,
                    test=task.name,
                    prompt=final_prompt,
                    response=None,
                    passed=False,
                    evaluator_results=[],
                    timestamp=datetime.utcnow().isoformat()
                )
            
            # Evaluate if evaluator engine is available
            evaluator_results = []
            if self.evaluator_engine and task.evaluators:
                evaluator_results = await self.evaluator_engine.evaluate(
                    response.content,
                    task.evaluators
                )
            
            # Determine if passed
            passed = all(None) if evaluator_results else True
            
            return ExecutionResult(
                treatment=treatment_name,
                test=task.name,
                prompt=final_prompt,
                response=response,
                passed=passed,
                evaluator_results=evaluator_results,
                timestamp=datetime.utcnow().isoformat()
            )
    
    async def xǁExecutionEngineǁrun_single__mutmut_40(
        self,
        treatment: Treatment,
        task: Task,
        treatment_name: str,
    ) -> ExecutionResult:
        """Run a single evaluation.
        
        Args:
            treatment: Treatment configuration
            task: Task configuration
            treatment_name: Name of treatment
            
        Returns:
            ExecutionResult
        """
        async with self._get_semaphore():
            # Inject skill if present
            final_prompt, system_prompt = inject_skill(
                task.prompt,
                treatment.skill_path
            )
            
            # Replace variables in prompt
            for key, value in task.variables.items():
                placeholder = f"{{{key}}}"
                final_prompt = final_prompt.replace(placeholder, value)
            
            # Call LLM
            try:
                response = await self.llm_adapter.complete(
                    prompt=final_prompt,
                    system_prompt=system_prompt,
                )
            except LLMError as e:
                # Return error result
                return ExecutionResult(
                    treatment=treatment_name,
                    test=task.name,
                    prompt=final_prompt,
                    response=None,
                    passed=False,
                    evaluator_results=[],
                    timestamp=datetime.utcnow().isoformat()
                )
            
            # Evaluate if evaluator engine is available
            evaluator_results = []
            if self.evaluator_engine and task.evaluators:
                evaluator_results = await self.evaluator_engine.evaluate(
                    response.content,
                    task.evaluators
                )
            
            # Determine if passed
            passed = all(r.passed for r in evaluator_results) if evaluator_results else False
            
            return ExecutionResult(
                treatment=treatment_name,
                test=task.name,
                prompt=final_prompt,
                response=response,
                passed=passed,
                evaluator_results=evaluator_results,
                timestamp=datetime.utcnow().isoformat()
            )
    
    async def xǁExecutionEngineǁrun_single__mutmut_41(
        self,
        treatment: Treatment,
        task: Task,
        treatment_name: str,
    ) -> ExecutionResult:
        """Run a single evaluation.
        
        Args:
            treatment: Treatment configuration
            task: Task configuration
            treatment_name: Name of treatment
            
        Returns:
            ExecutionResult
        """
        async with self._get_semaphore():
            # Inject skill if present
            final_prompt, system_prompt = inject_skill(
                task.prompt,
                treatment.skill_path
            )
            
            # Replace variables in prompt
            for key, value in task.variables.items():
                placeholder = f"{{{key}}}"
                final_prompt = final_prompt.replace(placeholder, value)
            
            # Call LLM
            try:
                response = await self.llm_adapter.complete(
                    prompt=final_prompt,
                    system_prompt=system_prompt,
                )
            except LLMError as e:
                # Return error result
                return ExecutionResult(
                    treatment=treatment_name,
                    test=task.name,
                    prompt=final_prompt,
                    response=None,
                    passed=False,
                    evaluator_results=[],
                    timestamp=datetime.utcnow().isoformat()
                )
            
            # Evaluate if evaluator engine is available
            evaluator_results = []
            if self.evaluator_engine and task.evaluators:
                evaluator_results = await self.evaluator_engine.evaluate(
                    response.content,
                    task.evaluators
                )
            
            # Determine if passed
            passed = all(r.passed for r in evaluator_results) if evaluator_results else True
            
            return ExecutionResult(
                treatment=None,
                test=task.name,
                prompt=final_prompt,
                response=response,
                passed=passed,
                evaluator_results=evaluator_results,
                timestamp=datetime.utcnow().isoformat()
            )
    
    async def xǁExecutionEngineǁrun_single__mutmut_42(
        self,
        treatment: Treatment,
        task: Task,
        treatment_name: str,
    ) -> ExecutionResult:
        """Run a single evaluation.
        
        Args:
            treatment: Treatment configuration
            task: Task configuration
            treatment_name: Name of treatment
            
        Returns:
            ExecutionResult
        """
        async with self._get_semaphore():
            # Inject skill if present
            final_prompt, system_prompt = inject_skill(
                task.prompt,
                treatment.skill_path
            )
            
            # Replace variables in prompt
            for key, value in task.variables.items():
                placeholder = f"{{{key}}}"
                final_prompt = final_prompt.replace(placeholder, value)
            
            # Call LLM
            try:
                response = await self.llm_adapter.complete(
                    prompt=final_prompt,
                    system_prompt=system_prompt,
                )
            except LLMError as e:
                # Return error result
                return ExecutionResult(
                    treatment=treatment_name,
                    test=task.name,
                    prompt=final_prompt,
                    response=None,
                    passed=False,
                    evaluator_results=[],
                    timestamp=datetime.utcnow().isoformat()
                )
            
            # Evaluate if evaluator engine is available
            evaluator_results = []
            if self.evaluator_engine and task.evaluators:
                evaluator_results = await self.evaluator_engine.evaluate(
                    response.content,
                    task.evaluators
                )
            
            # Determine if passed
            passed = all(r.passed for r in evaluator_results) if evaluator_results else True
            
            return ExecutionResult(
                treatment=treatment_name,
                test=None,
                prompt=final_prompt,
                response=response,
                passed=passed,
                evaluator_results=evaluator_results,
                timestamp=datetime.utcnow().isoformat()
            )
    
    async def xǁExecutionEngineǁrun_single__mutmut_43(
        self,
        treatment: Treatment,
        task: Task,
        treatment_name: str,
    ) -> ExecutionResult:
        """Run a single evaluation.
        
        Args:
            treatment: Treatment configuration
            task: Task configuration
            treatment_name: Name of treatment
            
        Returns:
            ExecutionResult
        """
        async with self._get_semaphore():
            # Inject skill if present
            final_prompt, system_prompt = inject_skill(
                task.prompt,
                treatment.skill_path
            )
            
            # Replace variables in prompt
            for key, value in task.variables.items():
                placeholder = f"{{{key}}}"
                final_prompt = final_prompt.replace(placeholder, value)
            
            # Call LLM
            try:
                response = await self.llm_adapter.complete(
                    prompt=final_prompt,
                    system_prompt=system_prompt,
                )
            except LLMError as e:
                # Return error result
                return ExecutionResult(
                    treatment=treatment_name,
                    test=task.name,
                    prompt=final_prompt,
                    response=None,
                    passed=False,
                    evaluator_results=[],
                    timestamp=datetime.utcnow().isoformat()
                )
            
            # Evaluate if evaluator engine is available
            evaluator_results = []
            if self.evaluator_engine and task.evaluators:
                evaluator_results = await self.evaluator_engine.evaluate(
                    response.content,
                    task.evaluators
                )
            
            # Determine if passed
            passed = all(r.passed for r in evaluator_results) if evaluator_results else True
            
            return ExecutionResult(
                treatment=treatment_name,
                test=task.name,
                prompt=None,
                response=response,
                passed=passed,
                evaluator_results=evaluator_results,
                timestamp=datetime.utcnow().isoformat()
            )
    
    async def xǁExecutionEngineǁrun_single__mutmut_44(
        self,
        treatment: Treatment,
        task: Task,
        treatment_name: str,
    ) -> ExecutionResult:
        """Run a single evaluation.
        
        Args:
            treatment: Treatment configuration
            task: Task configuration
            treatment_name: Name of treatment
            
        Returns:
            ExecutionResult
        """
        async with self._get_semaphore():
            # Inject skill if present
            final_prompt, system_prompt = inject_skill(
                task.prompt,
                treatment.skill_path
            )
            
            # Replace variables in prompt
            for key, value in task.variables.items():
                placeholder = f"{{{key}}}"
                final_prompt = final_prompt.replace(placeholder, value)
            
            # Call LLM
            try:
                response = await self.llm_adapter.complete(
                    prompt=final_prompt,
                    system_prompt=system_prompt,
                )
            except LLMError as e:
                # Return error result
                return ExecutionResult(
                    treatment=treatment_name,
                    test=task.name,
                    prompt=final_prompt,
                    response=None,
                    passed=False,
                    evaluator_results=[],
                    timestamp=datetime.utcnow().isoformat()
                )
            
            # Evaluate if evaluator engine is available
            evaluator_results = []
            if self.evaluator_engine and task.evaluators:
                evaluator_results = await self.evaluator_engine.evaluate(
                    response.content,
                    task.evaluators
                )
            
            # Determine if passed
            passed = all(r.passed for r in evaluator_results) if evaluator_results else True
            
            return ExecutionResult(
                treatment=treatment_name,
                test=task.name,
                prompt=final_prompt,
                response=None,
                passed=passed,
                evaluator_results=evaluator_results,
                timestamp=datetime.utcnow().isoformat()
            )
    
    async def xǁExecutionEngineǁrun_single__mutmut_45(
        self,
        treatment: Treatment,
        task: Task,
        treatment_name: str,
    ) -> ExecutionResult:
        """Run a single evaluation.
        
        Args:
            treatment: Treatment configuration
            task: Task configuration
            treatment_name: Name of treatment
            
        Returns:
            ExecutionResult
        """
        async with self._get_semaphore():
            # Inject skill if present
            final_prompt, system_prompt = inject_skill(
                task.prompt,
                treatment.skill_path
            )
            
            # Replace variables in prompt
            for key, value in task.variables.items():
                placeholder = f"{{{key}}}"
                final_prompt = final_prompt.replace(placeholder, value)
            
            # Call LLM
            try:
                response = await self.llm_adapter.complete(
                    prompt=final_prompt,
                    system_prompt=system_prompt,
                )
            except LLMError as e:
                # Return error result
                return ExecutionResult(
                    treatment=treatment_name,
                    test=task.name,
                    prompt=final_prompt,
                    response=None,
                    passed=False,
                    evaluator_results=[],
                    timestamp=datetime.utcnow().isoformat()
                )
            
            # Evaluate if evaluator engine is available
            evaluator_results = []
            if self.evaluator_engine and task.evaluators:
                evaluator_results = await self.evaluator_engine.evaluate(
                    response.content,
                    task.evaluators
                )
            
            # Determine if passed
            passed = all(r.passed for r in evaluator_results) if evaluator_results else True
            
            return ExecutionResult(
                treatment=treatment_name,
                test=task.name,
                prompt=final_prompt,
                response=response,
                passed=None,
                evaluator_results=evaluator_results,
                timestamp=datetime.utcnow().isoformat()
            )
    
    async def xǁExecutionEngineǁrun_single__mutmut_46(
        self,
        treatment: Treatment,
        task: Task,
        treatment_name: str,
    ) -> ExecutionResult:
        """Run a single evaluation.
        
        Args:
            treatment: Treatment configuration
            task: Task configuration
            treatment_name: Name of treatment
            
        Returns:
            ExecutionResult
        """
        async with self._get_semaphore():
            # Inject skill if present
            final_prompt, system_prompt = inject_skill(
                task.prompt,
                treatment.skill_path
            )
            
            # Replace variables in prompt
            for key, value in task.variables.items():
                placeholder = f"{{{key}}}"
                final_prompt = final_prompt.replace(placeholder, value)
            
            # Call LLM
            try:
                response = await self.llm_adapter.complete(
                    prompt=final_prompt,
                    system_prompt=system_prompt,
                )
            except LLMError as e:
                # Return error result
                return ExecutionResult(
                    treatment=treatment_name,
                    test=task.name,
                    prompt=final_prompt,
                    response=None,
                    passed=False,
                    evaluator_results=[],
                    timestamp=datetime.utcnow().isoformat()
                )
            
            # Evaluate if evaluator engine is available
            evaluator_results = []
            if self.evaluator_engine and task.evaluators:
                evaluator_results = await self.evaluator_engine.evaluate(
                    response.content,
                    task.evaluators
                )
            
            # Determine if passed
            passed = all(r.passed for r in evaluator_results) if evaluator_results else True
            
            return ExecutionResult(
                treatment=treatment_name,
                test=task.name,
                prompt=final_prompt,
                response=response,
                passed=passed,
                evaluator_results=None,
                timestamp=datetime.utcnow().isoformat()
            )
    
    async def xǁExecutionEngineǁrun_single__mutmut_47(
        self,
        treatment: Treatment,
        task: Task,
        treatment_name: str,
    ) -> ExecutionResult:
        """Run a single evaluation.
        
        Args:
            treatment: Treatment configuration
            task: Task configuration
            treatment_name: Name of treatment
            
        Returns:
            ExecutionResult
        """
        async with self._get_semaphore():
            # Inject skill if present
            final_prompt, system_prompt = inject_skill(
                task.prompt,
                treatment.skill_path
            )
            
            # Replace variables in prompt
            for key, value in task.variables.items():
                placeholder = f"{{{key}}}"
                final_prompt = final_prompt.replace(placeholder, value)
            
            # Call LLM
            try:
                response = await self.llm_adapter.complete(
                    prompt=final_prompt,
                    system_prompt=system_prompt,
                )
            except LLMError as e:
                # Return error result
                return ExecutionResult(
                    treatment=treatment_name,
                    test=task.name,
                    prompt=final_prompt,
                    response=None,
                    passed=False,
                    evaluator_results=[],
                    timestamp=datetime.utcnow().isoformat()
                )
            
            # Evaluate if evaluator engine is available
            evaluator_results = []
            if self.evaluator_engine and task.evaluators:
                evaluator_results = await self.evaluator_engine.evaluate(
                    response.content,
                    task.evaluators
                )
            
            # Determine if passed
            passed = all(r.passed for r in evaluator_results) if evaluator_results else True
            
            return ExecutionResult(
                treatment=treatment_name,
                test=task.name,
                prompt=final_prompt,
                response=response,
                passed=passed,
                evaluator_results=evaluator_results,
                timestamp=None
            )
    
    async def xǁExecutionEngineǁrun_single__mutmut_48(
        self,
        treatment: Treatment,
        task: Task,
        treatment_name: str,
    ) -> ExecutionResult:
        """Run a single evaluation.
        
        Args:
            treatment: Treatment configuration
            task: Task configuration
            treatment_name: Name of treatment
            
        Returns:
            ExecutionResult
        """
        async with self._get_semaphore():
            # Inject skill if present
            final_prompt, system_prompt = inject_skill(
                task.prompt,
                treatment.skill_path
            )
            
            # Replace variables in prompt
            for key, value in task.variables.items():
                placeholder = f"{{{key}}}"
                final_prompt = final_prompt.replace(placeholder, value)
            
            # Call LLM
            try:
                response = await self.llm_adapter.complete(
                    prompt=final_prompt,
                    system_prompt=system_prompt,
                )
            except LLMError as e:
                # Return error result
                return ExecutionResult(
                    treatment=treatment_name,
                    test=task.name,
                    prompt=final_prompt,
                    response=None,
                    passed=False,
                    evaluator_results=[],
                    timestamp=datetime.utcnow().isoformat()
                )
            
            # Evaluate if evaluator engine is available
            evaluator_results = []
            if self.evaluator_engine and task.evaluators:
                evaluator_results = await self.evaluator_engine.evaluate(
                    response.content,
                    task.evaluators
                )
            
            # Determine if passed
            passed = all(r.passed for r in evaluator_results) if evaluator_results else True
            
            return ExecutionResult(
                test=task.name,
                prompt=final_prompt,
                response=response,
                passed=passed,
                evaluator_results=evaluator_results,
                timestamp=datetime.utcnow().isoformat()
            )
    
    async def xǁExecutionEngineǁrun_single__mutmut_49(
        self,
        treatment: Treatment,
        task: Task,
        treatment_name: str,
    ) -> ExecutionResult:
        """Run a single evaluation.
        
        Args:
            treatment: Treatment configuration
            task: Task configuration
            treatment_name: Name of treatment
            
        Returns:
            ExecutionResult
        """
        async with self._get_semaphore():
            # Inject skill if present
            final_prompt, system_prompt = inject_skill(
                task.prompt,
                treatment.skill_path
            )
            
            # Replace variables in prompt
            for key, value in task.variables.items():
                placeholder = f"{{{key}}}"
                final_prompt = final_prompt.replace(placeholder, value)
            
            # Call LLM
            try:
                response = await self.llm_adapter.complete(
                    prompt=final_prompt,
                    system_prompt=system_prompt,
                )
            except LLMError as e:
                # Return error result
                return ExecutionResult(
                    treatment=treatment_name,
                    test=task.name,
                    prompt=final_prompt,
                    response=None,
                    passed=False,
                    evaluator_results=[],
                    timestamp=datetime.utcnow().isoformat()
                )
            
            # Evaluate if evaluator engine is available
            evaluator_results = []
            if self.evaluator_engine and task.evaluators:
                evaluator_results = await self.evaluator_engine.evaluate(
                    response.content,
                    task.evaluators
                )
            
            # Determine if passed
            passed = all(r.passed for r in evaluator_results) if evaluator_results else True
            
            return ExecutionResult(
                treatment=treatment_name,
                prompt=final_prompt,
                response=response,
                passed=passed,
                evaluator_results=evaluator_results,
                timestamp=datetime.utcnow().isoformat()
            )
    
    async def xǁExecutionEngineǁrun_single__mutmut_50(
        self,
        treatment: Treatment,
        task: Task,
        treatment_name: str,
    ) -> ExecutionResult:
        """Run a single evaluation.
        
        Args:
            treatment: Treatment configuration
            task: Task configuration
            treatment_name: Name of treatment
            
        Returns:
            ExecutionResult
        """
        async with self._get_semaphore():
            # Inject skill if present
            final_prompt, system_prompt = inject_skill(
                task.prompt,
                treatment.skill_path
            )
            
            # Replace variables in prompt
            for key, value in task.variables.items():
                placeholder = f"{{{key}}}"
                final_prompt = final_prompt.replace(placeholder, value)
            
            # Call LLM
            try:
                response = await self.llm_adapter.complete(
                    prompt=final_prompt,
                    system_prompt=system_prompt,
                )
            except LLMError as e:
                # Return error result
                return ExecutionResult(
                    treatment=treatment_name,
                    test=task.name,
                    prompt=final_prompt,
                    response=None,
                    passed=False,
                    evaluator_results=[],
                    timestamp=datetime.utcnow().isoformat()
                )
            
            # Evaluate if evaluator engine is available
            evaluator_results = []
            if self.evaluator_engine and task.evaluators:
                evaluator_results = await self.evaluator_engine.evaluate(
                    response.content,
                    task.evaluators
                )
            
            # Determine if passed
            passed = all(r.passed for r in evaluator_results) if evaluator_results else True
            
            return ExecutionResult(
                treatment=treatment_name,
                test=task.name,
                response=response,
                passed=passed,
                evaluator_results=evaluator_results,
                timestamp=datetime.utcnow().isoformat()
            )
    
    async def xǁExecutionEngineǁrun_single__mutmut_51(
        self,
        treatment: Treatment,
        task: Task,
        treatment_name: str,
    ) -> ExecutionResult:
        """Run a single evaluation.
        
        Args:
            treatment: Treatment configuration
            task: Task configuration
            treatment_name: Name of treatment
            
        Returns:
            ExecutionResult
        """
        async with self._get_semaphore():
            # Inject skill if present
            final_prompt, system_prompt = inject_skill(
                task.prompt,
                treatment.skill_path
            )
            
            # Replace variables in prompt
            for key, value in task.variables.items():
                placeholder = f"{{{key}}}"
                final_prompt = final_prompt.replace(placeholder, value)
            
            # Call LLM
            try:
                response = await self.llm_adapter.complete(
                    prompt=final_prompt,
                    system_prompt=system_prompt,
                )
            except LLMError as e:
                # Return error result
                return ExecutionResult(
                    treatment=treatment_name,
                    test=task.name,
                    prompt=final_prompt,
                    response=None,
                    passed=False,
                    evaluator_results=[],
                    timestamp=datetime.utcnow().isoformat()
                )
            
            # Evaluate if evaluator engine is available
            evaluator_results = []
            if self.evaluator_engine and task.evaluators:
                evaluator_results = await self.evaluator_engine.evaluate(
                    response.content,
                    task.evaluators
                )
            
            # Determine if passed
            passed = all(r.passed for r in evaluator_results) if evaluator_results else True
            
            return ExecutionResult(
                treatment=treatment_name,
                test=task.name,
                prompt=final_prompt,
                passed=passed,
                evaluator_results=evaluator_results,
                timestamp=datetime.utcnow().isoformat()
            )
    
    async def xǁExecutionEngineǁrun_single__mutmut_52(
        self,
        treatment: Treatment,
        task: Task,
        treatment_name: str,
    ) -> ExecutionResult:
        """Run a single evaluation.
        
        Args:
            treatment: Treatment configuration
            task: Task configuration
            treatment_name: Name of treatment
            
        Returns:
            ExecutionResult
        """
        async with self._get_semaphore():
            # Inject skill if present
            final_prompt, system_prompt = inject_skill(
                task.prompt,
                treatment.skill_path
            )
            
            # Replace variables in prompt
            for key, value in task.variables.items():
                placeholder = f"{{{key}}}"
                final_prompt = final_prompt.replace(placeholder, value)
            
            # Call LLM
            try:
                response = await self.llm_adapter.complete(
                    prompt=final_prompt,
                    system_prompt=system_prompt,
                )
            except LLMError as e:
                # Return error result
                return ExecutionResult(
                    treatment=treatment_name,
                    test=task.name,
                    prompt=final_prompt,
                    response=None,
                    passed=False,
                    evaluator_results=[],
                    timestamp=datetime.utcnow().isoformat()
                )
            
            # Evaluate if evaluator engine is available
            evaluator_results = []
            if self.evaluator_engine and task.evaluators:
                evaluator_results = await self.evaluator_engine.evaluate(
                    response.content,
                    task.evaluators
                )
            
            # Determine if passed
            passed = all(r.passed for r in evaluator_results) if evaluator_results else True
            
            return ExecutionResult(
                treatment=treatment_name,
                test=task.name,
                prompt=final_prompt,
                response=response,
                evaluator_results=evaluator_results,
                timestamp=datetime.utcnow().isoformat()
            )
    
    async def xǁExecutionEngineǁrun_single__mutmut_53(
        self,
        treatment: Treatment,
        task: Task,
        treatment_name: str,
    ) -> ExecutionResult:
        """Run a single evaluation.
        
        Args:
            treatment: Treatment configuration
            task: Task configuration
            treatment_name: Name of treatment
            
        Returns:
            ExecutionResult
        """
        async with self._get_semaphore():
            # Inject skill if present
            final_prompt, system_prompt = inject_skill(
                task.prompt,
                treatment.skill_path
            )
            
            # Replace variables in prompt
            for key, value in task.variables.items():
                placeholder = f"{{{key}}}"
                final_prompt = final_prompt.replace(placeholder, value)
            
            # Call LLM
            try:
                response = await self.llm_adapter.complete(
                    prompt=final_prompt,
                    system_prompt=system_prompt,
                )
            except LLMError as e:
                # Return error result
                return ExecutionResult(
                    treatment=treatment_name,
                    test=task.name,
                    prompt=final_prompt,
                    response=None,
                    passed=False,
                    evaluator_results=[],
                    timestamp=datetime.utcnow().isoformat()
                )
            
            # Evaluate if evaluator engine is available
            evaluator_results = []
            if self.evaluator_engine and task.evaluators:
                evaluator_results = await self.evaluator_engine.evaluate(
                    response.content,
                    task.evaluators
                )
            
            # Determine if passed
            passed = all(r.passed for r in evaluator_results) if evaluator_results else True
            
            return ExecutionResult(
                treatment=treatment_name,
                test=task.name,
                prompt=final_prompt,
                response=response,
                passed=passed,
                timestamp=datetime.utcnow().isoformat()
            )
    
    async def xǁExecutionEngineǁrun_single__mutmut_54(
        self,
        treatment: Treatment,
        task: Task,
        treatment_name: str,
    ) -> ExecutionResult:
        """Run a single evaluation.
        
        Args:
            treatment: Treatment configuration
            task: Task configuration
            treatment_name: Name of treatment
            
        Returns:
            ExecutionResult
        """
        async with self._get_semaphore():
            # Inject skill if present
            final_prompt, system_prompt = inject_skill(
                task.prompt,
                treatment.skill_path
            )
            
            # Replace variables in prompt
            for key, value in task.variables.items():
                placeholder = f"{{{key}}}"
                final_prompt = final_prompt.replace(placeholder, value)
            
            # Call LLM
            try:
                response = await self.llm_adapter.complete(
                    prompt=final_prompt,
                    system_prompt=system_prompt,
                )
            except LLMError as e:
                # Return error result
                return ExecutionResult(
                    treatment=treatment_name,
                    test=task.name,
                    prompt=final_prompt,
                    response=None,
                    passed=False,
                    evaluator_results=[],
                    timestamp=datetime.utcnow().isoformat()
                )
            
            # Evaluate if evaluator engine is available
            evaluator_results = []
            if self.evaluator_engine and task.evaluators:
                evaluator_results = await self.evaluator_engine.evaluate(
                    response.content,
                    task.evaluators
                )
            
            # Determine if passed
            passed = all(r.passed for r in evaluator_results) if evaluator_results else True
            
            return ExecutionResult(
                treatment=treatment_name,
                test=task.name,
                prompt=final_prompt,
                response=response,
                passed=passed,
                evaluator_results=evaluator_results,
                )
    
    xǁExecutionEngineǁrun_single__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
    'xǁExecutionEngineǁrun_single__mutmut_1': xǁExecutionEngineǁrun_single__mutmut_1, 
        'xǁExecutionEngineǁrun_single__mutmut_2': xǁExecutionEngineǁrun_single__mutmut_2, 
        'xǁExecutionEngineǁrun_single__mutmut_3': xǁExecutionEngineǁrun_single__mutmut_3, 
        'xǁExecutionEngineǁrun_single__mutmut_4': xǁExecutionEngineǁrun_single__mutmut_4, 
        'xǁExecutionEngineǁrun_single__mutmut_5': xǁExecutionEngineǁrun_single__mutmut_5, 
        'xǁExecutionEngineǁrun_single__mutmut_6': xǁExecutionEngineǁrun_single__mutmut_6, 
        'xǁExecutionEngineǁrun_single__mutmut_7': xǁExecutionEngineǁrun_single__mutmut_7, 
        'xǁExecutionEngineǁrun_single__mutmut_8': xǁExecutionEngineǁrun_single__mutmut_8, 
        'xǁExecutionEngineǁrun_single__mutmut_9': xǁExecutionEngineǁrun_single__mutmut_9, 
        'xǁExecutionEngineǁrun_single__mutmut_10': xǁExecutionEngineǁrun_single__mutmut_10, 
        'xǁExecutionEngineǁrun_single__mutmut_11': xǁExecutionEngineǁrun_single__mutmut_11, 
        'xǁExecutionEngineǁrun_single__mutmut_12': xǁExecutionEngineǁrun_single__mutmut_12, 
        'xǁExecutionEngineǁrun_single__mutmut_13': xǁExecutionEngineǁrun_single__mutmut_13, 
        'xǁExecutionEngineǁrun_single__mutmut_14': xǁExecutionEngineǁrun_single__mutmut_14, 
        'xǁExecutionEngineǁrun_single__mutmut_15': xǁExecutionEngineǁrun_single__mutmut_15, 
        'xǁExecutionEngineǁrun_single__mutmut_16': xǁExecutionEngineǁrun_single__mutmut_16, 
        'xǁExecutionEngineǁrun_single__mutmut_17': xǁExecutionEngineǁrun_single__mutmut_17, 
        'xǁExecutionEngineǁrun_single__mutmut_18': xǁExecutionEngineǁrun_single__mutmut_18, 
        'xǁExecutionEngineǁrun_single__mutmut_19': xǁExecutionEngineǁrun_single__mutmut_19, 
        'xǁExecutionEngineǁrun_single__mutmut_20': xǁExecutionEngineǁrun_single__mutmut_20, 
        'xǁExecutionEngineǁrun_single__mutmut_21': xǁExecutionEngineǁrun_single__mutmut_21, 
        'xǁExecutionEngineǁrun_single__mutmut_22': xǁExecutionEngineǁrun_single__mutmut_22, 
        'xǁExecutionEngineǁrun_single__mutmut_23': xǁExecutionEngineǁrun_single__mutmut_23, 
        'xǁExecutionEngineǁrun_single__mutmut_24': xǁExecutionEngineǁrun_single__mutmut_24, 
        'xǁExecutionEngineǁrun_single__mutmut_25': xǁExecutionEngineǁrun_single__mutmut_25, 
        'xǁExecutionEngineǁrun_single__mutmut_26': xǁExecutionEngineǁrun_single__mutmut_26, 
        'xǁExecutionEngineǁrun_single__mutmut_27': xǁExecutionEngineǁrun_single__mutmut_27, 
        'xǁExecutionEngineǁrun_single__mutmut_28': xǁExecutionEngineǁrun_single__mutmut_28, 
        'xǁExecutionEngineǁrun_single__mutmut_29': xǁExecutionEngineǁrun_single__mutmut_29, 
        'xǁExecutionEngineǁrun_single__mutmut_30': xǁExecutionEngineǁrun_single__mutmut_30, 
        'xǁExecutionEngineǁrun_single__mutmut_31': xǁExecutionEngineǁrun_single__mutmut_31, 
        'xǁExecutionEngineǁrun_single__mutmut_32': xǁExecutionEngineǁrun_single__mutmut_32, 
        'xǁExecutionEngineǁrun_single__mutmut_33': xǁExecutionEngineǁrun_single__mutmut_33, 
        'xǁExecutionEngineǁrun_single__mutmut_34': xǁExecutionEngineǁrun_single__mutmut_34, 
        'xǁExecutionEngineǁrun_single__mutmut_35': xǁExecutionEngineǁrun_single__mutmut_35, 
        'xǁExecutionEngineǁrun_single__mutmut_36': xǁExecutionEngineǁrun_single__mutmut_36, 
        'xǁExecutionEngineǁrun_single__mutmut_37': xǁExecutionEngineǁrun_single__mutmut_37, 
        'xǁExecutionEngineǁrun_single__mutmut_38': xǁExecutionEngineǁrun_single__mutmut_38, 
        'xǁExecutionEngineǁrun_single__mutmut_39': xǁExecutionEngineǁrun_single__mutmut_39, 
        'xǁExecutionEngineǁrun_single__mutmut_40': xǁExecutionEngineǁrun_single__mutmut_40, 
        'xǁExecutionEngineǁrun_single__mutmut_41': xǁExecutionEngineǁrun_single__mutmut_41, 
        'xǁExecutionEngineǁrun_single__mutmut_42': xǁExecutionEngineǁrun_single__mutmut_42, 
        'xǁExecutionEngineǁrun_single__mutmut_43': xǁExecutionEngineǁrun_single__mutmut_43, 
        'xǁExecutionEngineǁrun_single__mutmut_44': xǁExecutionEngineǁrun_single__mutmut_44, 
        'xǁExecutionEngineǁrun_single__mutmut_45': xǁExecutionEngineǁrun_single__mutmut_45, 
        'xǁExecutionEngineǁrun_single__mutmut_46': xǁExecutionEngineǁrun_single__mutmut_46, 
        'xǁExecutionEngineǁrun_single__mutmut_47': xǁExecutionEngineǁrun_single__mutmut_47, 
        'xǁExecutionEngineǁrun_single__mutmut_48': xǁExecutionEngineǁrun_single__mutmut_48, 
        'xǁExecutionEngineǁrun_single__mutmut_49': xǁExecutionEngineǁrun_single__mutmut_49, 
        'xǁExecutionEngineǁrun_single__mutmut_50': xǁExecutionEngineǁrun_single__mutmut_50, 
        'xǁExecutionEngineǁrun_single__mutmut_51': xǁExecutionEngineǁrun_single__mutmut_51, 
        'xǁExecutionEngineǁrun_single__mutmut_52': xǁExecutionEngineǁrun_single__mutmut_52, 
        'xǁExecutionEngineǁrun_single__mutmut_53': xǁExecutionEngineǁrun_single__mutmut_53, 
        'xǁExecutionEngineǁrun_single__mutmut_54': xǁExecutionEngineǁrun_single__mutmut_54
    }
    xǁExecutionEngineǁrun_single__mutmut_orig.__name__ = 'xǁExecutionEngineǁrun_single'
    
    async def run_all(
        self,
        treatments: list[str],
        progress: bool = False,
    ) -> list[ExecutionResult]:
        args = [treatments, progress]# type: ignore
        kwargs = {}# type: ignore
        return await _mutmut_trampoline(object.__getattribute__(self, 'xǁExecutionEngineǁrun_all__mutmut_orig'), object.__getattribute__(self, 'xǁExecutionEngineǁrun_all__mutmut_mutants'), args, kwargs, self)
    
    async def xǁExecutionEngineǁrun_all__mutmut_orig(
        self,
        treatments: list[str],
        progress: bool = False,
    ) -> list[ExecutionResult]:
        """Run all treatments and tasks.
        
        Args:
            treatments: List of treatment names to run
            progress: Show progress (not implemented yet)
            
        Returns:
            List of ExecutionResults
        """
        results = []
        
        # Get actual treatments from config
        available_treatments = {
            name: self.config.treatments.get(name, Treatment(skill_path=None))
            for name in treatments
        }
        
        # Add CONTROL if not present
        if "CONTROL" not in available_treatments:
            available_treatments["CONTROL"] = Treatment(skill_path=None)
        
        # Create tasks for each combination
        tasks_to_run = []
        for treatment_name in available_treatments:
            for task in self.config.tests:
                tasks_to_run.append((
                    available_treatments[treatment_name],
                    task,
                    treatment_name
                ))
        
        # Run with repetitions
        all_results = []
        repetitions = self.config.execution.repetitions
        
        for rep in range(repetitions):
            # Run all tasks
            coroutines = [
                self.run_single(treatment, task, treatment_name)
                for treatment, task, treatment_name in tasks_to_run
            ]
            
            # Execute concurrently (limited by semaphore)
            results = await asyncio.gather(*coroutines, return_exceptions=True)
            
            # Handle exceptions
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    # Create error result with minimal response
                    treatment, task, treatment_name = tasks_to_run[i]
                    error_result = ExecutionResult(
                        treatment=treatment_name,
                        test=task.name,
                        prompt=task.prompt,
                        response=LLMResponse(
                            content="",
                            model="error",
                            provider="error",
                            duration_ms=0,
                            raw_response={"error": str(result)}
                        ),
                        passed=False,
                        evaluator_results=[],
                        timestamp=datetime.utcnow().isoformat()
                    )
                    all_results.append(error_result)
                else:
                    all_results.append(result)
        
        return all_results
    
    async def xǁExecutionEngineǁrun_all__mutmut_1(
        self,
        treatments: list[str],
        progress: bool = True,
    ) -> list[ExecutionResult]:
        """Run all treatments and tasks.
        
        Args:
            treatments: List of treatment names to run
            progress: Show progress (not implemented yet)
            
        Returns:
            List of ExecutionResults
        """
        results = []
        
        # Get actual treatments from config
        available_treatments = {
            name: self.config.treatments.get(name, Treatment(skill_path=None))
            for name in treatments
        }
        
        # Add CONTROL if not present
        if "CONTROL" not in available_treatments:
            available_treatments["CONTROL"] = Treatment(skill_path=None)
        
        # Create tasks for each combination
        tasks_to_run = []
        for treatment_name in available_treatments:
            for task in self.config.tests:
                tasks_to_run.append((
                    available_treatments[treatment_name],
                    task,
                    treatment_name
                ))
        
        # Run with repetitions
        all_results = []
        repetitions = self.config.execution.repetitions
        
        for rep in range(repetitions):
            # Run all tasks
            coroutines = [
                self.run_single(treatment, task, treatment_name)
                for treatment, task, treatment_name in tasks_to_run
            ]
            
            # Execute concurrently (limited by semaphore)
            results = await asyncio.gather(*coroutines, return_exceptions=True)
            
            # Handle exceptions
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    # Create error result with minimal response
                    treatment, task, treatment_name = tasks_to_run[i]
                    error_result = ExecutionResult(
                        treatment=treatment_name,
                        test=task.name,
                        prompt=task.prompt,
                        response=LLMResponse(
                            content="",
                            model="error",
                            provider="error",
                            duration_ms=0,
                            raw_response={"error": str(result)}
                        ),
                        passed=False,
                        evaluator_results=[],
                        timestamp=datetime.utcnow().isoformat()
                    )
                    all_results.append(error_result)
                else:
                    all_results.append(result)
        
        return all_results
    
    async def xǁExecutionEngineǁrun_all__mutmut_2(
        self,
        treatments: list[str],
        progress: bool = False,
    ) -> list[ExecutionResult]:
        """Run all treatments and tasks.
        
        Args:
            treatments: List of treatment names to run
            progress: Show progress (not implemented yet)
            
        Returns:
            List of ExecutionResults
        """
        results = None
        
        # Get actual treatments from config
        available_treatments = {
            name: self.config.treatments.get(name, Treatment(skill_path=None))
            for name in treatments
        }
        
        # Add CONTROL if not present
        if "CONTROL" not in available_treatments:
            available_treatments["CONTROL"] = Treatment(skill_path=None)
        
        # Create tasks for each combination
        tasks_to_run = []
        for treatment_name in available_treatments:
            for task in self.config.tests:
                tasks_to_run.append((
                    available_treatments[treatment_name],
                    task,
                    treatment_name
                ))
        
        # Run with repetitions
        all_results = []
        repetitions = self.config.execution.repetitions
        
        for rep in range(repetitions):
            # Run all tasks
            coroutines = [
                self.run_single(treatment, task, treatment_name)
                for treatment, task, treatment_name in tasks_to_run
            ]
            
            # Execute concurrently (limited by semaphore)
            results = await asyncio.gather(*coroutines, return_exceptions=True)
            
            # Handle exceptions
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    # Create error result with minimal response
                    treatment, task, treatment_name = tasks_to_run[i]
                    error_result = ExecutionResult(
                        treatment=treatment_name,
                        test=task.name,
                        prompt=task.prompt,
                        response=LLMResponse(
                            content="",
                            model="error",
                            provider="error",
                            duration_ms=0,
                            raw_response={"error": str(result)}
                        ),
                        passed=False,
                        evaluator_results=[],
                        timestamp=datetime.utcnow().isoformat()
                    )
                    all_results.append(error_result)
                else:
                    all_results.append(result)
        
        return all_results
    
    async def xǁExecutionEngineǁrun_all__mutmut_3(
        self,
        treatments: list[str],
        progress: bool = False,
    ) -> list[ExecutionResult]:
        """Run all treatments and tasks.
        
        Args:
            treatments: List of treatment names to run
            progress: Show progress (not implemented yet)
            
        Returns:
            List of ExecutionResults
        """
        results = []
        
        # Get actual treatments from config
        available_treatments = None
        
        # Add CONTROL if not present
        if "CONTROL" not in available_treatments:
            available_treatments["CONTROL"] = Treatment(skill_path=None)
        
        # Create tasks for each combination
        tasks_to_run = []
        for treatment_name in available_treatments:
            for task in self.config.tests:
                tasks_to_run.append((
                    available_treatments[treatment_name],
                    task,
                    treatment_name
                ))
        
        # Run with repetitions
        all_results = []
        repetitions = self.config.execution.repetitions
        
        for rep in range(repetitions):
            # Run all tasks
            coroutines = [
                self.run_single(treatment, task, treatment_name)
                for treatment, task, treatment_name in tasks_to_run
            ]
            
            # Execute concurrently (limited by semaphore)
            results = await asyncio.gather(*coroutines, return_exceptions=True)
            
            # Handle exceptions
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    # Create error result with minimal response
                    treatment, task, treatment_name = tasks_to_run[i]
                    error_result = ExecutionResult(
                        treatment=treatment_name,
                        test=task.name,
                        prompt=task.prompt,
                        response=LLMResponse(
                            content="",
                            model="error",
                            provider="error",
                            duration_ms=0,
                            raw_response={"error": str(result)}
                        ),
                        passed=False,
                        evaluator_results=[],
                        timestamp=datetime.utcnow().isoformat()
                    )
                    all_results.append(error_result)
                else:
                    all_results.append(result)
        
        return all_results
    
    async def xǁExecutionEngineǁrun_all__mutmut_4(
        self,
        treatments: list[str],
        progress: bool = False,
    ) -> list[ExecutionResult]:
        """Run all treatments and tasks.
        
        Args:
            treatments: List of treatment names to run
            progress: Show progress (not implemented yet)
            
        Returns:
            List of ExecutionResults
        """
        results = []
        
        # Get actual treatments from config
        available_treatments = {
            name: self.config.treatments.get(None, Treatment(skill_path=None))
            for name in treatments
        }
        
        # Add CONTROL if not present
        if "CONTROL" not in available_treatments:
            available_treatments["CONTROL"] = Treatment(skill_path=None)
        
        # Create tasks for each combination
        tasks_to_run = []
        for treatment_name in available_treatments:
            for task in self.config.tests:
                tasks_to_run.append((
                    available_treatments[treatment_name],
                    task,
                    treatment_name
                ))
        
        # Run with repetitions
        all_results = []
        repetitions = self.config.execution.repetitions
        
        for rep in range(repetitions):
            # Run all tasks
            coroutines = [
                self.run_single(treatment, task, treatment_name)
                for treatment, task, treatment_name in tasks_to_run
            ]
            
            # Execute concurrently (limited by semaphore)
            results = await asyncio.gather(*coroutines, return_exceptions=True)
            
            # Handle exceptions
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    # Create error result with minimal response
                    treatment, task, treatment_name = tasks_to_run[i]
                    error_result = ExecutionResult(
                        treatment=treatment_name,
                        test=task.name,
                        prompt=task.prompt,
                        response=LLMResponse(
                            content="",
                            model="error",
                            provider="error",
                            duration_ms=0,
                            raw_response={"error": str(result)}
                        ),
                        passed=False,
                        evaluator_results=[],
                        timestamp=datetime.utcnow().isoformat()
                    )
                    all_results.append(error_result)
                else:
                    all_results.append(result)
        
        return all_results
    
    async def xǁExecutionEngineǁrun_all__mutmut_5(
        self,
        treatments: list[str],
        progress: bool = False,
    ) -> list[ExecutionResult]:
        """Run all treatments and tasks.
        
        Args:
            treatments: List of treatment names to run
            progress: Show progress (not implemented yet)
            
        Returns:
            List of ExecutionResults
        """
        results = []
        
        # Get actual treatments from config
        available_treatments = {
            name: self.config.treatments.get(name, None)
            for name in treatments
        }
        
        # Add CONTROL if not present
        if "CONTROL" not in available_treatments:
            available_treatments["CONTROL"] = Treatment(skill_path=None)
        
        # Create tasks for each combination
        tasks_to_run = []
        for treatment_name in available_treatments:
            for task in self.config.tests:
                tasks_to_run.append((
                    available_treatments[treatment_name],
                    task,
                    treatment_name
                ))
        
        # Run with repetitions
        all_results = []
        repetitions = self.config.execution.repetitions
        
        for rep in range(repetitions):
            # Run all tasks
            coroutines = [
                self.run_single(treatment, task, treatment_name)
                for treatment, task, treatment_name in tasks_to_run
            ]
            
            # Execute concurrently (limited by semaphore)
            results = await asyncio.gather(*coroutines, return_exceptions=True)
            
            # Handle exceptions
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    # Create error result with minimal response
                    treatment, task, treatment_name = tasks_to_run[i]
                    error_result = ExecutionResult(
                        treatment=treatment_name,
                        test=task.name,
                        prompt=task.prompt,
                        response=LLMResponse(
                            content="",
                            model="error",
                            provider="error",
                            duration_ms=0,
                            raw_response={"error": str(result)}
                        ),
                        passed=False,
                        evaluator_results=[],
                        timestamp=datetime.utcnow().isoformat()
                    )
                    all_results.append(error_result)
                else:
                    all_results.append(result)
        
        return all_results
    
    async def xǁExecutionEngineǁrun_all__mutmut_6(
        self,
        treatments: list[str],
        progress: bool = False,
    ) -> list[ExecutionResult]:
        """Run all treatments and tasks.
        
        Args:
            treatments: List of treatment names to run
            progress: Show progress (not implemented yet)
            
        Returns:
            List of ExecutionResults
        """
        results = []
        
        # Get actual treatments from config
        available_treatments = {
            name: self.config.treatments.get(Treatment(skill_path=None))
            for name in treatments
        }
        
        # Add CONTROL if not present
        if "CONTROL" not in available_treatments:
            available_treatments["CONTROL"] = Treatment(skill_path=None)
        
        # Create tasks for each combination
        tasks_to_run = []
        for treatment_name in available_treatments:
            for task in self.config.tests:
                tasks_to_run.append((
                    available_treatments[treatment_name],
                    task,
                    treatment_name
                ))
        
        # Run with repetitions
        all_results = []
        repetitions = self.config.execution.repetitions
        
        for rep in range(repetitions):
            # Run all tasks
            coroutines = [
                self.run_single(treatment, task, treatment_name)
                for treatment, task, treatment_name in tasks_to_run
            ]
            
            # Execute concurrently (limited by semaphore)
            results = await asyncio.gather(*coroutines, return_exceptions=True)
            
            # Handle exceptions
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    # Create error result with minimal response
                    treatment, task, treatment_name = tasks_to_run[i]
                    error_result = ExecutionResult(
                        treatment=treatment_name,
                        test=task.name,
                        prompt=task.prompt,
                        response=LLMResponse(
                            content="",
                            model="error",
                            provider="error",
                            duration_ms=0,
                            raw_response={"error": str(result)}
                        ),
                        passed=False,
                        evaluator_results=[],
                        timestamp=datetime.utcnow().isoformat()
                    )
                    all_results.append(error_result)
                else:
                    all_results.append(result)
        
        return all_results
    
    async def xǁExecutionEngineǁrun_all__mutmut_7(
        self,
        treatments: list[str],
        progress: bool = False,
    ) -> list[ExecutionResult]:
        """Run all treatments and tasks.
        
        Args:
            treatments: List of treatment names to run
            progress: Show progress (not implemented yet)
            
        Returns:
            List of ExecutionResults
        """
        results = []
        
        # Get actual treatments from config
        available_treatments = {
            name: self.config.treatments.get(name, )
            for name in treatments
        }
        
        # Add CONTROL if not present
        if "CONTROL" not in available_treatments:
            available_treatments["CONTROL"] = Treatment(skill_path=None)
        
        # Create tasks for each combination
        tasks_to_run = []
        for treatment_name in available_treatments:
            for task in self.config.tests:
                tasks_to_run.append((
                    available_treatments[treatment_name],
                    task,
                    treatment_name
                ))
        
        # Run with repetitions
        all_results = []
        repetitions = self.config.execution.repetitions
        
        for rep in range(repetitions):
            # Run all tasks
            coroutines = [
                self.run_single(treatment, task, treatment_name)
                for treatment, task, treatment_name in tasks_to_run
            ]
            
            # Execute concurrently (limited by semaphore)
            results = await asyncio.gather(*coroutines, return_exceptions=True)
            
            # Handle exceptions
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    # Create error result with minimal response
                    treatment, task, treatment_name = tasks_to_run[i]
                    error_result = ExecutionResult(
                        treatment=treatment_name,
                        test=task.name,
                        prompt=task.prompt,
                        response=LLMResponse(
                            content="",
                            model="error",
                            provider="error",
                            duration_ms=0,
                            raw_response={"error": str(result)}
                        ),
                        passed=False,
                        evaluator_results=[],
                        timestamp=datetime.utcnow().isoformat()
                    )
                    all_results.append(error_result)
                else:
                    all_results.append(result)
        
        return all_results
    
    async def xǁExecutionEngineǁrun_all__mutmut_8(
        self,
        treatments: list[str],
        progress: bool = False,
    ) -> list[ExecutionResult]:
        """Run all treatments and tasks.
        
        Args:
            treatments: List of treatment names to run
            progress: Show progress (not implemented yet)
            
        Returns:
            List of ExecutionResults
        """
        results = []
        
        # Get actual treatments from config
        available_treatments = {
            name: self.config.treatments.get(name, Treatment(skill_path=None))
            for name in treatments
        }
        
        # Add CONTROL if not present
        if "XXCONTROLXX" not in available_treatments:
            available_treatments["CONTROL"] = Treatment(skill_path=None)
        
        # Create tasks for each combination
        tasks_to_run = []
        for treatment_name in available_treatments:
            for task in self.config.tests:
                tasks_to_run.append((
                    available_treatments[treatment_name],
                    task,
                    treatment_name
                ))
        
        # Run with repetitions
        all_results = []
        repetitions = self.config.execution.repetitions
        
        for rep in range(repetitions):
            # Run all tasks
            coroutines = [
                self.run_single(treatment, task, treatment_name)
                for treatment, task, treatment_name in tasks_to_run
            ]
            
            # Execute concurrently (limited by semaphore)
            results = await asyncio.gather(*coroutines, return_exceptions=True)
            
            # Handle exceptions
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    # Create error result with minimal response
                    treatment, task, treatment_name = tasks_to_run[i]
                    error_result = ExecutionResult(
                        treatment=treatment_name,
                        test=task.name,
                        prompt=task.prompt,
                        response=LLMResponse(
                            content="",
                            model="error",
                            provider="error",
                            duration_ms=0,
                            raw_response={"error": str(result)}
                        ),
                        passed=False,
                        evaluator_results=[],
                        timestamp=datetime.utcnow().isoformat()
                    )
                    all_results.append(error_result)
                else:
                    all_results.append(result)
        
        return all_results
    
    async def xǁExecutionEngineǁrun_all__mutmut_9(
        self,
        treatments: list[str],
        progress: bool = False,
    ) -> list[ExecutionResult]:
        """Run all treatments and tasks.
        
        Args:
            treatments: List of treatment names to run
            progress: Show progress (not implemented yet)
            
        Returns:
            List of ExecutionResults
        """
        results = []
        
        # Get actual treatments from config
        available_treatments = {
            name: self.config.treatments.get(name, Treatment(skill_path=None))
            for name in treatments
        }
        
        # Add CONTROL if not present
        if "control" not in available_treatments:
            available_treatments["CONTROL"] = Treatment(skill_path=None)
        
        # Create tasks for each combination
        tasks_to_run = []
        for treatment_name in available_treatments:
            for task in self.config.tests:
                tasks_to_run.append((
                    available_treatments[treatment_name],
                    task,
                    treatment_name
                ))
        
        # Run with repetitions
        all_results = []
        repetitions = self.config.execution.repetitions
        
        for rep in range(repetitions):
            # Run all tasks
            coroutines = [
                self.run_single(treatment, task, treatment_name)
                for treatment, task, treatment_name in tasks_to_run
            ]
            
            # Execute concurrently (limited by semaphore)
            results = await asyncio.gather(*coroutines, return_exceptions=True)
            
            # Handle exceptions
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    # Create error result with minimal response
                    treatment, task, treatment_name = tasks_to_run[i]
                    error_result = ExecutionResult(
                        treatment=treatment_name,
                        test=task.name,
                        prompt=task.prompt,
                        response=LLMResponse(
                            content="",
                            model="error",
                            provider="error",
                            duration_ms=0,
                            raw_response={"error": str(result)}
                        ),
                        passed=False,
                        evaluator_results=[],
                        timestamp=datetime.utcnow().isoformat()
                    )
                    all_results.append(error_result)
                else:
                    all_results.append(result)
        
        return all_results
    
    async def xǁExecutionEngineǁrun_all__mutmut_10(
        self,
        treatments: list[str],
        progress: bool = False,
    ) -> list[ExecutionResult]:
        """Run all treatments and tasks.
        
        Args:
            treatments: List of treatment names to run
            progress: Show progress (not implemented yet)
            
        Returns:
            List of ExecutionResults
        """
        results = []
        
        # Get actual treatments from config
        available_treatments = {
            name: self.config.treatments.get(name, Treatment(skill_path=None))
            for name in treatments
        }
        
        # Add CONTROL if not present
        if "CONTROL" in available_treatments:
            available_treatments["CONTROL"] = Treatment(skill_path=None)
        
        # Create tasks for each combination
        tasks_to_run = []
        for treatment_name in available_treatments:
            for task in self.config.tests:
                tasks_to_run.append((
                    available_treatments[treatment_name],
                    task,
                    treatment_name
                ))
        
        # Run with repetitions
        all_results = []
        repetitions = self.config.execution.repetitions
        
        for rep in range(repetitions):
            # Run all tasks
            coroutines = [
                self.run_single(treatment, task, treatment_name)
                for treatment, task, treatment_name in tasks_to_run
            ]
            
            # Execute concurrently (limited by semaphore)
            results = await asyncio.gather(*coroutines, return_exceptions=True)
            
            # Handle exceptions
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    # Create error result with minimal response
                    treatment, task, treatment_name = tasks_to_run[i]
                    error_result = ExecutionResult(
                        treatment=treatment_name,
                        test=task.name,
                        prompt=task.prompt,
                        response=LLMResponse(
                            content="",
                            model="error",
                            provider="error",
                            duration_ms=0,
                            raw_response={"error": str(result)}
                        ),
                        passed=False,
                        evaluator_results=[],
                        timestamp=datetime.utcnow().isoformat()
                    )
                    all_results.append(error_result)
                else:
                    all_results.append(result)
        
        return all_results
    
    async def xǁExecutionEngineǁrun_all__mutmut_11(
        self,
        treatments: list[str],
        progress: bool = False,
    ) -> list[ExecutionResult]:
        """Run all treatments and tasks.
        
        Args:
            treatments: List of treatment names to run
            progress: Show progress (not implemented yet)
            
        Returns:
            List of ExecutionResults
        """
        results = []
        
        # Get actual treatments from config
        available_treatments = {
            name: self.config.treatments.get(name, Treatment(skill_path=None))
            for name in treatments
        }
        
        # Add CONTROL if not present
        if "CONTROL" not in available_treatments:
            available_treatments["CONTROL"] = None
        
        # Create tasks for each combination
        tasks_to_run = []
        for treatment_name in available_treatments:
            for task in self.config.tests:
                tasks_to_run.append((
                    available_treatments[treatment_name],
                    task,
                    treatment_name
                ))
        
        # Run with repetitions
        all_results = []
        repetitions = self.config.execution.repetitions
        
        for rep in range(repetitions):
            # Run all tasks
            coroutines = [
                self.run_single(treatment, task, treatment_name)
                for treatment, task, treatment_name in tasks_to_run
            ]
            
            # Execute concurrently (limited by semaphore)
            results = await asyncio.gather(*coroutines, return_exceptions=True)
            
            # Handle exceptions
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    # Create error result with minimal response
                    treatment, task, treatment_name = tasks_to_run[i]
                    error_result = ExecutionResult(
                        treatment=treatment_name,
                        test=task.name,
                        prompt=task.prompt,
                        response=LLMResponse(
                            content="",
                            model="error",
                            provider="error",
                            duration_ms=0,
                            raw_response={"error": str(result)}
                        ),
                        passed=False,
                        evaluator_results=[],
                        timestamp=datetime.utcnow().isoformat()
                    )
                    all_results.append(error_result)
                else:
                    all_results.append(result)
        
        return all_results
    
    async def xǁExecutionEngineǁrun_all__mutmut_12(
        self,
        treatments: list[str],
        progress: bool = False,
    ) -> list[ExecutionResult]:
        """Run all treatments and tasks.
        
        Args:
            treatments: List of treatment names to run
            progress: Show progress (not implemented yet)
            
        Returns:
            List of ExecutionResults
        """
        results = []
        
        # Get actual treatments from config
        available_treatments = {
            name: self.config.treatments.get(name, Treatment(skill_path=None))
            for name in treatments
        }
        
        # Add CONTROL if not present
        if "CONTROL" not in available_treatments:
            available_treatments["XXCONTROLXX"] = Treatment(skill_path=None)
        
        # Create tasks for each combination
        tasks_to_run = []
        for treatment_name in available_treatments:
            for task in self.config.tests:
                tasks_to_run.append((
                    available_treatments[treatment_name],
                    task,
                    treatment_name
                ))
        
        # Run with repetitions
        all_results = []
        repetitions = self.config.execution.repetitions
        
        for rep in range(repetitions):
            # Run all tasks
            coroutines = [
                self.run_single(treatment, task, treatment_name)
                for treatment, task, treatment_name in tasks_to_run
            ]
            
            # Execute concurrently (limited by semaphore)
            results = await asyncio.gather(*coroutines, return_exceptions=True)
            
            # Handle exceptions
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    # Create error result with minimal response
                    treatment, task, treatment_name = tasks_to_run[i]
                    error_result = ExecutionResult(
                        treatment=treatment_name,
                        test=task.name,
                        prompt=task.prompt,
                        response=LLMResponse(
                            content="",
                            model="error",
                            provider="error",
                            duration_ms=0,
                            raw_response={"error": str(result)}
                        ),
                        passed=False,
                        evaluator_results=[],
                        timestamp=datetime.utcnow().isoformat()
                    )
                    all_results.append(error_result)
                else:
                    all_results.append(result)
        
        return all_results
    
    async def xǁExecutionEngineǁrun_all__mutmut_13(
        self,
        treatments: list[str],
        progress: bool = False,
    ) -> list[ExecutionResult]:
        """Run all treatments and tasks.
        
        Args:
            treatments: List of treatment names to run
            progress: Show progress (not implemented yet)
            
        Returns:
            List of ExecutionResults
        """
        results = []
        
        # Get actual treatments from config
        available_treatments = {
            name: self.config.treatments.get(name, Treatment(skill_path=None))
            for name in treatments
        }
        
        # Add CONTROL if not present
        if "CONTROL" not in available_treatments:
            available_treatments["control"] = Treatment(skill_path=None)
        
        # Create tasks for each combination
        tasks_to_run = []
        for treatment_name in available_treatments:
            for task in self.config.tests:
                tasks_to_run.append((
                    available_treatments[treatment_name],
                    task,
                    treatment_name
                ))
        
        # Run with repetitions
        all_results = []
        repetitions = self.config.execution.repetitions
        
        for rep in range(repetitions):
            # Run all tasks
            coroutines = [
                self.run_single(treatment, task, treatment_name)
                for treatment, task, treatment_name in tasks_to_run
            ]
            
            # Execute concurrently (limited by semaphore)
            results = await asyncio.gather(*coroutines, return_exceptions=True)
            
            # Handle exceptions
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    # Create error result with minimal response
                    treatment, task, treatment_name = tasks_to_run[i]
                    error_result = ExecutionResult(
                        treatment=treatment_name,
                        test=task.name,
                        prompt=task.prompt,
                        response=LLMResponse(
                            content="",
                            model="error",
                            provider="error",
                            duration_ms=0,
                            raw_response={"error": str(result)}
                        ),
                        passed=False,
                        evaluator_results=[],
                        timestamp=datetime.utcnow().isoformat()
                    )
                    all_results.append(error_result)
                else:
                    all_results.append(result)
        
        return all_results
    
    async def xǁExecutionEngineǁrun_all__mutmut_14(
        self,
        treatments: list[str],
        progress: bool = False,
    ) -> list[ExecutionResult]:
        """Run all treatments and tasks.
        
        Args:
            treatments: List of treatment names to run
            progress: Show progress (not implemented yet)
            
        Returns:
            List of ExecutionResults
        """
        results = []
        
        # Get actual treatments from config
        available_treatments = {
            name: self.config.treatments.get(name, Treatment(skill_path=None))
            for name in treatments
        }
        
        # Add CONTROL if not present
        if "CONTROL" not in available_treatments:
            available_treatments["CONTROL"] = Treatment(skill_path=None)
        
        # Create tasks for each combination
        tasks_to_run = None
        for treatment_name in available_treatments:
            for task in self.config.tests:
                tasks_to_run.append((
                    available_treatments[treatment_name],
                    task,
                    treatment_name
                ))
        
        # Run with repetitions
        all_results = []
        repetitions = self.config.execution.repetitions
        
        for rep in range(repetitions):
            # Run all tasks
            coroutines = [
                self.run_single(treatment, task, treatment_name)
                for treatment, task, treatment_name in tasks_to_run
            ]
            
            # Execute concurrently (limited by semaphore)
            results = await asyncio.gather(*coroutines, return_exceptions=True)
            
            # Handle exceptions
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    # Create error result with minimal response
                    treatment, task, treatment_name = tasks_to_run[i]
                    error_result = ExecutionResult(
                        treatment=treatment_name,
                        test=task.name,
                        prompt=task.prompt,
                        response=LLMResponse(
                            content="",
                            model="error",
                            provider="error",
                            duration_ms=0,
                            raw_response={"error": str(result)}
                        ),
                        passed=False,
                        evaluator_results=[],
                        timestamp=datetime.utcnow().isoformat()
                    )
                    all_results.append(error_result)
                else:
                    all_results.append(result)
        
        return all_results
    
    async def xǁExecutionEngineǁrun_all__mutmut_15(
        self,
        treatments: list[str],
        progress: bool = False,
    ) -> list[ExecutionResult]:
        """Run all treatments and tasks.
        
        Args:
            treatments: List of treatment names to run
            progress: Show progress (not implemented yet)
            
        Returns:
            List of ExecutionResults
        """
        results = []
        
        # Get actual treatments from config
        available_treatments = {
            name: self.config.treatments.get(name, Treatment(skill_path=None))
            for name in treatments
        }
        
        # Add CONTROL if not present
        if "CONTROL" not in available_treatments:
            available_treatments["CONTROL"] = Treatment(skill_path=None)
        
        # Create tasks for each combination
        tasks_to_run = []
        for treatment_name in available_treatments:
            for task in self.config.tests:
                tasks_to_run.append(None)
        
        # Run with repetitions
        all_results = []
        repetitions = self.config.execution.repetitions
        
        for rep in range(repetitions):
            # Run all tasks
            coroutines = [
                self.run_single(treatment, task, treatment_name)
                for treatment, task, treatment_name in tasks_to_run
            ]
            
            # Execute concurrently (limited by semaphore)
            results = await asyncio.gather(*coroutines, return_exceptions=True)
            
            # Handle exceptions
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    # Create error result with minimal response
                    treatment, task, treatment_name = tasks_to_run[i]
                    error_result = ExecutionResult(
                        treatment=treatment_name,
                        test=task.name,
                        prompt=task.prompt,
                        response=LLMResponse(
                            content="",
                            model="error",
                            provider="error",
                            duration_ms=0,
                            raw_response={"error": str(result)}
                        ),
                        passed=False,
                        evaluator_results=[],
                        timestamp=datetime.utcnow().isoformat()
                    )
                    all_results.append(error_result)
                else:
                    all_results.append(result)
        
        return all_results
    
    async def xǁExecutionEngineǁrun_all__mutmut_16(
        self,
        treatments: list[str],
        progress: bool = False,
    ) -> list[ExecutionResult]:
        """Run all treatments and tasks.
        
        Args:
            treatments: List of treatment names to run
            progress: Show progress (not implemented yet)
            
        Returns:
            List of ExecutionResults
        """
        results = []
        
        # Get actual treatments from config
        available_treatments = {
            name: self.config.treatments.get(name, Treatment(skill_path=None))
            for name in treatments
        }
        
        # Add CONTROL if not present
        if "CONTROL" not in available_treatments:
            available_treatments["CONTROL"] = Treatment(skill_path=None)
        
        # Create tasks for each combination
        tasks_to_run = []
        for treatment_name in available_treatments:
            for task in self.config.tests:
                tasks_to_run.append((
                    available_treatments[treatment_name],
                    task,
                    treatment_name
                ))
        
        # Run with repetitions
        all_results = None
        repetitions = self.config.execution.repetitions
        
        for rep in range(repetitions):
            # Run all tasks
            coroutines = [
                self.run_single(treatment, task, treatment_name)
                for treatment, task, treatment_name in tasks_to_run
            ]
            
            # Execute concurrently (limited by semaphore)
            results = await asyncio.gather(*coroutines, return_exceptions=True)
            
            # Handle exceptions
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    # Create error result with minimal response
                    treatment, task, treatment_name = tasks_to_run[i]
                    error_result = ExecutionResult(
                        treatment=treatment_name,
                        test=task.name,
                        prompt=task.prompt,
                        response=LLMResponse(
                            content="",
                            model="error",
                            provider="error",
                            duration_ms=0,
                            raw_response={"error": str(result)}
                        ),
                        passed=False,
                        evaluator_results=[],
                        timestamp=datetime.utcnow().isoformat()
                    )
                    all_results.append(error_result)
                else:
                    all_results.append(result)
        
        return all_results
    
    async def xǁExecutionEngineǁrun_all__mutmut_17(
        self,
        treatments: list[str],
        progress: bool = False,
    ) -> list[ExecutionResult]:
        """Run all treatments and tasks.
        
        Args:
            treatments: List of treatment names to run
            progress: Show progress (not implemented yet)
            
        Returns:
            List of ExecutionResults
        """
        results = []
        
        # Get actual treatments from config
        available_treatments = {
            name: self.config.treatments.get(name, Treatment(skill_path=None))
            for name in treatments
        }
        
        # Add CONTROL if not present
        if "CONTROL" not in available_treatments:
            available_treatments["CONTROL"] = Treatment(skill_path=None)
        
        # Create tasks for each combination
        tasks_to_run = []
        for treatment_name in available_treatments:
            for task in self.config.tests:
                tasks_to_run.append((
                    available_treatments[treatment_name],
                    task,
                    treatment_name
                ))
        
        # Run with repetitions
        all_results = []
        repetitions = None
        
        for rep in range(repetitions):
            # Run all tasks
            coroutines = [
                self.run_single(treatment, task, treatment_name)
                for treatment, task, treatment_name in tasks_to_run
            ]
            
            # Execute concurrently (limited by semaphore)
            results = await asyncio.gather(*coroutines, return_exceptions=True)
            
            # Handle exceptions
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    # Create error result with minimal response
                    treatment, task, treatment_name = tasks_to_run[i]
                    error_result = ExecutionResult(
                        treatment=treatment_name,
                        test=task.name,
                        prompt=task.prompt,
                        response=LLMResponse(
                            content="",
                            model="error",
                            provider="error",
                            duration_ms=0,
                            raw_response={"error": str(result)}
                        ),
                        passed=False,
                        evaluator_results=[],
                        timestamp=datetime.utcnow().isoformat()
                    )
                    all_results.append(error_result)
                else:
                    all_results.append(result)
        
        return all_results
    
    async def xǁExecutionEngineǁrun_all__mutmut_18(
        self,
        treatments: list[str],
        progress: bool = False,
    ) -> list[ExecutionResult]:
        """Run all treatments and tasks.
        
        Args:
            treatments: List of treatment names to run
            progress: Show progress (not implemented yet)
            
        Returns:
            List of ExecutionResults
        """
        results = []
        
        # Get actual treatments from config
        available_treatments = {
            name: self.config.treatments.get(name, Treatment(skill_path=None))
            for name in treatments
        }
        
        # Add CONTROL if not present
        if "CONTROL" not in available_treatments:
            available_treatments["CONTROL"] = Treatment(skill_path=None)
        
        # Create tasks for each combination
        tasks_to_run = []
        for treatment_name in available_treatments:
            for task in self.config.tests:
                tasks_to_run.append((
                    available_treatments[treatment_name],
                    task,
                    treatment_name
                ))
        
        # Run with repetitions
        all_results = []
        repetitions = self.config.execution.repetitions
        
        for rep in range(None):
            # Run all tasks
            coroutines = [
                self.run_single(treatment, task, treatment_name)
                for treatment, task, treatment_name in tasks_to_run
            ]
            
            # Execute concurrently (limited by semaphore)
            results = await asyncio.gather(*coroutines, return_exceptions=True)
            
            # Handle exceptions
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    # Create error result with minimal response
                    treatment, task, treatment_name = tasks_to_run[i]
                    error_result = ExecutionResult(
                        treatment=treatment_name,
                        test=task.name,
                        prompt=task.prompt,
                        response=LLMResponse(
                            content="",
                            model="error",
                            provider="error",
                            duration_ms=0,
                            raw_response={"error": str(result)}
                        ),
                        passed=False,
                        evaluator_results=[],
                        timestamp=datetime.utcnow().isoformat()
                    )
                    all_results.append(error_result)
                else:
                    all_results.append(result)
        
        return all_results
    
    async def xǁExecutionEngineǁrun_all__mutmut_19(
        self,
        treatments: list[str],
        progress: bool = False,
    ) -> list[ExecutionResult]:
        """Run all treatments and tasks.
        
        Args:
            treatments: List of treatment names to run
            progress: Show progress (not implemented yet)
            
        Returns:
            List of ExecutionResults
        """
        results = []
        
        # Get actual treatments from config
        available_treatments = {
            name: self.config.treatments.get(name, Treatment(skill_path=None))
            for name in treatments
        }
        
        # Add CONTROL if not present
        if "CONTROL" not in available_treatments:
            available_treatments["CONTROL"] = Treatment(skill_path=None)
        
        # Create tasks for each combination
        tasks_to_run = []
        for treatment_name in available_treatments:
            for task in self.config.tests:
                tasks_to_run.append((
                    available_treatments[treatment_name],
                    task,
                    treatment_name
                ))
        
        # Run with repetitions
        all_results = []
        repetitions = self.config.execution.repetitions
        
        for rep in range(repetitions):
            # Run all tasks
            coroutines = None
            
            # Execute concurrently (limited by semaphore)
            results = await asyncio.gather(*coroutines, return_exceptions=True)
            
            # Handle exceptions
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    # Create error result with minimal response
                    treatment, task, treatment_name = tasks_to_run[i]
                    error_result = ExecutionResult(
                        treatment=treatment_name,
                        test=task.name,
                        prompt=task.prompt,
                        response=LLMResponse(
                            content="",
                            model="error",
                            provider="error",
                            duration_ms=0,
                            raw_response={"error": str(result)}
                        ),
                        passed=False,
                        evaluator_results=[],
                        timestamp=datetime.utcnow().isoformat()
                    )
                    all_results.append(error_result)
                else:
                    all_results.append(result)
        
        return all_results
    
    async def xǁExecutionEngineǁrun_all__mutmut_20(
        self,
        treatments: list[str],
        progress: bool = False,
    ) -> list[ExecutionResult]:
        """Run all treatments and tasks.
        
        Args:
            treatments: List of treatment names to run
            progress: Show progress (not implemented yet)
            
        Returns:
            List of ExecutionResults
        """
        results = []
        
        # Get actual treatments from config
        available_treatments = {
            name: self.config.treatments.get(name, Treatment(skill_path=None))
            for name in treatments
        }
        
        # Add CONTROL if not present
        if "CONTROL" not in available_treatments:
            available_treatments["CONTROL"] = Treatment(skill_path=None)
        
        # Create tasks for each combination
        tasks_to_run = []
        for treatment_name in available_treatments:
            for task in self.config.tests:
                tasks_to_run.append((
                    available_treatments[treatment_name],
                    task,
                    treatment_name
                ))
        
        # Run with repetitions
        all_results = []
        repetitions = self.config.execution.repetitions
        
        for rep in range(repetitions):
            # Run all tasks
            coroutines = [
                self.run_single(None, task, treatment_name)
                for treatment, task, treatment_name in tasks_to_run
            ]
            
            # Execute concurrently (limited by semaphore)
            results = await asyncio.gather(*coroutines, return_exceptions=True)
            
            # Handle exceptions
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    # Create error result with minimal response
                    treatment, task, treatment_name = tasks_to_run[i]
                    error_result = ExecutionResult(
                        treatment=treatment_name,
                        test=task.name,
                        prompt=task.prompt,
                        response=LLMResponse(
                            content="",
                            model="error",
                            provider="error",
                            duration_ms=0,
                            raw_response={"error": str(result)}
                        ),
                        passed=False,
                        evaluator_results=[],
                        timestamp=datetime.utcnow().isoformat()
                    )
                    all_results.append(error_result)
                else:
                    all_results.append(result)
        
        return all_results
    
    async def xǁExecutionEngineǁrun_all__mutmut_21(
        self,
        treatments: list[str],
        progress: bool = False,
    ) -> list[ExecutionResult]:
        """Run all treatments and tasks.
        
        Args:
            treatments: List of treatment names to run
            progress: Show progress (not implemented yet)
            
        Returns:
            List of ExecutionResults
        """
        results = []
        
        # Get actual treatments from config
        available_treatments = {
            name: self.config.treatments.get(name, Treatment(skill_path=None))
            for name in treatments
        }
        
        # Add CONTROL if not present
        if "CONTROL" not in available_treatments:
            available_treatments["CONTROL"] = Treatment(skill_path=None)
        
        # Create tasks for each combination
        tasks_to_run = []
        for treatment_name in available_treatments:
            for task in self.config.tests:
                tasks_to_run.append((
                    available_treatments[treatment_name],
                    task,
                    treatment_name
                ))
        
        # Run with repetitions
        all_results = []
        repetitions = self.config.execution.repetitions
        
        for rep in range(repetitions):
            # Run all tasks
            coroutines = [
                self.run_single(treatment, None, treatment_name)
                for treatment, task, treatment_name in tasks_to_run
            ]
            
            # Execute concurrently (limited by semaphore)
            results = await asyncio.gather(*coroutines, return_exceptions=True)
            
            # Handle exceptions
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    # Create error result with minimal response
                    treatment, task, treatment_name = tasks_to_run[i]
                    error_result = ExecutionResult(
                        treatment=treatment_name,
                        test=task.name,
                        prompt=task.prompt,
                        response=LLMResponse(
                            content="",
                            model="error",
                            provider="error",
                            duration_ms=0,
                            raw_response={"error": str(result)}
                        ),
                        passed=False,
                        evaluator_results=[],
                        timestamp=datetime.utcnow().isoformat()
                    )
                    all_results.append(error_result)
                else:
                    all_results.append(result)
        
        return all_results
    
    async def xǁExecutionEngineǁrun_all__mutmut_22(
        self,
        treatments: list[str],
        progress: bool = False,
    ) -> list[ExecutionResult]:
        """Run all treatments and tasks.
        
        Args:
            treatments: List of treatment names to run
            progress: Show progress (not implemented yet)
            
        Returns:
            List of ExecutionResults
        """
        results = []
        
        # Get actual treatments from config
        available_treatments = {
            name: self.config.treatments.get(name, Treatment(skill_path=None))
            for name in treatments
        }
        
        # Add CONTROL if not present
        if "CONTROL" not in available_treatments:
            available_treatments["CONTROL"] = Treatment(skill_path=None)
        
        # Create tasks for each combination
        tasks_to_run = []
        for treatment_name in available_treatments:
            for task in self.config.tests:
                tasks_to_run.append((
                    available_treatments[treatment_name],
                    task,
                    treatment_name
                ))
        
        # Run with repetitions
        all_results = []
        repetitions = self.config.execution.repetitions
        
        for rep in range(repetitions):
            # Run all tasks
            coroutines = [
                self.run_single(treatment, task, None)
                for treatment, task, treatment_name in tasks_to_run
            ]
            
            # Execute concurrently (limited by semaphore)
            results = await asyncio.gather(*coroutines, return_exceptions=True)
            
            # Handle exceptions
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    # Create error result with minimal response
                    treatment, task, treatment_name = tasks_to_run[i]
                    error_result = ExecutionResult(
                        treatment=treatment_name,
                        test=task.name,
                        prompt=task.prompt,
                        response=LLMResponse(
                            content="",
                            model="error",
                            provider="error",
                            duration_ms=0,
                            raw_response={"error": str(result)}
                        ),
                        passed=False,
                        evaluator_results=[],
                        timestamp=datetime.utcnow().isoformat()
                    )
                    all_results.append(error_result)
                else:
                    all_results.append(result)
        
        return all_results
    
    async def xǁExecutionEngineǁrun_all__mutmut_23(
        self,
        treatments: list[str],
        progress: bool = False,
    ) -> list[ExecutionResult]:
        """Run all treatments and tasks.
        
        Args:
            treatments: List of treatment names to run
            progress: Show progress (not implemented yet)
            
        Returns:
            List of ExecutionResults
        """
        results = []
        
        # Get actual treatments from config
        available_treatments = {
            name: self.config.treatments.get(name, Treatment(skill_path=None))
            for name in treatments
        }
        
        # Add CONTROL if not present
        if "CONTROL" not in available_treatments:
            available_treatments["CONTROL"] = Treatment(skill_path=None)
        
        # Create tasks for each combination
        tasks_to_run = []
        for treatment_name in available_treatments:
            for task in self.config.tests:
                tasks_to_run.append((
                    available_treatments[treatment_name],
                    task,
                    treatment_name
                ))
        
        # Run with repetitions
        all_results = []
        repetitions = self.config.execution.repetitions
        
        for rep in range(repetitions):
            # Run all tasks
            coroutines = [
                self.run_single(task, treatment_name)
                for treatment, task, treatment_name in tasks_to_run
            ]
            
            # Execute concurrently (limited by semaphore)
            results = await asyncio.gather(*coroutines, return_exceptions=True)
            
            # Handle exceptions
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    # Create error result with minimal response
                    treatment, task, treatment_name = tasks_to_run[i]
                    error_result = ExecutionResult(
                        treatment=treatment_name,
                        test=task.name,
                        prompt=task.prompt,
                        response=LLMResponse(
                            content="",
                            model="error",
                            provider="error",
                            duration_ms=0,
                            raw_response={"error": str(result)}
                        ),
                        passed=False,
                        evaluator_results=[],
                        timestamp=datetime.utcnow().isoformat()
                    )
                    all_results.append(error_result)
                else:
                    all_results.append(result)
        
        return all_results
    
    async def xǁExecutionEngineǁrun_all__mutmut_24(
        self,
        treatments: list[str],
        progress: bool = False,
    ) -> list[ExecutionResult]:
        """Run all treatments and tasks.
        
        Args:
            treatments: List of treatment names to run
            progress: Show progress (not implemented yet)
            
        Returns:
            List of ExecutionResults
        """
        results = []
        
        # Get actual treatments from config
        available_treatments = {
            name: self.config.treatments.get(name, Treatment(skill_path=None))
            for name in treatments
        }
        
        # Add CONTROL if not present
        if "CONTROL" not in available_treatments:
            available_treatments["CONTROL"] = Treatment(skill_path=None)
        
        # Create tasks for each combination
        tasks_to_run = []
        for treatment_name in available_treatments:
            for task in self.config.tests:
                tasks_to_run.append((
                    available_treatments[treatment_name],
                    task,
                    treatment_name
                ))
        
        # Run with repetitions
        all_results = []
        repetitions = self.config.execution.repetitions
        
        for rep in range(repetitions):
            # Run all tasks
            coroutines = [
                self.run_single(treatment, treatment_name)
                for treatment, task, treatment_name in tasks_to_run
            ]
            
            # Execute concurrently (limited by semaphore)
            results = await asyncio.gather(*coroutines, return_exceptions=True)
            
            # Handle exceptions
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    # Create error result with minimal response
                    treatment, task, treatment_name = tasks_to_run[i]
                    error_result = ExecutionResult(
                        treatment=treatment_name,
                        test=task.name,
                        prompt=task.prompt,
                        response=LLMResponse(
                            content="",
                            model="error",
                            provider="error",
                            duration_ms=0,
                            raw_response={"error": str(result)}
                        ),
                        passed=False,
                        evaluator_results=[],
                        timestamp=datetime.utcnow().isoformat()
                    )
                    all_results.append(error_result)
                else:
                    all_results.append(result)
        
        return all_results
    
    async def xǁExecutionEngineǁrun_all__mutmut_25(
        self,
        treatments: list[str],
        progress: bool = False,
    ) -> list[ExecutionResult]:
        """Run all treatments and tasks.
        
        Args:
            treatments: List of treatment names to run
            progress: Show progress (not implemented yet)
            
        Returns:
            List of ExecutionResults
        """
        results = []
        
        # Get actual treatments from config
        available_treatments = {
            name: self.config.treatments.get(name, Treatment(skill_path=None))
            for name in treatments
        }
        
        # Add CONTROL if not present
        if "CONTROL" not in available_treatments:
            available_treatments["CONTROL"] = Treatment(skill_path=None)
        
        # Create tasks for each combination
        tasks_to_run = []
        for treatment_name in available_treatments:
            for task in self.config.tests:
                tasks_to_run.append((
                    available_treatments[treatment_name],
                    task,
                    treatment_name
                ))
        
        # Run with repetitions
        all_results = []
        repetitions = self.config.execution.repetitions
        
        for rep in range(repetitions):
            # Run all tasks
            coroutines = [
                self.run_single(treatment, task, )
                for treatment, task, treatment_name in tasks_to_run
            ]
            
            # Execute concurrently (limited by semaphore)
            results = await asyncio.gather(*coroutines, return_exceptions=True)
            
            # Handle exceptions
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    # Create error result with minimal response
                    treatment, task, treatment_name = tasks_to_run[i]
                    error_result = ExecutionResult(
                        treatment=treatment_name,
                        test=task.name,
                        prompt=task.prompt,
                        response=LLMResponse(
                            content="",
                            model="error",
                            provider="error",
                            duration_ms=0,
                            raw_response={"error": str(result)}
                        ),
                        passed=False,
                        evaluator_results=[],
                        timestamp=datetime.utcnow().isoformat()
                    )
                    all_results.append(error_result)
                else:
                    all_results.append(result)
        
        return all_results
    
    async def xǁExecutionEngineǁrun_all__mutmut_26(
        self,
        treatments: list[str],
        progress: bool = False,
    ) -> list[ExecutionResult]:
        """Run all treatments and tasks.
        
        Args:
            treatments: List of treatment names to run
            progress: Show progress (not implemented yet)
            
        Returns:
            List of ExecutionResults
        """
        results = []
        
        # Get actual treatments from config
        available_treatments = {
            name: self.config.treatments.get(name, Treatment(skill_path=None))
            for name in treatments
        }
        
        # Add CONTROL if not present
        if "CONTROL" not in available_treatments:
            available_treatments["CONTROL"] = Treatment(skill_path=None)
        
        # Create tasks for each combination
        tasks_to_run = []
        for treatment_name in available_treatments:
            for task in self.config.tests:
                tasks_to_run.append((
                    available_treatments[treatment_name],
                    task,
                    treatment_name
                ))
        
        # Run with repetitions
        all_results = []
        repetitions = self.config.execution.repetitions
        
        for rep in range(repetitions):
            # Run all tasks
            coroutines = [
                self.run_single(treatment, task, treatment_name)
                for treatment, task, treatment_name in tasks_to_run
            ]
            
            # Execute concurrently (limited by semaphore)
            results = None
            
            # Handle exceptions
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    # Create error result with minimal response
                    treatment, task, treatment_name = tasks_to_run[i]
                    error_result = ExecutionResult(
                        treatment=treatment_name,
                        test=task.name,
                        prompt=task.prompt,
                        response=LLMResponse(
                            content="",
                            model="error",
                            provider="error",
                            duration_ms=0,
                            raw_response={"error": str(result)}
                        ),
                        passed=False,
                        evaluator_results=[],
                        timestamp=datetime.utcnow().isoformat()
                    )
                    all_results.append(error_result)
                else:
                    all_results.append(result)
        
        return all_results
    
    async def xǁExecutionEngineǁrun_all__mutmut_27(
        self,
        treatments: list[str],
        progress: bool = False,
    ) -> list[ExecutionResult]:
        """Run all treatments and tasks.
        
        Args:
            treatments: List of treatment names to run
            progress: Show progress (not implemented yet)
            
        Returns:
            List of ExecutionResults
        """
        results = []
        
        # Get actual treatments from config
        available_treatments = {
            name: self.config.treatments.get(name, Treatment(skill_path=None))
            for name in treatments
        }
        
        # Add CONTROL if not present
        if "CONTROL" not in available_treatments:
            available_treatments["CONTROL"] = Treatment(skill_path=None)
        
        # Create tasks for each combination
        tasks_to_run = []
        for treatment_name in available_treatments:
            for task in self.config.tests:
                tasks_to_run.append((
                    available_treatments[treatment_name],
                    task,
                    treatment_name
                ))
        
        # Run with repetitions
        all_results = []
        repetitions = self.config.execution.repetitions
        
        for rep in range(repetitions):
            # Run all tasks
            coroutines = [
                self.run_single(treatment, task, treatment_name)
                for treatment, task, treatment_name in tasks_to_run
            ]
            
            # Execute concurrently (limited by semaphore)
            results = await asyncio.gather(*coroutines, return_exceptions=None)
            
            # Handle exceptions
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    # Create error result with minimal response
                    treatment, task, treatment_name = tasks_to_run[i]
                    error_result = ExecutionResult(
                        treatment=treatment_name,
                        test=task.name,
                        prompt=task.prompt,
                        response=LLMResponse(
                            content="",
                            model="error",
                            provider="error",
                            duration_ms=0,
                            raw_response={"error": str(result)}
                        ),
                        passed=False,
                        evaluator_results=[],
                        timestamp=datetime.utcnow().isoformat()
                    )
                    all_results.append(error_result)
                else:
                    all_results.append(result)
        
        return all_results
    
    async def xǁExecutionEngineǁrun_all__mutmut_28(
        self,
        treatments: list[str],
        progress: bool = False,
    ) -> list[ExecutionResult]:
        """Run all treatments and tasks.
        
        Args:
            treatments: List of treatment names to run
            progress: Show progress (not implemented yet)
            
        Returns:
            List of ExecutionResults
        """
        results = []
        
        # Get actual treatments from config
        available_treatments = {
            name: self.config.treatments.get(name, Treatment(skill_path=None))
            for name in treatments
        }
        
        # Add CONTROL if not present
        if "CONTROL" not in available_treatments:
            available_treatments["CONTROL"] = Treatment(skill_path=None)
        
        # Create tasks for each combination
        tasks_to_run = []
        for treatment_name in available_treatments:
            for task in self.config.tests:
                tasks_to_run.append((
                    available_treatments[treatment_name],
                    task,
                    treatment_name
                ))
        
        # Run with repetitions
        all_results = []
        repetitions = self.config.execution.repetitions
        
        for rep in range(repetitions):
            # Run all tasks
            coroutines = [
                self.run_single(treatment, task, treatment_name)
                for treatment, task, treatment_name in tasks_to_run
            ]
            
            # Execute concurrently (limited by semaphore)
            results = await asyncio.gather(return_exceptions=True)
            
            # Handle exceptions
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    # Create error result with minimal response
                    treatment, task, treatment_name = tasks_to_run[i]
                    error_result = ExecutionResult(
                        treatment=treatment_name,
                        test=task.name,
                        prompt=task.prompt,
                        response=LLMResponse(
                            content="",
                            model="error",
                            provider="error",
                            duration_ms=0,
                            raw_response={"error": str(result)}
                        ),
                        passed=False,
                        evaluator_results=[],
                        timestamp=datetime.utcnow().isoformat()
                    )
                    all_results.append(error_result)
                else:
                    all_results.append(result)
        
        return all_results
    
    async def xǁExecutionEngineǁrun_all__mutmut_29(
        self,
        treatments: list[str],
        progress: bool = False,
    ) -> list[ExecutionResult]:
        """Run all treatments and tasks.
        
        Args:
            treatments: List of treatment names to run
            progress: Show progress (not implemented yet)
            
        Returns:
            List of ExecutionResults
        """
        results = []
        
        # Get actual treatments from config
        available_treatments = {
            name: self.config.treatments.get(name, Treatment(skill_path=None))
            for name in treatments
        }
        
        # Add CONTROL if not present
        if "CONTROL" not in available_treatments:
            available_treatments["CONTROL"] = Treatment(skill_path=None)
        
        # Create tasks for each combination
        tasks_to_run = []
        for treatment_name in available_treatments:
            for task in self.config.tests:
                tasks_to_run.append((
                    available_treatments[treatment_name],
                    task,
                    treatment_name
                ))
        
        # Run with repetitions
        all_results = []
        repetitions = self.config.execution.repetitions
        
        for rep in range(repetitions):
            # Run all tasks
            coroutines = [
                self.run_single(treatment, task, treatment_name)
                for treatment, task, treatment_name in tasks_to_run
            ]
            
            # Execute concurrently (limited by semaphore)
            results = await asyncio.gather(*coroutines, )
            
            # Handle exceptions
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    # Create error result with minimal response
                    treatment, task, treatment_name = tasks_to_run[i]
                    error_result = ExecutionResult(
                        treatment=treatment_name,
                        test=task.name,
                        prompt=task.prompt,
                        response=LLMResponse(
                            content="",
                            model="error",
                            provider="error",
                            duration_ms=0,
                            raw_response={"error": str(result)}
                        ),
                        passed=False,
                        evaluator_results=[],
                        timestamp=datetime.utcnow().isoformat()
                    )
                    all_results.append(error_result)
                else:
                    all_results.append(result)
        
        return all_results
    
    async def xǁExecutionEngineǁrun_all__mutmut_30(
        self,
        treatments: list[str],
        progress: bool = False,
    ) -> list[ExecutionResult]:
        """Run all treatments and tasks.
        
        Args:
            treatments: List of treatment names to run
            progress: Show progress (not implemented yet)
            
        Returns:
            List of ExecutionResults
        """
        results = []
        
        # Get actual treatments from config
        available_treatments = {
            name: self.config.treatments.get(name, Treatment(skill_path=None))
            for name in treatments
        }
        
        # Add CONTROL if not present
        if "CONTROL" not in available_treatments:
            available_treatments["CONTROL"] = Treatment(skill_path=None)
        
        # Create tasks for each combination
        tasks_to_run = []
        for treatment_name in available_treatments:
            for task in self.config.tests:
                tasks_to_run.append((
                    available_treatments[treatment_name],
                    task,
                    treatment_name
                ))
        
        # Run with repetitions
        all_results = []
        repetitions = self.config.execution.repetitions
        
        for rep in range(repetitions):
            # Run all tasks
            coroutines = [
                self.run_single(treatment, task, treatment_name)
                for treatment, task, treatment_name in tasks_to_run
            ]
            
            # Execute concurrently (limited by semaphore)
            results = await asyncio.gather(*coroutines, return_exceptions=False)
            
            # Handle exceptions
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    # Create error result with minimal response
                    treatment, task, treatment_name = tasks_to_run[i]
                    error_result = ExecutionResult(
                        treatment=treatment_name,
                        test=task.name,
                        prompt=task.prompt,
                        response=LLMResponse(
                            content="",
                            model="error",
                            provider="error",
                            duration_ms=0,
                            raw_response={"error": str(result)}
                        ),
                        passed=False,
                        evaluator_results=[],
                        timestamp=datetime.utcnow().isoformat()
                    )
                    all_results.append(error_result)
                else:
                    all_results.append(result)
        
        return all_results
    
    async def xǁExecutionEngineǁrun_all__mutmut_31(
        self,
        treatments: list[str],
        progress: bool = False,
    ) -> list[ExecutionResult]:
        """Run all treatments and tasks.
        
        Args:
            treatments: List of treatment names to run
            progress: Show progress (not implemented yet)
            
        Returns:
            List of ExecutionResults
        """
        results = []
        
        # Get actual treatments from config
        available_treatments = {
            name: self.config.treatments.get(name, Treatment(skill_path=None))
            for name in treatments
        }
        
        # Add CONTROL if not present
        if "CONTROL" not in available_treatments:
            available_treatments["CONTROL"] = Treatment(skill_path=None)
        
        # Create tasks for each combination
        tasks_to_run = []
        for treatment_name in available_treatments:
            for task in self.config.tests:
                tasks_to_run.append((
                    available_treatments[treatment_name],
                    task,
                    treatment_name
                ))
        
        # Run with repetitions
        all_results = []
        repetitions = self.config.execution.repetitions
        
        for rep in range(repetitions):
            # Run all tasks
            coroutines = [
                self.run_single(treatment, task, treatment_name)
                for treatment, task, treatment_name in tasks_to_run
            ]
            
            # Execute concurrently (limited by semaphore)
            results = await asyncio.gather(*coroutines, return_exceptions=True)
            
            # Handle exceptions
            for i, result in enumerate(None):
                if isinstance(result, Exception):
                    # Create error result with minimal response
                    treatment, task, treatment_name = tasks_to_run[i]
                    error_result = ExecutionResult(
                        treatment=treatment_name,
                        test=task.name,
                        prompt=task.prompt,
                        response=LLMResponse(
                            content="",
                            model="error",
                            provider="error",
                            duration_ms=0,
                            raw_response={"error": str(result)}
                        ),
                        passed=False,
                        evaluator_results=[],
                        timestamp=datetime.utcnow().isoformat()
                    )
                    all_results.append(error_result)
                else:
                    all_results.append(result)
        
        return all_results
    
    async def xǁExecutionEngineǁrun_all__mutmut_32(
        self,
        treatments: list[str],
        progress: bool = False,
    ) -> list[ExecutionResult]:
        """Run all treatments and tasks.
        
        Args:
            treatments: List of treatment names to run
            progress: Show progress (not implemented yet)
            
        Returns:
            List of ExecutionResults
        """
        results = []
        
        # Get actual treatments from config
        available_treatments = {
            name: self.config.treatments.get(name, Treatment(skill_path=None))
            for name in treatments
        }
        
        # Add CONTROL if not present
        if "CONTROL" not in available_treatments:
            available_treatments["CONTROL"] = Treatment(skill_path=None)
        
        # Create tasks for each combination
        tasks_to_run = []
        for treatment_name in available_treatments:
            for task in self.config.tests:
                tasks_to_run.append((
                    available_treatments[treatment_name],
                    task,
                    treatment_name
                ))
        
        # Run with repetitions
        all_results = []
        repetitions = self.config.execution.repetitions
        
        for rep in range(repetitions):
            # Run all tasks
            coroutines = [
                self.run_single(treatment, task, treatment_name)
                for treatment, task, treatment_name in tasks_to_run
            ]
            
            # Execute concurrently (limited by semaphore)
            results = await asyncio.gather(*coroutines, return_exceptions=True)
            
            # Handle exceptions
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    # Create error result with minimal response
                    treatment, task, treatment_name = None
                    error_result = ExecutionResult(
                        treatment=treatment_name,
                        test=task.name,
                        prompt=task.prompt,
                        response=LLMResponse(
                            content="",
                            model="error",
                            provider="error",
                            duration_ms=0,
                            raw_response={"error": str(result)}
                        ),
                        passed=False,
                        evaluator_results=[],
                        timestamp=datetime.utcnow().isoformat()
                    )
                    all_results.append(error_result)
                else:
                    all_results.append(result)
        
        return all_results
    
    async def xǁExecutionEngineǁrun_all__mutmut_33(
        self,
        treatments: list[str],
        progress: bool = False,
    ) -> list[ExecutionResult]:
        """Run all treatments and tasks.
        
        Args:
            treatments: List of treatment names to run
            progress: Show progress (not implemented yet)
            
        Returns:
            List of ExecutionResults
        """
        results = []
        
        # Get actual treatments from config
        available_treatments = {
            name: self.config.treatments.get(name, Treatment(skill_path=None))
            for name in treatments
        }
        
        # Add CONTROL if not present
        if "CONTROL" not in available_treatments:
            available_treatments["CONTROL"] = Treatment(skill_path=None)
        
        # Create tasks for each combination
        tasks_to_run = []
        for treatment_name in available_treatments:
            for task in self.config.tests:
                tasks_to_run.append((
                    available_treatments[treatment_name],
                    task,
                    treatment_name
                ))
        
        # Run with repetitions
        all_results = []
        repetitions = self.config.execution.repetitions
        
        for rep in range(repetitions):
            # Run all tasks
            coroutines = [
                self.run_single(treatment, task, treatment_name)
                for treatment, task, treatment_name in tasks_to_run
            ]
            
            # Execute concurrently (limited by semaphore)
            results = await asyncio.gather(*coroutines, return_exceptions=True)
            
            # Handle exceptions
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    # Create error result with minimal response
                    treatment, task, treatment_name = tasks_to_run[i]
                    error_result = None
                    all_results.append(error_result)
                else:
                    all_results.append(result)
        
        return all_results
    
    async def xǁExecutionEngineǁrun_all__mutmut_34(
        self,
        treatments: list[str],
        progress: bool = False,
    ) -> list[ExecutionResult]:
        """Run all treatments and tasks.
        
        Args:
            treatments: List of treatment names to run
            progress: Show progress (not implemented yet)
            
        Returns:
            List of ExecutionResults
        """
        results = []
        
        # Get actual treatments from config
        available_treatments = {
            name: self.config.treatments.get(name, Treatment(skill_path=None))
            for name in treatments
        }
        
        # Add CONTROL if not present
        if "CONTROL" not in available_treatments:
            available_treatments["CONTROL"] = Treatment(skill_path=None)
        
        # Create tasks for each combination
        tasks_to_run = []
        for treatment_name in available_treatments:
            for task in self.config.tests:
                tasks_to_run.append((
                    available_treatments[treatment_name],
                    task,
                    treatment_name
                ))
        
        # Run with repetitions
        all_results = []
        repetitions = self.config.execution.repetitions
        
        for rep in range(repetitions):
            # Run all tasks
            coroutines = [
                self.run_single(treatment, task, treatment_name)
                for treatment, task, treatment_name in tasks_to_run
            ]
            
            # Execute concurrently (limited by semaphore)
            results = await asyncio.gather(*coroutines, return_exceptions=True)
            
            # Handle exceptions
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    # Create error result with minimal response
                    treatment, task, treatment_name = tasks_to_run[i]
                    error_result = ExecutionResult(
                        treatment=None,
                        test=task.name,
                        prompt=task.prompt,
                        response=LLMResponse(
                            content="",
                            model="error",
                            provider="error",
                            duration_ms=0,
                            raw_response={"error": str(result)}
                        ),
                        passed=False,
                        evaluator_results=[],
                        timestamp=datetime.utcnow().isoformat()
                    )
                    all_results.append(error_result)
                else:
                    all_results.append(result)
        
        return all_results
    
    async def xǁExecutionEngineǁrun_all__mutmut_35(
        self,
        treatments: list[str],
        progress: bool = False,
    ) -> list[ExecutionResult]:
        """Run all treatments and tasks.
        
        Args:
            treatments: List of treatment names to run
            progress: Show progress (not implemented yet)
            
        Returns:
            List of ExecutionResults
        """
        results = []
        
        # Get actual treatments from config
        available_treatments = {
            name: self.config.treatments.get(name, Treatment(skill_path=None))
            for name in treatments
        }
        
        # Add CONTROL if not present
        if "CONTROL" not in available_treatments:
            available_treatments["CONTROL"] = Treatment(skill_path=None)
        
        # Create tasks for each combination
        tasks_to_run = []
        for treatment_name in available_treatments:
            for task in self.config.tests:
                tasks_to_run.append((
                    available_treatments[treatment_name],
                    task,
                    treatment_name
                ))
        
        # Run with repetitions
        all_results = []
        repetitions = self.config.execution.repetitions
        
        for rep in range(repetitions):
            # Run all tasks
            coroutines = [
                self.run_single(treatment, task, treatment_name)
                for treatment, task, treatment_name in tasks_to_run
            ]
            
            # Execute concurrently (limited by semaphore)
            results = await asyncio.gather(*coroutines, return_exceptions=True)
            
            # Handle exceptions
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    # Create error result with minimal response
                    treatment, task, treatment_name = tasks_to_run[i]
                    error_result = ExecutionResult(
                        treatment=treatment_name,
                        test=None,
                        prompt=task.prompt,
                        response=LLMResponse(
                            content="",
                            model="error",
                            provider="error",
                            duration_ms=0,
                            raw_response={"error": str(result)}
                        ),
                        passed=False,
                        evaluator_results=[],
                        timestamp=datetime.utcnow().isoformat()
                    )
                    all_results.append(error_result)
                else:
                    all_results.append(result)
        
        return all_results
    
    async def xǁExecutionEngineǁrun_all__mutmut_36(
        self,
        treatments: list[str],
        progress: bool = False,
    ) -> list[ExecutionResult]:
        """Run all treatments and tasks.
        
        Args:
            treatments: List of treatment names to run
            progress: Show progress (not implemented yet)
            
        Returns:
            List of ExecutionResults
        """
        results = []
        
        # Get actual treatments from config
        available_treatments = {
            name: self.config.treatments.get(name, Treatment(skill_path=None))
            for name in treatments
        }
        
        # Add CONTROL if not present
        if "CONTROL" not in available_treatments:
            available_treatments["CONTROL"] = Treatment(skill_path=None)
        
        # Create tasks for each combination
        tasks_to_run = []
        for treatment_name in available_treatments:
            for task in self.config.tests:
                tasks_to_run.append((
                    available_treatments[treatment_name],
                    task,
                    treatment_name
                ))
        
        # Run with repetitions
        all_results = []
        repetitions = self.config.execution.repetitions
        
        for rep in range(repetitions):
            # Run all tasks
            coroutines = [
                self.run_single(treatment, task, treatment_name)
                for treatment, task, treatment_name in tasks_to_run
            ]
            
            # Execute concurrently (limited by semaphore)
            results = await asyncio.gather(*coroutines, return_exceptions=True)
            
            # Handle exceptions
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    # Create error result with minimal response
                    treatment, task, treatment_name = tasks_to_run[i]
                    error_result = ExecutionResult(
                        treatment=treatment_name,
                        test=task.name,
                        prompt=None,
                        response=LLMResponse(
                            content="",
                            model="error",
                            provider="error",
                            duration_ms=0,
                            raw_response={"error": str(result)}
                        ),
                        passed=False,
                        evaluator_results=[],
                        timestamp=datetime.utcnow().isoformat()
                    )
                    all_results.append(error_result)
                else:
                    all_results.append(result)
        
        return all_results
    
    async def xǁExecutionEngineǁrun_all__mutmut_37(
        self,
        treatments: list[str],
        progress: bool = False,
    ) -> list[ExecutionResult]:
        """Run all treatments and tasks.
        
        Args:
            treatments: List of treatment names to run
            progress: Show progress (not implemented yet)
            
        Returns:
            List of ExecutionResults
        """
        results = []
        
        # Get actual treatments from config
        available_treatments = {
            name: self.config.treatments.get(name, Treatment(skill_path=None))
            for name in treatments
        }
        
        # Add CONTROL if not present
        if "CONTROL" not in available_treatments:
            available_treatments["CONTROL"] = Treatment(skill_path=None)
        
        # Create tasks for each combination
        tasks_to_run = []
        for treatment_name in available_treatments:
            for task in self.config.tests:
                tasks_to_run.append((
                    available_treatments[treatment_name],
                    task,
                    treatment_name
                ))
        
        # Run with repetitions
        all_results = []
        repetitions = self.config.execution.repetitions
        
        for rep in range(repetitions):
            # Run all tasks
            coroutines = [
                self.run_single(treatment, task, treatment_name)
                for treatment, task, treatment_name in tasks_to_run
            ]
            
            # Execute concurrently (limited by semaphore)
            results = await asyncio.gather(*coroutines, return_exceptions=True)
            
            # Handle exceptions
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    # Create error result with minimal response
                    treatment, task, treatment_name = tasks_to_run[i]
                    error_result = ExecutionResult(
                        treatment=treatment_name,
                        test=task.name,
                        prompt=task.prompt,
                        response=None,
                        passed=False,
                        evaluator_results=[],
                        timestamp=datetime.utcnow().isoformat()
                    )
                    all_results.append(error_result)
                else:
                    all_results.append(result)
        
        return all_results
    
    async def xǁExecutionEngineǁrun_all__mutmut_38(
        self,
        treatments: list[str],
        progress: bool = False,
    ) -> list[ExecutionResult]:
        """Run all treatments and tasks.
        
        Args:
            treatments: List of treatment names to run
            progress: Show progress (not implemented yet)
            
        Returns:
            List of ExecutionResults
        """
        results = []
        
        # Get actual treatments from config
        available_treatments = {
            name: self.config.treatments.get(name, Treatment(skill_path=None))
            for name in treatments
        }
        
        # Add CONTROL if not present
        if "CONTROL" not in available_treatments:
            available_treatments["CONTROL"] = Treatment(skill_path=None)
        
        # Create tasks for each combination
        tasks_to_run = []
        for treatment_name in available_treatments:
            for task in self.config.tests:
                tasks_to_run.append((
                    available_treatments[treatment_name],
                    task,
                    treatment_name
                ))
        
        # Run with repetitions
        all_results = []
        repetitions = self.config.execution.repetitions
        
        for rep in range(repetitions):
            # Run all tasks
            coroutines = [
                self.run_single(treatment, task, treatment_name)
                for treatment, task, treatment_name in tasks_to_run
            ]
            
            # Execute concurrently (limited by semaphore)
            results = await asyncio.gather(*coroutines, return_exceptions=True)
            
            # Handle exceptions
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    # Create error result with minimal response
                    treatment, task, treatment_name = tasks_to_run[i]
                    error_result = ExecutionResult(
                        treatment=treatment_name,
                        test=task.name,
                        prompt=task.prompt,
                        response=LLMResponse(
                            content="",
                            model="error",
                            provider="error",
                            duration_ms=0,
                            raw_response={"error": str(result)}
                        ),
                        passed=None,
                        evaluator_results=[],
                        timestamp=datetime.utcnow().isoformat()
                    )
                    all_results.append(error_result)
                else:
                    all_results.append(result)
        
        return all_results
    
    async def xǁExecutionEngineǁrun_all__mutmut_39(
        self,
        treatments: list[str],
        progress: bool = False,
    ) -> list[ExecutionResult]:
        """Run all treatments and tasks.
        
        Args:
            treatments: List of treatment names to run
            progress: Show progress (not implemented yet)
            
        Returns:
            List of ExecutionResults
        """
        results = []
        
        # Get actual treatments from config
        available_treatments = {
            name: self.config.treatments.get(name, Treatment(skill_path=None))
            for name in treatments
        }
        
        # Add CONTROL if not present
        if "CONTROL" not in available_treatments:
            available_treatments["CONTROL"] = Treatment(skill_path=None)
        
        # Create tasks for each combination
        tasks_to_run = []
        for treatment_name in available_treatments:
            for task in self.config.tests:
                tasks_to_run.append((
                    available_treatments[treatment_name],
                    task,
                    treatment_name
                ))
        
        # Run with repetitions
        all_results = []
        repetitions = self.config.execution.repetitions
        
        for rep in range(repetitions):
            # Run all tasks
            coroutines = [
                self.run_single(treatment, task, treatment_name)
                for treatment, task, treatment_name in tasks_to_run
            ]
            
            # Execute concurrently (limited by semaphore)
            results = await asyncio.gather(*coroutines, return_exceptions=True)
            
            # Handle exceptions
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    # Create error result with minimal response
                    treatment, task, treatment_name = tasks_to_run[i]
                    error_result = ExecutionResult(
                        treatment=treatment_name,
                        test=task.name,
                        prompt=task.prompt,
                        response=LLMResponse(
                            content="",
                            model="error",
                            provider="error",
                            duration_ms=0,
                            raw_response={"error": str(result)}
                        ),
                        passed=False,
                        evaluator_results=None,
                        timestamp=datetime.utcnow().isoformat()
                    )
                    all_results.append(error_result)
                else:
                    all_results.append(result)
        
        return all_results
    
    async def xǁExecutionEngineǁrun_all__mutmut_40(
        self,
        treatments: list[str],
        progress: bool = False,
    ) -> list[ExecutionResult]:
        """Run all treatments and tasks.
        
        Args:
            treatments: List of treatment names to run
            progress: Show progress (not implemented yet)
            
        Returns:
            List of ExecutionResults
        """
        results = []
        
        # Get actual treatments from config
        available_treatments = {
            name: self.config.treatments.get(name, Treatment(skill_path=None))
            for name in treatments
        }
        
        # Add CONTROL if not present
        if "CONTROL" not in available_treatments:
            available_treatments["CONTROL"] = Treatment(skill_path=None)
        
        # Create tasks for each combination
        tasks_to_run = []
        for treatment_name in available_treatments:
            for task in self.config.tests:
                tasks_to_run.append((
                    available_treatments[treatment_name],
                    task,
                    treatment_name
                ))
        
        # Run with repetitions
        all_results = []
        repetitions = self.config.execution.repetitions
        
        for rep in range(repetitions):
            # Run all tasks
            coroutines = [
                self.run_single(treatment, task, treatment_name)
                for treatment, task, treatment_name in tasks_to_run
            ]
            
            # Execute concurrently (limited by semaphore)
            results = await asyncio.gather(*coroutines, return_exceptions=True)
            
            # Handle exceptions
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    # Create error result with minimal response
                    treatment, task, treatment_name = tasks_to_run[i]
                    error_result = ExecutionResult(
                        treatment=treatment_name,
                        test=task.name,
                        prompt=task.prompt,
                        response=LLMResponse(
                            content="",
                            model="error",
                            provider="error",
                            duration_ms=0,
                            raw_response={"error": str(result)}
                        ),
                        passed=False,
                        evaluator_results=[],
                        timestamp=None
                    )
                    all_results.append(error_result)
                else:
                    all_results.append(result)
        
        return all_results
    
    async def xǁExecutionEngineǁrun_all__mutmut_41(
        self,
        treatments: list[str],
        progress: bool = False,
    ) -> list[ExecutionResult]:
        """Run all treatments and tasks.
        
        Args:
            treatments: List of treatment names to run
            progress: Show progress (not implemented yet)
            
        Returns:
            List of ExecutionResults
        """
        results = []
        
        # Get actual treatments from config
        available_treatments = {
            name: self.config.treatments.get(name, Treatment(skill_path=None))
            for name in treatments
        }
        
        # Add CONTROL if not present
        if "CONTROL" not in available_treatments:
            available_treatments["CONTROL"] = Treatment(skill_path=None)
        
        # Create tasks for each combination
        tasks_to_run = []
        for treatment_name in available_treatments:
            for task in self.config.tests:
                tasks_to_run.append((
                    available_treatments[treatment_name],
                    task,
                    treatment_name
                ))
        
        # Run with repetitions
        all_results = []
        repetitions = self.config.execution.repetitions
        
        for rep in range(repetitions):
            # Run all tasks
            coroutines = [
                self.run_single(treatment, task, treatment_name)
                for treatment, task, treatment_name in tasks_to_run
            ]
            
            # Execute concurrently (limited by semaphore)
            results = await asyncio.gather(*coroutines, return_exceptions=True)
            
            # Handle exceptions
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    # Create error result with minimal response
                    treatment, task, treatment_name = tasks_to_run[i]
                    error_result = ExecutionResult(
                        test=task.name,
                        prompt=task.prompt,
                        response=LLMResponse(
                            content="",
                            model="error",
                            provider="error",
                            duration_ms=0,
                            raw_response={"error": str(result)}
                        ),
                        passed=False,
                        evaluator_results=[],
                        timestamp=datetime.utcnow().isoformat()
                    )
                    all_results.append(error_result)
                else:
                    all_results.append(result)
        
        return all_results
    
    async def xǁExecutionEngineǁrun_all__mutmut_42(
        self,
        treatments: list[str],
        progress: bool = False,
    ) -> list[ExecutionResult]:
        """Run all treatments and tasks.
        
        Args:
            treatments: List of treatment names to run
            progress: Show progress (not implemented yet)
            
        Returns:
            List of ExecutionResults
        """
        results = []
        
        # Get actual treatments from config
        available_treatments = {
            name: self.config.treatments.get(name, Treatment(skill_path=None))
            for name in treatments
        }
        
        # Add CONTROL if not present
        if "CONTROL" not in available_treatments:
            available_treatments["CONTROL"] = Treatment(skill_path=None)
        
        # Create tasks for each combination
        tasks_to_run = []
        for treatment_name in available_treatments:
            for task in self.config.tests:
                tasks_to_run.append((
                    available_treatments[treatment_name],
                    task,
                    treatment_name
                ))
        
        # Run with repetitions
        all_results = []
        repetitions = self.config.execution.repetitions
        
        for rep in range(repetitions):
            # Run all tasks
            coroutines = [
                self.run_single(treatment, task, treatment_name)
                for treatment, task, treatment_name in tasks_to_run
            ]
            
            # Execute concurrently (limited by semaphore)
            results = await asyncio.gather(*coroutines, return_exceptions=True)
            
            # Handle exceptions
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    # Create error result with minimal response
                    treatment, task, treatment_name = tasks_to_run[i]
                    error_result = ExecutionResult(
                        treatment=treatment_name,
                        prompt=task.prompt,
                        response=LLMResponse(
                            content="",
                            model="error",
                            provider="error",
                            duration_ms=0,
                            raw_response={"error": str(result)}
                        ),
                        passed=False,
                        evaluator_results=[],
                        timestamp=datetime.utcnow().isoformat()
                    )
                    all_results.append(error_result)
                else:
                    all_results.append(result)
        
        return all_results
    
    async def xǁExecutionEngineǁrun_all__mutmut_43(
        self,
        treatments: list[str],
        progress: bool = False,
    ) -> list[ExecutionResult]:
        """Run all treatments and tasks.
        
        Args:
            treatments: List of treatment names to run
            progress: Show progress (not implemented yet)
            
        Returns:
            List of ExecutionResults
        """
        results = []
        
        # Get actual treatments from config
        available_treatments = {
            name: self.config.treatments.get(name, Treatment(skill_path=None))
            for name in treatments
        }
        
        # Add CONTROL if not present
        if "CONTROL" not in available_treatments:
            available_treatments["CONTROL"] = Treatment(skill_path=None)
        
        # Create tasks for each combination
        tasks_to_run = []
        for treatment_name in available_treatments:
            for task in self.config.tests:
                tasks_to_run.append((
                    available_treatments[treatment_name],
                    task,
                    treatment_name
                ))
        
        # Run with repetitions
        all_results = []
        repetitions = self.config.execution.repetitions
        
        for rep in range(repetitions):
            # Run all tasks
            coroutines = [
                self.run_single(treatment, task, treatment_name)
                for treatment, task, treatment_name in tasks_to_run
            ]
            
            # Execute concurrently (limited by semaphore)
            results = await asyncio.gather(*coroutines, return_exceptions=True)
            
            # Handle exceptions
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    # Create error result with minimal response
                    treatment, task, treatment_name = tasks_to_run[i]
                    error_result = ExecutionResult(
                        treatment=treatment_name,
                        test=task.name,
                        response=LLMResponse(
                            content="",
                            model="error",
                            provider="error",
                            duration_ms=0,
                            raw_response={"error": str(result)}
                        ),
                        passed=False,
                        evaluator_results=[],
                        timestamp=datetime.utcnow().isoformat()
                    )
                    all_results.append(error_result)
                else:
                    all_results.append(result)
        
        return all_results
    
    async def xǁExecutionEngineǁrun_all__mutmut_44(
        self,
        treatments: list[str],
        progress: bool = False,
    ) -> list[ExecutionResult]:
        """Run all treatments and tasks.
        
        Args:
            treatments: List of treatment names to run
            progress: Show progress (not implemented yet)
            
        Returns:
            List of ExecutionResults
        """
        results = []
        
        # Get actual treatments from config
        available_treatments = {
            name: self.config.treatments.get(name, Treatment(skill_path=None))
            for name in treatments
        }
        
        # Add CONTROL if not present
        if "CONTROL" not in available_treatments:
            available_treatments["CONTROL"] = Treatment(skill_path=None)
        
        # Create tasks for each combination
        tasks_to_run = []
        for treatment_name in available_treatments:
            for task in self.config.tests:
                tasks_to_run.append((
                    available_treatments[treatment_name],
                    task,
                    treatment_name
                ))
        
        # Run with repetitions
        all_results = []
        repetitions = self.config.execution.repetitions
        
        for rep in range(repetitions):
            # Run all tasks
            coroutines = [
                self.run_single(treatment, task, treatment_name)
                for treatment, task, treatment_name in tasks_to_run
            ]
            
            # Execute concurrently (limited by semaphore)
            results = await asyncio.gather(*coroutines, return_exceptions=True)
            
            # Handle exceptions
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    # Create error result with minimal response
                    treatment, task, treatment_name = tasks_to_run[i]
                    error_result = ExecutionResult(
                        treatment=treatment_name,
                        test=task.name,
                        prompt=task.prompt,
                        passed=False,
                        evaluator_results=[],
                        timestamp=datetime.utcnow().isoformat()
                    )
                    all_results.append(error_result)
                else:
                    all_results.append(result)
        
        return all_results
    
    async def xǁExecutionEngineǁrun_all__mutmut_45(
        self,
        treatments: list[str],
        progress: bool = False,
    ) -> list[ExecutionResult]:
        """Run all treatments and tasks.
        
        Args:
            treatments: List of treatment names to run
            progress: Show progress (not implemented yet)
            
        Returns:
            List of ExecutionResults
        """
        results = []
        
        # Get actual treatments from config
        available_treatments = {
            name: self.config.treatments.get(name, Treatment(skill_path=None))
            for name in treatments
        }
        
        # Add CONTROL if not present
        if "CONTROL" not in available_treatments:
            available_treatments["CONTROL"] = Treatment(skill_path=None)
        
        # Create tasks for each combination
        tasks_to_run = []
        for treatment_name in available_treatments:
            for task in self.config.tests:
                tasks_to_run.append((
                    available_treatments[treatment_name],
                    task,
                    treatment_name
                ))
        
        # Run with repetitions
        all_results = []
        repetitions = self.config.execution.repetitions
        
        for rep in range(repetitions):
            # Run all tasks
            coroutines = [
                self.run_single(treatment, task, treatment_name)
                for treatment, task, treatment_name in tasks_to_run
            ]
            
            # Execute concurrently (limited by semaphore)
            results = await asyncio.gather(*coroutines, return_exceptions=True)
            
            # Handle exceptions
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    # Create error result with minimal response
                    treatment, task, treatment_name = tasks_to_run[i]
                    error_result = ExecutionResult(
                        treatment=treatment_name,
                        test=task.name,
                        prompt=task.prompt,
                        response=LLMResponse(
                            content="",
                            model="error",
                            provider="error",
                            duration_ms=0,
                            raw_response={"error": str(result)}
                        ),
                        evaluator_results=[],
                        timestamp=datetime.utcnow().isoformat()
                    )
                    all_results.append(error_result)
                else:
                    all_results.append(result)
        
        return all_results
    
    async def xǁExecutionEngineǁrun_all__mutmut_46(
        self,
        treatments: list[str],
        progress: bool = False,
    ) -> list[ExecutionResult]:
        """Run all treatments and tasks.
        
        Args:
            treatments: List of treatment names to run
            progress: Show progress (not implemented yet)
            
        Returns:
            List of ExecutionResults
        """
        results = []
        
        # Get actual treatments from config
        available_treatments = {
            name: self.config.treatments.get(name, Treatment(skill_path=None))
            for name in treatments
        }
        
        # Add CONTROL if not present
        if "CONTROL" not in available_treatments:
            available_treatments["CONTROL"] = Treatment(skill_path=None)
        
        # Create tasks for each combination
        tasks_to_run = []
        for treatment_name in available_treatments:
            for task in self.config.tests:
                tasks_to_run.append((
                    available_treatments[treatment_name],
                    task,
                    treatment_name
                ))
        
        # Run with repetitions
        all_results = []
        repetitions = self.config.execution.repetitions
        
        for rep in range(repetitions):
            # Run all tasks
            coroutines = [
                self.run_single(treatment, task, treatment_name)
                for treatment, task, treatment_name in tasks_to_run
            ]
            
            # Execute concurrently (limited by semaphore)
            results = await asyncio.gather(*coroutines, return_exceptions=True)
            
            # Handle exceptions
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    # Create error result with minimal response
                    treatment, task, treatment_name = tasks_to_run[i]
                    error_result = ExecutionResult(
                        treatment=treatment_name,
                        test=task.name,
                        prompt=task.prompt,
                        response=LLMResponse(
                            content="",
                            model="error",
                            provider="error",
                            duration_ms=0,
                            raw_response={"error": str(result)}
                        ),
                        passed=False,
                        timestamp=datetime.utcnow().isoformat()
                    )
                    all_results.append(error_result)
                else:
                    all_results.append(result)
        
        return all_results
    
    async def xǁExecutionEngineǁrun_all__mutmut_47(
        self,
        treatments: list[str],
        progress: bool = False,
    ) -> list[ExecutionResult]:
        """Run all treatments and tasks.
        
        Args:
            treatments: List of treatment names to run
            progress: Show progress (not implemented yet)
            
        Returns:
            List of ExecutionResults
        """
        results = []
        
        # Get actual treatments from config
        available_treatments = {
            name: self.config.treatments.get(name, Treatment(skill_path=None))
            for name in treatments
        }
        
        # Add CONTROL if not present
        if "CONTROL" not in available_treatments:
            available_treatments["CONTROL"] = Treatment(skill_path=None)
        
        # Create tasks for each combination
        tasks_to_run = []
        for treatment_name in available_treatments:
            for task in self.config.tests:
                tasks_to_run.append((
                    available_treatments[treatment_name],
                    task,
                    treatment_name
                ))
        
        # Run with repetitions
        all_results = []
        repetitions = self.config.execution.repetitions
        
        for rep in range(repetitions):
            # Run all tasks
            coroutines = [
                self.run_single(treatment, task, treatment_name)
                for treatment, task, treatment_name in tasks_to_run
            ]
            
            # Execute concurrently (limited by semaphore)
            results = await asyncio.gather(*coroutines, return_exceptions=True)
            
            # Handle exceptions
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    # Create error result with minimal response
                    treatment, task, treatment_name = tasks_to_run[i]
                    error_result = ExecutionResult(
                        treatment=treatment_name,
                        test=task.name,
                        prompt=task.prompt,
                        response=LLMResponse(
                            content="",
                            model="error",
                            provider="error",
                            duration_ms=0,
                            raw_response={"error": str(result)}
                        ),
                        passed=False,
                        evaluator_results=[],
                        )
                    all_results.append(error_result)
                else:
                    all_results.append(result)
        
        return all_results
    
    async def xǁExecutionEngineǁrun_all__mutmut_48(
        self,
        treatments: list[str],
        progress: bool = False,
    ) -> list[ExecutionResult]:
        """Run all treatments and tasks.
        
        Args:
            treatments: List of treatment names to run
            progress: Show progress (not implemented yet)
            
        Returns:
            List of ExecutionResults
        """
        results = []
        
        # Get actual treatments from config
        available_treatments = {
            name: self.config.treatments.get(name, Treatment(skill_path=None))
            for name in treatments
        }
        
        # Add CONTROL if not present
        if "CONTROL" not in available_treatments:
            available_treatments["CONTROL"] = Treatment(skill_path=None)
        
        # Create tasks for each combination
        tasks_to_run = []
        for treatment_name in available_treatments:
            for task in self.config.tests:
                tasks_to_run.append((
                    available_treatments[treatment_name],
                    task,
                    treatment_name
                ))
        
        # Run with repetitions
        all_results = []
        repetitions = self.config.execution.repetitions
        
        for rep in range(repetitions):
            # Run all tasks
            coroutines = [
                self.run_single(treatment, task, treatment_name)
                for treatment, task, treatment_name in tasks_to_run
            ]
            
            # Execute concurrently (limited by semaphore)
            results = await asyncio.gather(*coroutines, return_exceptions=True)
            
            # Handle exceptions
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    # Create error result with minimal response
                    treatment, task, treatment_name = tasks_to_run[i]
                    error_result = ExecutionResult(
                        treatment=treatment_name,
                        test=task.name,
                        prompt=task.prompt,
                        response=LLMResponse(
                            content=None,
                            model="error",
                            provider="error",
                            duration_ms=0,
                            raw_response={"error": str(result)}
                        ),
                        passed=False,
                        evaluator_results=[],
                        timestamp=datetime.utcnow().isoformat()
                    )
                    all_results.append(error_result)
                else:
                    all_results.append(result)
        
        return all_results
    
    async def xǁExecutionEngineǁrun_all__mutmut_49(
        self,
        treatments: list[str],
        progress: bool = False,
    ) -> list[ExecutionResult]:
        """Run all treatments and tasks.
        
        Args:
            treatments: List of treatment names to run
            progress: Show progress (not implemented yet)
            
        Returns:
            List of ExecutionResults
        """
        results = []
        
        # Get actual treatments from config
        available_treatments = {
            name: self.config.treatments.get(name, Treatment(skill_path=None))
            for name in treatments
        }
        
        # Add CONTROL if not present
        if "CONTROL" not in available_treatments:
            available_treatments["CONTROL"] = Treatment(skill_path=None)
        
        # Create tasks for each combination
        tasks_to_run = []
        for treatment_name in available_treatments:
            for task in self.config.tests:
                tasks_to_run.append((
                    available_treatments[treatment_name],
                    task,
                    treatment_name
                ))
        
        # Run with repetitions
        all_results = []
        repetitions = self.config.execution.repetitions
        
        for rep in range(repetitions):
            # Run all tasks
            coroutines = [
                self.run_single(treatment, task, treatment_name)
                for treatment, task, treatment_name in tasks_to_run
            ]
            
            # Execute concurrently (limited by semaphore)
            results = await asyncio.gather(*coroutines, return_exceptions=True)
            
            # Handle exceptions
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    # Create error result with minimal response
                    treatment, task, treatment_name = tasks_to_run[i]
                    error_result = ExecutionResult(
                        treatment=treatment_name,
                        test=task.name,
                        prompt=task.prompt,
                        response=LLMResponse(
                            content="",
                            model=None,
                            provider="error",
                            duration_ms=0,
                            raw_response={"error": str(result)}
                        ),
                        passed=False,
                        evaluator_results=[],
                        timestamp=datetime.utcnow().isoformat()
                    )
                    all_results.append(error_result)
                else:
                    all_results.append(result)
        
        return all_results
    
    async def xǁExecutionEngineǁrun_all__mutmut_50(
        self,
        treatments: list[str],
        progress: bool = False,
    ) -> list[ExecutionResult]:
        """Run all treatments and tasks.
        
        Args:
            treatments: List of treatment names to run
            progress: Show progress (not implemented yet)
            
        Returns:
            List of ExecutionResults
        """
        results = []
        
        # Get actual treatments from config
        available_treatments = {
            name: self.config.treatments.get(name, Treatment(skill_path=None))
            for name in treatments
        }
        
        # Add CONTROL if not present
        if "CONTROL" not in available_treatments:
            available_treatments["CONTROL"] = Treatment(skill_path=None)
        
        # Create tasks for each combination
        tasks_to_run = []
        for treatment_name in available_treatments:
            for task in self.config.tests:
                tasks_to_run.append((
                    available_treatments[treatment_name],
                    task,
                    treatment_name
                ))
        
        # Run with repetitions
        all_results = []
        repetitions = self.config.execution.repetitions
        
        for rep in range(repetitions):
            # Run all tasks
            coroutines = [
                self.run_single(treatment, task, treatment_name)
                for treatment, task, treatment_name in tasks_to_run
            ]
            
            # Execute concurrently (limited by semaphore)
            results = await asyncio.gather(*coroutines, return_exceptions=True)
            
            # Handle exceptions
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    # Create error result with minimal response
                    treatment, task, treatment_name = tasks_to_run[i]
                    error_result = ExecutionResult(
                        treatment=treatment_name,
                        test=task.name,
                        prompt=task.prompt,
                        response=LLMResponse(
                            content="",
                            model="error",
                            provider=None,
                            duration_ms=0,
                            raw_response={"error": str(result)}
                        ),
                        passed=False,
                        evaluator_results=[],
                        timestamp=datetime.utcnow().isoformat()
                    )
                    all_results.append(error_result)
                else:
                    all_results.append(result)
        
        return all_results
    
    async def xǁExecutionEngineǁrun_all__mutmut_51(
        self,
        treatments: list[str],
        progress: bool = False,
    ) -> list[ExecutionResult]:
        """Run all treatments and tasks.
        
        Args:
            treatments: List of treatment names to run
            progress: Show progress (not implemented yet)
            
        Returns:
            List of ExecutionResults
        """
        results = []
        
        # Get actual treatments from config
        available_treatments = {
            name: self.config.treatments.get(name, Treatment(skill_path=None))
            for name in treatments
        }
        
        # Add CONTROL if not present
        if "CONTROL" not in available_treatments:
            available_treatments["CONTROL"] = Treatment(skill_path=None)
        
        # Create tasks for each combination
        tasks_to_run = []
        for treatment_name in available_treatments:
            for task in self.config.tests:
                tasks_to_run.append((
                    available_treatments[treatment_name],
                    task,
                    treatment_name
                ))
        
        # Run with repetitions
        all_results = []
        repetitions = self.config.execution.repetitions
        
        for rep in range(repetitions):
            # Run all tasks
            coroutines = [
                self.run_single(treatment, task, treatment_name)
                for treatment, task, treatment_name in tasks_to_run
            ]
            
            # Execute concurrently (limited by semaphore)
            results = await asyncio.gather(*coroutines, return_exceptions=True)
            
            # Handle exceptions
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    # Create error result with minimal response
                    treatment, task, treatment_name = tasks_to_run[i]
                    error_result = ExecutionResult(
                        treatment=treatment_name,
                        test=task.name,
                        prompt=task.prompt,
                        response=LLMResponse(
                            content="",
                            model="error",
                            provider="error",
                            duration_ms=None,
                            raw_response={"error": str(result)}
                        ),
                        passed=False,
                        evaluator_results=[],
                        timestamp=datetime.utcnow().isoformat()
                    )
                    all_results.append(error_result)
                else:
                    all_results.append(result)
        
        return all_results
    
    async def xǁExecutionEngineǁrun_all__mutmut_52(
        self,
        treatments: list[str],
        progress: bool = False,
    ) -> list[ExecutionResult]:
        """Run all treatments and tasks.
        
        Args:
            treatments: List of treatment names to run
            progress: Show progress (not implemented yet)
            
        Returns:
            List of ExecutionResults
        """
        results = []
        
        # Get actual treatments from config
        available_treatments = {
            name: self.config.treatments.get(name, Treatment(skill_path=None))
            for name in treatments
        }
        
        # Add CONTROL if not present
        if "CONTROL" not in available_treatments:
            available_treatments["CONTROL"] = Treatment(skill_path=None)
        
        # Create tasks for each combination
        tasks_to_run = []
        for treatment_name in available_treatments:
            for task in self.config.tests:
                tasks_to_run.append((
                    available_treatments[treatment_name],
                    task,
                    treatment_name
                ))
        
        # Run with repetitions
        all_results = []
        repetitions = self.config.execution.repetitions
        
        for rep in range(repetitions):
            # Run all tasks
            coroutines = [
                self.run_single(treatment, task, treatment_name)
                for treatment, task, treatment_name in tasks_to_run
            ]
            
            # Execute concurrently (limited by semaphore)
            results = await asyncio.gather(*coroutines, return_exceptions=True)
            
            # Handle exceptions
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    # Create error result with minimal response
                    treatment, task, treatment_name = tasks_to_run[i]
                    error_result = ExecutionResult(
                        treatment=treatment_name,
                        test=task.name,
                        prompt=task.prompt,
                        response=LLMResponse(
                            content="",
                            model="error",
                            provider="error",
                            duration_ms=0,
                            raw_response=None
                        ),
                        passed=False,
                        evaluator_results=[],
                        timestamp=datetime.utcnow().isoformat()
                    )
                    all_results.append(error_result)
                else:
                    all_results.append(result)
        
        return all_results
    
    async def xǁExecutionEngineǁrun_all__mutmut_53(
        self,
        treatments: list[str],
        progress: bool = False,
    ) -> list[ExecutionResult]:
        """Run all treatments and tasks.
        
        Args:
            treatments: List of treatment names to run
            progress: Show progress (not implemented yet)
            
        Returns:
            List of ExecutionResults
        """
        results = []
        
        # Get actual treatments from config
        available_treatments = {
            name: self.config.treatments.get(name, Treatment(skill_path=None))
            for name in treatments
        }
        
        # Add CONTROL if not present
        if "CONTROL" not in available_treatments:
            available_treatments["CONTROL"] = Treatment(skill_path=None)
        
        # Create tasks for each combination
        tasks_to_run = []
        for treatment_name in available_treatments:
            for task in self.config.tests:
                tasks_to_run.append((
                    available_treatments[treatment_name],
                    task,
                    treatment_name
                ))
        
        # Run with repetitions
        all_results = []
        repetitions = self.config.execution.repetitions
        
        for rep in range(repetitions):
            # Run all tasks
            coroutines = [
                self.run_single(treatment, task, treatment_name)
                for treatment, task, treatment_name in tasks_to_run
            ]
            
            # Execute concurrently (limited by semaphore)
            results = await asyncio.gather(*coroutines, return_exceptions=True)
            
            # Handle exceptions
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    # Create error result with minimal response
                    treatment, task, treatment_name = tasks_to_run[i]
                    error_result = ExecutionResult(
                        treatment=treatment_name,
                        test=task.name,
                        prompt=task.prompt,
                        response=LLMResponse(
                            model="error",
                            provider="error",
                            duration_ms=0,
                            raw_response={"error": str(result)}
                        ),
                        passed=False,
                        evaluator_results=[],
                        timestamp=datetime.utcnow().isoformat()
                    )
                    all_results.append(error_result)
                else:
                    all_results.append(result)
        
        return all_results
    
    async def xǁExecutionEngineǁrun_all__mutmut_54(
        self,
        treatments: list[str],
        progress: bool = False,
    ) -> list[ExecutionResult]:
        """Run all treatments and tasks.
        
        Args:
            treatments: List of treatment names to run
            progress: Show progress (not implemented yet)
            
        Returns:
            List of ExecutionResults
        """
        results = []
        
        # Get actual treatments from config
        available_treatments = {
            name: self.config.treatments.get(name, Treatment(skill_path=None))
            for name in treatments
        }
        
        # Add CONTROL if not present
        if "CONTROL" not in available_treatments:
            available_treatments["CONTROL"] = Treatment(skill_path=None)
        
        # Create tasks for each combination
        tasks_to_run = []
        for treatment_name in available_treatments:
            for task in self.config.tests:
                tasks_to_run.append((
                    available_treatments[treatment_name],
                    task,
                    treatment_name
                ))
        
        # Run with repetitions
        all_results = []
        repetitions = self.config.execution.repetitions
        
        for rep in range(repetitions):
            # Run all tasks
            coroutines = [
                self.run_single(treatment, task, treatment_name)
                for treatment, task, treatment_name in tasks_to_run
            ]
            
            # Execute concurrently (limited by semaphore)
            results = await asyncio.gather(*coroutines, return_exceptions=True)
            
            # Handle exceptions
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    # Create error result with minimal response
                    treatment, task, treatment_name = tasks_to_run[i]
                    error_result = ExecutionResult(
                        treatment=treatment_name,
                        test=task.name,
                        prompt=task.prompt,
                        response=LLMResponse(
                            content="",
                            provider="error",
                            duration_ms=0,
                            raw_response={"error": str(result)}
                        ),
                        passed=False,
                        evaluator_results=[],
                        timestamp=datetime.utcnow().isoformat()
                    )
                    all_results.append(error_result)
                else:
                    all_results.append(result)
        
        return all_results
    
    async def xǁExecutionEngineǁrun_all__mutmut_55(
        self,
        treatments: list[str],
        progress: bool = False,
    ) -> list[ExecutionResult]:
        """Run all treatments and tasks.
        
        Args:
            treatments: List of treatment names to run
            progress: Show progress (not implemented yet)
            
        Returns:
            List of ExecutionResults
        """
        results = []
        
        # Get actual treatments from config
        available_treatments = {
            name: self.config.treatments.get(name, Treatment(skill_path=None))
            for name in treatments
        }
        
        # Add CONTROL if not present
        if "CONTROL" not in available_treatments:
            available_treatments["CONTROL"] = Treatment(skill_path=None)
        
        # Create tasks for each combination
        tasks_to_run = []
        for treatment_name in available_treatments:
            for task in self.config.tests:
                tasks_to_run.append((
                    available_treatments[treatment_name],
                    task,
                    treatment_name
                ))
        
        # Run with repetitions
        all_results = []
        repetitions = self.config.execution.repetitions
        
        for rep in range(repetitions):
            # Run all tasks
            coroutines = [
                self.run_single(treatment, task, treatment_name)
                for treatment, task, treatment_name in tasks_to_run
            ]
            
            # Execute concurrently (limited by semaphore)
            results = await asyncio.gather(*coroutines, return_exceptions=True)
            
            # Handle exceptions
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    # Create error result with minimal response
                    treatment, task, treatment_name = tasks_to_run[i]
                    error_result = ExecutionResult(
                        treatment=treatment_name,
                        test=task.name,
                        prompt=task.prompt,
                        response=LLMResponse(
                            content="",
                            model="error",
                            duration_ms=0,
                            raw_response={"error": str(result)}
                        ),
                        passed=False,
                        evaluator_results=[],
                        timestamp=datetime.utcnow().isoformat()
                    )
                    all_results.append(error_result)
                else:
                    all_results.append(result)
        
        return all_results
    
    async def xǁExecutionEngineǁrun_all__mutmut_56(
        self,
        treatments: list[str],
        progress: bool = False,
    ) -> list[ExecutionResult]:
        """Run all treatments and tasks.
        
        Args:
            treatments: List of treatment names to run
            progress: Show progress (not implemented yet)
            
        Returns:
            List of ExecutionResults
        """
        results = []
        
        # Get actual treatments from config
        available_treatments = {
            name: self.config.treatments.get(name, Treatment(skill_path=None))
            for name in treatments
        }
        
        # Add CONTROL if not present
        if "CONTROL" not in available_treatments:
            available_treatments["CONTROL"] = Treatment(skill_path=None)
        
        # Create tasks for each combination
        tasks_to_run = []
        for treatment_name in available_treatments:
            for task in self.config.tests:
                tasks_to_run.append((
                    available_treatments[treatment_name],
                    task,
                    treatment_name
                ))
        
        # Run with repetitions
        all_results = []
        repetitions = self.config.execution.repetitions
        
        for rep in range(repetitions):
            # Run all tasks
            coroutines = [
                self.run_single(treatment, task, treatment_name)
                for treatment, task, treatment_name in tasks_to_run
            ]
            
            # Execute concurrently (limited by semaphore)
            results = await asyncio.gather(*coroutines, return_exceptions=True)
            
            # Handle exceptions
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    # Create error result with minimal response
                    treatment, task, treatment_name = tasks_to_run[i]
                    error_result = ExecutionResult(
                        treatment=treatment_name,
                        test=task.name,
                        prompt=task.prompt,
                        response=LLMResponse(
                            content="",
                            model="error",
                            provider="error",
                            raw_response={"error": str(result)}
                        ),
                        passed=False,
                        evaluator_results=[],
                        timestamp=datetime.utcnow().isoformat()
                    )
                    all_results.append(error_result)
                else:
                    all_results.append(result)
        
        return all_results
    
    async def xǁExecutionEngineǁrun_all__mutmut_57(
        self,
        treatments: list[str],
        progress: bool = False,
    ) -> list[ExecutionResult]:
        """Run all treatments and tasks.
        
        Args:
            treatments: List of treatment names to run
            progress: Show progress (not implemented yet)
            
        Returns:
            List of ExecutionResults
        """
        results = []
        
        # Get actual treatments from config
        available_treatments = {
            name: self.config.treatments.get(name, Treatment(skill_path=None))
            for name in treatments
        }
        
        # Add CONTROL if not present
        if "CONTROL" not in available_treatments:
            available_treatments["CONTROL"] = Treatment(skill_path=None)
        
        # Create tasks for each combination
        tasks_to_run = []
        for treatment_name in available_treatments:
            for task in self.config.tests:
                tasks_to_run.append((
                    available_treatments[treatment_name],
                    task,
                    treatment_name
                ))
        
        # Run with repetitions
        all_results = []
        repetitions = self.config.execution.repetitions
        
        for rep in range(repetitions):
            # Run all tasks
            coroutines = [
                self.run_single(treatment, task, treatment_name)
                for treatment, task, treatment_name in tasks_to_run
            ]
            
            # Execute concurrently (limited by semaphore)
            results = await asyncio.gather(*coroutines, return_exceptions=True)
            
            # Handle exceptions
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    # Create error result with minimal response
                    treatment, task, treatment_name = tasks_to_run[i]
                    error_result = ExecutionResult(
                        treatment=treatment_name,
                        test=task.name,
                        prompt=task.prompt,
                        response=LLMResponse(
                            content="",
                            model="error",
                            provider="error",
                            duration_ms=0,
                            ),
                        passed=False,
                        evaluator_results=[],
                        timestamp=datetime.utcnow().isoformat()
                    )
                    all_results.append(error_result)
                else:
                    all_results.append(result)
        
        return all_results
    
    async def xǁExecutionEngineǁrun_all__mutmut_58(
        self,
        treatments: list[str],
        progress: bool = False,
    ) -> list[ExecutionResult]:
        """Run all treatments and tasks.
        
        Args:
            treatments: List of treatment names to run
            progress: Show progress (not implemented yet)
            
        Returns:
            List of ExecutionResults
        """
        results = []
        
        # Get actual treatments from config
        available_treatments = {
            name: self.config.treatments.get(name, Treatment(skill_path=None))
            for name in treatments
        }
        
        # Add CONTROL if not present
        if "CONTROL" not in available_treatments:
            available_treatments["CONTROL"] = Treatment(skill_path=None)
        
        # Create tasks for each combination
        tasks_to_run = []
        for treatment_name in available_treatments:
            for task in self.config.tests:
                tasks_to_run.append((
                    available_treatments[treatment_name],
                    task,
                    treatment_name
                ))
        
        # Run with repetitions
        all_results = []
        repetitions = self.config.execution.repetitions
        
        for rep in range(repetitions):
            # Run all tasks
            coroutines = [
                self.run_single(treatment, task, treatment_name)
                for treatment, task, treatment_name in tasks_to_run
            ]
            
            # Execute concurrently (limited by semaphore)
            results = await asyncio.gather(*coroutines, return_exceptions=True)
            
            # Handle exceptions
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    # Create error result with minimal response
                    treatment, task, treatment_name = tasks_to_run[i]
                    error_result = ExecutionResult(
                        treatment=treatment_name,
                        test=task.name,
                        prompt=task.prompt,
                        response=LLMResponse(
                            content="XXXX",
                            model="error",
                            provider="error",
                            duration_ms=0,
                            raw_response={"error": str(result)}
                        ),
                        passed=False,
                        evaluator_results=[],
                        timestamp=datetime.utcnow().isoformat()
                    )
                    all_results.append(error_result)
                else:
                    all_results.append(result)
        
        return all_results
    
    async def xǁExecutionEngineǁrun_all__mutmut_59(
        self,
        treatments: list[str],
        progress: bool = False,
    ) -> list[ExecutionResult]:
        """Run all treatments and tasks.
        
        Args:
            treatments: List of treatment names to run
            progress: Show progress (not implemented yet)
            
        Returns:
            List of ExecutionResults
        """
        results = []
        
        # Get actual treatments from config
        available_treatments = {
            name: self.config.treatments.get(name, Treatment(skill_path=None))
            for name in treatments
        }
        
        # Add CONTROL if not present
        if "CONTROL" not in available_treatments:
            available_treatments["CONTROL"] = Treatment(skill_path=None)
        
        # Create tasks for each combination
        tasks_to_run = []
        for treatment_name in available_treatments:
            for task in self.config.tests:
                tasks_to_run.append((
                    available_treatments[treatment_name],
                    task,
                    treatment_name
                ))
        
        # Run with repetitions
        all_results = []
        repetitions = self.config.execution.repetitions
        
        for rep in range(repetitions):
            # Run all tasks
            coroutines = [
                self.run_single(treatment, task, treatment_name)
                for treatment, task, treatment_name in tasks_to_run
            ]
            
            # Execute concurrently (limited by semaphore)
            results = await asyncio.gather(*coroutines, return_exceptions=True)
            
            # Handle exceptions
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    # Create error result with minimal response
                    treatment, task, treatment_name = tasks_to_run[i]
                    error_result = ExecutionResult(
                        treatment=treatment_name,
                        test=task.name,
                        prompt=task.prompt,
                        response=LLMResponse(
                            content="",
                            model="XXerrorXX",
                            provider="error",
                            duration_ms=0,
                            raw_response={"error": str(result)}
                        ),
                        passed=False,
                        evaluator_results=[],
                        timestamp=datetime.utcnow().isoformat()
                    )
                    all_results.append(error_result)
                else:
                    all_results.append(result)
        
        return all_results
    
    async def xǁExecutionEngineǁrun_all__mutmut_60(
        self,
        treatments: list[str],
        progress: bool = False,
    ) -> list[ExecutionResult]:
        """Run all treatments and tasks.
        
        Args:
            treatments: List of treatment names to run
            progress: Show progress (not implemented yet)
            
        Returns:
            List of ExecutionResults
        """
        results = []
        
        # Get actual treatments from config
        available_treatments = {
            name: self.config.treatments.get(name, Treatment(skill_path=None))
            for name in treatments
        }
        
        # Add CONTROL if not present
        if "CONTROL" not in available_treatments:
            available_treatments["CONTROL"] = Treatment(skill_path=None)
        
        # Create tasks for each combination
        tasks_to_run = []
        for treatment_name in available_treatments:
            for task in self.config.tests:
                tasks_to_run.append((
                    available_treatments[treatment_name],
                    task,
                    treatment_name
                ))
        
        # Run with repetitions
        all_results = []
        repetitions = self.config.execution.repetitions
        
        for rep in range(repetitions):
            # Run all tasks
            coroutines = [
                self.run_single(treatment, task, treatment_name)
                for treatment, task, treatment_name in tasks_to_run
            ]
            
            # Execute concurrently (limited by semaphore)
            results = await asyncio.gather(*coroutines, return_exceptions=True)
            
            # Handle exceptions
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    # Create error result with minimal response
                    treatment, task, treatment_name = tasks_to_run[i]
                    error_result = ExecutionResult(
                        treatment=treatment_name,
                        test=task.name,
                        prompt=task.prompt,
                        response=LLMResponse(
                            content="",
                            model="ERROR",
                            provider="error",
                            duration_ms=0,
                            raw_response={"error": str(result)}
                        ),
                        passed=False,
                        evaluator_results=[],
                        timestamp=datetime.utcnow().isoformat()
                    )
                    all_results.append(error_result)
                else:
                    all_results.append(result)
        
        return all_results
    
    async def xǁExecutionEngineǁrun_all__mutmut_61(
        self,
        treatments: list[str],
        progress: bool = False,
    ) -> list[ExecutionResult]:
        """Run all treatments and tasks.
        
        Args:
            treatments: List of treatment names to run
            progress: Show progress (not implemented yet)
            
        Returns:
            List of ExecutionResults
        """
        results = []
        
        # Get actual treatments from config
        available_treatments = {
            name: self.config.treatments.get(name, Treatment(skill_path=None))
            for name in treatments
        }
        
        # Add CONTROL if not present
        if "CONTROL" not in available_treatments:
            available_treatments["CONTROL"] = Treatment(skill_path=None)
        
        # Create tasks for each combination
        tasks_to_run = []
        for treatment_name in available_treatments:
            for task in self.config.tests:
                tasks_to_run.append((
                    available_treatments[treatment_name],
                    task,
                    treatment_name
                ))
        
        # Run with repetitions
        all_results = []
        repetitions = self.config.execution.repetitions
        
        for rep in range(repetitions):
            # Run all tasks
            coroutines = [
                self.run_single(treatment, task, treatment_name)
                for treatment, task, treatment_name in tasks_to_run
            ]
            
            # Execute concurrently (limited by semaphore)
            results = await asyncio.gather(*coroutines, return_exceptions=True)
            
            # Handle exceptions
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    # Create error result with minimal response
                    treatment, task, treatment_name = tasks_to_run[i]
                    error_result = ExecutionResult(
                        treatment=treatment_name,
                        test=task.name,
                        prompt=task.prompt,
                        response=LLMResponse(
                            content="",
                            model="error",
                            provider="XXerrorXX",
                            duration_ms=0,
                            raw_response={"error": str(result)}
                        ),
                        passed=False,
                        evaluator_results=[],
                        timestamp=datetime.utcnow().isoformat()
                    )
                    all_results.append(error_result)
                else:
                    all_results.append(result)
        
        return all_results
    
    async def xǁExecutionEngineǁrun_all__mutmut_62(
        self,
        treatments: list[str],
        progress: bool = False,
    ) -> list[ExecutionResult]:
        """Run all treatments and tasks.
        
        Args:
            treatments: List of treatment names to run
            progress: Show progress (not implemented yet)
            
        Returns:
            List of ExecutionResults
        """
        results = []
        
        # Get actual treatments from config
        available_treatments = {
            name: self.config.treatments.get(name, Treatment(skill_path=None))
            for name in treatments
        }
        
        # Add CONTROL if not present
        if "CONTROL" not in available_treatments:
            available_treatments["CONTROL"] = Treatment(skill_path=None)
        
        # Create tasks for each combination
        tasks_to_run = []
        for treatment_name in available_treatments:
            for task in self.config.tests:
                tasks_to_run.append((
                    available_treatments[treatment_name],
                    task,
                    treatment_name
                ))
        
        # Run with repetitions
        all_results = []
        repetitions = self.config.execution.repetitions
        
        for rep in range(repetitions):
            # Run all tasks
            coroutines = [
                self.run_single(treatment, task, treatment_name)
                for treatment, task, treatment_name in tasks_to_run
            ]
            
            # Execute concurrently (limited by semaphore)
            results = await asyncio.gather(*coroutines, return_exceptions=True)
            
            # Handle exceptions
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    # Create error result with minimal response
                    treatment, task, treatment_name = tasks_to_run[i]
                    error_result = ExecutionResult(
                        treatment=treatment_name,
                        test=task.name,
                        prompt=task.prompt,
                        response=LLMResponse(
                            content="",
                            model="error",
                            provider="ERROR",
                            duration_ms=0,
                            raw_response={"error": str(result)}
                        ),
                        passed=False,
                        evaluator_results=[],
                        timestamp=datetime.utcnow().isoformat()
                    )
                    all_results.append(error_result)
                else:
                    all_results.append(result)
        
        return all_results
    
    async def xǁExecutionEngineǁrun_all__mutmut_63(
        self,
        treatments: list[str],
        progress: bool = False,
    ) -> list[ExecutionResult]:
        """Run all treatments and tasks.
        
        Args:
            treatments: List of treatment names to run
            progress: Show progress (not implemented yet)
            
        Returns:
            List of ExecutionResults
        """
        results = []
        
        # Get actual treatments from config
        available_treatments = {
            name: self.config.treatments.get(name, Treatment(skill_path=None))
            for name in treatments
        }
        
        # Add CONTROL if not present
        if "CONTROL" not in available_treatments:
            available_treatments["CONTROL"] = Treatment(skill_path=None)
        
        # Create tasks for each combination
        tasks_to_run = []
        for treatment_name in available_treatments:
            for task in self.config.tests:
                tasks_to_run.append((
                    available_treatments[treatment_name],
                    task,
                    treatment_name
                ))
        
        # Run with repetitions
        all_results = []
        repetitions = self.config.execution.repetitions
        
        for rep in range(repetitions):
            # Run all tasks
            coroutines = [
                self.run_single(treatment, task, treatment_name)
                for treatment, task, treatment_name in tasks_to_run
            ]
            
            # Execute concurrently (limited by semaphore)
            results = await asyncio.gather(*coroutines, return_exceptions=True)
            
            # Handle exceptions
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    # Create error result with minimal response
                    treatment, task, treatment_name = tasks_to_run[i]
                    error_result = ExecutionResult(
                        treatment=treatment_name,
                        test=task.name,
                        prompt=task.prompt,
                        response=LLMResponse(
                            content="",
                            model="error",
                            provider="error",
                            duration_ms=1,
                            raw_response={"error": str(result)}
                        ),
                        passed=False,
                        evaluator_results=[],
                        timestamp=datetime.utcnow().isoformat()
                    )
                    all_results.append(error_result)
                else:
                    all_results.append(result)
        
        return all_results
    
    async def xǁExecutionEngineǁrun_all__mutmut_64(
        self,
        treatments: list[str],
        progress: bool = False,
    ) -> list[ExecutionResult]:
        """Run all treatments and tasks.
        
        Args:
            treatments: List of treatment names to run
            progress: Show progress (not implemented yet)
            
        Returns:
            List of ExecutionResults
        """
        results = []
        
        # Get actual treatments from config
        available_treatments = {
            name: self.config.treatments.get(name, Treatment(skill_path=None))
            for name in treatments
        }
        
        # Add CONTROL if not present
        if "CONTROL" not in available_treatments:
            available_treatments["CONTROL"] = Treatment(skill_path=None)
        
        # Create tasks for each combination
        tasks_to_run = []
        for treatment_name in available_treatments:
            for task in self.config.tests:
                tasks_to_run.append((
                    available_treatments[treatment_name],
                    task,
                    treatment_name
                ))
        
        # Run with repetitions
        all_results = []
        repetitions = self.config.execution.repetitions
        
        for rep in range(repetitions):
            # Run all tasks
            coroutines = [
                self.run_single(treatment, task, treatment_name)
                for treatment, task, treatment_name in tasks_to_run
            ]
            
            # Execute concurrently (limited by semaphore)
            results = await asyncio.gather(*coroutines, return_exceptions=True)
            
            # Handle exceptions
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    # Create error result with minimal response
                    treatment, task, treatment_name = tasks_to_run[i]
                    error_result = ExecutionResult(
                        treatment=treatment_name,
                        test=task.name,
                        prompt=task.prompt,
                        response=LLMResponse(
                            content="",
                            model="error",
                            provider="error",
                            duration_ms=0,
                            raw_response={"XXerrorXX": str(result)}
                        ),
                        passed=False,
                        evaluator_results=[],
                        timestamp=datetime.utcnow().isoformat()
                    )
                    all_results.append(error_result)
                else:
                    all_results.append(result)
        
        return all_results
    
    async def xǁExecutionEngineǁrun_all__mutmut_65(
        self,
        treatments: list[str],
        progress: bool = False,
    ) -> list[ExecutionResult]:
        """Run all treatments and tasks.
        
        Args:
            treatments: List of treatment names to run
            progress: Show progress (not implemented yet)
            
        Returns:
            List of ExecutionResults
        """
        results = []
        
        # Get actual treatments from config
        available_treatments = {
            name: self.config.treatments.get(name, Treatment(skill_path=None))
            for name in treatments
        }
        
        # Add CONTROL if not present
        if "CONTROL" not in available_treatments:
            available_treatments["CONTROL"] = Treatment(skill_path=None)
        
        # Create tasks for each combination
        tasks_to_run = []
        for treatment_name in available_treatments:
            for task in self.config.tests:
                tasks_to_run.append((
                    available_treatments[treatment_name],
                    task,
                    treatment_name
                ))
        
        # Run with repetitions
        all_results = []
        repetitions = self.config.execution.repetitions
        
        for rep in range(repetitions):
            # Run all tasks
            coroutines = [
                self.run_single(treatment, task, treatment_name)
                for treatment, task, treatment_name in tasks_to_run
            ]
            
            # Execute concurrently (limited by semaphore)
            results = await asyncio.gather(*coroutines, return_exceptions=True)
            
            # Handle exceptions
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    # Create error result with minimal response
                    treatment, task, treatment_name = tasks_to_run[i]
                    error_result = ExecutionResult(
                        treatment=treatment_name,
                        test=task.name,
                        prompt=task.prompt,
                        response=LLMResponse(
                            content="",
                            model="error",
                            provider="error",
                            duration_ms=0,
                            raw_response={"ERROR": str(result)}
                        ),
                        passed=False,
                        evaluator_results=[],
                        timestamp=datetime.utcnow().isoformat()
                    )
                    all_results.append(error_result)
                else:
                    all_results.append(result)
        
        return all_results
    
    async def xǁExecutionEngineǁrun_all__mutmut_66(
        self,
        treatments: list[str],
        progress: bool = False,
    ) -> list[ExecutionResult]:
        """Run all treatments and tasks.
        
        Args:
            treatments: List of treatment names to run
            progress: Show progress (not implemented yet)
            
        Returns:
            List of ExecutionResults
        """
        results = []
        
        # Get actual treatments from config
        available_treatments = {
            name: self.config.treatments.get(name, Treatment(skill_path=None))
            for name in treatments
        }
        
        # Add CONTROL if not present
        if "CONTROL" not in available_treatments:
            available_treatments["CONTROL"] = Treatment(skill_path=None)
        
        # Create tasks for each combination
        tasks_to_run = []
        for treatment_name in available_treatments:
            for task in self.config.tests:
                tasks_to_run.append((
                    available_treatments[treatment_name],
                    task,
                    treatment_name
                ))
        
        # Run with repetitions
        all_results = []
        repetitions = self.config.execution.repetitions
        
        for rep in range(repetitions):
            # Run all tasks
            coroutines = [
                self.run_single(treatment, task, treatment_name)
                for treatment, task, treatment_name in tasks_to_run
            ]
            
            # Execute concurrently (limited by semaphore)
            results = await asyncio.gather(*coroutines, return_exceptions=True)
            
            # Handle exceptions
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    # Create error result with minimal response
                    treatment, task, treatment_name = tasks_to_run[i]
                    error_result = ExecutionResult(
                        treatment=treatment_name,
                        test=task.name,
                        prompt=task.prompt,
                        response=LLMResponse(
                            content="",
                            model="error",
                            provider="error",
                            duration_ms=0,
                            raw_response={"error": str(None)}
                        ),
                        passed=False,
                        evaluator_results=[],
                        timestamp=datetime.utcnow().isoformat()
                    )
                    all_results.append(error_result)
                else:
                    all_results.append(result)
        
        return all_results
    
    async def xǁExecutionEngineǁrun_all__mutmut_67(
        self,
        treatments: list[str],
        progress: bool = False,
    ) -> list[ExecutionResult]:
        """Run all treatments and tasks.
        
        Args:
            treatments: List of treatment names to run
            progress: Show progress (not implemented yet)
            
        Returns:
            List of ExecutionResults
        """
        results = []
        
        # Get actual treatments from config
        available_treatments = {
            name: self.config.treatments.get(name, Treatment(skill_path=None))
            for name in treatments
        }
        
        # Add CONTROL if not present
        if "CONTROL" not in available_treatments:
            available_treatments["CONTROL"] = Treatment(skill_path=None)
        
        # Create tasks for each combination
        tasks_to_run = []
        for treatment_name in available_treatments:
            for task in self.config.tests:
                tasks_to_run.append((
                    available_treatments[treatment_name],
                    task,
                    treatment_name
                ))
        
        # Run with repetitions
        all_results = []
        repetitions = self.config.execution.repetitions
        
        for rep in range(repetitions):
            # Run all tasks
            coroutines = [
                self.run_single(treatment, task, treatment_name)
                for treatment, task, treatment_name in tasks_to_run
            ]
            
            # Execute concurrently (limited by semaphore)
            results = await asyncio.gather(*coroutines, return_exceptions=True)
            
            # Handle exceptions
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    # Create error result with minimal response
                    treatment, task, treatment_name = tasks_to_run[i]
                    error_result = ExecutionResult(
                        treatment=treatment_name,
                        test=task.name,
                        prompt=task.prompt,
                        response=LLMResponse(
                            content="",
                            model="error",
                            provider="error",
                            duration_ms=0,
                            raw_response={"error": str(result)}
                        ),
                        passed=True,
                        evaluator_results=[],
                        timestamp=datetime.utcnow().isoformat()
                    )
                    all_results.append(error_result)
                else:
                    all_results.append(result)
        
        return all_results
    
    async def xǁExecutionEngineǁrun_all__mutmut_68(
        self,
        treatments: list[str],
        progress: bool = False,
    ) -> list[ExecutionResult]:
        """Run all treatments and tasks.
        
        Args:
            treatments: List of treatment names to run
            progress: Show progress (not implemented yet)
            
        Returns:
            List of ExecutionResults
        """
        results = []
        
        # Get actual treatments from config
        available_treatments = {
            name: self.config.treatments.get(name, Treatment(skill_path=None))
            for name in treatments
        }
        
        # Add CONTROL if not present
        if "CONTROL" not in available_treatments:
            available_treatments["CONTROL"] = Treatment(skill_path=None)
        
        # Create tasks for each combination
        tasks_to_run = []
        for treatment_name in available_treatments:
            for task in self.config.tests:
                tasks_to_run.append((
                    available_treatments[treatment_name],
                    task,
                    treatment_name
                ))
        
        # Run with repetitions
        all_results = []
        repetitions = self.config.execution.repetitions
        
        for rep in range(repetitions):
            # Run all tasks
            coroutines = [
                self.run_single(treatment, task, treatment_name)
                for treatment, task, treatment_name in tasks_to_run
            ]
            
            # Execute concurrently (limited by semaphore)
            results = await asyncio.gather(*coroutines, return_exceptions=True)
            
            # Handle exceptions
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    # Create error result with minimal response
                    treatment, task, treatment_name = tasks_to_run[i]
                    error_result = ExecutionResult(
                        treatment=treatment_name,
                        test=task.name,
                        prompt=task.prompt,
                        response=LLMResponse(
                            content="",
                            model="error",
                            provider="error",
                            duration_ms=0,
                            raw_response={"error": str(result)}
                        ),
                        passed=False,
                        evaluator_results=[],
                        timestamp=datetime.utcnow().isoformat()
                    )
                    all_results.append(None)
                else:
                    all_results.append(result)
        
        return all_results
    
    async def xǁExecutionEngineǁrun_all__mutmut_69(
        self,
        treatments: list[str],
        progress: bool = False,
    ) -> list[ExecutionResult]:
        """Run all treatments and tasks.
        
        Args:
            treatments: List of treatment names to run
            progress: Show progress (not implemented yet)
            
        Returns:
            List of ExecutionResults
        """
        results = []
        
        # Get actual treatments from config
        available_treatments = {
            name: self.config.treatments.get(name, Treatment(skill_path=None))
            for name in treatments
        }
        
        # Add CONTROL if not present
        if "CONTROL" not in available_treatments:
            available_treatments["CONTROL"] = Treatment(skill_path=None)
        
        # Create tasks for each combination
        tasks_to_run = []
        for treatment_name in available_treatments:
            for task in self.config.tests:
                tasks_to_run.append((
                    available_treatments[treatment_name],
                    task,
                    treatment_name
                ))
        
        # Run with repetitions
        all_results = []
        repetitions = self.config.execution.repetitions
        
        for rep in range(repetitions):
            # Run all tasks
            coroutines = [
                self.run_single(treatment, task, treatment_name)
                for treatment, task, treatment_name in tasks_to_run
            ]
            
            # Execute concurrently (limited by semaphore)
            results = await asyncio.gather(*coroutines, return_exceptions=True)
            
            # Handle exceptions
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    # Create error result with minimal response
                    treatment, task, treatment_name = tasks_to_run[i]
                    error_result = ExecutionResult(
                        treatment=treatment_name,
                        test=task.name,
                        prompt=task.prompt,
                        response=LLMResponse(
                            content="",
                            model="error",
                            provider="error",
                            duration_ms=0,
                            raw_response={"error": str(result)}
                        ),
                        passed=False,
                        evaluator_results=[],
                        timestamp=datetime.utcnow().isoformat()
                    )
                    all_results.append(error_result)
                else:
                    all_results.append(None)
        
        return all_results
    
    xǁExecutionEngineǁrun_all__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
    'xǁExecutionEngineǁrun_all__mutmut_1': xǁExecutionEngineǁrun_all__mutmut_1, 
        'xǁExecutionEngineǁrun_all__mutmut_2': xǁExecutionEngineǁrun_all__mutmut_2, 
        'xǁExecutionEngineǁrun_all__mutmut_3': xǁExecutionEngineǁrun_all__mutmut_3, 
        'xǁExecutionEngineǁrun_all__mutmut_4': xǁExecutionEngineǁrun_all__mutmut_4, 
        'xǁExecutionEngineǁrun_all__mutmut_5': xǁExecutionEngineǁrun_all__mutmut_5, 
        'xǁExecutionEngineǁrun_all__mutmut_6': xǁExecutionEngineǁrun_all__mutmut_6, 
        'xǁExecutionEngineǁrun_all__mutmut_7': xǁExecutionEngineǁrun_all__mutmut_7, 
        'xǁExecutionEngineǁrun_all__mutmut_8': xǁExecutionEngineǁrun_all__mutmut_8, 
        'xǁExecutionEngineǁrun_all__mutmut_9': xǁExecutionEngineǁrun_all__mutmut_9, 
        'xǁExecutionEngineǁrun_all__mutmut_10': xǁExecutionEngineǁrun_all__mutmut_10, 
        'xǁExecutionEngineǁrun_all__mutmut_11': xǁExecutionEngineǁrun_all__mutmut_11, 
        'xǁExecutionEngineǁrun_all__mutmut_12': xǁExecutionEngineǁrun_all__mutmut_12, 
        'xǁExecutionEngineǁrun_all__mutmut_13': xǁExecutionEngineǁrun_all__mutmut_13, 
        'xǁExecutionEngineǁrun_all__mutmut_14': xǁExecutionEngineǁrun_all__mutmut_14, 
        'xǁExecutionEngineǁrun_all__mutmut_15': xǁExecutionEngineǁrun_all__mutmut_15, 
        'xǁExecutionEngineǁrun_all__mutmut_16': xǁExecutionEngineǁrun_all__mutmut_16, 
        'xǁExecutionEngineǁrun_all__mutmut_17': xǁExecutionEngineǁrun_all__mutmut_17, 
        'xǁExecutionEngineǁrun_all__mutmut_18': xǁExecutionEngineǁrun_all__mutmut_18, 
        'xǁExecutionEngineǁrun_all__mutmut_19': xǁExecutionEngineǁrun_all__mutmut_19, 
        'xǁExecutionEngineǁrun_all__mutmut_20': xǁExecutionEngineǁrun_all__mutmut_20, 
        'xǁExecutionEngineǁrun_all__mutmut_21': xǁExecutionEngineǁrun_all__mutmut_21, 
        'xǁExecutionEngineǁrun_all__mutmut_22': xǁExecutionEngineǁrun_all__mutmut_22, 
        'xǁExecutionEngineǁrun_all__mutmut_23': xǁExecutionEngineǁrun_all__mutmut_23, 
        'xǁExecutionEngineǁrun_all__mutmut_24': xǁExecutionEngineǁrun_all__mutmut_24, 
        'xǁExecutionEngineǁrun_all__mutmut_25': xǁExecutionEngineǁrun_all__mutmut_25, 
        'xǁExecutionEngineǁrun_all__mutmut_26': xǁExecutionEngineǁrun_all__mutmut_26, 
        'xǁExecutionEngineǁrun_all__mutmut_27': xǁExecutionEngineǁrun_all__mutmut_27, 
        'xǁExecutionEngineǁrun_all__mutmut_28': xǁExecutionEngineǁrun_all__mutmut_28, 
        'xǁExecutionEngineǁrun_all__mutmut_29': xǁExecutionEngineǁrun_all__mutmut_29, 
        'xǁExecutionEngineǁrun_all__mutmut_30': xǁExecutionEngineǁrun_all__mutmut_30, 
        'xǁExecutionEngineǁrun_all__mutmut_31': xǁExecutionEngineǁrun_all__mutmut_31, 
        'xǁExecutionEngineǁrun_all__mutmut_32': xǁExecutionEngineǁrun_all__mutmut_32, 
        'xǁExecutionEngineǁrun_all__mutmut_33': xǁExecutionEngineǁrun_all__mutmut_33, 
        'xǁExecutionEngineǁrun_all__mutmut_34': xǁExecutionEngineǁrun_all__mutmut_34, 
        'xǁExecutionEngineǁrun_all__mutmut_35': xǁExecutionEngineǁrun_all__mutmut_35, 
        'xǁExecutionEngineǁrun_all__mutmut_36': xǁExecutionEngineǁrun_all__mutmut_36, 
        'xǁExecutionEngineǁrun_all__mutmut_37': xǁExecutionEngineǁrun_all__mutmut_37, 
        'xǁExecutionEngineǁrun_all__mutmut_38': xǁExecutionEngineǁrun_all__mutmut_38, 
        'xǁExecutionEngineǁrun_all__mutmut_39': xǁExecutionEngineǁrun_all__mutmut_39, 
        'xǁExecutionEngineǁrun_all__mutmut_40': xǁExecutionEngineǁrun_all__mutmut_40, 
        'xǁExecutionEngineǁrun_all__mutmut_41': xǁExecutionEngineǁrun_all__mutmut_41, 
        'xǁExecutionEngineǁrun_all__mutmut_42': xǁExecutionEngineǁrun_all__mutmut_42, 
        'xǁExecutionEngineǁrun_all__mutmut_43': xǁExecutionEngineǁrun_all__mutmut_43, 
        'xǁExecutionEngineǁrun_all__mutmut_44': xǁExecutionEngineǁrun_all__mutmut_44, 
        'xǁExecutionEngineǁrun_all__mutmut_45': xǁExecutionEngineǁrun_all__mutmut_45, 
        'xǁExecutionEngineǁrun_all__mutmut_46': xǁExecutionEngineǁrun_all__mutmut_46, 
        'xǁExecutionEngineǁrun_all__mutmut_47': xǁExecutionEngineǁrun_all__mutmut_47, 
        'xǁExecutionEngineǁrun_all__mutmut_48': xǁExecutionEngineǁrun_all__mutmut_48, 
        'xǁExecutionEngineǁrun_all__mutmut_49': xǁExecutionEngineǁrun_all__mutmut_49, 
        'xǁExecutionEngineǁrun_all__mutmut_50': xǁExecutionEngineǁrun_all__mutmut_50, 
        'xǁExecutionEngineǁrun_all__mutmut_51': xǁExecutionEngineǁrun_all__mutmut_51, 
        'xǁExecutionEngineǁrun_all__mutmut_52': xǁExecutionEngineǁrun_all__mutmut_52, 
        'xǁExecutionEngineǁrun_all__mutmut_53': xǁExecutionEngineǁrun_all__mutmut_53, 
        'xǁExecutionEngineǁrun_all__mutmut_54': xǁExecutionEngineǁrun_all__mutmut_54, 
        'xǁExecutionEngineǁrun_all__mutmut_55': xǁExecutionEngineǁrun_all__mutmut_55, 
        'xǁExecutionEngineǁrun_all__mutmut_56': xǁExecutionEngineǁrun_all__mutmut_56, 
        'xǁExecutionEngineǁrun_all__mutmut_57': xǁExecutionEngineǁrun_all__mutmut_57, 
        'xǁExecutionEngineǁrun_all__mutmut_58': xǁExecutionEngineǁrun_all__mutmut_58, 
        'xǁExecutionEngineǁrun_all__mutmut_59': xǁExecutionEngineǁrun_all__mutmut_59, 
        'xǁExecutionEngineǁrun_all__mutmut_60': xǁExecutionEngineǁrun_all__mutmut_60, 
        'xǁExecutionEngineǁrun_all__mutmut_61': xǁExecutionEngineǁrun_all__mutmut_61, 
        'xǁExecutionEngineǁrun_all__mutmut_62': xǁExecutionEngineǁrun_all__mutmut_62, 
        'xǁExecutionEngineǁrun_all__mutmut_63': xǁExecutionEngineǁrun_all__mutmut_63, 
        'xǁExecutionEngineǁrun_all__mutmut_64': xǁExecutionEngineǁrun_all__mutmut_64, 
        'xǁExecutionEngineǁrun_all__mutmut_65': xǁExecutionEngineǁrun_all__mutmut_65, 
        'xǁExecutionEngineǁrun_all__mutmut_66': xǁExecutionEngineǁrun_all__mutmut_66, 
        'xǁExecutionEngineǁrun_all__mutmut_67': xǁExecutionEngineǁrun_all__mutmut_67, 
        'xǁExecutionEngineǁrun_all__mutmut_68': xǁExecutionEngineǁrun_all__mutmut_68, 
        'xǁExecutionEngineǁrun_all__mutmut_69': xǁExecutionEngineǁrun_all__mutmut_69
    }
    xǁExecutionEngineǁrun_all__mutmut_orig.__name__ = 'xǁExecutionEngineǁrun_all'
    
    async def run_treatment(
        self,
        treatment_name: str,
    ) -> list[ExecutionResult]:
        args = [treatment_name]# type: ignore
        kwargs = {}# type: ignore
        return await _mutmut_trampoline(object.__getattribute__(self, 'xǁExecutionEngineǁrun_treatment__mutmut_orig'), object.__getattribute__(self, 'xǁExecutionEngineǁrun_treatment__mutmut_mutants'), args, kwargs, self)
    
    async def xǁExecutionEngineǁrun_treatment__mutmut_orig(
        self,
        treatment_name: str,
    ) -> list[ExecutionResult]:
        """Run a specific treatment.
        
        Args:
            treatment_name: Name of treatment to run
            
        Returns:
            List of ExecutionResults
        """
        return await self.run_all([treatment_name])
    
    async def xǁExecutionEngineǁrun_treatment__mutmut_1(
        self,
        treatment_name: str,
    ) -> list[ExecutionResult]:
        """Run a specific treatment.
        
        Args:
            treatment_name: Name of treatment to run
            
        Returns:
            List of ExecutionResults
        """
        return await self.run_all(None)
    
    xǁExecutionEngineǁrun_treatment__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
    'xǁExecutionEngineǁrun_treatment__mutmut_1': xǁExecutionEngineǁrun_treatment__mutmut_1
    }
    xǁExecutionEngineǁrun_treatment__mutmut_orig.__name__ = 'xǁExecutionEngineǁrun_treatment'
