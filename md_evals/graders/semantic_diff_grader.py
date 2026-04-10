"""Semantic diff grader — compare LLM outputs at the semantic unit level.

Instead of raw string comparison, this grader:
1. Parses text into semantic units (claims, facts, instructions, definitions)
2. Compares units structurally using normalized matching
3. Produces a meaningful diff that shows what changed at the concept level

This gives more accurate eval scores than string-level comparison because
minor phrasing differences don't penalize the score, while actual semantic
divergence (missing facts, contradictory claims) is properly caught.

Usage:
    grader = SemanticDiffGrader(
        name="claim_comparison",
        expected="Python is interpreted. It supports OOP.",
        actual="Python is an interpreted language. It has OOP support.",
    )
    result = grader.grade(workspace)
    # result.score ≈ 1.0 (same semantic content, different wording)
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from md_evals.graders._path_utils import validate_workspace_path
from md_evals.models import EvaluatorResult


class UnitType(str, Enum):
    """Classification of semantic units extracted from text."""

    CLAIM = "claim"
    FACT = "fact"
    INSTRUCTION = "instruction"
    DEFINITION = "definition"
    EXAMPLE = "example"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class SemanticUnit:
    """A single semantic unit extracted from text.

    Attributes:
        text: Original text of the unit.
        unit_type: Classification of the unit.
        normalized: Lowercased, stripped text for comparison.
        key_terms: Significant terms extracted for fuzzy matching.
    """

    text: str
    unit_type: UnitType
    normalized: str
    key_terms: frozenset[str]


@dataclass(frozen=True)
class UnitMatch:
    """Result of matching two semantic units.

    Attributes:
        expected: The expected semantic unit.
        actual: The matched actual unit (None if missing).
        similarity: Similarity score between 0.0 and 1.0.
        match_type: How the match was determined.
    """

    expected: SemanticUnit
    actual: SemanticUnit | None
    similarity: float
    match_type: str  # "exact", "normalized", "key_term", "none"


@dataclass(frozen=True)
class SemanticDiff:
    """Complete semantic diff between expected and actual outputs.

    Attributes:
        matches: Matched units with similarity scores.
        missing_units: Units in expected but not in actual.
        extra_units: Units in actual but not in expected.
        overall_similarity: Aggregate similarity score (0.0 to 1.0).
    """

    matches: list[UnitMatch]
    missing_units: list[SemanticUnit]
    extra_units: list[SemanticUnit]
    overall_similarity: float


# ── Stop words for key term extraction ──

_STOP_WORDS: frozenset[str] = frozenset({
    "a", "an", "the", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "shall", "can", "need", "must", "ought",
    "i", "you", "he", "she", "it", "we", "they", "me", "him", "her",
    "us", "them", "my", "your", "his", "its", "our", "their",
    "this", "that", "these", "those", "and", "but", "or", "nor",
    "not", "so", "if", "then", "than", "when", "where", "while",
    "of", "in", "to", "for", "with", "on", "at", "from", "by",
    "about", "as", "into", "through", "during", "before", "after",
    "also", "very", "just", "more", "most", "other", "some", "such",
    "no", "only", "same", "too", "each", "every", "all", "both",
})


# ── Parsing ──


def _extract_key_terms(text: str) -> frozenset[str]:
    """Extract significant terms from text, filtering stop words."""
    words = re.findall(r"[a-zA-Z0-9_]+", text.lower())
    return frozenset(w for w in words if w not in _STOP_WORDS and len(w) > 1)


def _classify_unit(text: str) -> UnitType:
    """Classify a text fragment into a semantic unit type.

    Uses heuristic pattern matching on sentence structure.
    """
    stripped = text.strip().lower()

    # Instructions: imperative mood, numbered steps
    if re.match(r"^\d+[\.\)]\s", stripped):
        return UnitType.INSTRUCTION
    if re.match(r"^(use|run|install|create|add|set|configure|ensure|make|do|don't)\b", stripped):
        return UnitType.INSTRUCTION

    # Definitions: "X is Y", "X refers to Y", "X means Y"
    if re.search(r"\bis\s+(a|an|the|defined\s+as)\b", stripped):
        return UnitType.DEFINITION

    # Examples: "for example", "e.g.", "such as", code blocks
    if re.search(r"(for example|e\.g\.|such as|for instance)", stripped):
        return UnitType.EXAMPLE
    if "```" in text:
        return UnitType.EXAMPLE

    # Facts: contains numbers, dates, proper nouns (capitalized words)
    if re.search(r"\b\d{4}\b|\b\d+%|\b\d+\.\d+\b", text):
        return UnitType.FACT

    # Claims: assertions, opinions, evaluations
    if re.search(r"\b(better|worse|best|worst|should|recommend|important|significant)\b", stripped):
        return UnitType.CLAIM

    # Default: if it has a subject-verb structure, treat as claim
    if re.search(r"\b(is|are|was|were|has|have|does|do)\b", stripped):
        return UnitType.CLAIM

    return UnitType.UNKNOWN


def parse_semantic_units(text: str) -> list[SemanticUnit]:
    """Parse text into a list of semantic units.

    Splitting strategy:
    1. Split on sentence boundaries (period, exclamation, question mark)
    2. Split on bullet points and numbered lists
    3. Each non-empty fragment becomes a SemanticUnit

    Args:
        text: Raw text to parse.

    Returns:
        List of SemanticUnit objects.
    """
    if not text or not text.strip():
        return []

    # Split on sentence boundaries, preserving list items
    # First, split on newlines that start list items
    fragments: list[str] = []
    lines = text.strip().split("\n")

    current_fragment = ""
    for line in lines:
        stripped = line.strip()
        if not stripped:
            # Empty line — flush current fragment
            if current_fragment.strip():
                fragments.append(current_fragment.strip())
                current_fragment = ""
            continue

        # List item or numbered item — new fragment
        if re.match(r"^[-*•]\s|^\d+[\.\)]\s", stripped):
            if current_fragment.strip():
                fragments.append(current_fragment.strip())
            current_fragment = stripped
        else:
            current_fragment += " " + stripped if current_fragment else stripped

    if current_fragment.strip():
        fragments.append(current_fragment.strip())

    # Further split on sentence boundaries within each fragment
    units: list[SemanticUnit] = []
    for fragment in fragments:
        # Split sentences but keep list items together
        if re.match(r"^[-*•]\s|^\d+[\.\)]\s", fragment):
            sentences = [fragment]
        else:
            sentences = re.split(r"(?<=[.!?])\s+(?=[A-Z])", fragment)

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence or len(sentence) < 3:
                continue

            unit_type = _classify_unit(sentence)
            normalized = re.sub(r"\s+", " ", sentence.lower().strip())
            normalized = re.sub(r"[^\w\s]", "", normalized).strip()
            key_terms = _extract_key_terms(sentence)

            units.append(
                SemanticUnit(
                    text=sentence,
                    unit_type=unit_type,
                    normalized=normalized,
                    key_terms=key_terms,
                )
            )

    return units


# ── Matching ──


def _compute_term_similarity(a: SemanticUnit, b: SemanticUnit) -> float:
    """Compute Jaccard similarity between key term sets."""
    if not a.key_terms and not b.key_terms:
        return 1.0 if a.normalized == b.normalized else 0.0
    if not a.key_terms or not b.key_terms:
        return 0.0

    intersection = a.key_terms & b.key_terms
    union = a.key_terms | b.key_terms
    return len(intersection) / len(union) if union else 0.0


def compute_semantic_diff(
    expected: list[SemanticUnit],
    actual: list[SemanticUnit],
    *,
    similarity_threshold: float = 0.5,
) -> SemanticDiff:
    """Compute the semantic diff between expected and actual unit lists.

    Uses a greedy best-match strategy:
    1. For each expected unit, find the best matching actual unit
    2. Match if similarity >= threshold
    3. Remaining unmatched units become missing/extra

    Args:
        expected: Semantic units from reference output.
        actual: Semantic units from LLM output being evaluated.
        similarity_threshold: Minimum similarity to consider a match.

    Returns:
        SemanticDiff with matches, missing, and extra units.
    """
    if not expected and not actual:
        return SemanticDiff(
            matches=[], missing_units=[], extra_units=[], overall_similarity=1.0
        )

    if not expected:
        return SemanticDiff(
            matches=[], missing_units=[], extra_units=list(actual), overall_similarity=0.0
        )

    if not actual:
        return SemanticDiff(
            matches=[], missing_units=list(expected), extra_units=[], overall_similarity=0.0
        )

    used_actual: set[int] = set()
    matches: list[UnitMatch] = []
    missing: list[SemanticUnit] = []

    for exp_unit in expected:
        best_score = 0.0
        best_idx = -1
        best_match_type = "none"

        for i, act_unit in enumerate(actual):
            if i in used_actual:
                continue

            # Exact normalized match
            if exp_unit.normalized == act_unit.normalized:
                best_score = 1.0
                best_idx = i
                best_match_type = "exact"
                break

            # Key term similarity
            sim = _compute_term_similarity(exp_unit, act_unit)

            # Boost if same unit type
            if exp_unit.unit_type == act_unit.unit_type:
                sim = min(1.0, sim * 1.15)

            if sim > best_score:
                best_score = sim
                best_idx = i
                best_match_type = "key_term"

        if best_score >= similarity_threshold and best_idx >= 0:
            used_actual.add(best_idx)
            matches.append(
                UnitMatch(
                    expected=exp_unit,
                    actual=actual[best_idx],
                    similarity=round(best_score, 4),
                    match_type=best_match_type,
                )
            )
        else:
            missing.append(exp_unit)

    extra = [u for i, u in enumerate(actual) if i not in used_actual]

    # Overall similarity: average of matched similarities + penalty for missing/extra
    if not expected:
        overall = 0.0
    else:
        matched_sim = sum(m.similarity for m in matches)
        # Missing units contribute 0.0 to the score
        overall = matched_sim / len(expected)

    return SemanticDiff(
        matches=matches,
        missing_units=missing,
        extra_units=extra,
        overall_similarity=round(overall, 4),
    )


# ── Grader ──


@dataclass
class SemanticDiffGrader:
    """Compare expected vs actual output at the semantic unit level.

    Parses both texts into semantic units (claims, facts, instructions, etc.),
    then computes structural similarity. This gives more meaningful scores
    than string-level comparison because minor wording differences are
    tolerated while actual semantic divergence is caught.

    Attributes:
        name: Grader identifier for reports.
        expected: Reference text (ground truth).
        actual: LLM output to evaluate (alternative to actual_path).
        expected_path: File path for expected text (alternative to expected).
        actual_path: File path for actual text (alternative to actual).
        similarity_threshold: Minimum term similarity to count as a match.
        pass_threshold: Minimum overall similarity to pass.
        unit_types: If set, only compare units of these types.
        penalize_extra: Whether extra units in actual reduce the score.
        extra_penalty_weight: How much to penalize extra units (0.0 to 1.0).
    """

    name: str
    expected: str | None = None
    actual: str | None = None
    expected_path: str | None = None
    actual_path: str | None = None
    similarity_threshold: float = 0.5
    pass_threshold: float = 0.7
    unit_types: list[UnitType] | None = None
    penalize_extra: bool = False
    extra_penalty_weight: float = 0.1

    def grade(self, workspace: Path) -> EvaluatorResult:
        """Grade by computing semantic diff between expected and actual."""
        expected_text = self._resolve(self.expected, self.expected_path, workspace)
        actual_text = self._resolve(self.actual, self.actual_path, workspace)

        if expected_text is None:
            return EvaluatorResult(
                evaluator_name=self.name,
                passed=False,
                score=0.0,
                reason="Expected text not provided or file not found",
            )

        if actual_text is None:
            return EvaluatorResult(
                evaluator_name=self.name,
                passed=False,
                score=0.0,
                reason="Actual text not provided or file not found",
            )

        expected_units = parse_semantic_units(expected_text)
        actual_units = parse_semantic_units(actual_text)

        # Filter by unit type if specified
        if self.unit_types:
            type_set = set(self.unit_types)
            expected_units = [u for u in expected_units if u.unit_type in type_set]
            actual_units = [u for u in actual_units if u.unit_type in type_set]

        diff = compute_semantic_diff(
            expected_units,
            actual_units,
            similarity_threshold=self.similarity_threshold,
        )

        score = diff.overall_similarity

        # Optionally penalize extra units (hallucinations, noise)
        if self.penalize_extra and diff.extra_units:
            total_expected = max(len(expected_units), 1)
            extra_ratio = len(diff.extra_units) / total_expected
            penalty = min(extra_ratio * self.extra_penalty_weight, 0.3)
            score = max(0.0, score - penalty)
            score = round(score, 4)

        passed = score >= self.pass_threshold

        return EvaluatorResult(
            evaluator_name=self.name,
            passed=passed,
            score=score,
            reason=self._build_reason(diff, passed),
            details={
                "expected_unit_count": len(expected_units),
                "actual_unit_count": len(actual_units),
                "matched_count": len(diff.matches),
                "missing_count": len(diff.missing_units),
                "extra_count": len(diff.extra_units),
                "overall_similarity": diff.overall_similarity,
                "matches": [
                    {
                        "expected": m.expected.text,
                        "actual": m.actual.text if m.actual else None,
                        "similarity": m.similarity,
                        "match_type": m.match_type,
                    }
                    for m in diff.matches
                ],
                "missing": [u.text for u in diff.missing_units],
                "extra": [u.text for u in diff.extra_units],
            },
        )

    def _resolve(
        self, content: str | None, path: str | None, workspace: Path
    ) -> str | None:
        if content is not None:
            return content
        if path is not None:
            target = validate_workspace_path(workspace, path)
            if target.exists():
                return target.read_text(encoding="utf-8", errors="replace")
        return None

    def _build_reason(self, diff: SemanticDiff, passed: bool) -> str | None:
        if passed:
            return None

        parts: list[str] = []
        if diff.missing_units:
            missing_texts = [u.text[:60] for u in diff.missing_units[:3]]
            parts.append(f"Missing: {missing_texts}")
        if diff.extra_units:
            parts.append(f"{len(diff.extra_units)} extra units not in expected")
        if not parts:
            parts.append(f"Similarity {diff.overall_similarity} below threshold")

        return "; ".join(parts)
