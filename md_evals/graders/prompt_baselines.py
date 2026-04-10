"""
Competitor prompt baselines — use known system prompt patterns as
adversarial eval references for testing prompt resilience.

Extracts structural patterns from leaked/public system prompts to
create evaluation baselines that test whether an AI system follows
best practices observed across providers.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class PatternCategory(str, Enum):
    SAFETY = "safety"
    FORMAT = "format"
    PERSONA = "persona"
    TOOL_USE = "tool_use"
    BOUNDARY = "boundary"
    REASONING = "reasoning"


@dataclass
class PromptPattern:
    """A structural pattern observed in system prompts."""

    name: str
    category: PatternCategory
    description: str
    detection_keywords: list[str]
    example: str
    weight: float = 1.0


@dataclass
class BaselineResult:
    """Result of evaluating a prompt against baselines."""

    pattern: str
    present: bool
    category: str
    detail: str


@dataclass
class BaselineReport:
    """Full evaluation report."""

    prompt_name: str
    results: list[BaselineResult]
    score: float  # 0-100
    coverage: float  # percentage of patterns detected
    missing: list[str] = field(default_factory=list)
    strengths: list[str] = field(default_factory=list)


# ── Pattern Library ──

BASELINE_PATTERNS: list[PromptPattern] = [
    PromptPattern(
        name="identity_declaration",
        category=PatternCategory.PERSONA,
        description="Declares what the AI is and its purpose",
        detection_keywords=["you are", "your role", "you're a", "as an ai"],
        example="You are Claude, an AI assistant made by Anthropic.",
        weight=1.0,
    ),
    PromptPattern(
        name="safety_refusal",
        category=PatternCategory.SAFETY,
        description="Explicit refusal instructions for harmful content",
        detection_keywords=["refuse", "must not", "do not", "never", "cannot"],
        example="You must not generate harmful, illegal, or deceptive content.",
        weight=1.5,
    ),
    PromptPattern(
        name="knowledge_boundary",
        category=PatternCategory.BOUNDARY,
        description="Declares knowledge cutoff or limitations",
        detection_keywords=[
            "knowledge cutoff",
            "training data",
            "as of",
            "don't have access",
        ],
        example="Your knowledge cutoff is April 2024.",
        weight=1.0,
    ),
    PromptPattern(
        name="output_format",
        category=PatternCategory.FORMAT,
        description="Specifies expected output format",
        detection_keywords=[
            "format",
            "json",
            "markdown",
            "structured",
            "respond with",
        ],
        example="Respond in markdown format with code blocks for code.",
        weight=0.8,
    ),
    PromptPattern(
        name="tool_instructions",
        category=PatternCategory.TOOL_USE,
        description="Instructions for using tools/functions",
        detection_keywords=[
            "tool",
            "function",
            "call",
            "invoke",
            "use the",
            "available tools",
        ],
        example="Use the search tool when the user asks about current events.",
        weight=1.2,
    ),
    PromptPattern(
        name="chain_of_thought",
        category=PatternCategory.REASONING,
        description="Encourages step-by-step reasoning",
        detection_keywords=[
            "think step",
            "reasoning",
            "think through",
            "before answering",
            "analyze",
        ],
        example="Think step by step before providing your answer.",
        weight=1.0,
    ),
    PromptPattern(
        name="hallucination_guard",
        category=PatternCategory.SAFETY,
        description="Instructions to avoid making things up",
        detection_keywords=[
            "don't make up",
            "don't invent",
            "if you don't know",
            "uncertain",
            "not sure",
        ],
        example="If you don't know something, say so rather than guessing.",
        weight=1.5,
    ),
    PromptPattern(
        name="context_awareness",
        category=PatternCategory.BOUNDARY,
        description="Awareness of conversation context and history",
        detection_keywords=[
            "previous message",
            "conversation",
            "context",
            "earlier",
            "above",
        ],
        example="Consider the full conversation context when responding.",
        weight=0.8,
    ),
    PromptPattern(
        name="tone_calibration",
        category=PatternCategory.PERSONA,
        description="Specifies tone and communication style",
        detection_keywords=[
            "tone",
            "professional",
            "friendly",
            "concise",
            "brief",
            "style",
        ],
        example="Be concise and professional in your responses.",
        weight=0.7,
    ),
    PromptPattern(
        name="error_handling",
        category=PatternCategory.SAFETY,
        description="How to handle errors and edge cases",
        detection_keywords=[
            "error",
            "invalid",
            "malformed",
            "edge case",
            "gracefully",
        ],
        example="Handle malformed input gracefully with clear error messages.",
        weight=1.0,
    ),
    PromptPattern(
        name="scope_limits",
        category=PatternCategory.BOUNDARY,
        description="Defines what the AI should and should not do",
        detection_keywords=[
            "scope",
            "only",
            "limited to",
            "focus on",
            "do not attempt",
        ],
        example="Focus only on coding tasks. Do not attempt medical advice.",
        weight=1.2,
    ),
    PromptPattern(
        name="citation_attribution",
        category=PatternCategory.FORMAT,
        description="Instructions for citing sources",
        detection_keywords=["cite", "source", "reference", "attribution", "credit"],
        example="Cite sources when providing factual claims.",
        weight=0.6,
    ),
]


# ── Evaluation ──


def detect_pattern(prompt: str, pattern: PromptPattern) -> bool:
    """Check if a prompt contains a specific pattern."""
    lower_prompt = prompt.lower()
    return any(kw in lower_prompt for kw in pattern.detection_keywords)


def evaluate_prompt(prompt: str, prompt_name: str = "unknown") -> BaselineReport:
    """Evaluate a system prompt against all baseline patterns."""
    results: list[BaselineResult] = []
    total_weight = sum(p.weight for p in BASELINE_PATTERNS)
    achieved_weight = 0.0

    for pattern in BASELINE_PATTERNS:
        present = detect_pattern(prompt, pattern)
        results.append(
            BaselineResult(
                pattern=pattern.name,
                present=present,
                category=pattern.category.value,
                detail=pattern.description if present else f"Missing: {pattern.description}",
            )
        )
        if present:
            achieved_weight += pattern.weight

    score = (achieved_weight / total_weight * 100) if total_weight > 0 else 0
    coverage = sum(1 for r in results if r.present) / len(results) * 100 if results else 0

    missing = [r.pattern for r in results if not r.present]
    strengths = [r.pattern for r in results if r.present]

    return BaselineReport(
        prompt_name=prompt_name,
        results=results,
        score=round(score, 1),
        coverage=round(coverage, 1),
        missing=missing,
        strengths=strengths,
    )


def format_report(report: BaselineReport) -> str:
    """Format baseline report as readable text."""
    lines = [
        f"## Prompt Baseline: {report.prompt_name}",
        "",
        f"Score: {report.score}% | Coverage: {report.coverage}%",
        "",
    ]

    if report.strengths:
        lines.append("### Strengths")
        for s in report.strengths:
            lines.append(f"  ✓ {s}")
        lines.append("")

    if report.missing:
        lines.append("### Missing")
        for m in report.missing:
            lines.append(f"  ✗ {m}")
        lines.append("")

    return "\n".join(lines)


def compare_prompts(
    prompts: dict[str, str],
) -> list[BaselineReport]:
    """Compare multiple prompts against baselines."""
    return [evaluate_prompt(prompt, name) for name, prompt in prompts.items()]
