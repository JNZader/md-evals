# Captured Pilot Plan

`prepare_captured_pilot(*, cases, provider, model, backend_config_sha256,
limits)` produces a deterministic, offline `CapturedPilotPlan`. The result has
canonical `manifest_json`, its exact UTF-8 SHA-256 digest, and `to_dict()` for
a fresh mutable copy. It does not write files, execute a runner, launch a
model, contact a provider, or authorize execution.

## Input contract

`cases` is an ordered list of one to three exact objects:

```python
{"name": "case-a", "prompt": "unchanged prompt", "expected": gold, "packs": arms}
```

Names and prompts are nonblank; names are unique. `arms` has exactly
`CONTROL`, `B_STRUCTURE`, `C_MEMORY`, and `D_UNION`. CONTROL is `None`; every
other arm is a supported non-`None` union pack. B may select only structure
evidence, C only memory evidence, and D either/both/neither. All non-CONTROL
packs in a case share repository and revision. Selected ID order and duplicates
are retained. Repeated record IDs must have identical full record definitions.

One strict gold envelope belongs to each case and is reused unchanged in every
arm. Gold is validated before rendering any context. Hidden gold citations are
valid declarations; this planner does not require their visibility, weaken gold,
or change abstention by arm. Gold is case metadata, never model-prompt context.

`provider` and `model` are explicit nonblank declarations. The lowercase
64-hex `backend_config_sha256` declares backend configuration; it is not an
attestation. `limits` exactly contains positive non-boolean integer
`max_primary_calls`, `per_call_timeout_seconds`, and `total_timeout_seconds`.
For 1–3 cases there are exactly 4–12 planned adapter calls, repetitions are
fixed at one, and `max_primary_calls` must cover planned calls without exceeding
12. Planned calls are not a billable-inference limit. Timeouts are declared
requirements, not enforced here. The policy requires no fallback and zero
adapter retries; CLI-internal retries remain unverified. Usage and cost are
unmeasured/unknown, never defaulted to zero.

## Manifest and limits

The profile is `CapturedPilotPlan.v1`, purpose `conformance`. Each non-CONTROL
arm binds repository, revision, a SHA-256 of canonical whole-pack JSON, selected
IDs, rendered selected context, and rendered-context digest. The whole-pack hash
is not an original-file-bytes hash: sorted compact ASCII JSON makes audit
metadata changes bind the plan while omitting pack metadata and credentials from
the manifest. Case order changes the digest; nested inputs are snapshotted. The
encoded manifest is capped at 1 MiB.

Every plan has `execution_authorized: false` and these stable blockers:
`runner_admission_not_verified`, `backend_preflight_not_verified`, and
`live_execution_not_authorized`. Required later backend checks are pre-dispatch
provider pinning, context isolation, bounded termination, and observed usage
semantics. `strict: true` is not a provider pin; real-pilot and utility gates
remain pending. Prepared data is not a signature, permission receipt, capability
proof, or proof that settings executed identically. Post-response identity cannot
undo unwanted execution.

## Optional runner binding

`run_captured_arms(config, adapter, packs_by_task, *, plan=None)` retains its
legacy behavior when `plan` is absent. A supplied exact `CapturedPilotPlan` is
an input-consistency check only: before the first adapter call it deep-snapshots
the config and packs, rebuilds the plan through the public preparer, and requires
identical canonical manifest bytes and digest. It verifies ordered literal task
names/prompts, selected evidence and whole-pack audit metadata, provider/model,
one repetition, four calls per case, a single primary attempt
(`Defaults.retry_attempts == 1`), and matching per-call timeout declaration.
Malformed, oversized, non-UTF-8, excessively nested, or invalid manually
constructed plans fail as runner admission errors before any adapter call.

The binding neither grants execution authority nor changes the plan's false
authorization/blockers. It is not a live-safe launcher or runtime enforcement.
Backend configuration digest, provider pinning, usage, internal adapter retries,
total deadline, and real isolation remain unchecked; blocker metadata is not a
runtime guarantee.
