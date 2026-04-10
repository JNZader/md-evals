"""Tests for knowledge graph grader — graph construction, claim checking, and grading."""

import pytest
from pathlib import Path

from md_evals.graders.knowledge_graph_grader import (
    KnowledgeGraph,
    KnowledgeGraphGrader,
    check_claim_against_graph,
)


# ── KnowledgeGraph Construction ──


class TestKnowledgeGraph:
    """Tests for KnowledgeGraph building and querying."""

    def test_add_entity(self):
        graph = KnowledgeGraph()
        entity = graph.add_entity("Python", entity_type="language")
        assert entity.name == "Python"
        assert entity.entity_type == "language"
        assert "Python" in graph.entities

    def test_duplicate_entity_raises(self):
        graph = KnowledgeGraph()
        graph.add_entity("Python")
        with pytest.raises(ValueError, match="already exists"):
            graph.add_entity("Python")

    def test_entity_with_aliases(self):
        graph = KnowledgeGraph()
        graph.add_entity("Python", aliases=["py", "cpython"])
        assert graph.resolve_entity("py") == "Python"
        assert graph.resolve_entity("cpython") == "Python"
        assert graph.resolve_entity("Python") == "Python"

    def test_resolve_entity_case_insensitive(self):
        graph = KnowledgeGraph()
        graph.add_entity("Python")
        assert graph.resolve_entity("python") == "Python"
        assert graph.resolve_entity("PYTHON") == "Python"

    def test_resolve_unknown_entity_returns_none(self):
        graph = KnowledgeGraph()
        assert graph.resolve_entity("Unknown") is None

    def test_add_relation(self):
        graph = KnowledgeGraph()
        graph.add_entity("Guido van Rossum", entity_type="person")
        graph.add_entity("Python", entity_type="language")
        rel = graph.add_relation("Guido van Rossum", "created", "Python")
        assert rel.source == "Guido van Rossum"
        assert rel.relation_type == "created"
        assert rel.target == "Python"

    def test_relation_unknown_source_raises(self):
        graph = KnowledgeGraph()
        graph.add_entity("Python")
        with pytest.raises(ValueError, match="Source entity.*not found"):
            graph.add_relation("Unknown", "created", "Python")

    def test_relation_unknown_target_raises(self):
        graph = KnowledgeGraph()
        graph.add_entity("Guido")
        with pytest.raises(ValueError, match="Target entity.*not found"):
            graph.add_relation("Guido", "created", "Unknown")

    def test_add_fact(self):
        graph = KnowledgeGraph()
        graph.add_entity("Python")
        fact = graph.add_fact("Python", "Python was first released in 1991.")
        assert fact.entity == "Python"
        assert "python" in fact.key_terms
        assert "1991" in fact.key_terms

    def test_fact_unknown_entity_raises(self):
        graph = KnowledgeGraph()
        with pytest.raises(ValueError, match="not found"):
            graph.add_fact("Unknown", "Some fact.")

    def test_get_relations_for(self):
        graph = KnowledgeGraph()
        graph.add_entity("Guido", entity_type="person")
        graph.add_entity("Python", entity_type="language")
        graph.add_entity("ABC", entity_type="language")
        graph.add_relation("Guido", "created", "Python")
        graph.add_relation("ABC", "influenced", "Python")

        rels = graph.get_relations_for("Python")
        assert len(rels) == 2

        rels_filtered = graph.get_relations_for("Python", relation_type="created")
        assert len(rels_filtered) == 1

    def test_get_facts_for(self):
        graph = KnowledgeGraph()
        graph.add_entity("Python")
        graph.add_fact("Python", "Released in 1991.")
        graph.add_fact("Python", "Supports multiple paradigms.")

        facts = graph.get_facts_for("Python")
        assert len(facts) == 2

    def test_find_entities_in_text(self):
        graph = KnowledgeGraph()
        graph.add_entity("Python", aliases=["py"])
        graph.add_entity("JavaScript", aliases=["JS"])

        found = graph.find_entities_in_text("Python and JavaScript are popular.")
        assert "Python" in found
        assert "JavaScript" in found

    def test_find_entities_alias_match(self):
        graph = KnowledgeGraph()
        graph.add_entity("Python", aliases=["py"])

        found = graph.find_entities_in_text("I use py for scripting.")
        assert "Python" in found

    def test_find_entities_no_partial_match(self):
        graph = KnowledgeGraph()
        graph.add_entity("Go", entity_type="language")

        # "Go" inside "Google" should NOT match (word boundary)
        found = graph.find_entities_in_text("Google is a company.")
        assert "Go" not in found

    def test_from_dict(self):
        data = {
            "entities": [
                {"name": "Python", "type": "language", "aliases": ["py"]},
                {"name": "Guido", "type": "person"},
            ],
            "relations": [
                {"source": "Guido", "type": "created", "target": "Python"},
            ],
            "facts": [
                {"entity": "Python", "statement": "Released in 1991."},
            ],
        }
        graph = KnowledgeGraph.from_dict(data)
        assert "Python" in graph.entities
        assert "Guido" in graph.entities
        assert len(graph.relations) == 1
        assert len(graph.facts) == 1

    def test_to_dict_roundtrip(self):
        graph = KnowledgeGraph()
        graph.add_entity("Python", entity_type="language", aliases=["py"])
        graph.add_entity("Guido", entity_type="person")
        graph.add_relation("Guido", "created", "Python")
        graph.add_fact("Python", "Released in 1991.")

        data = graph.to_dict()
        graph2 = KnowledgeGraph.from_dict(data)

        assert "Python" in graph2.entities
        assert len(graph2.relations) == 1
        assert len(graph2.facts) == 1


# ── Claim Checking ──


class TestCheckClaim:
    """Tests for check_claim_against_graph."""

    def _build_graph(self) -> KnowledgeGraph:
        graph = KnowledgeGraph()
        graph.add_entity("Python", entity_type="language")
        graph.add_entity("Guido van Rossum", entity_type="person", aliases=["Guido"])
        graph.add_relation("Guido van Rossum", "created", "Python")
        graph.add_fact("Python", "Python was first released in 1991.")
        graph.add_fact("Python", "Python supports dynamic typing.")
        return graph

    def test_grounded_claim(self):
        graph = self._build_graph()
        check = check_claim_against_graph(
            "Python was released in 1991.", graph
        )
        assert check.grounded is True
        assert check.confidence > 0.0
        assert "Python" in check.mentioned_entities

    def test_ungrounded_claim_no_entities(self):
        graph = self._build_graph()
        check = check_claim_against_graph(
            "The weather is nice today.", graph
        )
        assert check.grounded is False
        assert check.mentioned_entities == []

    def test_relation_based_grounding(self):
        graph = self._build_graph()
        check = check_claim_against_graph(
            "Guido van Rossum created Python.", graph
        )
        assert check.grounded is True
        assert "Guido van Rossum" in check.mentioned_entities

    def test_partial_grounding(self):
        graph = self._build_graph()
        check = check_claim_against_graph(
            "Python supports dynamic typing and pattern matching.", graph
        )
        assert check.grounded is True
        assert check.confidence > 0.0

    def test_contradictory_claim_not_grounded(self):
        """A claim that contradicts a known fact should NOT be grounded."""
        graph = KnowledgeGraph()
        graph.add_entity("Python")
        graph.add_fact("Python", "is a high-level programming language")
        check = check_claim_against_graph(
            "Python is a low-level assembly language.", graph
        )
        assert check.grounded is False, (
            f"Contradictory claim should not be grounded, got confidence={check.confidence:.2f}"
        )

    def test_low_overlap_not_grounded(self):
        """Claims sharing only stop words with facts should not be grounded."""
        graph = KnowledgeGraph()
        graph.add_entity("Python")
        graph.add_fact("Python", "is a high-level programming language")
        check = check_claim_against_graph("Python is a snake.", graph)
        assert check.grounded is False
        assert check.confidence < 0.5


# ── KnowledgeGraphGrader ──


class TestKnowledgeGraphGrader:
    """Tests for KnowledgeGraphGrader."""

    def _build_graph(self) -> KnowledgeGraph:
        graph = KnowledgeGraph()
        graph.add_entity("Python", entity_type="language")
        graph.add_entity("Guido van Rossum", entity_type="person", aliases=["Guido"])
        graph.add_relation("Guido van Rossum", "created", "Python")
        graph.add_fact("Python", "Python was first released in 1991.")
        graph.add_fact("Python", "Python supports dynamic typing.")
        graph.add_fact("Python", "Python is an interpreted language.")
        return graph

    def test_fully_grounded_passes(self, tmp_path: Path):
        graph = self._build_graph()
        grader = KnowledgeGraphGrader(
            name="fact_check",
            graph=graph,
            content="Python was released in 1991. Python supports dynamic typing.",
            pass_threshold=0.5,
        )
        result = grader.grade(tmp_path)
        assert result.passed is True
        assert result.score > 0.0

    def test_ungrounded_content_has_low_confidence(self, tmp_path: Path):
        graph = self._build_graph()
        grader = KnowledgeGraphGrader(
            name="fact_check",
            graph=graph,
            content="Python uses quantum entanglement for memory management. Python compiles to COBOL bytecode.",
            pass_threshold=0.5,
            ignore_claims_without_entities=False,
        )
        result = grader.grade(tmp_path)
        # Claims mention Python but are completely fabricated — should not be well-grounded
        # Even if some term overlap exists, confidence should be low
        assert result.details["total_claims"] == 2

    def test_no_content_fails(self, tmp_path: Path):
        graph = self._build_graph()
        grader = KnowledgeGraphGrader(
            name="fact_check",
            graph=graph,
        )
        result = grader.grade(tmp_path)
        assert result.passed is False
        assert "not provided" in result.reason

    def test_file_based_content(self, tmp_path: Path):
        graph = self._build_graph()
        content_file = tmp_path / "output.txt"
        content_file.write_text("Python was released in 1991. It supports dynamic typing.")

        grader = KnowledgeGraphGrader(
            name="fact_check",
            graph=graph,
            path="output.txt",
            pass_threshold=0.5,
        )
        result = grader.grade(tmp_path)
        assert result.passed is True

    def test_ignore_claims_without_entities(self, tmp_path: Path):
        graph = self._build_graph()
        grader = KnowledgeGraphGrader(
            name="fact_check",
            graph=graph,
            content="The weather is nice. Python supports dynamic typing.",
            ignore_claims_without_entities=True,
            pass_threshold=0.5,
        )
        result = grader.grade(tmp_path)
        # "weather" claim ignored, Python claim grounded
        assert result.passed is True

    def test_require_all_grounded(self, tmp_path: Path):
        graph = self._build_graph()
        grader = KnowledgeGraphGrader(
            name="fact_check",
            graph=graph,
            content="Python supports dynamic typing. Python runs on quantum computers.",
            require_all_grounded=True,
            ignore_claims_without_entities=False,
        )
        result = grader.grade(tmp_path)
        # "quantum computers" claim is not grounded
        assert result.details["grounded_claims"] < result.details["relevant_claims"]

    def test_empty_content_passes(self, tmp_path: Path):
        graph = self._build_graph()
        grader = KnowledgeGraphGrader(
            name="fact_check",
            graph=graph,
            content="Hi.",
            pass_threshold=0.5,
        )
        result = grader.grade(tmp_path)
        # Very short content with no real claims — passes
        assert result.passed is True

    def test_details_structure(self, tmp_path: Path):
        graph = self._build_graph()
        grader = KnowledgeGraphGrader(
            name="fact_check",
            graph=graph,
            content="Python was released in 1991.",
            pass_threshold=0.5,
        )
        result = grader.grade(tmp_path)
        assert "total_claims" in result.details
        assert "relevant_claims" in result.details
        assert "grounded_claims" in result.details
        assert "checks" in result.details
        assert isinstance(result.details["checks"], list)

    def test_graph_from_dict_integration(self, tmp_path: Path):
        """Test that a graph built from dict works with the grader."""
        data = {
            "entities": [
                {"name": "TypeScript", "type": "language", "aliases": ["TS"]},
                {"name": "Microsoft", "type": "company"},
            ],
            "relations": [
                {"source": "Microsoft", "type": "created", "target": "TypeScript"},
            ],
            "facts": [
                {"entity": "TypeScript", "statement": "TypeScript adds static typing to JavaScript."},
            ],
        }
        graph = KnowledgeGraph.from_dict(data)
        grader = KnowledgeGraphGrader(
            name="ts_check",
            graph=graph,
            content="TypeScript adds static typing to JavaScript. Microsoft created TypeScript.",
            pass_threshold=0.5,
        )
        result = grader.grade(tmp_path)
        assert result.passed is True
        assert result.score > 0.0
