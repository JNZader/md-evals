"""Config loader for eval.yaml."""

from pathlib import Path
import yaml
from md_evals.models import EvalConfig


class ConfigLoaderError(Exception):
    """Configuration loader error."""
    pass


class ConfigLoader:
    """Loads and validates eval.yaml configuration."""
    
    @staticmethod
    def load(path: str = "eval.yaml") -> EvalConfig:
        """Load configuration from YAML file.
        
        Args:
            path: Path to eval.yaml file
            
        Returns:
            EvalConfig instance
            
        Raises:
            ConfigLoaderError: If file not found or invalid YAML
        """
        file_path = Path(path)
        
        if not file_path.exists():
            raise ConfigLoaderError(f"Config file not found: {path}")
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ConfigLoaderError(f"Invalid YAML: {e}")
        
        if data is None:
            raise ConfigLoaderError("Empty config file")
        
        try:
            config = EvalConfig(**data)
        except Exception as e:
            raise ConfigLoaderError(f"Invalid configuration: {e}")
        
        return config
    
    @staticmethod
    def validate(config: EvalConfig) -> list[str]:
        """Validate configuration.
        
        Args:
            config: EvalConfig instance
            
        Returns:
            List of validation warnings (empty if all valid)
        """
        warnings = []
        
        # Check if at least one treatment exists
        if not config.treatments:
            warnings.append("No treatments defined")
        
        # Check if at least one test exists
        if not config.tests:
            warnings.append("No tests defined")
        
        # Check for CONTROL treatment
        if "CONTROL" not in config.treatments:
            warnings.append("No CONTROL treatment defined (recommended)")
        
        # Validate treatment skill paths exist
        for name, treatment in config.treatments.items():
            if treatment.skill_path:
                skill_path = Path(treatment.skill_path)
                if not skill_path.exists():
                    warnings.append(f"Treatment '{name}': skill file not found: {treatment.skill_path}")
        
        return warnings
    
    @staticmethod
    def expand_wildcards(treatments: list[str], available: dict) -> list[str]:
        """Expand treatment wildcards.
        
        Args:
            treatments: List of treatment names (may include wildcards)
            available: Dict of available treatment names
            
        Returns:
            Expanded list of treatment names
        """
        import fnmatch
        
        expanded = []
        available_names = list(available.keys())
        
        for treatment in treatments:
            if "*" in treatment or "?" in treatment:
                # Expand wildcard
                pattern = treatment.replace("?", "?").replace("*", "*")
                matches = [n for n in available_names if fnmatch.fnmatch(n, pattern)]
                expanded.extend(matches)
            else:
                if treatment in available_names:
                    expanded.append(treatment)
                else:
                    raise ConfigLoaderError(f"Unknown treatment: {treatment}")
        
        return expanded
    
    @staticmethod
    def save(config: EvalConfig, path: str = "eval.yaml") -> None:
        """Save configuration to YAML file.
        
        Args:
            config: EvalConfig instance
            path: Path to save YAML file
        """
        file_path = Path(path)
        data = config.model_dump(exclude_none=True, mode="json")
        
        with open(file_path, "w", encoding="utf-8") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)
