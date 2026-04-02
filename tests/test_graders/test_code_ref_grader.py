"""Tests for CodeRefGrader — backtick reference validation."""

from pathlib import Path

import pytest

from md_evals.graders.code_ref_grader import CodeRefGrader


class TestStripFencedBlocks:
    """_strip_fenced_blocks removes code blocks, keeps inline backticks."""

    def test_removes_fenced_block(self):
        md = (
            "Some text `inline_ref`\n"
            "```python\n"
            "not_a_ref.py\n"
            "```\n"
            "More text `another_ref`\n"
        )
        grader = CodeRefGrader()
        result = grader._strip_fenced_blocks(md)
        assert "not_a_ref.py" not in result
        assert "`inline_ref`" in result
        assert "`another_ref`" in result

    def test_removes_multiple_fenced_blocks(self):
        md = (
            "```js\ncode1\n```\n"
            "middle `keep_this`\n"
            "```\ncode2\n```\n"
        )
        grader = CodeRefGrader()
        result = grader._strip_fenced_blocks(md)
        assert "code1" not in result
        assert "code2" not in result
        assert "`keep_this`" in result

    def test_no_fenced_blocks_unchanged(self):
        md = "Just `some` inline `refs` here."
        grader = CodeRefGrader()
        result = grader._strip_fenced_blocks(md)
        assert result == md


class TestExtractRefs:
    """_extract_refs extracts backtick content, deduplicates, filters exclusions."""

    def test_extracts_inline_refs(self):
        md = "Use `src/main.py` and `EvaluatorResult` in your code."
        grader = CodeRefGrader()
        refs = grader._extract_refs(md)
        assert "src/main.py" in refs
        assert "EvaluatorResult" in refs

    def test_excludes_fenced_block_content(self):
        md = (
            "Ref `src/main.py` inline.\n"
            "```python\nnot_a_ref.py\n```\n"
        )
        grader = CodeRefGrader()
        refs = grader._extract_refs(md)
        assert "src/main.py" in refs
        assert "not_a_ref.py" not in refs

    def test_filters_exclusions(self):
        md = "Values: `true`, `false`, `None`, `src/utils.py`"
        grader = CodeRefGrader()
        refs = grader._extract_refs(md)
        assert refs == ["src/utils.py"]

    def test_deduplicates(self):
        md = "Use `foo.py` and `foo.py` again."
        grader = CodeRefGrader()
        refs = grader._extract_refs(md)
        assert refs == ["foo.py"]

    def test_empty_backticks_ignored(self):
        md = "Empty `` and valid `ref.py`."
        grader = CodeRefGrader()
        refs = grader._extract_refs(md)
        assert "ref.py" in refs
        assert len(refs) == 1

    def test_no_refs(self):
        md = "No backticks at all."
        grader = CodeRefGrader()
        refs = grader._extract_refs(md)
        assert refs == []


class TestClassifyRef:
    """_classify_ref distinguishes file paths from symbols."""

    def test_slash_is_file(self):
        grader = CodeRefGrader()
        assert grader._classify_ref("src/graders/base.py") == "file"

    def test_known_extension_is_file(self):
        grader = CodeRefGrader()
        assert grader._classify_ref("base.py") == "file"
        assert grader._classify_ref("index.ts") == "file"
        assert grader._classify_ref("main.go") == "file"

    def test_identifier_is_symbol(self):
        grader = CodeRefGrader()
        assert grader._classify_ref("EvaluatorResult") == "symbol"
        assert grader._classify_ref("grade") == "symbol"

    def test_no_extension_is_symbol(self):
        grader = CodeRefGrader()
        assert grader._classify_ref("Makefile") == "symbol"


class TestResolveFile:
    """_resolve_file checks workspace-relative file existence."""

    def test_existing_file_resolves(self, tmp_path: Path):
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "main.py").write_text("print('hello')")
        grader = CodeRefGrader()
        assert grader._resolve_file("src/main.py", tmp_path) is True

    def test_missing_file_unresolved(self, tmp_path: Path):
        grader = CodeRefGrader()
        assert grader._resolve_file("lib/missing.py", tmp_path) is False


class TestResolveSymbol:
    """_resolve_symbol searches source files for the symbol string."""

    def test_symbol_found_in_source(self, tmp_path: Path):
        (tmp_path / "models.py").write_text("class EvaluatorResult:\n    pass\n")
        grader = CodeRefGrader(search_dirs=["."], file_extensions=[".py"])
        assert grader._resolve_symbol("EvaluatorResult", tmp_path) is True

    def test_symbol_not_found(self, tmp_path: Path):
        (tmp_path / "models.py").write_text("class Something:\n    pass\n")
        grader = CodeRefGrader(search_dirs=["."], file_extensions=[".py"])
        assert grader._resolve_symbol("NonExistentClass", tmp_path) is False

    def test_symbol_respects_search_dirs(self, tmp_path: Path):
        """Symbol in tests/ not found when search_dirs is ['src/']."""
        (tmp_path / "src").mkdir()
        (tmp_path / "tests").mkdir()
        (tmp_path / "tests" / "helper.py").write_text("class MyHelper:\n    pass\n")
        (tmp_path / "src" / "main.py").write_text("x = 1\n")
        grader = CodeRefGrader(search_dirs=["src/"], file_extensions=[".py"])
        assert grader._resolve_symbol("MyHelper", tmp_path) is False

    def test_symbol_respects_file_extensions(self, tmp_path: Path):
        """Symbol in .txt not found when extensions are ['.py']."""
        (tmp_path / "notes.txt").write_text("class MyClass:\n    pass\n")
        grader = CodeRefGrader(search_dirs=["."], file_extensions=[".py"])
        assert grader._resolve_symbol("MyClass", tmp_path) is False


class TestGrade:
    """Full grade() integration tests."""

    def test_all_resolved(self, tmp_path: Path):
        """All refs exist -> score 1.0, passed True."""
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "main.py").write_text("class Foo:\n    pass\n")
        md = "See `src/main.py` and `Foo` for details."
        (tmp_path / "output.md").write_text(md)

        grader = CodeRefGrader(
            search_dirs=["."], file_extensions=[".py"], pass_threshold=0.8
        )
        result = grader.grade(tmp_path)
        assert result.passed is True
        assert result.score == 1.0
        assert result.reason is None
        assert len(result.details["resolved"]) == 2
        assert len(result.details["unresolved"]) == 0

    def test_partial_resolution(self, tmp_path: Path):
        """Some refs exist -> proportional score."""
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "main.py").write_text("class Foo:\n    pass\n")
        # 4 refs: src/main.py (file, exists), Foo (symbol, exists),
        # missing.py (file, missing), Bar (symbol, missing)
        md = "Refs: `src/main.py`, `Foo`, `missing.py`, `Bar`"
        (tmp_path / "output.md").write_text(md)

        grader = CodeRefGrader(
            search_dirs=["."], file_extensions=[".py"], pass_threshold=0.8
        )
        result = grader.grade(tmp_path)
        assert result.score == pytest.approx(0.5)
        assert result.passed is False
        assert len(result.details["resolved"]) == 2
        assert len(result.details["unresolved"]) == 2

    def test_below_threshold(self, tmp_path: Path):
        """Too many missing -> passed False."""
        md = "Refs: `missing1.py`, `missing2.py`, `missing3.py`, `missing4.py`, `missing5.py`"
        (tmp_path / "output.md").write_text(md)

        grader = CodeRefGrader(pass_threshold=0.8)
        result = grader.grade(tmp_path)
        assert result.score == 0.0
        assert result.passed is False
        assert "unresolved" in result.reason

    def test_no_refs_vacuous_pass(self, tmp_path: Path):
        """Empty refs -> vacuous pass (score 1.0)."""
        (tmp_path / "output.md").write_text("No backtick refs at all.")

        grader = CodeRefGrader()
        result = grader.grade(tmp_path)
        assert result.passed is True
        assert result.score == 1.0

    def test_missing_markdown_file(self, tmp_path: Path):
        """Markdown file doesn't exist -> score 0.0, passed False."""
        grader = CodeRefGrader(markdown_file="nonexistent.md")
        result = grader.grade(tmp_path)
        assert result.passed is False
        assert result.score == 0.0
        assert "not found" in result.reason

    def test_evaluator_name_set(self, tmp_path: Path):
        """Result uses the grader's name."""
        (tmp_path / "output.md").write_text("No refs.")
        grader = CodeRefGrader(name="my_code_ref")
        result = grader.grade(tmp_path)
        assert result.evaluator_name == "my_code_ref"

    def test_fenced_blocks_excluded_from_grading(self, tmp_path: Path):
        """Refs inside fenced blocks are not graded."""
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "real.py").write_text("x = 1")
        md = (
            "Valid: `src/real.py`\n"
            "```python\n"
            "fake_ref.py\n"
            "```\n"
        )
        (tmp_path / "output.md").write_text(md)

        grader = CodeRefGrader(search_dirs=["."], file_extensions=[".py"])
        result = grader.grade(tmp_path)
        assert result.passed is True
        assert result.score == 1.0
        assert result.details["total"] == 1

    def test_custom_search_dirs(self, tmp_path: Path):
        """search_dirs=['src/'] limits symbol search scope."""
        (tmp_path / "src").mkdir()
        (tmp_path / "tests").mkdir()
        (tmp_path / "tests" / "test_foo.py").write_text("class MySymbol:\n    pass\n")
        (tmp_path / "src" / "main.py").write_text("x = 1\n")
        md = "See `MySymbol` for details."
        (tmp_path / "output.md").write_text(md)

        grader = CodeRefGrader(
            search_dirs=["src/"], file_extensions=[".py"], pass_threshold=0.5
        )
        result = grader.grade(tmp_path)
        assert result.passed is False
        assert "MySymbol" in result.details["unresolved"]
