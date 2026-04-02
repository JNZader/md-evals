"""Tests for SQLGrader — SQL execution and validation."""

from pathlib import Path

import pytest
import sqlite3

from md_evals.graders.sql_grader import SQLGrader


def _create_db(workspace: Path, db_name: str = "test.db") -> None:
    """Create a simple SQLite database with a users table."""
    db_path = workspace / db_name
    conn = sqlite3.connect(str(db_path))
    conn.execute(
        "CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, email TEXT)"
    )
    conn.execute("INSERT INTO users VALUES (1, 'Alice', 'alice@test.com')")
    conn.execute("INSERT INTO users VALUES (2, 'Bob', 'bob@test.com')")
    conn.execute("INSERT INTO users VALUES (3, 'Carol', 'carol@test.com')")
    conn.commit()
    conn.close()


class TestExtractSqlBlocks:
    """_extract_sql_blocks finds SQL blocks and ignores other language blocks."""

    def test_finds_sql_blocks(self):
        text = (
            "Some text\n"
            "```sql\n"
            "SELECT * FROM users;\n"
            "```\n"
            "More text\n"
            "```sql\n"
            "INSERT INTO logs VALUES (1, 'test');\n"
            "```\n"
        )
        blocks = SQLGrader._extract_sql_blocks(text)
        assert len(blocks) == 2
        assert "SELECT * FROM users;" in blocks[0]
        assert "INSERT INTO logs VALUES (1, 'test');" in blocks[1]

    def test_ignores_other_language_blocks(self):
        text = (
            "```python\n"
            "print('hello')\n"
            "```\n"
            "```sql\n"
            "SELECT 1;\n"
            "```\n"
            "```javascript\n"
            "console.log('hi');\n"
            "```\n"
        )
        blocks = SQLGrader._extract_sql_blocks(text)
        assert len(blocks) == 1
        assert "SELECT 1;" in blocks[0]

    def test_no_sql_blocks(self):
        text = "No code blocks here at all."
        blocks = SQLGrader._extract_sql_blocks(text)
        assert blocks == []

    def test_empty_sql_block_ignored(self):
        text = "```sql\n\n```\n```sql\nSELECT 1;\n```\n"
        blocks = SQLGrader._extract_sql_blocks(text)
        assert len(blocks) == 1
        assert "SELECT 1;" in blocks[0]

    def test_case_insensitive_tag(self):
        text = "```SQL\nSELECT 1;\n```\n"
        blocks = SQLGrader._extract_sql_blocks(text)
        assert len(blocks) == 1


class TestGradeAllPass:
    """All queries valid + assertions met -> score 1.0."""

    def test_all_pass(self, tmp_path: Path):
        _create_db(tmp_path)
        md = (
            "```sql\n"
            "SELECT * FROM users;\n"
            "```\n"
            "```sql\n"
            "SELECT name FROM users WHERE id = 1;\n"
            "```\n"
        )
        (tmp_path / "output.md").write_text(md)

        grader = SQLGrader()
        result = grader.grade(tmp_path)
        assert result.passed is True
        assert result.score == 1.0
        assert result.reason is None
        assert result.details["passed_count"] == 2
        assert result.details["total"] == 2


class TestGradePartial:
    """Some queries fail -> proportional score."""

    def test_partial(self, tmp_path: Path):
        _create_db(tmp_path)
        md = (
            "```sql\n"
            "SELECT * FROM users;\n"
            "```\n"
            "```sql\n"
            "SELECT * FROM nonexistent_table;\n"
            "```\n"
        )
        (tmp_path / "output.md").write_text(md)

        grader = SQLGrader(pass_threshold=1.0)
        result = grader.grade(tmp_path)
        assert result.passed is False
        assert result.score == pytest.approx(0.5)
        assert result.details["passed_count"] == 1
        assert result.details["total"] == 2


class TestGradeNoBlocks:
    """No SQL blocks -> vacuous pass (score 1.0)."""

    def test_no_blocks(self, tmp_path: Path):
        (tmp_path / "output.md").write_text("Just regular markdown, no SQL.")

        grader = SQLGrader()
        result = grader.grade(tmp_path)
        assert result.passed is True
        assert result.score == 1.0
        assert result.details["total"] == 0


class TestGradeMissingDb:
    """Database doesn't exist -> score 0.0."""

    def test_missing_db(self, tmp_path: Path):
        md = "```sql\nSELECT 1;\n```\n"
        (tmp_path / "output.md").write_text(md)
        # No database created

        grader = SQLGrader()
        result = grader.grade(tmp_path)
        assert result.passed is False
        assert result.score == 0.0
        assert "not found" in result.reason


class TestGradeMissingMarkdown:
    """Markdown file doesn't exist -> score 0.0."""

    def test_missing_markdown(self, tmp_path: Path):
        grader = SQLGrader(markdown_file="nonexistent.md")
        result = grader.grade(tmp_path)
        assert result.passed is False
        assert result.score == 0.0
        assert "not found" in result.reason


class TestExpectRows:
    """Validates row count."""

    def test_exact_row_count_pass(self, tmp_path: Path):
        _create_db(tmp_path)
        md = "```sql\nSELECT * FROM users;\n```\n"
        (tmp_path / "output.md").write_text(md)

        grader = SQLGrader(expect_rows=3)
        result = grader.grade(tmp_path)
        assert result.passed is True
        assert result.score == 1.0

    def test_wrong_row_count_fail(self, tmp_path: Path):
        _create_db(tmp_path)
        md = "```sql\nSELECT * FROM users;\n```\n"
        (tmp_path / "output.md").write_text(md)

        grader = SQLGrader(expect_rows=5)
        result = grader.grade(tmp_path)
        assert result.passed is False
        assert result.score == 0.0


class TestExpectColumns:
    """Validates column names."""

    def test_correct_columns_pass(self, tmp_path: Path):
        _create_db(tmp_path)
        md = "```sql\nSELECT id, name FROM users;\n```\n"
        (tmp_path / "output.md").write_text(md)

        grader = SQLGrader(expect_columns=["id", "name"])
        result = grader.grade(tmp_path)
        assert result.passed is True
        assert result.score == 1.0

    def test_wrong_columns_fail(self, tmp_path: Path):
        _create_db(tmp_path)
        md = "```sql\nSELECT id, name FROM users;\n```\n"
        (tmp_path / "output.md").write_text(md)

        grader = SQLGrader(expect_columns=["id", "email"])
        result = grader.grade(tmp_path)
        assert result.passed is False
        assert result.score == 0.0


class TestExpectNonEmpty:
    """Validates non-empty result."""

    def test_non_empty_pass(self, tmp_path: Path):
        _create_db(tmp_path)
        md = "```sql\nSELECT * FROM users;\n```\n"
        (tmp_path / "output.md").write_text(md)

        grader = SQLGrader(expect_non_empty=True)
        result = grader.grade(tmp_path)
        assert result.passed is True

    def test_empty_result_fail(self, tmp_path: Path):
        _create_db(tmp_path)
        md = "```sql\nSELECT * FROM users WHERE id = 999;\n```\n"
        (tmp_path / "output.md").write_text(md)

        grader = SQLGrader(expect_non_empty=True)
        result = grader.grade(tmp_path)
        assert result.passed is False
        assert result.score == 0.0

    def test_non_empty_disabled(self, tmp_path: Path):
        _create_db(tmp_path)
        md = "```sql\nSELECT * FROM users WHERE id = 999;\n```\n"
        (tmp_path / "output.md").write_text(md)

        grader = SQLGrader(expect_non_empty=False, expect_rows=None)
        result = grader.grade(tmp_path)
        assert result.passed is True
        assert result.score == 1.0


class TestSyntaxError:
    """Bad SQL -> that query fails, others still run."""

    def test_syntax_error_partial(self, tmp_path: Path):
        _create_db(tmp_path)
        md = (
            "```sql\n"
            "SELECT * FROM users;\n"
            "```\n"
            "```sql\n"
            "SELEKT BAD SYNTAX HERE;\n"
            "```\n"
            "```sql\n"
            "SELECT name FROM users WHERE id = 2;\n"
            "```\n"
        )
        (tmp_path / "output.md").write_text(md)

        grader = SQLGrader(pass_threshold=0.5)
        result = grader.grade(tmp_path)
        assert result.passed is True
        assert result.score == pytest.approx(2 / 3)
        assert result.details["passed_count"] == 2
        assert result.details["total"] == 3
        # The bad query should have an error
        bad_query = result.details["queries"][1]
        assert bad_query["passed"] is False
        assert bad_query["error"] is not None


class TestEvaluatorName:
    """Result uses the grader's name."""

    def test_custom_name(self, tmp_path: Path):
        (tmp_path / "output.md").write_text("No SQL.")
        grader = SQLGrader(name="my_sql_grader")
        result = grader.grade(tmp_path)
        assert result.evaluator_name == "my_sql_grader"
