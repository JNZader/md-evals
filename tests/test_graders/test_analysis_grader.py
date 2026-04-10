"""Tests for analysis phase graders (keyword coverage, sections, length)."""

from pathlib import Path

from md_evals.graders.analysis_grader import (
    KeywordCoverageGrader,
    SectionCoverageGrader,
    MinLengthGrader,
)


class TestKeywordCoverageGrader:
    """Tests for KeywordCoverageGrader."""

    def test_all_keywords_found(self, tmp_path: Path):
        grader = KeywordCoverageGrader(
            name="kw_check",
            content="The system uses React and TypeScript for the frontend.",
            keywords=["React", "TypeScript"],
        )
        result = grader.grade(tmp_path)
        assert result.passed is True
        assert result.score == 1.0

    def test_partial_keywords(self, tmp_path: Path):
        grader = KeywordCoverageGrader(
            name="kw_check",
            content="Uses React for UI.",
            keywords=["React", "TypeScript", "Redux"],
            pass_threshold=0.5,
        )
        result = grader.grade(tmp_path)
        # 1/3 = 0.33, below 0.5 threshold
        assert result.passed is False
        assert result.details["missing"] == ["TypeScript", "Redux"]

    def test_threshold_met(self, tmp_path: Path):
        grader = KeywordCoverageGrader(
            name="kw_check",
            content="Uses React and Redux.",
            keywords=["React", "TypeScript", "Redux"],
            pass_threshold=0.6,
        )
        result = grader.grade(tmp_path)
        # 2/3 = 0.66, above 0.6 threshold
        assert result.passed is True

    def test_case_insensitive_default(self, tmp_path: Path):
        grader = KeywordCoverageGrader(
            name="kw_check",
            content="react and typescript are great",
            keywords=["React", "TypeScript"],
        )
        result = grader.grade(tmp_path)
        assert result.passed is True

    def test_case_sensitive(self, tmp_path: Path):
        grader = KeywordCoverageGrader(
            name="kw_check",
            content="react is good",
            keywords=["React"],
            case_sensitive=True,
        )
        result = grader.grade(tmp_path)
        assert result.passed is False

    def test_empty_keywords(self, tmp_path: Path):
        grader = KeywordCoverageGrader(
            name="kw_check", content="anything", keywords=[]
        )
        result = grader.grade(tmp_path)
        assert result.passed is True

    def test_file_mode(self, tmp_path: Path):
        (tmp_path / "analysis.txt").write_text("Contains React and Angular")
        grader = KeywordCoverageGrader(
            name="kw_check",
            path="analysis.txt",
            keywords=["React", "Angular"],
        )
        result = grader.grade(tmp_path)
        assert result.passed is True

    def test_file_not_found(self, tmp_path: Path):
        grader = KeywordCoverageGrader(
            name="kw_check", path="missing.txt", keywords=["test"]
        )
        result = grader.grade(tmp_path)
        assert result.passed is False
        assert "not found" in result.reason

    def test_score_is_proportional(self, tmp_path: Path):
        grader = KeywordCoverageGrader(
            name="kw_check",
            content="Only has keyword_a and keyword_b",
            keywords=["keyword_a", "keyword_b", "keyword_c", "keyword_d"],
            pass_threshold=0.0,  # Always pass for score testing
        )
        result = grader.grade(tmp_path)
        assert result.score == 0.5  # 2/4

    def test_no_content_or_path(self, tmp_path: Path):
        grader = KeywordCoverageGrader(name="kw_check", keywords=["test"])
        result = grader.grade(tmp_path)
        assert result.passed is False


class TestSectionCoverageGrader:
    """Tests for SectionCoverageGrader."""

    def test_all_sections_found(self, tmp_path: Path):
        content = "# Introduction\nSome text\n## Methods\nMore text\n## Results\n"
        grader = SectionCoverageGrader(
            name="section_check",
            content=content,
            sections=[r"^#\s+Introduction", r"^##\s+Methods", r"^##\s+Results"],
        )
        result = grader.grade(tmp_path)
        assert result.passed is True

    def test_missing_section(self, tmp_path: Path):
        content = "# Introduction\n## Methods\n"
        grader = SectionCoverageGrader(
            name="section_check",
            content=content,
            sections=[r"^##\s+Results"],
        )
        result = grader.grade(tmp_path)
        assert result.passed is False

    def test_partial_threshold(self, tmp_path: Path):
        content = "# Intro\n## Analysis\n"
        grader = SectionCoverageGrader(
            name="section_check",
            content=content,
            sections=[r"Intro", r"Analysis", r"Conclusion"],
            pass_threshold=0.6,
        )
        result = grader.grade(tmp_path)
        # 2/3 = 0.66, above 0.6
        assert result.passed is True

    def test_empty_sections(self, tmp_path: Path):
        grader = SectionCoverageGrader(
            name="section_check", content="anything", sections=[]
        )
        result = grader.grade(tmp_path)
        assert result.passed is True

    def test_invalid_regex_counted_as_missing(self, tmp_path: Path):
        grader = SectionCoverageGrader(
            name="section_check",
            content="test content",
            sections=["[invalid"],
        )
        result = grader.grade(tmp_path)
        assert result.passed is False

    def test_file_mode(self, tmp_path: Path):
        (tmp_path / "doc.md").write_text("# Header\n## Section\n")
        grader = SectionCoverageGrader(
            name="section_check",
            path="doc.md",
            sections=[r"^#\s+Header"],
        )
        result = grader.grade(tmp_path)
        assert result.passed is True


class TestMinLengthGrader:
    """Tests for MinLengthGrader."""

    def test_meets_word_minimum(self, tmp_path: Path):
        grader = MinLengthGrader(
            name="len_check",
            content="one two three four five",
            min_words=5,
        )
        result = grader.grade(tmp_path)
        assert result.passed is True

    def test_below_word_minimum(self, tmp_path: Path):
        grader = MinLengthGrader(
            name="len_check",
            content="too short",
            min_words=10,
        )
        result = grader.grade(tmp_path)
        assert result.passed is False
        assert "Word count" in result.reason

    def test_meets_char_minimum(self, tmp_path: Path):
        grader = MinLengthGrader(
            name="len_check",
            content="a" * 100,
            min_chars=50,
        )
        result = grader.grade(tmp_path)
        assert result.passed is True

    def test_below_char_minimum(self, tmp_path: Path):
        grader = MinLengthGrader(
            name="len_check",
            content="short",
            min_chars=100,
        )
        result = grader.grade(tmp_path)
        assert result.passed is False
        assert "Char count" in result.reason

    def test_both_constraints(self, tmp_path: Path):
        grader = MinLengthGrader(
            name="len_check",
            content="word " * 20,  # 20 words, 100 chars
            min_words=10,
            min_chars=50,
        )
        result = grader.grade(tmp_path)
        assert result.passed is True

    def test_no_constraints(self, tmp_path: Path):
        grader = MinLengthGrader(name="len_check", content="x")
        result = grader.grade(tmp_path)
        assert result.passed is True

    def test_file_mode(self, tmp_path: Path):
        (tmp_path / "out.txt").write_text("word " * 50)
        grader = MinLengthGrader(
            name="len_check", path="out.txt", min_words=20
        )
        result = grader.grade(tmp_path)
        assert result.passed is True

    def test_file_not_found(self, tmp_path: Path):
        grader = MinLengthGrader(
            name="len_check", path="missing.txt", min_words=1
        )
        result = grader.grade(tmp_path)
        assert result.passed is False

    def test_details_include_counts(self, tmp_path: Path):
        grader = MinLengthGrader(
            name="len_check",
            content="hello world",
            min_words=1,
            min_chars=1,
        )
        result = grader.grade(tmp_path)
        assert result.details["word_count"] == 2
        assert result.details["char_count"] == 11
