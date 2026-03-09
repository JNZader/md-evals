"""Execution engine for running evaluations."""

import asyncio
from datetime import datetime
from typing import TYPE_CHECKING

from md_evals.models import (
    EvalConfig, ExecutionResult, Defaults,
    Task, Treatment
)
from md_evals.llm import LLMAdapter, inject_skill, LLMError

if TYPE_CHECKING:
    from md_evals.evaluator import EvaluatorEngine as EvaluatorEngineType


class ExecutionEngine:
    """Orchestrates evaluation runs."""
    
    def __init__(
        self,
        config: EvalConfig,
        llm_adapter: LLMAdapter,
        evaluator_engine: "EvaluatorEngineType | None" = None
    ):
        self.config = config
        self.llm_adapter = llm_adapter
        self.evaluator_engine = evaluator_engine
        self._semaphore: asyncio.Semaphore | None = None
    
    def _get_semaphore(self) -> asyncio.Semaphore:
        """Get or create semaphore for concurrency control."""
        if self._semaphore is None:
            self._semaphore = asyncio.Semaphore(self.config.execution.parallel_workers)
        return self._semaphore
    
    async def run_single(
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
    
    async def run_all(
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
                    # Create error result
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
    
    async def run_treatment(
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
