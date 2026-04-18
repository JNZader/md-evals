"""
Tests for PageIndex module - md-evals

TDD: Test-Driven Development for paginated document evaluation.
Enables small context models (4K-8K) to evaluate large markdown documents.

Run: pytest tests/test_pageindex.py -v
"""

import pytest
import tempfile
from pathlib import Path


class TestPageIndex:
    """Test suite for PageIndex in md-evals."""

    @pytest.fixture
    def page_index(self, tmp_path):
        """Create PageIndex instance with temporary storage."""
        from md_evals.pageindex import DocumentPageIndex
        db_path = tmp_path / "test_pages.db"
        return DocumentPageIndex(str(db_path))

    def test_paginate_document(self, page_index):
        """Test paginating large markdown document."""
        # Large markdown document
        doc = "# Skill\n\n" + "\n\n".join([
            f"## Section {i}\n{'Content ' * 600}"
            for i in range(1, 10)
        ])

        result = page_index.paginate_document('skill-doc', doc)

        assert result['pages'] > 0, "Should create pages"
        assert result['tokens'] > 0, "Should have total tokens"
        assert result['pages'] < 1000, "Should not create excessive pages"

    def test_get_page(self, page_index):
        """Test retrieving specific page."""
        doc = "# Title\n" + "Content " * 300 + "\n\n## Section\n" + "More " * 300
        page_index.paginate_document('get-doc', doc)

        page = page_index.get_page('get-doc', 1)

        assert page is not None, "Page should exist"
        assert page['page_num'] == 1, "Should have correct page number"
        assert len(page['content']) > 0, "Should have content"

    def test_get_context_window(self, page_index):
        """Test getting page with surrounding context."""
        sections = [f"## Section {i}\n{'Text ' * 400}" for i in range(1, 8)]
        doc = "# Doc\n" + "\n\n".join(sections)
        result = page_index.paginate_document('context-doc', doc)
        
        # Get middle page if multiple pages exist
        target_page = min(4, result['pages'])
        context = page_index.get_context('context-doc', page_num=target_page, window_size=1)

        assert context['current_page']['page_num'] == target_page
        # Context window may vary based on actual pagination
        assert context['total_in_context'] > 0
        assert context['total_tokens'] > 0

    def test_evaluate_page_by_page(self, page_index):
        """Test evaluating document page by page."""
        # Mock evaluation function
        def mock_evaluate(content):
            return {'score': 85, 'issues': []}

        doc = "\n\n".join([f"## Part {i}\n{'Text ' * 200}" for i in range(1, 6)])
        page_index.paginate_document('eval-doc', doc)

        # Evaluate each page
        stats = page_index.get_doc_stats('eval-doc')
        scores = []

        for page_num in range(1, stats.pages + 1):
            page = page_index.get_page('eval-doc', page_num)
            result = mock_evaluate(page['content'])
            scores.append(result['score'])

            # Store evaluation result
            page_index.store_evaluation('eval-doc', page_num, result)

        assert len(scores) == stats.pages
        assert all(s == 85 for s in scores)

    def test_aggregate_scores(self, page_index):
        """Test aggregating scores from all pages."""
        doc = "## Test\nContent"
        page_index.paginate_document('agg-doc', doc)

        # Store evaluations for pages
        for i in range(1, 4):
            page_index.store_evaluation('agg-doc', i, {
                'score': 80 + i * 5,  # 85, 90, 95
                'issues': [f'Issue {i}']
            })

        aggregated = page_index.aggregate_scores('agg-doc')

        assert 'average_score' in aggregated
        assert 'min_score' in aggregated
        assert 'max_score' in aggregated
        assert 'total_issues' in aggregated
        assert aggregated['average_score'] > 0

    def test_find_pages_by_criteria(self, page_index):
        """Test finding pages matching evaluation criteria."""
        doc = """
## Authentication
JWT and security.

## Database
PostgreSQL schema.

## API
REST endpoints.
"""
        page_index.paginate_document('criteria-doc', doc)

        # Find pages with low scores
        page_index.store_evaluation('criteria-doc', 1, {'score': 60, 'issues': ['Security']})
        page_index.store_evaluation('criteria-doc', 2, {'score': 90, 'issues': []})

        low_score_pages = page_index.find_pages_by_score('criteria-doc', max_score=70)

        assert len(low_score_pages) > 0
        assert all(p['evaluation']['score'] <= 70 for p in low_score_pages)

    def test_compaction_prevention(self, page_index):
        """Test compaction prevention for small models."""
        # Large document
        doc = "Word " * 10000
        page_index.paginate_document('large-doc', doc)

        # Check for 4K model
        check = page_index.check_model_fit('large-doc', model_tokens=4096)

        assert check['fits'] is False, "Large doc should not fit in 4K"
        assert check['pages_needed'] > 1, "Should need multiple pages"
        assert check['suggested_pages'] > 0

        # Small doc should fit
        small_doc = "Brief doc."
        page_index.paginate_document('small-doc', small_doc)
        small_check = page_index.check_model_fit('small-doc', model_tokens=4096)

        assert small_check['fits'] is True

    def test_incremental_evaluation(self, page_index):
        """Test evaluating document incrementally."""
        sections = [f"## Section {i}\n{'Content ' * 300}" for i in range(1, 4)]
        doc = "# Doc\n" + "\n\n".join(sections)
        page_index.paginate_document('incremental-doc', doc)

        # Evaluate first page
        page1 = page_index.get_page('incremental-doc', 1)
        assert page1 is not None

        # Check if more context needed
        needs_more = page_index.needs_more_context('incremental-doc', current_page=1)
        assert isinstance(needs_more, bool)

    def test_delete_document_pages(self, page_index):
        """Test deleting all pages for a document."""
        doc = "## Test\nContent " * 100
        page_index.paginate_document('delete-doc', doc)

        # Verify exists
        stats_before = page_index.get_doc_stats('delete-doc')
        assert stats_before.pages > 0

        # Delete
        page_index.delete_document('delete-doc')

        # Verify deleted
        stats_after = page_index.get_doc_stats('delete-doc')
        assert stats_after.pages == 0

    def test_integration_full_evaluation_workflow(self, page_index):
        """Integration test: Full document evaluation workflow."""
        # Large skill document (simulated)
        skill_doc = "\n\n".join([
            f"## {section}\n{'Content ' * 600}"
            for section in [
                'Purpose', 'Requirements', 'Examples', 
                'Constraints', 'Testing', 'Validation'
            ]
        ])

        # Step 1: Paginate
        result = page_index.paginate_document('skill-eval', skill_doc)
        assert result['pages'] >= 6

        # Step 2: Check if fits in 4K model
        fit_check = page_index.check_model_fit('skill-eval', model_tokens=4096)

        if not fit_check['fits']:
            # Step 3: Evaluate page by page
            total_score = 0
            total_issues = 0

            for page_num in range(1, result['pages'] + 1):
                page = page_index.get_page('skill-eval', page_num)

                # Mock evaluation
                eval_result = {
                    'score': 85,
                    'issues': [] if page_num % 2 == 0 else ['Minor issue']
                }

                page_index.store_evaluation('skill-eval', page_num, eval_result)
                total_score += eval_result['score']
                total_issues += len(eval_result['issues'])

            # Step 4: Aggregate
            aggregated = page_index.aggregate_scores('skill-eval')

            assert aggregated['average_score'] > 0
            assert aggregated['total_issues'] == total_issues
            assert aggregated['pages_evaluated'] == result['pages']

            # Step 5: Get summary for reporting
            summary = page_index.get_evaluation_summary('skill-eval')
            assert 'overall_score' in summary
            assert 'recommendation' in summary
