"""Evaluator engine for regex and LLM-judge evaluation."""


class EvaluatorEngine:
    """Evaluates outputs with regex and LLM-judge."""
    
    def __init__(self, llm_adapter=None):
        self.llm_adapter = llm_adapter
    
    async def evaluate(self, output: str, evaluators: list):
        """Evaluate output against evaluators."""
        # TODO: Implement
        pass
