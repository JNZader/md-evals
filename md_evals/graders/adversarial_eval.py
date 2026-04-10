"""Adversarial eval loop — two adversary agents attack a system, a judge
auto-patches or escalates. Each resolved case becomes a permanent test.

Loophole Finder: finds cases where the model technically passes but gives wrong answers.
Overreach Finder: finds cases where the model fails but should pass.
Judge: decides if a finding is valid, patches the eval suite, or escalates.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class FindingType(str, Enum):
    LOOPHOLE = "loophole"  # passes eval but answer is wrong
    OVERREACH = "overreach"  # fails eval but answer is correct


class Verdict(str, Enum):
    VALID = "valid"  # finding is real, add as new eval case
    INVALID = "invalid"  # false alarm, discard
    ESCALATE = "escalate"  # needs human review


@dataclass
class AdversarialFinding:
    """A finding from either adversary agent."""
    finding_type: FindingType
    input_text: str
    model_output: str
    expected: str
    explanation: str
    verdict: Verdict = Verdict.VALID
    round_number: int = 0


@dataclass
class EvalPatch:
    """A new eval case generated from a valid finding."""
    name: str
    input_text: str
    expected: str
    grading_criteria: str
    source_finding: FindingType


@dataclass
class AdversarialRound:
    """One round of adversarial testing."""
    round_number: int
    loopholes: list[AdversarialFinding] = field(default_factory=list)
    overreaches: list[AdversarialFinding] = field(default_factory=list)
    patches: list[EvalPatch] = field(default_factory=list)
    escalations: list[AdversarialFinding] = field(default_factory=list)


@dataclass
class AdversarialResult:
    """Result of the full adversarial eval loop."""
    rounds: list[AdversarialRound] = field(default_factory=list)
    total_findings: int = 0
    total_patches: int = 0
    total_escalations: int = 0
    converged: bool = False


# ── Agent interfaces ──

AdversaryFn = type(lambda input_text, expected, model_output: [])  # placeholder

LoopholeFinder = "Callable[[str, str, str], list[AdversarialFinding]]"
OverreachFinder = "Callable[[str, str, str], list[AdversarialFinding]]"
JudgeFn = "Callable[[AdversarialFinding], Verdict]"


# ── Default implementations ──

def find_loopholes(
    eval_cases: list[dict[str, str]],
    model_outputs: list[str],
) -> list[AdversarialFinding]:
    """Find cases where model output passes but is semantically wrong.

    Simple heuristic: check if output contains expected keywords but
    in a contradictory context.
    """
    findings: list[AdversarialFinding] = []
    for case, output in zip(eval_cases, model_outputs):
        expected = case.get("expected", "")
        input_text = case.get("input", "")

        # Heuristic: output is suspiciously short relative to expected
        if len(output.strip()) < len(expected) // 3 and len(expected) > 20:
            findings.append(AdversarialFinding(
                finding_type=FindingType.LOOPHOLE,
                input_text=input_text,
                model_output=output,
                expected=expected,
                explanation="Output is suspiciously short — may have skipped required content",
            ))

        # Heuristic: output contradicts expected with negation
        if _has_contradiction(output, expected):
            findings.append(AdversarialFinding(
                finding_type=FindingType.LOOPHOLE,
                input_text=input_text,
                model_output=output,
                expected=expected,
                explanation="Output contains contradictory language relative to expected",
            ))

    return findings


def find_overreaches(
    eval_cases: list[dict[str, str]],
    model_outputs: list[str],
    failed_indices: list[int],
) -> list[AdversarialFinding]:
    """Find cases where model fails but output is actually correct.

    Checks if the model output is a valid rephrasing of expected.
    """
    findings: list[AdversarialFinding] = []
    for idx in failed_indices:
        if idx >= len(eval_cases) or idx >= len(model_outputs):
            continue
        case = eval_cases[idx]
        output = model_outputs[idx]
        expected = case.get("expected", "")
        input_text = case.get("input", "")

        # Heuristic: high word overlap suggests correct but different phrasing
        overlap = _word_overlap(output, expected)
        if overlap > 0.6:
            findings.append(AdversarialFinding(
                finding_type=FindingType.OVERREACH,
                input_text=input_text,
                model_output=output,
                expected=expected,
                explanation=f"Word overlap {overlap:.0%} suggests correct answer with different phrasing",
            ))

    return findings


def judge_finding(finding: AdversarialFinding) -> Verdict:
    """Simple rule-based judge — in production this would be an LLM call."""
    if finding.finding_type == FindingType.LOOPHOLE:
        # Loopholes with contradictions are likely valid
        if "contradict" in finding.explanation.lower():
            return Verdict.VALID
        return Verdict.ESCALATE

    if finding.finding_type == FindingType.OVERREACH:
        # High overlap overreaches are likely valid
        if "overlap" in finding.explanation and "%" in finding.explanation:
            return Verdict.VALID
        return Verdict.ESCALATE

    return Verdict.ESCALATE


def create_patch(finding: AdversarialFinding, round_num: int) -> EvalPatch:
    """Create a new eval case from a valid finding."""
    if finding.finding_type == FindingType.LOOPHOLE:
        return EvalPatch(
            name=f"loophole-r{round_num}-{hash(finding.input_text) % 10000}",
            input_text=finding.input_text,
            expected=finding.expected,
            grading_criteria=f"Must NOT produce: {finding.model_output[:100]}. "
                             f"Reason: {finding.explanation}",
            source_finding=FindingType.LOOPHOLE,
        )
    return EvalPatch(
        name=f"overreach-r{round_num}-{hash(finding.input_text) % 10000}",
        input_text=finding.input_text,
        expected=finding.model_output,  # the model was actually right
        grading_criteria=f"Accept rephrased answer. Original expected: {finding.expected[:100]}",
        source_finding=FindingType.OVERREACH,
    )


# ── Loop ──

def run_adversarial_loop(
    eval_cases: list[dict[str, str]],
    model_outputs: list[str],
    failed_indices: list[int],
    *,
    max_rounds: int = 3,
) -> AdversarialResult:
    """Run the adversarial eval loop.

    Each round:
    1. Loophole finder checks passing cases
    2. Overreach finder checks failing cases
    3. Judge validates findings
    4. Valid findings become new eval cases (patches)
    5. Stop when no new findings or max rounds reached
    """
    result = AdversarialResult()

    for round_num in range(1, max_rounds + 1):
        rnd = AdversarialRound(round_number=round_num)

        # Find adversarial cases
        loopholes = find_loopholes(eval_cases, model_outputs)
        overreaches = find_overreaches(eval_cases, model_outputs, failed_indices)

        # Judge each finding
        all_findings = loopholes + overreaches
        for finding in all_findings:
            finding.round_number = round_num
            verdict = judge_finding(finding)
            finding.verdict = verdict

            if verdict == Verdict.VALID:
                patch = create_patch(finding, round_num)
                rnd.patches.append(patch)
            elif verdict == Verdict.ESCALATE:
                rnd.escalations.append(finding)

        rnd.loopholes = loopholes
        rnd.overreaches = overreaches

        result.rounds.append(rnd)
        result.total_findings += len(loopholes) + len(overreaches)
        result.total_patches += len(rnd.patches)
        result.total_escalations += len(rnd.escalations)

        # Convergence: no new findings
        if not all_findings:
            result.converged = True
            break

    return result


# ── Helpers ──

def _has_contradiction(output: str, expected: str) -> bool:
    """Check if output contradicts expected using simple negation detection."""
    negations = {"not", "never", "no", "don't", "doesn't", "isn't", "aren't", "won't", "can't"}
    out_words = set(output.lower().split())
    exp_words = set(expected.lower().split())

    out_negs = out_words & negations
    exp_negs = exp_words & negations

    # Stem-like overlap: strip common suffixes for matching
    def _stems(words: set[str]) -> set[str]:
        result = set()
        for w in words:
            result.add(w)
            if w.endswith("s"):
                result.add(w[:-1])
            if w.endswith("ing"):
                result.add(w[:-3])
            if w.endswith("ed"):
                result.add(w[:-2])
        return result

    shared = _stems(out_words) & _stems(exp_words)

    # If one has negations the other doesn't, and they share content words
    return bool(out_negs ^ exp_negs) and len(shared) > 3


def _word_overlap(a: str, b: str) -> float:
    """Calculate word overlap ratio between two strings."""
    words_a = set(a.lower().split())
    words_b = set(b.lower().split())
    if not words_a or not words_b:
        return 0.0
    intersection = words_a & words_b
    smaller = min(len(words_a), len(words_b))
    return len(intersection) / smaller if smaller > 0 else 0.0


def format_adversarial_result(result: AdversarialResult) -> str:
    """Format as markdown."""
    lines = ["## Adversarial Eval Report\n"]
    status = "Converged" if result.converged else f"Max rounds ({len(result.rounds)})"
    lines.append(f"**Status**: {status} | **Findings**: {result.total_findings} | "
                 f"**Patches**: {result.total_patches} | **Escalations**: {result.total_escalations}\n")

    for rnd in result.rounds:
        lines.append(f"### Round {rnd.round_number}")
        lines.append(f"Loopholes: {len(rnd.loopholes)} | Overreaches: {len(rnd.overreaches)} | "
                     f"Patches: {len(rnd.patches)} | Escalations: {len(rnd.escalations)}")
        for patch in rnd.patches:
            lines.append(f"  + New eval case: `{patch.name}` ({patch.source_finding.value})")
        lines.append("")

    return "\n".join(lines)
