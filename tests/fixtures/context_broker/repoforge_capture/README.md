# Replay a real RepoForge capture without launching RepoForge

This experimental test-support adapter normalizes two captured static imports into
`ContextPack.capture.v1`. It is not a production broker, a general resolver, or a
new execution attestation. The original four `ContextPack.v0` files stay unchanged.

## Trust and identity

- `graph.json` and the three source files are byte-identical retained capture inputs.
- `provenance.json` is a derived, curated manifest; its expected SHA-256 is pinned
  independently in the test, before RED. The adapter requires that caller anchor.
- Replacing both payload and manifest cannot replace the caller's trust anchor.
- The recorded proof hash references an earlier run; replay does not reproduce or
  cryptographically authenticate that run. No machine-specific paths are required.
- Corpus identity is stable: `fixture://repoforge-file-graph`. Revision is the full
  `sha256:` content metadata digest, not RepoForge's Git commit.
- The corpus digest hashes the path-sorted list of `{path, sha256, bytes}` records
  using `json.dumps(..., sort_keys=True, separators=(",", ":"), ensure_ascii=True)`
  encoded as UTF-8 without a trailing newline. Freshness and Git state stay `unknown`.

## Narrow contract

`capture_schema(base_schema)` deep-copies v0 and changes only its `$id`, profile
version, and the pack/evidence revision patterns. Every other constraint and
internal reference is retained. No production schema or fixture validator changes.
The curated mappings check both graph endpoints and exact source/target lines;
only sibling named static imports in these three files are supported. Edge weight
is not confidence. Budgets estimate evidence quote bytes only; traces cover all
candidate records, including records omitted from the selected budget prefix.

## Check

Run the two scoped test files using the pinned guarded pytest invocation recorded
in the implementation proof. Do not regenerate this capture during tests. A new
capture or trust anchor requires deliberate enrollment and independent verification.
