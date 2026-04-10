"""Tests for adversarial_eval — loophole/overreach finding and patching."""

from md_evals.graders.adversarial_eval import (
    AdversarialFinding,
    FindingType,
    Verdict,
    create_patch,
    find_loopholes,
    find_overreaches,
    format_adversarial_result,
    judge_finding,
    run_adversarial_loop,
)


class TestFindLoopholes:
    def test_detects_suspiciously_short_output(self):
        cases = [{"input": "Explain Python", "expected": "Python is a high-level programming language with dynamic typing"}]
        outputs = ["Yes"]  # way too short
        findings = find_loopholes(cases, outputs)
        assert len(findings) >= 1
        assert findings[0].finding_type == FindingType.LOOPHOLE

    def test_detects_contradiction(self):
        cases = [{"input": "Is Python typed?", "expected": "Python supports dynamic typing"}]
        outputs = ["Python does not support typing at all"]
        findings = find_loopholes(cases, outputs)
        contradictions = [f for f in findings if "contradict" in f.explanation.lower()]
        assert len(contradictions) >= 1

    def test_no_findings_for_good_output(self):
        cases = [{"input": "What is 2+2?", "expected": "4"}]
        outputs = ["The answer is 4"]
        findings = find_loopholes(cases, outputs)
        assert len(findings) == 0


class TestFindOverreaches:
    def test_detects_valid_rephrasing(self):
        cases = [{"input": "What is Python?", "expected": "Python is a programming language"}]
        outputs = ["Python is a versatile programming language used widely"]
        findings = find_overreaches(cases, outputs, [0])
        assert len(findings) >= 1
        assert findings[0].finding_type == FindingType.OVERREACH

    def test_no_findings_for_wrong_answer(self):
        cases = [{"input": "What is Python?", "expected": "Python is a programming language"}]
        outputs = ["JavaScript is a web framework"]
        findings = find_overreaches(cases, outputs, [0])
        assert len(findings) == 0

    def test_handles_out_of_range_indices(self):
        cases = [{"input": "test", "expected": "test"}]
        outputs = ["test"]
        findings = find_overreaches(cases, outputs, [5, 10])
        assert len(findings) == 0


class TestJudge:
    def test_validates_contradiction_loophole(self):
        finding = AdversarialFinding(
            finding_type=FindingType.LOOPHOLE,
            input_text="test",
            model_output="not correct",
            expected="correct",
            explanation="Output contains contradictory language",
        )
        assert judge_finding(finding) == Verdict.VALID

    def test_validates_overlap_overreach(self):
        finding = AdversarialFinding(
            finding_type=FindingType.OVERREACH,
            input_text="test",
            model_output="correct answer rephrased",
            expected="correct answer",
            explanation="Word overlap 80% suggests correct answer",
        )
        assert judge_finding(finding) == Verdict.VALID

    def test_escalates_unclear_findings(self):
        finding = AdversarialFinding(
            finding_type=FindingType.LOOPHOLE,
            input_text="test",
            model_output="maybe",
            expected="yes",
            explanation="Output is suspiciously short",
        )
        assert judge_finding(finding) == Verdict.ESCALATE


class TestCreatePatch:
    def test_creates_loophole_patch(self):
        finding = AdversarialFinding(
            finding_type=FindingType.LOOPHOLE,
            input_text="What is X?",
            model_output="Wrong answer",
            expected="Right answer",
            explanation="Contradiction detected",
        )
        patch = create_patch(finding, 1)
        assert "loophole" in patch.name
        assert patch.source_finding == FindingType.LOOPHOLE
        assert "Must NOT produce" in patch.grading_criteria

    def test_creates_overreach_patch(self):
        finding = AdversarialFinding(
            finding_type=FindingType.OVERREACH,
            input_text="What is X?",
            model_output="Correct rephrasing",
            expected="Original expected",
            explanation="High overlap",
        )
        patch = create_patch(finding, 2)
        assert "overreach" in patch.name
        assert patch.expected == "Correct rephrasing"  # uses model output as new expected


class TestAdversarialLoop:
    def test_runs_and_produces_results(self):
        cases = [
            {"input": "Explain X", "expected": "X is a complex concept with multiple facets and implications"},
            {"input": "Is Y true?", "expected": "Y is generally considered true in most contexts"},
        ]
        outputs = ["Yes", "Y is true and well-established in academic literature"]
        failed = [0]  # first one "failed" the eval

        result = run_adversarial_loop(cases, outputs, failed, max_rounds=2)
        assert len(result.rounds) >= 1
        assert result.total_findings >= 0

    def test_converges_with_no_findings(self):
        cases = [{"input": "2+2?", "expected": "4"}]
        outputs = ["The answer is 4"]
        result = run_adversarial_loop(cases, outputs, [], max_rounds=3)
        assert result.converged

    def test_max_rounds_respected(self):
        # Force findings every round
        cases = [{"input": "test", "expected": "a very long expected answer that the model will not fully reproduce in its output"}]
        outputs = ["x"]  # suspiciously short
        result = run_adversarial_loop(cases, outputs, [], max_rounds=2)
        assert len(result.rounds) <= 2


class TestFormat:
    def test_produces_markdown(self):
        cases = [{"input": "test", "expected": "test answer"}]
        outputs = ["test answer"]
        result = run_adversarial_loop(cases, outputs, [], max_rounds=1)
        text = format_adversarial_result(result)
        assert "Adversarial Eval Report" in text
        assert "Round 1" in text
