"""Tests for the SDD quality benchmark suite."""


from md_evals.benchmarks.sdd_benchmark import (
    SDDArtifactType,
    SDDBenchmarkResult,
    SDDBenchmarkSuite,
    SDDRubric,
    SDDRubricCriterion,
    build_cascade_for_artifact,
    get_rubric,
    get_sample_cases,
    score_against_rubric,
)


# ============================================================================
# get_rubric
# ============================================================================


class TestGetRubric:
    """Tests for rubric retrieval."""

    def test_returns_rubric_for_each_artifact_type(self):
        for artifact_type in SDDArtifactType:
            rubric = get_rubric(artifact_type)
            assert isinstance(rubric, SDDRubric)
            assert rubric.artifact_type == artifact_type

    def test_rubric_criteria_weights_sum_to_one(self):
        for artifact_type in SDDArtifactType:
            rubric = get_rubric(artifact_type)
            total_weight = sum(c.weight for c in rubric.criteria)
            assert abs(total_weight - 1.0) < 0.01, (
                f"{artifact_type.value} criteria weights sum to {total_weight}, expected 1.0"
            )

    def test_rubric_has_at_least_two_criteria(self):
        for artifact_type in SDDArtifactType:
            rubric = get_rubric(artifact_type)
            assert len(rubric.criteria) >= 2

    def test_rubric_min_pass_score_is_reasonable(self):
        for artifact_type in SDDArtifactType:
            rubric = get_rubric(artifact_type)
            assert 0.3 <= rubric.min_pass_score <= 0.9


# ============================================================================
# get_sample_cases
# ============================================================================


class TestGetSampleCases:
    """Tests for sample data retrieval."""

    def test_returns_all_cases_without_filter(self):
        cases = get_sample_cases()
        assert len(cases) >= 7  # at least 7 sample cases defined

    def test_filters_by_artifact_type(self):
        proposals = get_sample_cases(artifact_type=SDDArtifactType.PROPOSAL)
        assert all(c.artifact_type == SDDArtifactType.PROPOSAL for c in proposals)
        assert len(proposals) >= 2  # at least 2 proposal samples

    def test_filters_by_tags(self):
        good_cases = get_sample_cases(tags=["good"])
        assert all("good" in c.tags for c in good_cases)

    def test_combined_filter(self):
        good_proposals = get_sample_cases(
            artifact_type=SDDArtifactType.PROPOSAL, tags=["good"]
        )
        assert all(
            c.artifact_type == SDDArtifactType.PROPOSAL and "good" in c.tags
            for c in good_proposals
        )

    def test_each_case_has_required_fields(self):
        for case in get_sample_cases():
            assert case.case_id
            assert case.artifact_type in SDDArtifactType
            assert case.description
            assert case.input_context
            assert case.expected_output

    def test_case_ids_are_unique(self):
        cases = get_sample_cases()
        ids = [c.case_id for c in cases]
        assert len(ids) == len(set(ids)), "Duplicate case IDs found"

    def test_returns_empty_for_impossible_filter(self):
        cases = get_sample_cases(tags=["nonexistent-tag-xyz"])
        assert cases == []


# ============================================================================
# score_against_rubric
# ============================================================================


class TestScoreAgainstRubric:
    """Tests for rubric scoring."""

    def test_good_proposal_scores_above_threshold(self):
        cases = get_sample_cases(artifact_type=SDDArtifactType.PROPOSAL, tags=["good"])
        rubric = get_rubric(SDDArtifactType.PROPOSAL)

        for case in cases:
            score, criterion_scores = score_against_rubric(case.expected_output, rubric)
            assert score >= rubric.min_pass_score, (
                f"Case {case.case_id} scored {score:.2f}, expected >= {rubric.min_pass_score}"
            )

    def test_bad_proposal_scores_below_threshold(self):
        cases = get_sample_cases(artifact_type=SDDArtifactType.PROPOSAL, tags=["bad"])
        rubric = get_rubric(SDDArtifactType.PROPOSAL)

        for case in cases:
            score, _ = score_against_rubric(case.expected_output, rubric)
            assert score < rubric.min_pass_score, (
                f"Bad case {case.case_id} scored {score:.2f}, expected < {rubric.min_pass_score}"
            )

    def test_good_spec_scores_above_threshold(self):
        cases = get_sample_cases(artifact_type=SDDArtifactType.SPEC, tags=["good"])
        rubric = get_rubric(SDDArtifactType.SPEC)

        for case in cases:
            score, _ = score_against_rubric(case.expected_output, rubric)
            assert score >= rubric.min_pass_score

    def test_bad_spec_scores_below_threshold(self):
        cases = get_sample_cases(artifact_type=SDDArtifactType.SPEC, tags=["bad"])
        rubric = get_rubric(SDDArtifactType.SPEC)

        for case in cases:
            score, _ = score_against_rubric(case.expected_output, rubric)
            assert score < rubric.min_pass_score

    def test_returns_per_criterion_scores(self):
        rubric = get_rubric(SDDArtifactType.PROPOSAL)
        _, criterion_scores = score_against_rubric("## Intent\nSome intent text", rubric)

        assert "intent" in criterion_scores
        assert "scope" in criterion_scores
        assert all(0.0 <= s <= 1.0 for s in criterion_scores.values())

    def test_empty_output_scores_low(self):
        rubric = get_rubric(SDDArtifactType.PROPOSAL)
        score, _ = score_against_rubric("", rubric)
        assert score < 0.3

    def test_score_is_between_zero_and_one(self):
        for artifact_type in SDDArtifactType:
            rubric = get_rubric(artifact_type)
            score, _ = score_against_rubric("Some random text", rubric)
            assert 0.0 <= score <= 1.0

    def test_custom_rubric_with_no_keywords_or_sections(self):
        rubric = SDDRubric(
            artifact_type=SDDArtifactType.PROPOSAL,
            criteria=[
                SDDRubricCriterion(
                    name="empty",
                    description="No requirements",
                    weight=1.0,
                ),
            ],
        )
        score, criterion_scores = score_against_rubric("anything", rubric)
        # With no keywords or sections, should return neutral 0.5
        assert criterion_scores["empty"] == 0.5


# ============================================================================
# build_cascade_for_artifact
# ============================================================================


class TestBuildCascade:
    """Tests for cascade evaluator integration."""

    def test_builds_cascade_for_each_artifact_type(self):
        for artifact_type in SDDArtifactType:
            cascade = build_cascade_for_artifact(artifact_type)
            assert cascade.name == f"sdd_{artifact_type.value}_benchmark"
            assert len(cascade.steps) >= 1

    def test_cascade_fails_empty_output(self):
        cascade = build_cascade_for_artifact(SDDArtifactType.PROPOSAL)
        result = cascade.evaluate("")
        assert not result.passed

    def test_cascade_result_has_step_details(self):
        cascade = build_cascade_for_artifact(SDDArtifactType.PROPOSAL)
        result = cascade.evaluate("## Intent\nSome text about intent and motivation")
        assert result.steps_executed > 0
        assert len(result.step_results) > 0


# ============================================================================
# SDDBenchmarkSuite
# ============================================================================


class TestSDDBenchmarkSuite:
    """Tests for the benchmark suite orchestrator."""

    def test_run_all_returns_results_for_all_samples(self):
        suite = SDDBenchmarkSuite()
        results = suite.run_all()
        assert len(results) >= 7
        assert all(isinstance(r, SDDBenchmarkResult) for r in results)

    def test_run_samples_with_tag_filter(self):
        suite = SDDBenchmarkSuite()
        good_results = suite.run_samples(tags=["good"])
        assert all(r.passed for r in good_results), (
            "All 'good' tagged samples should pass their rubrics"
        )

    def test_run_samples_bad_tag_fails(self):
        suite = SDDBenchmarkSuite()
        bad_results = suite.run_samples(tags=["bad"])
        assert all(not r.passed for r in bad_results), (
            "All 'bad' tagged samples should fail their rubrics"
        )

    def test_suite_with_artifact_type_filter(self):
        suite = SDDBenchmarkSuite(artifact_types=[SDDArtifactType.PROPOSAL])
        results = suite.run_all()
        assert all(r.artifact_type == SDDArtifactType.PROPOSAL for r in results)

    def test_evaluate_custom_output(self):
        suite = SDDBenchmarkSuite()
        result = suite.evaluate(
            output="## Intent\nMigrate auth. The goal is security.\n## Scope\nAll endpoints in scope.\n## Approach\nThe approach uses JWT. Tradeoff: complexity.\n## Risks\nRisk of breaking changes.",
            artifact_type=SDDArtifactType.PROPOSAL,
        )
        assert isinstance(result, SDDBenchmarkResult)
        assert result.case_id == "custom-proposal"
        assert 0.0 <= result.score <= 1.0

    def test_result_includes_cascade(self):
        suite = SDDBenchmarkSuite()
        results = suite.run_all()
        for result in results:
            assert result.cascade_result is not None
            assert "cascade_passed" in result.details

    def test_result_includes_criterion_scores(self):
        suite = SDDBenchmarkSuite()
        results = suite.run_all()
        for result in results:
            assert len(result.criterion_scores) > 0
