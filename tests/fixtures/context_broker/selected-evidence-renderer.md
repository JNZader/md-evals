# Render selected evidence without audit metadata

`md_evals.context_renderer.render_selected_evidence(pack)` is a pure prerequisite
for a later evaluation runner. It accepts only a caller-validated
`ContextPack.capture.union.v1` dictionary, or `None` for CONTROL.

## Output contract

- CONTROL returns `None`. A supported envelope with empty evidence also returns
  `None`, but its shape is checked first.
- Nonempty output is one JSON string with exactly `format` and `evidence`.
  The marker is `ContextPack.selected-evidence.v1`; no trailing newline is added.
- Encoding uses sorted object keys, compact separators, ASCII escaping, and
  `allow_nan=False`. Evidence array order and duplicate records are preserved.
- All 13 selected fields survive unchanged: `id`, `kind`, `repository`,
  `revision`, `producer_instance`, `source_id`, `path`, `line`, `quote`,
  `claim`, `value`, `freshness`, and `git_state`.

## Validation boundary

The caller must validate the complete schema, trust anchors, provenance,
applicability, and selection before rendering. This function checks the exact root
and evidence field sets, root container types, supported profile, and selected
scalar constraints. Invalid supported shape raises `ContextRenderError`.
It is deliberately **not** a full ContextPack or provenance validator.

Producer details, manifests, traces, conflicts, and budget/drop audit information
are omitted, not inspected internally or serialized through a fallback. Already
selected records are not sorted, deduplicated, trimmed, revised, or re-budgeted.
Quotes containing markup or instruction-like text remain data: omission of
metadata and JSON escaping are **not a prompt-injection defense**.

## Scope

The renderer performs no I/O or provider/model calls and does not alter its input.
It is not yet wired to execution, scoring, or result persistence. The output has
no asserted model-token budget, cost, benchmark, or quality benefit.
