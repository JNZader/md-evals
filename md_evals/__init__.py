"""md-evals: Lightweight CLI tool for evaluating AI skills."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("md-evals")
except PackageNotFoundError:  # running from a source checkout without install
    __version__ = "0.3.0"
