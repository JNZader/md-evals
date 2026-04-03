"""Code reference validation grader.

Validates that backtick-quoted references in LLM-generated markdown
resolve to real files or symbols in the workspace.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

from md_evals.graders._path_utils import validate_workspace_path
from md_evals.models import EvaluatorResult

# Regex to match fenced code blocks: ```lang\n...\n```
_FENCED_BLOCK_RE = re.compile(r"```[^\n]*\n.*?```", re.DOTALL)

# Regex to match single-backtick content (not double/triple)
_SINGLE_BACKTICK_RE = re.compile(r"(?<!`)`([^`]+)`(?!`)")

_DEFAULT_EXCLUSIONS: list[str] = [
    "true",
    "false",
    "null",
    "None",
    "undefined",
    "npm",
    "pip",
    "git",
    "bash",
    "sh",
    "zsh",
    "cd",
    "ls",
    "mkdir",
    "npm install",
    "pip install",
    "git clone",
    "str",
    "int",
    "float",
    "bool",
    "list",
    "dict",
]


@dataclass
class CodeRefGrader:
    """Assert that backtick-quoted code references in markdown resolve.

    Reads a markdown file from the workspace, extracts single-backtick
    references (excluding fenced code blocks and common non-ref keywords),
    classifies each as a file path or symbol, and validates resolution.

    Score is proportional: ``resolved / total``.  Passes if score meets
    ``pass_threshold``.

    Attributes:
        name: Grader identifier for reports.
        markdown_file: Workspace-relative path to the markdown file.
        search_dirs: Directories (workspace-relative) to search for symbols.
        file_extensions: Source file extensions to scan for symbol search.
        pass_threshold: Minimum score to pass (0.0-1.0).
        exclusions: Backtick content to ignore (case-insensitive).
    """

    name: str = "code_ref"
    markdown_file: str = "output.md"
    search_dirs: list[str] = field(default_factory=lambda: ["."])
    file_extensions: list[str] = field(
        default_factory=lambda: [".py", ".ts", ".js", ".go", ".rs", ".java"],
    )
    pass_threshold: float = 0.8
    exclusions: list[str] = field(
        default_factory=lambda: list(_DEFAULT_EXCLUSIONS),
    )

    def grade(self, workspace: Path) -> EvaluatorResult:
        """Grade backtick references in the markdown file.

        Args:
            workspace: Root directory of the execution workspace.

        Returns:
            EvaluatorResult with proportional score and resolution details.
        """
        md_path = validate_workspace_path(workspace, self.markdown_file)
        if not md_path.exists():
            return EvaluatorResult(
                evaluator_name=self.name,
                passed=False,
                score=0.0,
                reason=f"Markdown file '{self.markdown_file}' not found",
                details={"resolved": [], "unresolved": [], "total": 0},
            )

        text = md_path.read_text(encoding="utf-8", errors="replace")
        refs = self._extract_refs(text)

        if not refs:
            return EvaluatorResult(
                evaluator_name=self.name,
                passed=True,
                score=1.0,
                reason=None,
                details={"resolved": [], "unresolved": [], "total": 0},
            )

        resolved: list[str] = []
        unresolved: list[str] = []

        for ref in refs:
            kind = self._classify_ref(ref)
            if kind == "file":
                found = self._resolve_file(ref, workspace)
            else:
                found = self._resolve_symbol(ref, workspace)

            if found:
                resolved.append(ref)
            else:
                unresolved.append(ref)

        total = len(refs)
        score = len(resolved) / total
        passed = score >= self.pass_threshold

        reason = None
        if not passed:
            reason = (
                f"{len(unresolved)}/{total} refs unresolved: "
                + ", ".join(unresolved[:5])
            )

        return EvaluatorResult(
            evaluator_name=self.name,
            passed=passed,
            score=score,
            reason=reason,
            details={
                "resolved": resolved,
                "unresolved": unresolved,
                "total": total,
                "score": score,
            },
        )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _strip_fenced_blocks(self, text: str) -> str:
        """Remove fenced code blocks (```...```) from markdown text."""
        return _FENCED_BLOCK_RE.sub("", text)

    def _extract_refs(self, text: str) -> list[str]:
        """Extract deduplicated backtick refs, excluding fenced blocks and exclusions."""
        stripped = self._strip_fenced_blocks(text)
        raw_refs = _SINGLE_BACKTICK_RE.findall(stripped)

        exclusion_set = {e.lower() for e in self.exclusions}
        seen: set[str] = set()
        result: list[str] = []

        for ref in raw_refs:
            ref_stripped = ref.strip()
            if not ref_stripped:
                continue
            if ref_stripped.lower() in exclusion_set:
                continue
            if ref_stripped not in seen:
                seen.add(ref_stripped)
                result.append(ref_stripped)

        return result

    def _classify_ref(self, ref: str) -> Literal["file", "symbol"]:
        """Classify a reference as file path or symbol.

        File if it contains ``/`` or ends with a known file extension.
        """
        if "/" in ref:
            return "file"
        for ext in self.file_extensions:
            if ref.endswith(ext):
                return "file"
        return "symbol"

    def _resolve_file(self, ref: str, workspace: Path) -> bool:
        """Check if a file-path reference exists in the workspace."""
        try:
            target = validate_workspace_path(workspace, ref)
            return target.exists()
        except ValueError:
            return False

    def _resolve_symbol(self, ref: str, workspace: Path) -> bool:
        """Search for a symbol string in source files within search_dirs."""
        for search_dir in self.search_dirs:
            try:
                base = validate_workspace_path(workspace, search_dir)
            except ValueError:
                continue
            if not base.is_dir():
                continue
            for ext in self.file_extensions:
                for source_file in base.rglob(f"*{ext}"):
                    try:
                        content = source_file.read_text(
                            encoding="utf-8", errors="replace"
                        )
                        if ref in content:
                            return True
                    except (OSError, UnicodeDecodeError):
                        continue
        return False
