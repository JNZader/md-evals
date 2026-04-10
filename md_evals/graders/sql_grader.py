"""SQL execution grader.

Extracts SQL blocks from markdown, executes them against a SQLite
database, and validates results against configurable expectations.
"""

from __future__ import annotations

import re
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from md_evals.graders._path_utils import validate_workspace_path
from md_evals.models import EvaluatorResult

# Regex to match ```sql ... ``` fenced code blocks
_SQL_BLOCK_RE = re.compile(r"```sql\s*\n(.*?)```", re.DOTALL | re.IGNORECASE)


@dataclass
class SQLGrader:
    """Assert that SQL blocks in markdown execute successfully against a SQLite DB.

    Reads a markdown file from the workspace, extracts fenced ``sql`` code
    blocks, connects to a SQLite database, executes each query, and
    validates results against optional expectations (row count, column
    names, non-empty).

    Score is proportional: ``passed_queries / total_queries``.
    Passes if score meets ``pass_threshold``.

    Attributes:
        name: Grader identifier for reports.
        markdown_file: Workspace-relative path to the markdown file.
        db_path: Workspace-relative path to the SQLite database.
        expect_rows: Expected number of result rows (None = skip check).
        expect_columns: Expected column names (None = skip check).
        expect_non_empty: If True, each query must return at least one row.
        pass_threshold: Minimum score to pass (0.0-1.0).
    """

    name: str = "sql"
    markdown_file: str = "output.md"
    db_path: str = "test.db"
    expect_rows: int | None = None
    expect_columns: list[str] | None = None
    expect_non_empty: bool = True
    pass_threshold: float = 1.0

    def grade(self, workspace: Path) -> EvaluatorResult:
        """Grade SQL blocks in the markdown file.

        Args:
            workspace: Root directory of the execution workspace.

        Returns:
            EvaluatorResult with proportional score and query details.
        """
        md_path = validate_workspace_path(workspace, self.markdown_file)
        if not md_path.exists():
            return EvaluatorResult(
                evaluator_name=self.name,
                passed=False,
                score=0.0,
                reason=f"Markdown file '{self.markdown_file}' not found",
                details={"queries": [], "total": 0},
            )

        text = md_path.read_text(encoding="utf-8", errors="replace")
        sql_blocks = self._extract_sql_blocks(text)

        if not sql_blocks:
            # No SQL blocks = vacuous pass
            return EvaluatorResult(
                evaluator_name=self.name,
                passed=True,
                score=1.0,
                reason=None,
                details={"queries": [], "total": 0},
            )

        conn = self._connect_db(self.db_path, workspace)
        if conn is None:
            return EvaluatorResult(
                evaluator_name=self.name,
                passed=False,
                score=0.0,
                reason=f"Database '{self.db_path}' not found",
                details={"queries": [], "total": len(sql_blocks)},
            )

        query_results: list[dict[str, Any]] = []
        passed_count = 0

        try:
            for sql in sql_blocks:
                rows, columns, error = self._execute_query(conn, sql)
                if error is not None:
                    query_results.append(
                        {"sql": sql, "passed": False, "error": error}
                    )
                    continue

                valid, validation_reason = self._validate_result(
                    rows, columns
                )
                query_results.append(
                    {
                        "sql": sql,
                        "passed": valid,
                        "rows": len(rows),
                        "columns": columns,
                        "error": validation_reason,
                    }
                )
                if valid:
                    passed_count += 1
        finally:
            conn.close()

        total = len(sql_blocks)
        score = passed_count / total
        passed = score >= self.pass_threshold

        reason = None
        if not passed:
            failed = [q for q in query_results if not q["passed"]]
            reason = (
                f"{len(failed)}/{total} queries failed"
                + (f": {failed[0].get('error', '')}" if failed else "")
            )

        return EvaluatorResult(
            evaluator_name=self.name,
            passed=passed,
            score=score,
            reason=reason,
            details={
                "queries": query_results,
                "total": total,
                "passed_count": passed_count,
            },
        )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_sql_blocks(text: str) -> list[str]:
        """Extract SQL code from fenced ```sql blocks.

        Only matches blocks explicitly tagged as ``sql``.
        Other language blocks (```python, ```js, etc.) are ignored.
        """
        return [match.strip() for match in _SQL_BLOCK_RE.findall(text) if match.strip()]

    @staticmethod
    def _connect_db(db_path: str, workspace: Path) -> sqlite3.Connection | None:
        """Connect to a SQLite database in the workspace.

        Returns None if the database file does not exist.
        """
        full_path = validate_workspace_path(workspace, db_path)
        if not full_path.exists():
            return None
        return sqlite3.connect(str(full_path))

    @staticmethod
    def _execute_query(
        conn: sqlite3.Connection, sql: str
    ) -> tuple[list[tuple[Any, ...]], list[str], str | None]:
        """Execute a SQL query and return (rows, column_names, error).

        On success, error is None.
        On failure, rows and columns are empty and error contains the message.
        """
        try:
            cursor = conn.execute(sql)
            if cursor.description is None:
                # Non-SELECT statement (INSERT, CREATE, etc.)
                return [], [], None
            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
            return rows, columns, None
        except sqlite3.Error as exc:
            return [], [], str(exc)

    def _validate_result(
        self,
        rows: list[tuple[Any, ...]],
        columns: list[str],
    ) -> tuple[bool, str | None]:
        """Validate query results against grader expectations.

        Returns (is_valid, reason_if_invalid).
        """
        if self.expect_non_empty and len(rows) == 0 and columns:
            # Only enforce non-empty for SELECT-like queries (has columns)
            return False, "Expected non-empty result, got 0 rows"

        if self.expect_rows is not None and len(rows) != self.expect_rows:
            return False, f"Expected {self.expect_rows} rows, got {len(rows)}"

        if self.expect_columns is not None:
            if columns != self.expect_columns:
                return False, (
                    f"Expected columns {self.expect_columns}, got {columns}"
                )

        return True, None
