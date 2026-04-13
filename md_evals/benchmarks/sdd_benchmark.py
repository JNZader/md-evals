"""SDD quality benchmark: scoring rubrics, sample data, and cascade integration.

Defines benchmark cases for each SDD phase (proposal, spec, design, tasks),
with known-good sample outputs and scoring rubrics. Integrates with the
existing CascadeEvaluator for layered evaluation.

Usage:
    suite = SDDBenchmarkSuite()
    results = suite.run_all()
    for result in results:
        print(f"{result.case_id}: {result.passed} ({result.score:.2f})")
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from md_evals.graders.cascade_evaluator import (
    CascadeEvaluator,
    CascadeResult,
    KeywordStep,
    RegexStep,
)


# ─── Artifact types ──────────────────────────────────────────────


class SDDArtifactType(str, Enum):
    """SDD artifact types that can be benchmarked."""

    PROPOSAL = "proposal"
    SPEC = "spec"
    DESIGN = "design"
    TASKS = "tasks"


# ─── Rubric definitions ─────────────────────────────────────────


@dataclass(frozen=True)
class SDDRubricCriterion:
    """A single criterion in a scoring rubric.

    Attributes:
        name: Criterion identifier.
        description: What this criterion evaluates.
        weight: Relative weight (0.0 to 1.0). Weights within a rubric should sum to 1.0.
        required_keywords: Keywords that must appear for this criterion to pass.
        required_sections: Section headers that must exist (markdown ## format).
    """

    name: str
    description: str
    weight: float
    required_keywords: list[str] = field(default_factory=list)
    required_sections: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class SDDRubric:
    """Scoring rubric for an SDD artifact type.

    Attributes:
        artifact_type: Which SDD phase this rubric evaluates.
        criteria: List of scored criteria.
        min_pass_score: Minimum weighted score to pass (0.0 to 1.0).
    """

    artifact_type: SDDArtifactType
    criteria: list[SDDRubricCriterion]
    min_pass_score: float = 0.7


# ─── Benchmark data structures ───────────────────────────────────


@dataclass(frozen=True)
class SDDBenchmarkCase:
    """A single benchmark case with input and expected output.

    Attributes:
        case_id: Unique identifier for this case.
        artifact_type: SDD phase being tested.
        description: What this case tests.
        input_context: Simulated input context (project description, change request, etc.).
        expected_output: Known-good reference output.
        tags: Optional tags for filtering (e.g., "edge-case", "minimal").
    """

    case_id: str
    artifact_type: SDDArtifactType
    description: str
    input_context: str
    expected_output: str
    tags: list[str] = field(default_factory=list)


@dataclass
class SDDBenchmarkResult:
    """Result from evaluating a single benchmark case.

    Attributes:
        case_id: Which case was evaluated.
        artifact_type: SDD phase.
        passed: Whether the output passed the rubric.
        score: Weighted score (0.0 to 1.0).
        criterion_scores: Per-criterion breakdown.
        cascade_result: Full cascade evaluator result (if cascade was used).
        details: Additional evaluation metadata.
    """

    case_id: str
    artifact_type: SDDArtifactType
    passed: bool
    score: float
    criterion_scores: dict[str, float] = field(default_factory=dict)
    cascade_result: CascadeResult | None = None
    details: dict[str, Any] = field(default_factory=dict)


# ─── Rubric definitions per artifact type ────────────────────────

_RUBRICS: dict[SDDArtifactType, SDDRubric] = {
    SDDArtifactType.PROPOSAL: SDDRubric(
        artifact_type=SDDArtifactType.PROPOSAL,
        criteria=[
            SDDRubricCriterion(
                name="intent",
                description="Clearly states the intent and motivation for the change",
                weight=0.3,
                required_keywords=["intent", "motivation", "problem", "goal"],
                required_sections=["Intent"],
            ),
            SDDRubricCriterion(
                name="scope",
                description="Defines what is in scope and what is explicitly out of scope",
                weight=0.3,
                required_keywords=["scope"],
                required_sections=["Scope"],
            ),
            SDDRubricCriterion(
                name="approach",
                description="Proposes at least one approach with tradeoffs",
                weight=0.25,
                required_keywords=["approach", "tradeoff"],
                required_sections=["Approach"],
            ),
            SDDRubricCriterion(
                name="risks",
                description="Identifies risks or unknowns",
                weight=0.15,
                required_keywords=["risk"],
                required_sections=["Risks"],
            ),
        ],
        min_pass_score=0.7,
    ),
    SDDArtifactType.SPEC: SDDRubric(
        artifact_type=SDDArtifactType.SPEC,
        criteria=[
            SDDRubricCriterion(
                name="requirements",
                description="Lists functional requirements with clear acceptance criteria",
                weight=0.35,
                required_keywords=["requirement", "must", "shall"],
                required_sections=["Requirements"],
            ),
            SDDRubricCriterion(
                name="scenarios",
                description="Includes testable scenarios (given/when/then or equivalent)",
                weight=0.30,
                required_keywords=["scenario", "given", "when", "then"],
                required_sections=["Scenarios"],
            ),
            SDDRubricCriterion(
                name="constraints",
                description="Documents technical constraints and non-functional requirements",
                weight=0.20,
                required_keywords=["constraint"],
            ),
            SDDRubricCriterion(
                name="dependencies",
                description="Lists external dependencies and integration points",
                weight=0.15,
                required_keywords=["dependency", "integration"],
            ),
        ],
        min_pass_score=0.7,
    ),
    SDDArtifactType.DESIGN: SDDRubric(
        artifact_type=SDDArtifactType.DESIGN,
        criteria=[
            SDDRubricCriterion(
                name="architecture",
                description="Describes architectural decisions with rationale",
                weight=0.30,
                required_keywords=["architecture", "decision"],
                required_sections=["Architecture"],
            ),
            SDDRubricCriterion(
                name="data_model",
                description="Defines data structures and interfaces",
                weight=0.25,
                required_keywords=["interface", "type", "schema"],
            ),
            SDDRubricCriterion(
                name="patterns",
                description="References design patterns or architectural patterns used",
                weight=0.20,
                required_keywords=["pattern"],
            ),
            SDDRubricCriterion(
                name="alternatives",
                description="Considers and documents alternative approaches",
                weight=0.25,
                required_keywords=["alternative", "tradeoff"],
                required_sections=["Alternatives"],
            ),
        ],
        min_pass_score=0.7,
    ),
    SDDArtifactType.TASKS: SDDRubric(
        artifact_type=SDDArtifactType.TASKS,
        criteria=[
            SDDRubricCriterion(
                name="breakdown",
                description="Breaks work into atomic, implementable tasks",
                weight=0.35,
                required_keywords=["task"],
                required_sections=["Tasks"],
            ),
            SDDRubricCriterion(
                name="ordering",
                description="Tasks have logical ordering with dependencies noted",
                weight=0.25,
                required_keywords=["phase", "dependency"],
            ),
            SDDRubricCriterion(
                name="acceptance",
                description="Each task has clear done criteria",
                weight=0.25,
                required_keywords=["done", "acceptance", "criteria"],
            ),
            SDDRubricCriterion(
                name="estimates",
                description="Includes rough effort estimates or T-shirt sizing",
                weight=0.15,
                required_keywords=["estimate", "size"],
            ),
        ],
        min_pass_score=0.7,
    ),
}


def get_rubric(artifact_type: SDDArtifactType) -> SDDRubric:
    """Get the scoring rubric for an artifact type."""
    return _RUBRICS[artifact_type]


# ─── Sample data ─────────────────────────────────────────────────

_SAMPLE_CASES: list[SDDBenchmarkCase] = [
    # ── Proposals ────────────────────────────────────────────────
    SDDBenchmarkCase(
        case_id="proposal-auth-refactor",
        artifact_type=SDDArtifactType.PROPOSAL,
        description="Good proposal: authentication system refactor",
        input_context="The current auth system uses session cookies and needs migration to JWT. The codebase is a Node.js monorepo with Express.",
        expected_output="""\
## Intent

The current authentication system relies on server-side session cookies stored in Redis. \
This creates scaling problems: every new server instance needs Redis connectivity, and \
session affinity adds deployment complexity. The goal is to migrate to stateless JWT \
tokens to eliminate session storage dependencies.

The motivation is reducing infrastructure cost and simplifying horizontal scaling. The \
problem manifests as increased latency during deployments when session stores are being \
rebalanced.

## Scope

**In scope:**
- Replace session cookie authentication with JWT access/refresh token pair
- Migrate existing session data to JWT claims
- Update all API middleware to validate JWT tokens

**Out of scope:**
- OAuth2/OIDC provider integration (separate initiative)
- User-facing login UI changes (backend-only)

## Approach

**Approach A: Big-bang migration** — Replace all auth in one release.
- Tradeoff: faster completion but higher risk of regression.

**Approach B: Parallel auth (recommended)** — Run both systems simultaneously with \
a feature flag, migrate endpoint-by-endpoint.
- Tradeoff: slower rollout but zero-downtime migration with rollback capability.

## Risks

- Risk: Token revocation requires a blocklist or short expiry + refresh flow
- Risk: JWT payload size increases header size for every request
- Risk: Clock skew between services may cause premature token rejection
""",
        tags=["good", "complete"],
    ),
    SDDBenchmarkCase(
        case_id="proposal-search-feature",
        artifact_type=SDDArtifactType.PROPOSAL,
        description="Good proposal: semantic search over historical reviews",
        input_context="Add the ability to search over past review comments to find patterns. The tool is a TypeScript monorepo for code review.",
        expected_output="""\
## Intent

Reviewers frequently encounter recurring patterns (memory leaks, SQL injection, missing \
error handling) but have no way to search past reviews for prior art. The goal is to add \
semantic search over historical review comments and PR descriptions so reviewers can find \
past discussions about similar problems.

The motivation is reducing duplicated reviewer effort and building institutional knowledge. \
The problem is that review insights are lost after the PR is merged.

## Scope

**In scope:**
- Text indexing of review comments and PR descriptions
- BM25-based search (no external embedding dependencies)
- Search API callable from the review pipeline

**Out of scope:**
- Vector/embedding-based semantic search (future enhancement)
- UI for search (CLI/API only)

## Approach

**Approach: In-process BM25 index** — Build an inverted index with TF-IDF/BM25 scoring, \
stored alongside the existing SQLite memory. Zero external dependencies.
- Tradeoff: less "semantic" than embeddings but simpler, faster, and deterministic.

## Risks

- Risk: Index size grows linearly with review history; may need pruning for large repos
- Risk: BM25 keyword matching may miss semantically similar but lexically different queries
""",
        tags=["good", "minimal"],
    ),
    SDDBenchmarkCase(
        case_id="proposal-incomplete",
        artifact_type=SDDArtifactType.PROPOSAL,
        description="Bad proposal: missing sections and vague",
        input_context="We need to add caching to the API",
        expected_output="""\
## Summary

Add caching to make things faster. We'll use Redis probably.

The API is slow so we need caching.
""",
        tags=["bad", "incomplete"],
    ),
    # ── Specs ────────────────────────────────────────────────────
    SDDBenchmarkCase(
        case_id="spec-auth-jwt",
        artifact_type=SDDArtifactType.SPEC,
        description="Good spec: JWT authentication requirements",
        input_context="Spec for the JWT auth migration described in proposal-auth-refactor.",
        expected_output="""\
## Requirements

- REQ-1: The system must issue JWT access tokens with configurable expiry (default: 15 minutes)
- REQ-2: The system shall issue refresh tokens stored in httpOnly cookies (expiry: 7 days)
- REQ-3: Token validation middleware must reject expired tokens with 401 status
- REQ-4: The system must support token blocklisting for forced logout
- REQ-5: All existing session-based endpoints shall accept JWT tokens in the Authorization header

## Scenarios

### Scenario: Successful authentication
- **Given** a user with valid credentials
- **When** they POST to /auth/login with username and password
- **Then** they receive a JWT access token and a refresh token cookie
- **And** the access token contains the user ID, roles, and expiry claims

### Scenario: Token refresh
- **Given** a user with a valid refresh token
- **When** their access token expires and they POST to /auth/refresh
- **Then** they receive a new access token
- **And** the old access token is no longer valid

### Scenario: Forced logout
- **Given** an admin blocklists a user's token family
- **When** the user makes any authenticated request
- **Then** the request is rejected with 401
- **And** the refresh token is invalidated

## Constraints

- Constraint: JWT signing must use RS256 (asymmetric) to allow verification without the private key
- Constraint: Access token payload must not exceed 1KB to avoid header size issues
- Constraint: Token validation must complete within 5ms (no database lookup for valid tokens)

## Dependencies

- Dependency: jsonwebtoken library for token signing/verification
- Integration point: Redis for the token blocklist (existing infrastructure)
- Integration point: User service for credential validation
""",
        tags=["good", "complete"],
    ),
    SDDBenchmarkCase(
        case_id="spec-vague",
        artifact_type=SDDArtifactType.SPEC,
        description="Bad spec: vague requirements, no scenarios",
        input_context="Spec for adding search to the tool.",
        expected_output="""\
## Overview

The search feature needs to work well. Users should be able to find things.
It should be fast and accurate.

## Notes

- Use some kind of search algorithm
- Make sure it works
""",
        tags=["bad", "vague"],
    ),
    # ── Design ───────────────────────────────────────────────────
    SDDBenchmarkCase(
        case_id="design-search-bm25",
        artifact_type=SDDArtifactType.DESIGN,
        description="Good design: BM25 search engine architecture",
        input_context="Technical design for the semantic search feature.",
        expected_output="""\
## Architecture

The search system follows a layered architecture decision:
- **Indexer layer**: Builds and maintains an inverted index from review documents
- **Scorer layer**: Implements BM25 ranking with configurable parameters
- **Query layer**: Tokenizes queries and orchestrates scoring

Key decision: in-process index (not a separate service) to avoid network overhead \
and deployment complexity for a feature that operates on small-to-medium corpora.

## Data Model

```typescript
interface SearchDocument {
  id: string;
  content: string;
  source: 'review-comment' | 'pr-description';
  createdAt: string;
}

interface TermStats {
  df: number;  // document frequency
  postings: Array<{ docId: string; tf: number; positions: number[] }>;
}

// The inverted index schema maps terms to their posting lists
type InvertedIndex = Map<string, TermStats>;
```

## Patterns

- **Inverted index pattern**: Standard IR pattern for efficient full-text search
- **Builder pattern**: SearchIndexer builds the index incrementally via addDocument()
- **Strategy pattern**: BM25Params injectable into SearchEngine for tuning

## Alternatives

**Alternative A: Embedding-based search (rejected)**
- Tradeoff: Better semantic matching but requires external model dependency
- Reason for rejection: Adds 200MB+ dependency, cold start latency, and API costs

**Alternative B: SQLite FTS5 (considered)**
- Tradeoff: Proven technology but couples search to SQLite storage
- Reason for not choosing: The index should be portable and storage-agnostic
""",
        tags=["good", "complete"],
    ),
    # ── Tasks ────────────────────────────────────────────────────
    SDDBenchmarkCase(
        case_id="tasks-search-impl",
        artifact_type=SDDArtifactType.TASKS,
        description="Good task breakdown: search feature implementation",
        input_context="Task breakdown for implementing BM25 search.",
        expected_output="""\
## Tasks

### Phase 1: Core Types and Indexer (dependency: none)

- **Task 1.1**: Define search types (SearchDocument, TermStats, IndexSnapshot, SearchResult)
  - Done criteria: Types compile, exported from index.ts
  - Estimate: S (small)

- **Task 1.2**: Implement tokenizer with stop-word filtering
  - Done criteria: tokenize() passes unit tests for edge cases
  - Estimate: S (small)
  - Size: ~50 lines

- **Task 1.3**: Implement SearchIndexer (add/remove/snapshot)
  - Done criteria: Acceptance criteria met — round-trip snapshot test passes
  - Estimate: M (medium)
  - Dependency on Task 1.1 and 1.2

### Phase 2: Search Engine

- **Task 2.1**: Implement BM25 scoring in SearchEngine
  - Done criteria: BM25 formula produces correct scores for known corpus
  - Estimate: M (medium)
  - Dependency on Phase 1

- **Task 2.2**: Add source filtering and limit options
  - Done criteria: Acceptance criteria — filter by source, respect limit
  - Estimate: S (small)
  - Dependency on Task 2.1

### Phase 3: Integration

- **Task 3.1**: Export search module from package index.ts
  - Done criteria: All types and classes importable from package root
  - Estimate: XS (extra small)
  - Dependency on Phase 2
""",
        tags=["good", "phased"],
    ),
]


def get_sample_cases(
    artifact_type: SDDArtifactType | None = None,
    tags: list[str] | None = None,
) -> list[SDDBenchmarkCase]:
    """Get sample benchmark cases, optionally filtered.

    Args:
        artifact_type: Filter by artifact type. None returns all.
        tags: Filter to cases that have ALL of these tags. None returns all.

    Returns:
        List of matching benchmark cases.
    """
    cases = _SAMPLE_CASES

    if artifact_type is not None:
        cases = [c for c in cases if c.artifact_type == artifact_type]

    if tags is not None:
        cases = [c for c in cases if all(t in c.tags for t in tags)]

    return cases


# ─── Rubric scorer ───────────────────────────────────────────────


def _score_criterion(criterion: SDDRubricCriterion, output: str) -> float:
    """Score a single rubric criterion against an output.

    Returns a score between 0.0 and 1.0 based on keyword and section coverage.
    """
    scores: list[float] = []

    # Keyword coverage
    if criterion.required_keywords:
        output_lower = output.lower()
        found = sum(1 for kw in criterion.required_keywords if kw.lower() in output_lower)
        scores.append(found / len(criterion.required_keywords))

    # Section coverage (look for ## headers)
    if criterion.required_sections:
        found = sum(
            1 for section in criterion.required_sections if f"## {section}" in output
        )
        scores.append(found / len(criterion.required_sections))

    if not scores:
        return 0.5  # No criteria to check — neutral score

    return sum(scores) / len(scores)


def score_against_rubric(
    output: str,
    rubric: SDDRubric,
) -> tuple[float, dict[str, float]]:
    """Score an output against a rubric.

    Args:
        output: The artifact text to evaluate.
        rubric: The scoring rubric to apply.

    Returns:
        Tuple of (weighted_score, per_criterion_scores).
    """
    criterion_scores: dict[str, float] = {}
    weighted_score = 0.0

    for criterion in rubric.criteria:
        score = _score_criterion(criterion, output)
        criterion_scores[criterion.name] = score
        weighted_score += score * criterion.weight

    return weighted_score, criterion_scores


# ─── Cascade integration ────────────────────────────────────────


def build_cascade_for_artifact(artifact_type: SDDArtifactType) -> CascadeEvaluator:
    """Build a CascadeEvaluator configured for an SDD artifact type.

    The cascade uses cheap checks (regex for sections, keywords for content)
    before any expensive LLM evaluation would be needed.

    Args:
        artifact_type: Which SDD phase to build the cascade for.

    Returns:
        A configured CascadeEvaluator.
    """
    rubric = get_rubric(artifact_type)
    steps = []

    # Step 1: Section structure check (regex)
    all_sections = []
    for criterion in rubric.criteria:
        all_sections.extend(criterion.required_sections)

    if all_sections:
        section_pattern = "|".join(rf"##\s+{s}" for s in all_sections)
        steps.append(
            RegexStep(
                name=f"{artifact_type.value}_structure",
                pattern=section_pattern,
                pass_on_match=True,  # section headers found = pass (gate check)
                uncertain_on_no_match=False,  # no section headers = fail early
            )
        )

    # Step 2: Keyword coverage check
    all_keywords = []
    for criterion in rubric.criteria:
        all_keywords.extend(criterion.required_keywords)

    if all_keywords:
        # Deduplicate
        unique_keywords = list(dict.fromkeys(all_keywords))
        steps.append(
            KeywordStep(
                name=f"{artifact_type.value}_keywords",
                keywords=unique_keywords,
                pass_threshold=0.6,
                fail_threshold=0.2,
            )
        )

    return CascadeEvaluator(
        name=f"sdd_{artifact_type.value}_benchmark",
        steps=steps,
        default_pass=False,
    )


# ─── Benchmark suite ────────────────────────────────────────────


@dataclass
class SDDBenchmarkSuite:
    """Runs SDD quality benchmarks against sample or custom outputs.

    Can evaluate the known-good sample outputs (regression testing) or
    evaluate new outputs against the rubrics.

    Args:
        artifact_types: Which artifact types to include. None means all.
    """

    artifact_types: list[SDDArtifactType] | None = None

    def evaluate(self, output: str, artifact_type: SDDArtifactType) -> SDDBenchmarkResult:
        """Evaluate a single output against its artifact rubric.

        Args:
            output: The artifact text to evaluate.
            artifact_type: Which SDD phase this output represents.

        Returns:
            Benchmark result with score and per-criterion breakdown.
        """
        rubric = get_rubric(artifact_type)
        weighted_score, criterion_scores = score_against_rubric(output, rubric)

        # Also run the cascade evaluator for a second opinion
        cascade = build_cascade_for_artifact(artifact_type)
        cascade_result = cascade.evaluate(output)

        passed = weighted_score >= rubric.min_pass_score

        return SDDBenchmarkResult(
            case_id=f"custom-{artifact_type.value}",
            artifact_type=artifact_type,
            passed=passed,
            score=weighted_score,
            criterion_scores=criterion_scores,
            cascade_result=cascade_result,
            details={
                "min_pass_score": rubric.min_pass_score,
                "cascade_passed": cascade_result.passed,
            },
        )

    def run_samples(
        self,
        tags: list[str] | None = None,
    ) -> list[SDDBenchmarkResult]:
        """Run benchmark on all sample cases (regression testing).

        Evaluates each sample's expected_output against its rubric.

        Args:
            tags: Optional tag filter for sample cases.

        Returns:
            List of benchmark results for all matching samples.
        """
        results: list[SDDBenchmarkResult] = []
        types = self.artifact_types or list(SDDArtifactType)

        for artifact_type in types:
            cases = get_sample_cases(artifact_type=artifact_type, tags=tags)
            rubric = get_rubric(artifact_type)

            for case in cases:
                weighted_score, criterion_scores = score_against_rubric(
                    case.expected_output, rubric
                )
                cascade = build_cascade_for_artifact(artifact_type)
                cascade_result = cascade.evaluate(case.expected_output)

                passed = weighted_score >= rubric.min_pass_score

                results.append(
                    SDDBenchmarkResult(
                        case_id=case.case_id,
                        artifact_type=artifact_type,
                        passed=passed,
                        score=weighted_score,
                        criterion_scores=criterion_scores,
                        cascade_result=cascade_result,
                        details={
                            "description": case.description,
                            "tags": case.tags,
                            "min_pass_score": rubric.min_pass_score,
                            "cascade_passed": cascade_result.passed,
                        },
                    )
                )

        return results

    def run_all(self) -> list[SDDBenchmarkResult]:
        """Run all sample benchmarks without tag filtering."""
        return self.run_samples()
