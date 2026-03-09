"""Reporter for formatting evaluation results."""


class Reporter:
    """Formats and outputs evaluation results."""
    
    def __init__(self, config):
        self.config = config
    
    def report_terminal(self, results: list):
        """Print results to terminal."""
        # TODO: Implement
        pass
    
    def report_json(self, results: list, output_path: str):
        """Save results as JSON."""
        # TODO: Implement
        pass
