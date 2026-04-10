"""Knowledge graph grader — ground evaluations against a fact graph.

Provides a lightweight knowledge graph that evals can reference for
factual accuracy verification. The graph stores entities and typed
relationships, and the grader checks whether an LLM output's claims
are consistent with known facts.

Usage:
    graph = KnowledgeGraph()
    graph.add_entity("Python", entity_type="language", properties={"paradigm": "multi"})
    graph.add_entity("Guido van Rossum", entity_type="person")
    graph.add_relation("Guido van Rossum", "created", "Python")
    graph.add_fact("Python", "Python was first released in 1991.")

    grader = KnowledgeGraphGrader(
        name="factual_accuracy",
        graph=graph,
        content="Python was created by Guido van Rossum and released in 1991.",
    )
    result = grader.grade(workspace)
    # result.score ≈ 1.0 (all claims grounded in the graph)
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from md_evals.graders._path_utils import validate_workspace_path
from md_evals.models import EvaluatorResult


# ── Graph Data Structures ──


@dataclass
class Entity:
    """A node in the knowledge graph.

    Attributes:
        name: Canonical name of the entity.
        entity_type: Category (e.g. "person", "language", "concept").
        aliases: Alternative names that refer to the same entity.
        properties: Key-value metadata about the entity.
    """

    name: str
    entity_type: str = "unknown"
    aliases: list[str] = field(default_factory=list)
    properties: dict[str, Any] = field(default_factory=dict)


@dataclass
class Relation:
    """A directed edge between two entities.

    Attributes:
        source: Name of the source entity.
        relation_type: Type of relationship (e.g. "created", "is_a", "uses").
        target: Name of the target entity.
        properties: Additional metadata about the relation.
    """

    source: str
    relation_type: str
    target: str
    properties: dict[str, Any] = field(default_factory=dict)


@dataclass
class Fact:
    """A factual statement associated with an entity.

    Attributes:
        entity: Name of the entity this fact relates to.
        statement: The factual claim in natural language.
        key_terms: Extracted terms for matching (auto-populated).
    """

    entity: str
    statement: str
    key_terms: frozenset[str] = field(default_factory=frozenset)


# ── Stop words (shared with semantic_diff for consistency) ──

_STOP_WORDS: frozenset[str] = frozenset({
    "a", "an", "the", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "shall", "can", "need", "must", "ought",
    "i", "you", "he", "she", "it", "we", "they", "me", "him", "her",
    "us", "them", "my", "your", "his", "its", "our", "their",
    "this", "that", "these", "those", "and", "but", "or", "nor",
    "not", "so", "if", "then", "than", "when", "where", "while",
    "of", "in", "to", "for", "with", "on", "at", "from", "by",
    "about", "as", "into", "through", "during", "before", "after",
    "also", "very", "just", "more", "most", "other", "some", "such",
    "no", "only", "same", "too", "each", "every", "all", "both",
})


def _extract_terms(text: str) -> frozenset[str]:
    """Extract significant terms from text."""
    words = re.findall(r"[a-zA-Z0-9_]+", text.lower())
    return frozenset(w for w in words if w not in _STOP_WORDS and len(w) > 1)


# ── Knowledge Graph ──


class KnowledgeGraph:
    """In-memory knowledge graph for factual grounding.

    Stores entities, relations, and facts. Provides lookup methods
    that the grader uses to verify claims in LLM outputs.

    The graph can be built programmatically or loaded from a dict
    via :meth:`from_dict`.
    """

    def __init__(self) -> None:
        self._entities: dict[str, Entity] = {}
        self._relations: list[Relation] = []
        self._facts: list[Fact] = []
        self._alias_map: dict[str, str] = {}  # alias → canonical name

    @property
    def entities(self) -> dict[str, Entity]:
        return dict(self._entities)

    @property
    def relations(self) -> list[Relation]:
        return list(self._relations)

    @property
    def facts(self) -> list[Fact]:
        return list(self._facts)

    def add_entity(
        self,
        name: str,
        *,
        entity_type: str = "unknown",
        aliases: list[str] | None = None,
        properties: dict[str, Any] | None = None,
    ) -> Entity:
        """Add an entity to the graph.

        Args:
            name: Canonical entity name.
            entity_type: Category of entity.
            aliases: Alternative names.
            properties: Key-value metadata.

        Returns:
            The created Entity.

        Raises:
            ValueError: If an entity with that name already exists.
        """
        if name in self._entities:
            raise ValueError(f"Entity '{name}' already exists")

        entity = Entity(
            name=name,
            entity_type=entity_type,
            aliases=aliases or [],
            properties=properties or {},
        )
        self._entities[name] = entity

        # Register aliases
        self._alias_map[name.lower()] = name
        for alias in entity.aliases:
            self._alias_map[alias.lower()] = name

        return entity

    def add_relation(
        self,
        source: str,
        relation_type: str,
        target: str,
        *,
        properties: dict[str, Any] | None = None,
    ) -> Relation:
        """Add a directed relation between two entities.

        Args:
            source: Source entity name.
            relation_type: Relationship type (e.g. "created", "uses").
            target: Target entity name.
            properties: Additional metadata.

        Returns:
            The created Relation.

        Raises:
            ValueError: If source or target entity doesn't exist.
        """
        source_canonical = self.resolve_entity(source)
        target_canonical = self.resolve_entity(target)

        if source_canonical is None:
            raise ValueError(f"Source entity '{source}' not found")
        if target_canonical is None:
            raise ValueError(f"Target entity '{target}' not found")

        relation = Relation(
            source=source_canonical,
            relation_type=relation_type,
            target=target_canonical,
            properties=properties or {},
        )
        self._relations.append(relation)
        return relation

    def add_fact(self, entity: str, statement: str) -> Fact:
        """Add a factual statement associated with an entity.

        Args:
            entity: Entity name the fact relates to.
            statement: Natural language factual claim.

        Returns:
            The created Fact.

        Raises:
            ValueError: If the entity doesn't exist.
        """
        canonical = self.resolve_entity(entity)
        if canonical is None:
            raise ValueError(f"Entity '{entity}' not found")

        fact = Fact(
            entity=canonical,
            statement=statement,
            key_terms=_extract_terms(statement),
        )
        self._facts.append(fact)
        return fact

    def resolve_entity(self, name: str) -> str | None:
        """Resolve an entity name (or alias) to its canonical name.

        Args:
            name: Entity name or alias to resolve.

        Returns:
            Canonical entity name, or None if not found.
        """
        return self._alias_map.get(name.lower())

    def get_relations_for(
        self, entity: str, *, relation_type: str | None = None
    ) -> list[Relation]:
        """Get all relations involving an entity (as source or target).

        Args:
            entity: Entity name to search for.
            relation_type: Optional filter by relation type.

        Returns:
            List of matching relations.
        """
        canonical = self.resolve_entity(entity)
        if canonical is None:
            return []

        results = [
            r
            for r in self._relations
            if r.source == canonical or r.target == canonical
        ]

        if relation_type:
            results = [r for r in results if r.relation_type == relation_type]

        return results

    def get_facts_for(self, entity: str) -> list[Fact]:
        """Get all facts associated with an entity.

        Args:
            entity: Entity name.

        Returns:
            List of facts for that entity.
        """
        canonical = self.resolve_entity(entity)
        if canonical is None:
            return []
        return [f for f in self._facts if f.entity == canonical]

    def find_entities_in_text(self, text: str) -> list[str]:
        """Find all known entities mentioned in a text.

        Uses case-insensitive matching against entity names and aliases.

        Args:
            text: Text to search.

        Returns:
            List of canonical entity names found.
        """
        text_lower = text.lower()
        found: set[str] = set()

        for alias, canonical in self._alias_map.items():
            # Word boundary matching to avoid partial matches
            if re.search(r"\b" + re.escape(alias) + r"\b", text_lower):
                found.add(canonical)

        return sorted(found)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> KnowledgeGraph:
        """Build a KnowledgeGraph from a dictionary.

        Expected structure::

            {
                "entities": [
                    {"name": "Python", "type": "language", "aliases": ["py"], "properties": {}},
                ],
                "relations": [
                    {"source": "Guido", "type": "created", "target": "Python"},
                ],
                "facts": [
                    {"entity": "Python", "statement": "Released in 1991."},
                ],
            }

        Args:
            data: Dictionary with entities, relations, and facts.

        Returns:
            Populated KnowledgeGraph.
        """
        graph = cls()

        for entity_data in data.get("entities", []):
            graph.add_entity(
                entity_data["name"],
                entity_type=entity_data.get("type", "unknown"),
                aliases=entity_data.get("aliases", []),
                properties=entity_data.get("properties", {}),
            )

        for rel_data in data.get("relations", []):
            graph.add_relation(
                rel_data["source"],
                rel_data["type"],
                rel_data["target"],
                properties=rel_data.get("properties", {}),
            )

        for fact_data in data.get("facts", []):
            graph.add_fact(fact_data["entity"], fact_data["statement"])

        return graph

    def to_dict(self) -> dict[str, Any]:
        """Serialize the graph to a plain dictionary.

        Returns:
            Dict suitable for JSON/YAML serialization.
        """
        return {
            "entities": [
                {
                    "name": e.name,
                    "type": e.entity_type,
                    "aliases": e.aliases,
                    "properties": e.properties,
                }
                for e in self._entities.values()
            ],
            "relations": [
                {
                    "source": r.source,
                    "type": r.relation_type,
                    "target": r.target,
                    "properties": r.properties,
                }
                for r in self._relations
            ],
            "facts": [
                {"entity": f.entity, "statement": f.statement}
                for f in self._facts
            ],
        }


# ── Verification Logic ──


@dataclass(frozen=True)
class FactCheck:
    """Result of checking a single claim against the graph.

    Attributes:
        claim_text: The sentence from the LLM output.
        grounded: Whether the claim is supported by the graph.
        supporting_facts: Facts from the graph that support this claim.
        mentioned_entities: Entities referenced in this claim.
        confidence: How strongly the claim is grounded (0.0 to 1.0).
    """

    claim_text: str
    grounded: bool
    supporting_facts: list[str]
    mentioned_entities: list[str]
    confidence: float


def check_claim_against_graph(
    claim: str, graph: KnowledgeGraph
) -> FactCheck:
    """Check whether a claim is grounded in the knowledge graph.

    Strategy:
    1. Find all entities mentioned in the claim
    2. Gather facts and relations for those entities
    3. Compare claim terms against fact terms using Jaccard similarity
    4. A claim is grounded if it shares significant terms with known facts

    Args:
        claim: A sentence-level claim from LLM output.
        graph: The knowledge graph to check against.

    Returns:
        FactCheck result with grounding status and evidence.
    """
    mentioned = graph.find_entities_in_text(claim)

    if not mentioned:
        return FactCheck(
            claim_text=claim,
            grounded=False,
            supporting_facts=[],
            mentioned_entities=[],
            confidence=0.0,
        )

    # Gather all relevant facts and relations
    claim_terms = _extract_terms(claim)
    supporting: list[str] = []
    max_similarity = 0.0

    for entity in mentioned:
        # Check facts
        for fact in graph.get_facts_for(entity):
            if not fact.key_terms or not claim_terms:
                continue
            intersection = claim_terms & fact.key_terms
            union = claim_terms | fact.key_terms
            sim = len(intersection) / len(union) if union else 0.0
            if sim > 0.2:  # Minimum relevance threshold
                supporting.append(fact.statement)
                max_similarity = max(max_similarity, sim)

        # Check relations — convert to natural language for comparison
        for rel in graph.get_relations_for(entity):
            rel_text = f"{rel.source} {rel.relation_type} {rel.target}"
            rel_terms = _extract_terms(rel_text)
            if not rel_terms or not claim_terms:
                continue
            intersection = claim_terms & rel_terms
            union = claim_terms | rel_terms
            sim = len(intersection) / len(union) if union else 0.0
            if sim > 0.2:
                supporting.append(rel_text)
                max_similarity = max(max_similarity, sim)

    grounded = len(supporting) > 0
    confidence = max_similarity if grounded else 0.0

    return FactCheck(
        claim_text=claim,
        grounded=grounded,
        supporting_facts=supporting,
        mentioned_entities=mentioned,
        confidence=round(confidence, 4),
    )


# ── Grader ──


@dataclass
class KnowledgeGraphGrader:
    """Evaluate LLM output for factual accuracy against a knowledge graph.

    Splits the output into sentence-level claims, checks each against
    the graph, and scores based on the fraction of claims that are
    grounded (supported by facts/relations in the graph).

    Attributes:
        name: Grader identifier for reports.
        graph: Knowledge graph to check against.
        content: Raw text to evaluate (alternative to path).
        path: Relative path to file in workspace.
        pass_threshold: Minimum grounded fraction to pass.
        require_all_grounded: If True, ALL claims must be grounded to pass.
        ignore_claims_without_entities: Skip claims that don't mention
            any known entities (reduces false negatives).
    """

    name: str
    graph: KnowledgeGraph
    content: str | None = None
    path: str | None = None
    pass_threshold: float = 0.7
    require_all_grounded: bool = False
    ignore_claims_without_entities: bool = True

    def grade(self, workspace: Path) -> EvaluatorResult:
        """Grade the output against the knowledge graph."""
        text = self._resolve_content(workspace)
        if text is None:
            return EvaluatorResult(
                evaluator_name=self.name,
                passed=False,
                score=0.0,
                reason="Content not provided or file not found",
            )

        # Split into sentence-level claims
        sentences = re.split(r"(?<=[.!?])\s+", text.strip())
        sentences = [s.strip() for s in sentences if s.strip() and len(s.strip()) > 5]

        if not sentences:
            return EvaluatorResult(
                evaluator_name=self.name,
                passed=True,
                score=1.0,
                reason="No claims to check",
            )

        # Check each claim
        checks: list[FactCheck] = []
        for sentence in sentences:
            check = check_claim_against_graph(sentence, self.graph)
            checks.append(check)

        # Filter based on configuration
        relevant_checks = checks
        if self.ignore_claims_without_entities:
            relevant_checks = [c for c in checks if c.mentioned_entities]

        if not relevant_checks:
            # No claims mention known entities — can't verify
            return EvaluatorResult(
                evaluator_name=self.name,
                passed=True,
                score=1.0,
                reason="No claims reference known entities",
                details=self._build_details(checks, relevant_checks),
            )

        grounded_count = sum(1 for c in relevant_checks if c.grounded)
        total = len(relevant_checks)
        score = round(grounded_count / total, 4) if total > 0 else 0.0

        if self.require_all_grounded:
            passed = grounded_count == total
        else:
            passed = score >= self.pass_threshold

        reason: str | None = None
        if not passed:
            ungrounded = [c.claim_text[:60] for c in relevant_checks if not c.grounded]
            reason = f"{total - grounded_count}/{total} claims ungrounded: {ungrounded[:3]}"

        return EvaluatorResult(
            evaluator_name=self.name,
            passed=passed,
            score=score,
            reason=reason,
            details=self._build_details(checks, relevant_checks),
        )

    def _resolve_content(self, workspace: Path) -> str | None:
        if self.content is not None:
            return self.content
        if self.path is not None:
            target = validate_workspace_path(workspace, self.path)
            if target.exists():
                return target.read_text(encoding="utf-8", errors="replace")
        return None

    def _build_details(
        self,
        all_checks: list[FactCheck],
        relevant_checks: list[FactCheck],
    ) -> dict[str, Any]:
        return {
            "total_claims": len(all_checks),
            "relevant_claims": len(relevant_checks),
            "grounded_claims": sum(1 for c in relevant_checks if c.grounded),
            "checks": [
                {
                    "claim": c.claim_text,
                    "grounded": c.grounded,
                    "confidence": c.confidence,
                    "supporting_facts": c.supporting_facts,
                    "mentioned_entities": c.mentioned_entities,
                }
                for c in all_checks
            ],
        }
