"""SQL-in-Markdown dashboard for md-evals analytics.

Reads a Markdown file with ```sql-eval fenced blocks, executes each query
against an in-memory (or on-disk) SQLite database populated from the JSONL
analytics store, and replaces each block with a Markdown table of results.

Usage (via CLI):
    md-evals dashboard path/to/dashboard.md --store .md-evals/analytics.jsonl
"""

from __future__ import annotations

import re
import sqlite3
from pathlib import Path
from typing import Any

from md_evals.analytics import AnalyticsStore, EvalRecord

# Regex to find ```sql-eval blocks: captures the SQL inside
_SQL_BLOCK_RE = re.compile(
    r"```sql-eval\s*\n(.*?)```",
    re.DOTALL,
)


# ─── SQLite Export ─────────────────────────────────────────────────────────────


def _collect_dimension_keys(records: list[EvalRecord]) -> list[str]:
    """Return the sorted union of all dimension keys across all records."""
    keys: set[str] = set()
    for r in records:
        keys.update(r.dimensions.keys())
    return sorted(keys)


def export_to_sqlite(
    records: list[EvalRecord],
    db_path: str | Path | None = None,
) -> sqlite3.Connection:
    """Export EvalRecord list to a SQLite database.

    The ``dimensions`` dict is flattened into ``dimension_<key>`` REAL columns.
    Unknown dimensions for a given record are stored as NULL.

    Args:
        records: List of EvalRecord objects to export.
        db_path: Optional path for the DB file.  When ``None`` an in-memory DB
                 is used (``":memory:"``).

    Returns:
        An open ``sqlite3.Connection`` ready for querying.
    """
    target = str(db_path) if db_path else ":memory:"
    conn = sqlite3.connect(target)
    conn.row_factory = sqlite3.Row

    dim_keys = _collect_dimension_keys(records)

    dim_col_defs = "".join(f",\n    dimension_{k} REAL" for k in dim_keys)

    conn.execute(f"""
        CREATE TABLE IF NOT EXISTS eval_records (
            id TEXT,
            skill_path TEXT,
            timestamp TEXT,
            overall_grade TEXT,
            overall_score REAL,
            model TEXT,
            provider TEXT,
            cost_usd REAL,
            tokens_input INTEGER,
            tokens_output INTEGER,
            duration_ms INTEGER,
            citations_valid INTEGER,
            citations_total INTEGER,
            suite_name TEXT{dim_col_defs}
        )
    """)

    for r in records:
        base = (
            r.id,
            r.skill_path,
            r.timestamp,
            r.overall_grade,
            r.overall_score,
            r.model,
            r.provider,
            r.cost_usd,
            r.tokens_input,
            r.tokens_output,
            r.duration_ms,
            r.citations_valid,
            r.citations_total,
            r.suite_name,
        )
        dim_values = tuple(r.dimensions.get(k) for k in dim_keys)
        placeholders = ",".join(["?"] * (len(base) + len(dim_values)))
        conn.execute(
            f"INSERT INTO eval_records VALUES ({placeholders})",
            base + dim_values,
        )

    conn.commit()
    return conn


# ─── Markdown Rendering ────────────────────────────────────────────────────────


def _rows_to_md_table(cursor: sqlite3.Cursor) -> str:
    """Convert a cursor result set to a Markdown table string.

    Returns a "No results." line when the result set is empty.
    """
    rows = cursor.fetchall()
    if not rows:
        return "_No results._"

    col_names = [description[0] for description in cursor.description]

    def cell(v: Any) -> str:
        if v is None:
            return ""
        return str(v)

    header = "| " + " | ".join(col_names) + " |"
    separator = "| " + " | ".join("---" for _ in col_names) + " |"
    data_rows = ["| " + " | ".join(cell(c) for c in row) + " |" for row in rows]

    return "\n".join([header, separator, *data_rows])


# ─── SQL Block Execution ───────────────────────────────────────────────────────


def execute_sql_blocks(markdown: str, conn: sqlite3.Connection) -> str:
    """Replace every ```sql-eval block with a Markdown table of query results.

    Args:
        markdown: Raw Markdown text potentially containing sql-eval blocks.
        conn: Open SQLite connection to execute queries against.

    Returns:
        Markdown text with each sql-eval block replaced by a result table.
    """

    def _replace(match: re.Match) -> str:  # type: ignore[type-arg]
        sql = match.group(1).strip()
        try:
            cursor = conn.execute(sql)
            table = _rows_to_md_table(cursor)
        except sqlite3.Error as exc:
            table = f"_SQL error: {exc}_"
        return table

    return _SQL_BLOCK_RE.sub(_replace, markdown)


# ─── Public API ───────────────────────────────────────────────────────────────


def render_dashboard(
    dashboard_md: str | Path,
    store_path: str | Path,
    db_path: str | Path | None = None,
) -> str:
    """Load store, build SQLite DB, render dashboard.

    Args:
        dashboard_md: Path to the Markdown dashboard file, or raw Markdown text.
        store_path: Path to the JSONL analytics store.
        db_path: Optional path to persist the SQLite DB.  ``None`` = in-memory.

    Returns:
        Rendered Markdown with sql-eval blocks replaced by result tables.
    """
    # Resolve markdown source
    path = Path(dashboard_md)
    if path.exists():
        source = path.read_text(encoding="utf-8")
    else:
        # Treat as raw text (useful for testing)
        source = str(dashboard_md)

    # Load analytics records
    store = AnalyticsStore(store_path)
    records = store.load_all()

    # Build SQLite DB
    conn = export_to_sqlite(records, db_path=db_path)

    try:
        return execute_sql_blocks(source, conn)
    finally:
        conn.close()
