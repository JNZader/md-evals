"""Tests for md_evals.dashboard — SQLite export, SQL block parsing, table rendering,
and the full dashboard CLI command.
"""

from __future__ import annotations

import json
import sqlite3
import textwrap
from pathlib import Path

import pytest
from typer.testing import CliRunner

from md_evals.analytics import EvalRecord
from md_evals.cli import app
from md_evals.dashboard import (
    _rows_to_md_table,
    _SQL_BLOCK_RE,
    execute_sql_blocks,
    export_to_sqlite,
    render_dashboard,
)


# ─── Helpers ───────────────────────────────────────────────────────────────────


def _make_record(
    skill: str = "skill-a.md",
    grade: str = "B",
    score: float = 0.78,
    model: str = "gpt-4o",
    provider: str = "github-models",
    cost_usd: float | None = 0.0012,
    tokens_input: int = 100,
    tokens_output: int = 50,
    dimensions: dict | None = None,
    suite_name: str | None = None,
    idx: int = 0,
) -> EvalRecord:
    return EvalRecord(
        id=f"id-{idx}",
        skill_path=skill,
        timestamp=f"2024-01-0{idx + 1}T12:00:00Z",
        overall_grade=grade,
        overall_score=score,
        dimensions=dimensions or {"correctness": 0.9, "completeness": 0.7},
        model=model,
        provider=provider,
        cost_usd=cost_usd,
        tokens_input=tokens_input,
        tokens_output=tokens_output,
        duration_ms=1500,
        citations_valid=2,
        citations_total=4,
        suite_name=suite_name,
    )


# ─── SQLite Export Tests ───────────────────────────────────────────────────────


class TestExportToSqlite:
    def test_empty_records_creates_table(self):
        conn = export_to_sqlite([])
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='eval_records'")
        assert cursor.fetchone() is not None
        conn.close()

    def test_single_record_round_trip(self):
        r = _make_record()
        conn = export_to_sqlite([r])
        row = conn.execute("SELECT * FROM eval_records").fetchone()
        assert row is not None
        assert row["skill_path"] == r.skill_path
        assert row["overall_grade"] == r.overall_grade
        assert abs(row["overall_score"] - r.overall_score) < 1e-6
        assert row["model"] == r.model
        conn.close()

    def test_dimension_columns_created(self):
        r = _make_record(dimensions={"correctness": 0.9, "completeness": 0.7, "format": 0.8})
        conn = export_to_sqlite([r])
        # Check the dimension columns exist by querying them
        row = conn.execute(
            "SELECT dimension_correctness, dimension_completeness, dimension_format FROM eval_records"
        ).fetchone()
        assert abs(row[0] - 0.9) < 1e-6
        assert abs(row[1] - 0.7) < 1e-6
        assert abs(row[2] - 0.8) < 1e-6
        conn.close()

    def test_dimension_sparse_records(self):
        """Records with different dimension keys — missing ones must be NULL."""
        r1 = _make_record(dimensions={"correctness": 0.9}, idx=0)
        r2 = _make_record(dimensions={"completeness": 0.7}, idx=1)
        conn = export_to_sqlite([r1, r2])
        rows = conn.execute(
            "SELECT dimension_correctness, dimension_completeness FROM eval_records ORDER BY id"
        ).fetchall()
        assert rows[0][0] == pytest.approx(0.9)
        assert rows[0][1] is None
        assert rows[1][0] is None
        assert rows[1][1] == pytest.approx(0.7)
        conn.close()

    def test_multiple_records(self):
        records = [_make_record(skill=f"skill-{i}.md", idx=i) for i in range(5)]
        conn = export_to_sqlite(records)
        count = conn.execute("SELECT COUNT(*) FROM eval_records").fetchone()[0]
        assert count == 5
        conn.close()

    def test_persist_to_disk(self, tmp_path):
        r = _make_record()
        db_file = tmp_path / "test.db"
        conn = export_to_sqlite([r], db_path=db_file)
        conn.close()
        assert db_file.exists()
        # Reopen and verify data is persisted
        conn2 = sqlite3.connect(str(db_file))
        count = conn2.execute("SELECT COUNT(*) FROM eval_records").fetchone()[0]
        conn2.close()
        assert count == 1

    def test_none_cost_stored_as_null(self):
        r = _make_record(cost_usd=None)
        conn = export_to_sqlite([r])
        row = conn.execute("SELECT cost_usd FROM eval_records").fetchone()
        assert row[0] is None
        conn.close()


# ─── SQL Block Parsing Tests ───────────────────────────────────────────────────


class TestSqlBlockParsing:
    def test_finds_single_block(self):
        md = textwrap.dedent("""\
            # Title

            ```sql-eval
            SELECT 1
            ```
        """)
        matches = _SQL_BLOCK_RE.findall(md)
        assert len(matches) == 1
        assert "SELECT 1" in matches[0]

    def test_finds_multiple_blocks(self):
        md = textwrap.dedent("""\
            ```sql-eval
            SELECT 1
            ```

            Some text.

            ```sql-eval
            SELECT 2
            ```
        """)
        matches = _SQL_BLOCK_RE.findall(md)
        assert len(matches) == 2

    def test_does_not_match_plain_sql_fence(self):
        md = "```sql\nSELECT 1\n```"
        matches = _SQL_BLOCK_RE.findall(md)
        assert len(matches) == 0

    def test_does_not_match_python_fence(self):
        md = "```python\nprint('hello')\n```"
        matches = _SQL_BLOCK_RE.findall(md)
        assert len(matches) == 0

    def test_no_blocks_returns_empty(self):
        md = "# Just a heading\n\nSome text."
        matches = _SQL_BLOCK_RE.findall(md)
        assert len(matches) == 0


# ─── Markdown Table Rendering Tests ───────────────────────────────────────────


class TestRowsToMdTable:
    def _run_query(self, sql: str) -> sqlite3.Cursor:
        conn = sqlite3.connect(":memory:")
        conn.row_factory = sqlite3.Row
        cursor = conn.execute(sql)
        return cursor

    def test_single_row(self):
        cursor = self._run_query("SELECT 42 AS answer")
        table = _rows_to_md_table(cursor)
        assert "| answer |" in table
        assert "| 42 |" in table
        assert "| --- |" in table

    def test_multiple_columns(self):
        cursor = self._run_query("SELECT 1 AS a, 'hello' AS b, 3.14 AS c")
        table = _rows_to_md_table(cursor)
        assert "| a | b | c |" in table
        assert "| 1 | hello | 3.14 |" in table

    def test_empty_result_returns_no_results(self):
        conn = sqlite3.connect(":memory:")
        conn.row_factory = sqlite3.Row
        conn.execute("CREATE TABLE t (x INTEGER)")
        cursor = conn.execute("SELECT * FROM t")
        table = _rows_to_md_table(cursor)
        assert "No results" in table
        assert "|" not in table

    def test_null_value_rendered_as_empty_string(self):
        cursor = self._run_query("SELECT NULL AS val")
        table = _rows_to_md_table(cursor)
        assert "|  |" in table  # empty cell

    def test_separator_row_present(self):
        cursor = self._run_query("SELECT 1 AS x, 2 AS y")
        table = _rows_to_md_table(cursor)
        lines = table.splitlines()
        # line 0: header, line 1: separator
        assert lines[1] == "| --- | --- |"


# ─── execute_sql_blocks Tests ─────────────────────────────────────────────────


class TestExecuteSqlBlocks:
    def _conn_with_data(self) -> sqlite3.Connection:
        records = [_make_record(skill=f"skill-{i}.md", score=0.5 + i * 0.1, idx=i) for i in range(3)]
        return export_to_sqlite(records)

    def test_replaces_block_with_table(self):
        conn = self._conn_with_data()
        md = "# Title\n\n```sql-eval\nSELECT COUNT(*) AS total FROM eval_records\n```\n"
        result = execute_sql_blocks(md, conn)
        assert "```sql-eval" not in result
        assert "| total |" in result
        assert "| 3 |" in result
        conn.close()

    def test_multiple_blocks_replaced(self):
        conn = self._conn_with_data()
        md = textwrap.dedent("""\
            ```sql-eval
            SELECT COUNT(*) AS total FROM eval_records
            ```

            ```sql-eval
            SELECT MAX(overall_score) AS best FROM eval_records
            ```
        """)
        result = execute_sql_blocks(md, conn)
        assert "```sql-eval" not in result
        assert "| total |" in result
        assert "| best |" in result
        conn.close()

    def test_invalid_sql_shows_error(self):
        conn = self._conn_with_data()
        md = "```sql-eval\nSELECT * FROM nonexistent_table\n```"
        result = execute_sql_blocks(md, conn)
        assert "SQL error" in result
        conn.close()

    def test_empty_result_shows_no_results(self):
        conn = self._conn_with_data()
        md = "```sql-eval\nSELECT * FROM eval_records WHERE 1=0\n```"
        result = execute_sql_blocks(md, conn)
        assert "No results" in result
        conn.close()

    def test_no_blocks_returns_unchanged(self):
        conn = self._conn_with_data()
        md = "# Just text\n\nNo SQL here."
        result = execute_sql_blocks(md, conn)
        assert result == md
        conn.close()


# ─── Integration: render_dashboard ────────────────────────────────────────────


class TestRenderDashboard:
    def _write_store(self, path: Path, records: list[EvalRecord]) -> None:
        from dataclasses import asdict
        with open(path, "w") as f:
            for r in records:
                f.write(json.dumps(asdict(r)) + "\n")

    def test_end_to_end_renders_table(self, tmp_path):
        store_path = tmp_path / "analytics.jsonl"
        records = [_make_record(skill=f"s-{i}.md", score=0.6 + i * 0.1, idx=i) for i in range(3)]
        self._write_store(store_path, records)

        dashboard_path = tmp_path / "dashboard.md"
        dashboard_path.write_text(
            "# Dashboard\n\n```sql-eval\nSELECT COUNT(*) AS cnt FROM eval_records\n```\n"
        )

        result = render_dashboard(dashboard_path, store_path)
        assert "| cnt |" in result
        assert "| 3 |" in result

    def test_db_path_creates_file(self, tmp_path):
        store_path = tmp_path / "analytics.jsonl"
        records = [_make_record(idx=0)]
        self._write_store(store_path, records)

        dashboard_path = tmp_path / "d.md"
        dashboard_path.write_text("```sql-eval\nSELECT 1 AS x\n```")
        db_file = tmp_path / "test.db"

        render_dashboard(dashboard_path, store_path, db_path=db_file)
        assert db_file.exists()

    def test_empty_store_produces_no_results(self, tmp_path):
        store_path = tmp_path / "analytics.jsonl"
        store_path.write_text("")

        dashboard_path = tmp_path / "d.md"
        dashboard_path.write_text("```sql-eval\nSELECT * FROM eval_records\n```")

        result = render_dashboard(dashboard_path, store_path)
        assert "No results" in result


# ─── CLI Integration Tests ─────────────────────────────────────────────────────


class TestDashboardCLI:
    runner = CliRunner()

    def _write_store(self, path: Path, records: list[EvalRecord]) -> None:
        from dataclasses import asdict
        with open(path, "w") as f:
            for r in records:
                f.write(json.dumps(asdict(r)) + "\n")

    def test_missing_dashboard_file_exits_1(self, tmp_path):
        store = tmp_path / "store.jsonl"
        store.write_text("")
        result = self.runner.invoke(
            app,
            ["dashboard", str(tmp_path / "nope.md"), "--store", str(store)],
        )
        assert result.exit_code == 1

    def test_missing_store_exits_1(self, tmp_path):
        md = tmp_path / "d.md"
        md.write_text("# hi")
        result = self.runner.invoke(
            app,
            ["dashboard", str(md), "--store", str(tmp_path / "missing.jsonl")],
        )
        assert result.exit_code == 1

    def test_renders_to_stdout(self, tmp_path):
        store_path = tmp_path / "analytics.jsonl"
        records = [_make_record(idx=0)]
        self._write_store(store_path, records)

        md_path = tmp_path / "d.md"
        md_path.write_text("```sql-eval\nSELECT COUNT(*) AS cnt FROM eval_records\n```")

        result = self.runner.invoke(
            app,
            ["dashboard", str(md_path), "--store", str(store_path)],
        )
        assert result.exit_code == 0
        assert "| cnt |" in result.output
        assert "| 1 |" in result.output

    def test_renders_to_output_file(self, tmp_path):
        store_path = tmp_path / "analytics.jsonl"
        records = [_make_record(idx=0)]
        self._write_store(store_path, records)

        md_path = tmp_path / "d.md"
        md_path.write_text("```sql-eval\nSELECT COUNT(*) AS total FROM eval_records\n```")

        out_path = tmp_path / "result.md"
        result = self.runner.invoke(
            app,
            ["dashboard", str(md_path), "--store", str(store_path), "--output", str(out_path)],
        )
        assert result.exit_code == 0
        assert out_path.exists()
        content = out_path.read_text()
        assert "| total |" in content

    def test_db_path_option_persists_db(self, tmp_path):
        store_path = tmp_path / "analytics.jsonl"
        records = [_make_record(idx=0)]
        self._write_store(store_path, records)

        md_path = tmp_path / "d.md"
        md_path.write_text("```sql-eval\nSELECT 1 AS x\n```")
        db_path = tmp_path / "out.db"

        result = self.runner.invoke(
            app,
            [
                "dashboard",
                str(md_path),
                "--store",
                str(store_path),
                "--db-path",
                str(db_path),
            ],
        )
        assert result.exit_code == 0
        assert db_path.exists()
