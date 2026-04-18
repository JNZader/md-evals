"""
PageIndex for md-evals

Paginated document evaluation for small context models (4K-8K tokens).
Enables evaluating large markdown documents without exceeding context limits.
"""

import sqlite3
import json
import re
from pathlib import Path
from typing import List, Dict, Optional, Any
from dataclasses import dataclass


@dataclass
class DocumentStats:
    """Statistics for a document."""
    pages: int
    tokens: int
    evaluated_pages: int = 0
    average_score: float = 0.0


class DocumentPageIndex:
    """
    Manages paginated document evaluation.
    
    Enables small context models to evaluate large markdown documents
    by dividing them into manageable pages.
    """

    def __init__(self, db_path: str):
        """Initialize with database path."""
        self.db_path = db_path
        self._init_schema()

    def _init_schema(self) -> None:
        """Initialize database schema."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Pages table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS document_pages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    doc_id TEXT NOT NULL,
                    page_num INTEGER NOT NULL,
                    total_pages INTEGER NOT NULL,
                    content TEXT NOT NULL,
                    token_count INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(doc_id, page_num)
                )
            """)

            # Evaluations table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS page_evaluations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    doc_id TEXT NOT NULL,
                    page_num INTEGER NOT NULL,
                    score INTEGER,
                    issues TEXT,  -- JSON array
                    evaluated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(doc_id, page_num)
                )
            """)

            # Indexes
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_doc_pages 
                ON document_pages(doc_id)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_evaluations 
                ON page_evaluations(doc_id, page_num)
            """)

            conn.commit()

    def paginate_document(self, doc_id: str, content: str,
                         max_tokens_per_page: int = 1500) -> Dict[str, int]:
        """Paginate document into chunks."""
        # Check if already paginated
        existing = self._get_existing_pages(doc_id)
        if existing:
            return {'pages': existing['pages'], 'tokens': existing['tokens']}

        # Chunk content
        chunks = self._chunk_content(content, max_tokens_per_page)
        total_pages = len(chunks)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            for i, chunk in enumerate(chunks):
                page_num = i + 1
                token_count = self._estimate_tokens(chunk)

                cursor.execute("""
                    INSERT INTO document_pages 
                    (doc_id, page_num, total_pages, content, token_count)
                    VALUES (?, ?, ?, ?, ?)
                """, (doc_id, page_num, total_pages, chunk, token_count))

            conn.commit()

        total_tokens = sum(self._estimate_tokens(c) for c in chunks)
        return {'pages': total_pages, 'tokens': total_tokens}

    def _chunk_content(self, content: str, max_tokens: int) -> List[str]:
        """Split content into chunks."""
        max_chars = max_tokens * 4

        chunks = []
        pos = 0

        while pos < len(content):
            end = min(pos + max_chars, len(content))

            if end < len(content):
                # Try section boundary
                section_break = content.rfind('\n\n## ', pos, end)
                if section_break > pos + max_chars * 0.5:
                    end = section_break + 1
                else:
                    para_break = content.rfind('\n\n', pos, end)
                    if para_break > pos + max_chars * 0.7:
                        end = para_break + 2

            chunks.append(content[pos:end].strip())
            pos = end + 1 if end < len(content) else end

        return chunks if chunks else [content]

    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count."""
        return max(1, len(text) // 4)

    def get_page(self, doc_id: str, page_num: int) -> Optional[Dict[str, Any]]:
        """Get a specific page."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT page_num, total_pages, content, token_count
                FROM document_pages
                WHERE doc_id = ? AND page_num = ?
            """, (doc_id, page_num))

            row = cursor.fetchone()
            if not row:
                return None

            return {
                'page_num': row[0],
                'total_pages': row[1],
                'content': row[2],
                'token_count': row[3]
            }

    def get_context(self, doc_id: str, page_num: int,
                   window_size: int = 1) -> Dict[str, Any]:
        """Get page with surrounding context."""
        start_page = max(1, page_num - window_size)
        end_page = page_num + window_size

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT page_num, total_pages, content, token_count
                FROM document_pages
                WHERE doc_id = ? AND page_num BETWEEN ? AND ?
                ORDER BY page_num
            """, (doc_id, start_page, end_page))

            pages = []
            for row in cursor.fetchall():
                pages.append({
                    'page_num': row[0],
                    'total_pages': row[1],
                    'content': row[2],
                    'token_count': row[3]
                })

        current = next((p for p in pages if p['page_num'] == page_num), None)
        if not current:
            raise ValueError(f"Page {page_num} not found")

        previous = [p for p in pages if p['page_num'] < page_num]
        next_pages = [p for p in pages if p['page_num'] > page_num]

        return {
            'current_page': current,
            'previous_pages': previous,
            'next_pages': next_pages,
            'total_in_context': len(pages),
            'total_tokens': sum(p['token_count'] for p in pages)
        }

    def store_evaluation(self, doc_id: str, page_num: int,
                        result: Dict[str, Any]) -> None:
        """Store evaluation result for a page."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO page_evaluations 
                (doc_id, page_num, score, issues)
                VALUES (?, ?, ?, ?)
            """, (
                doc_id, page_num,
                result.get('score', 0),
                json.dumps(result.get('issues', []))
            ))
            conn.commit()

    def aggregate_scores(self, doc_id: str) -> Dict[str, Any]:
        """Aggregate scores from all evaluated pages."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Get all evaluations
            cursor.execute("""
                SELECT score, issues
                FROM page_evaluations
                WHERE doc_id = ?
            """, (doc_id,))

            scores = []
            total_issues = 0

            for row in cursor.fetchall():
                scores.append(row[0])
                issues = json.loads(row[1] or '[]')
                total_issues += len(issues)

            # Get total pages
            stats = self.get_doc_stats(doc_id)

            if not scores:
                return {
                    'average_score': 0,
                    'min_score': 0,
                    'max_score': 0,
                    'total_issues': 0,
                    'pages_evaluated': 0
                }

            return {
                'average_score': sum(scores) / len(scores),
                'min_score': min(scores),
                'max_score': max(scores),
                'total_issues': total_issues,
                'pages_evaluated': len(scores)
            }

    def find_pages_by_score(self, doc_id: str, max_score: int) -> List[Dict[str, Any]]:
        """Find pages with scores below threshold."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT e.page_num, e.score, e.issues, p.content
                FROM page_evaluations e
                JOIN document_pages p ON e.doc_id = p.doc_id AND e.page_num = p.page_num
                WHERE e.doc_id = ? AND e.score <= ?
            """, (doc_id, max_score))

            pages = []
            for row in cursor.fetchall():
                pages.append({
                    'page_num': row[0],
                    'evaluation': {
                        'score': row[1],
                        'issues': json.loads(row[2] or '[]')
                    },
                    'content': row[3][:200]  # Preview
                })

            return pages

    def check_model_fit(self, doc_id: str, model_tokens: int,
                       safety_margin: float = 0.3) -> Dict[str, Any]:
        """Check if document fits in model context."""
        stats = self.get_doc_stats(doc_id)
        threshold = model_tokens * (1 - safety_margin)

        fits = stats.tokens <= threshold

        return {
            'fits': fits,
            'total_tokens': stats.tokens,
            'model_tokens': model_tokens,
            'pages_needed': stats.pages if not fits else 1,
            'suggested_pages': max(1, stats.tokens // int(threshold)) if not fits else 1
        }

    def needs_more_context(self, doc_id: str, current_page: int) -> bool:
        """Check if more context is needed."""
        stats = self.get_doc_stats(doc_id)
        return current_page < stats.pages

    def get_doc_stats(self, doc_id: str) -> DocumentStats:
        """Get document statistics."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Get page count and tokens
            cursor.execute("""
                SELECT COUNT(*), COALESCE(SUM(token_count), 0)
                FROM document_pages
                WHERE doc_id = ?
            """, (doc_id,))

            row = cursor.fetchone()
            pages = row[0]
            tokens = row[1]

            # Get evaluation count
            cursor.execute("""
                SELECT COUNT(*)
                FROM page_evaluations
                WHERE doc_id = ?
            """, (doc_id,))

            evaluated = cursor.fetchone()[0]

            return DocumentStats(
                pages=pages,
                tokens=tokens,
                evaluated_pages=evaluated
            )

    def get_evaluation_summary(self, doc_id: str) -> Dict[str, Any]:
        """Get evaluation summary for reporting."""
        aggregated = self.aggregate_scores(doc_id)
        stats = self.get_doc_stats(doc_id)

        avg_score = aggregated['average_score']

        if avg_score >= 90:
            recommendation = "excellent"
        elif avg_score >= 80:
            recommendation = "good"
        elif avg_score >= 70:
            recommendation = "acceptable"
        else:
            recommendation = "needs_improvement"

        return {
            'overall_score': avg_score,
            'pages_evaluated': aggregated['pages_evaluated'],
            'total_pages': stats.pages,
            'total_issues': aggregated['total_issues'],
            'recommendation': recommendation
        }

    def delete_document(self, doc_id: str) -> None:
        """Delete all pages and evaluations for a document."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM document_pages WHERE doc_id = ?", (doc_id,))
            cursor.execute("DELETE FROM page_evaluations WHERE doc_id = ?", (doc_id,))
            conn.commit()

    def _get_existing_pages(self, doc_id: str) -> Optional[DocumentStats]:
        """Check if document already has pages."""
        stats = self.get_doc_stats(doc_id)
        if stats.pages > 0:
            return {'pages': stats.pages, 'tokens': stats.tokens}
        return None


# Convenience function
def create_page_index(db_path: str) -> DocumentPageIndex:
    """Create a DocumentPageIndex instance."""
    return DocumentPageIndex(db_path)
