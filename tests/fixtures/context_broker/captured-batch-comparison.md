# Captured Batch Comparison

`compare_captured_batch(rows, *, expected_by_task, repetitions)` is a pure
post-capture comparator for a declared four-arm batch. It imports the public
`grade_captured_answer` contract and does not run an engine, model, provider,
or capture process.

## Declared contract

`expected_by_task` is a nonempty mapping from a nonempty task name to one
strict grader gold envelope:

```python
{
    "answer": "VALUE",
    "citations": [],
    "abstain": False,
}
```

`repetitions` is a positive `int` (not `bool`). The exact planned grid is every
declared task, every repetition `0..repetitions - 1`, and these arms in order:
`CONTROL`, `B_STRUCTURE`, `C_MEMORY`, `D_UNION`. One unchanged gold envelope
is used for all four arms; gold is not inferred from a response, context, or
row metadata. Invalid gold rejects the batch before any real response content
is read. Required citations remain required even when CONTROL or a truncated
context cannot expose them; the comparator does not weaken gold or change an
abstention expectation.

## Required row interface

Rows may be any objects with these attributes:

```python
row.task                         # declared nonempty task name
row.repetition                   # int in range
row.arm                          # one declared arm
row.prompt                       # nonempty resolved prompt
row.rendered_context_sha256      # None or lowercase SHA-256 hex
row.selected_ids                 # ordered tuple/list of lowercase SHA-256 ids
row.status                       # "completed" or "llm_error"
row.response.content             # read only for completed rows
```

`CONTROL` must have no selected IDs and no context digest. Other arms must use
both selected IDs and a digest, or neither. IDs preserve their order and any
duplicates; they are not normalized. A task's resolved prompt must agree for
every supplied arm/repetition. Within a task and arm, selected IDs and the
digest must agree over supplied repetitions. Unknown tasks, arms, repetitions,
statuses, duplicate `(task, repetition, arm)` keys, and malformed relevant
fields reject the batch. Optional telemetry, timestamps, and other attributes
are untouched. An empty row collection is valid: it reports the full grid as
missing.

## Result schema and denominators

`BatchComparison` contains deterministic `cells`/`assessments`, four
`arm_summaries`, eight arm-local `cohort_summaries` (abstaining and
non-abstaining declared gold), and exactly two `paired_comparisons`:
`D_UNION_vs_B_STRUCTURE` and `D_UNION_vs_C_MEMORY`.

Each cell is `completed` with a `GradeResult`, `llm_error` with no grade, or
`missing` with no grade. An `llm_error` is never graded, even if its response
object resembles a valid answer. Invalid JSON or an invalid answer envelope in
a completed row is an existing strict-grader invalid result, not a setup error.

For a complete batch, `declared_n` per arm is
`len(expected_by_task) * repetitions`. Contract pass rate is `passes / N`;
errors and malformed answers remain in its denominator and have separate
counts. It is a declared-contract pass rate, not an answered-accuracy label.
Each pair has wins, losses, both-pass, and both-nonpass counts summing to N,
and `delta = (wins - losses) / N`.

If any planned cell is missing, `complete` is false. The comparison retains
cells and counts, but every arm rate and every paired delta is `None`; paired
counts are unavailable rather than calculated over a reduced cohort. Cohort
rates use their declared cohort N; a zero-size cohort reports `None`.

## Scope limit

Rows do not carry independent batch, configuration, capture, or gold
provenance. Therefore this comparator only joins rows to the caller-declared
same-batch contract. It cannot prove that settings were independently executed
identically. It makes no semantic-entailment, statistical-significance,
model-quality, quality-gain, token, or cost claim.
