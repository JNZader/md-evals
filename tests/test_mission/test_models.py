"""Tests for Mission models (Pydantic schemas)."""


from md_evals.mission.models import (
    MissionConfig,
    MissionPassCriteria,
    MissionResult,
    MissionSummary,
    MissionTestCase,
    MissionTestResult,
)


class TestMissionPassCriteria:
    """Tests for MissionPassCriteria model."""

    def test_defaults(self):
        c = MissionPassCriteria()
        assert c.type == "regex"
        assert c.name == ""
        assert c.pattern is None
        assert c.pass_on_match is True
        assert c.pass_threshold == 0.8

    def test_regex_criteria(self):
        c = MissionPassCriteria(
            type="regex", name="has_hello", pattern="[Hh]ello"
        )
        assert c.type == "regex"
        assert c.pattern == "[Hh]ello"

    def test_exact_match_criteria(self):
        c = MissionPassCriteria(
            type="exact-match", name="has_text", expected="hello world"
        )
        assert c.type == "exact-match"
        assert c.expected == "hello world"

    def test_llm_judge_criteria(self):
        c = MissionPassCriteria(
            type="llm-judge",
            name="quality",
            judge_model="gpt-4o",
            criteria="Is the response helpful?",
            pass_threshold=0.9,
        )
        assert c.type == "llm-judge"
        assert c.judge_model == "gpt-4o"
        assert c.pass_threshold == 0.9

    def test_grader_criteria(self):
        c = MissionPassCriteria(
            type="grader",
            name="file_check",
            grader_type="FileExistsGrader",
            grader_config={"path": "output.txt"},
        )
        assert c.type == "grader"
        assert c.grader_type == "FileExistsGrader"


class TestMissionTestCase:
    """Tests for MissionTestCase model."""

    def test_minimal(self):
        tc = MissionTestCase(name="basic", prompt="Say hello")
        assert tc.name == "basic"
        assert tc.prompt == "Say hello"
        assert tc.variables == {}
        assert tc.pass_criteria == []
        assert tc.tags == []

    def test_full(self):
        tc = MissionTestCase(
            name="greeting",
            description="Test greeting behavior",
            prompt="Hello {name}!",
            variables={"name": "World"},
            pass_criteria=[
                MissionPassCriteria(
                    type="regex", name="has_hello", pattern="Hello"
                )
            ],
            tags=["greeting", "basic"],
        )
        assert tc.description == "Test greeting behavior"
        assert tc.variables == {"name": "World"}
        assert len(tc.pass_criteria) == 1
        assert tc.tags == ["greeting", "basic"]


class TestMissionConfig:
    """Tests for MissionConfig model."""

    def test_defaults(self):
        cfg = MissionConfig(name="test-mission")
        assert cfg.name == "test-mission"
        assert cfg.version == "1.0"
        assert cfg.model == "gpt-4o"
        assert cfg.provider == "openai"
        assert cfg.temperature == 0.7
        assert cfg.results_dir == ".mission-results"
        assert cfg.test_cases == []

    def test_full_config(self):
        cfg = MissionConfig(
            name="regression-suite",
            version="2.0",
            description="Weekly regression test",
            skill_under_test="./SKILL.md",
            model="claude-3",
            provider="anthropic",
            schedule_hint="0 0 * * 0",
            test_cases=[
                MissionTestCase(name="t1", prompt="test")
            ],
            tags=["weekly", "regression"],
        )
        assert cfg.description == "Weekly regression test"
        assert cfg.skill_under_test == "./SKILL.md"
        assert cfg.schedule_hint == "0 0 * * 0"
        assert len(cfg.test_cases) == 1

    def test_from_dict(self):
        data = {
            "name": "from-dict",
            "test_cases": [
                {"name": "t1", "prompt": "hello"},
                {"name": "t2", "prompt": "world"},
            ],
        }
        cfg = MissionConfig(**data)
        assert cfg.name == "from-dict"
        assert len(cfg.test_cases) == 2


class TestMissionTestResult:
    """Tests for MissionTestResult model."""

    def test_defaults(self):
        r = MissionTestResult(test_name="t1", passed=True)
        assert r.test_name == "t1"
        assert r.passed is True
        assert r.score == 0.0
        assert r.criteria_results == []
        assert r.error is None

    def test_failed_with_error(self):
        r = MissionTestResult(
            test_name="t1", passed=False, error="LLM timeout"
        )
        assert r.passed is False
        assert r.error == "LLM timeout"


class TestMissionSummary:
    """Tests for MissionSummary model."""

    def test_defaults(self):
        s = MissionSummary()
        assert s.total == 0
        assert s.passed == 0
        assert s.pass_rate == 0.0

    def test_calculated(self):
        s = MissionSummary(total=10, passed=7, failed=3, pass_rate=0.7)
        assert s.pass_rate == 0.7


class TestMissionResult:
    """Tests for MissionResult model."""

    def test_minimal(self):
        r = MissionResult(mission_name="test")
        assert r.mission_name == "test"
        assert r.timestamp  # auto-generated
        assert r.test_results == []

    def test_serialization(self):
        r = MissionResult(
            mission_name="test",
            model="gpt-4o",
            provider="openai",
            test_results=[
                MissionTestResult(test_name="t1", passed=True, score=1.0),
            ],
            summary=MissionSummary(total=1, passed=1, pass_rate=1.0),
        )
        data = r.model_dump(mode="json")
        assert data["mission_name"] == "test"
        assert len(data["test_results"]) == 1
        # Roundtrip
        r2 = MissionResult(**data)
        assert r2.mission_name == "test"
