# IPLAN Definitions

## Purpose

This document defines the shared vocabulary used by IPLAN documents, plan
chains, temporary IPLANs, runtime tasks, execution records, evidence bundles,
and management records.

The definitions exist to prevent template drift between AIDoc Flow authoring
and Iplanic operation.

## Template Validity

Files under `docs/standards/templates/` are **schema-valid reference instances**.
They use valid example values (e.g. `IPLAN-01`, `STEP-001`) — not pattern-violating
placeholders — and CI validates each template against its schema with real JSON
Schema validation (`tests/contract/test_schema_contracts.py`, D-0025). Any value an
author substitutes must keep the template schema-valid.

Schema validation is structural (types, enums, patterns, required). It does **not**
assert `format` (e.g. `date-time`) — that is tracked separately as backlog item
14 — and it is not semantic validation (duplicate IDs, cross-references), which is
the runtime validator's job. Do not use a template as an executable payload without
also running semantic validation.

## Canonical Identifiers

| Identifier | Meaning | Notes |
| --- | --- | --- |
| `org_id` | Tenant organization ID | Top-level tenancy scope; an executor's `owner_org_id` is its home `org_id` |
| `project_id` | Project ID within an organization | Scoped within one `org_id` (a project belongs to exactly one org); the tenant is the `(org_id, project_id)` pair |
| `iplan_id` | Canonical Iplanic implementation-plan ID | Use for IPLAN, task, event, run, chain, and evidence records |
| `tmp_iplan_id` | Canonical temporary-plan ID | Used only for temporary IPLANs |
| `plan_version_id` | Immutable imported plan-version record | Points to locked canonical content |
| `chain_id` | IPLAN chain ID | Groups multiple approved plan versions |
| `run_id` | Runtime execution attempt | Never mutates plan content |
| `task_id` | Runtime task assignment | Created by Iplanic from a work order |
| `step_id` | Plan step ID | Unique inside one IPLAN |
| `work_order_id` | Dispatchable step work package | Unique inside one IPLAN |
| `todo_id` | Concrete executor TODO | Unique inside one work order |
| `executor_id` | Canonical Iplanic executor ID | Protocol-native agent IDs map to this value |
| `protocol_plan_id` | Optional protocol-native plan alias | Never replaces `iplan_id` in core state |
| `protocol_agent_id` | Optional protocol-native executor alias | Never replaces `executor_id` in core state |

## Status Families

Do not mix status families across artifacts.

| Family | Values | Applies To |
| --- | --- | --- |
| Authoring | `Draft`, `Review`, `Approved`, `Superseded`, `Abandoned` | IPLAN documents |
| Management | `Imported`, `Validated`, `Review`, `Approved`, `Rejected`, `Superseded`, `Abandoned` | IPLAN version status and version-status lifecycle events |
| Registry record | `Draft`, `Review`, `Approved`, `Active`, `Superseded`, `Abandoned`, `Archived` | IPLAN registry records (`iplan-record`); the `activated` lifecycle event drives the `Active` (current-version) state on this plane |
| Chain | `Draft`, `Review`, `Approved`, `Active`, `Completed`, `Superseded`, `Abandoned` | IPLAN chains |
| Temporary plan | `Draft`, `Review`, `Approved`, `Active`, `Completed`, `Abandoned`, `Promoted` | TMP-IPLAN documents |
| Document step | `Not Started`, `Queued`, `Running`, `Blocked`, `Completed`, `Failed`, `Cancelled` | IPLAN-document steps (document/TODO plane; see Status Projection) |
| File action | `Not Started`, `In Progress`, `Partial`, `Done`, `Skipped` | IPLAN-document files — file-lifecycle vocabulary tracked via `file.changed` + `verified`; not a status-projection target |
| Task payload | `queued`, `assigned`, `running`, `blocked`, `succeeded`, `failed`, `cancelled` | Task payloads |
| Execution event | `accepted`, `running`, `blocked`, `succeeded`, `failed`, `cancelled` | Execution events |
| Record (run-level) | `Queued`, `Running`, `Blocked`, `Completed`, `Failed`, `Cancelled`, `Abandoned` | Execution records (run) |
| Record (task-level) | `Queued`, `Assigned`, `Running`, `Blocked`, `Completed`, `Failed`, `Cancelled` | Execution records (task) |
| Attempt result | `pending`, `succeeded`, `failed`, `cancelled`, `blocked` | `execution-record.tasks[].attempts[]` — retry-outcome detail; cross-mapping deferred to backlog #11 (retry policy) |
| Evidence | `pending`, `passed`, `failed`, `partial` | Evidence bundles and verification summaries |

## Status Projection

The families above are distinct vocabularies. This section is the **authoritative
mapping** between them so executors and Iplanic project status identically rather
than each guessing. The **ingestion service is the authority** that applies the
runtime projection when it records a signed `execution-event`.

### Runtime: event → execution record

Each accepted `execution-event` projects its `event_type` (and `status`) onto the
execution record. `task.completed` carries event `status: succeeded`, which the
record stores as `Completed` — the word change between `succeeded` and `Completed`
is intentional, not a typo.

| `event_type` | event `status` | record **task** status | run-level effect |
| --- | --- | --- | --- |
| `task.assigned` | `accepted` | `Assigned` | `Queued` → `Running` on first task |
| `task.accepted` | `accepted` | `Assigned` | — |
| `task.started` | `running` | `Running` | `Running` |
| `step.started` | `running` | `Running` | `Running` |
| `mcp.tool.called` | `running` | `Running` (no transition) | — |
| `file.changed` | `running` | `Running` (no transition) | — |
| `artifact.created` | `running` | `Running` (no transition) | — |
| `test.started` | `running` | `Running` (no transition) | — |
| `test.passed` | `running` | `Running` (no transition) | — |
| `test.failed` | `running` | `Running` (no transition) | — |
| `task.blocked` | `blocked` | `Blocked` | `Blocked` if any task blocked |
| `task.completed` | `succeeded` | `Completed` | `Completed` when all required done |
| `task.failed` | `failed` | `Failed` | `Failed` |
| `task.cancelled` | `cancelled` | `Cancelled` | `Cancelled` |

Run-level `Abandoned` is a control-plane transition (`Blocked → Abandoned`,
`IPLAN-STANDARD.md` execution lifecycle), not driven by an executor event.
`test.passed`/`test.failed` carry event `status: running` — acceptance is recorded
on the task entry (`acceptance.result`), not as a terminal task status.

`task.assigned` and `task.accepted` are emitted by the Iplanic platform, not by a
remote executor; a remote executor (iplan-runner) emits from `task.started` onward.

### Document/TODO ↔ runtime record

The document `step.status` (planning-side, Title-Case) tracks the same lifecycle as
the record task status. They share six values and differ only by the document's
`Not Started` (pre-dispatch, before any event) and the record's `Assigned` (which
collapses to the document's `Queued`). The terminal link is normative: an IPLAN
document step declares `reporting.completion_event: task.completed`, so a step
reaches `Completed` exactly when the mapped `task.completed` / `succeeded` event
is accepted.

| document `step.status` | record task status    | driven by                                   |
| ---------------------- | --------------------- | ------------------------------------------- |
| `Not Started`          | (none — pre-dispatch) | no event yet                                |
| `Queued`               | `Queued` / `Assigned` | `task.assigned` / `task.accepted`           |
| `Running`              | `Running`             | `task.started`                              |
| `Blocked`              | `Blocked`             | `task.blocked`                              |
| `Completed`            | `Completed`           | `task.completed` (`completion_event` const) |
| `Failed`               | `Failed`              | `task.failed`                               |
| `Cancelled`            | `Cancelled`           | `task.cancelled`                            |

### Plane separation

The runtime plane (task / event / record) and the document/TODO plane above are
mapped here. The **management plane** (`Imported / Validated / Approved / Active /
Superseded / …` on IPLAN versions, records, and lifecycle events) is **separate**:
runtime status never projects into management status. The only link between runtime
progress and management state is the Completion Gate, which is a gate outcome, not a
status copy. Chain `Completed` is likewise a gate outcome, not a projected runtime
value. File-action status and `attempts.result` are listed in Status Families but
are not projection targets (see their notes).

## Tenant Scope-Check

Tenant isolation is enforced per event at ingestion. **Ingestion is the enforcing
authority**: a remote executor never writes record state directly. An
`execution-event` from `executor_id` is **accepted** iff **all** of the following
hold. Clauses 1–2 are evaluated **before** signature verification — they resolve
the signature trust root (`IPLAN trust model`: `executor_id` → registration →
registered key); clauses 3–4 are evaluated **after** the signature verifies,
authorizing the tenant only once the event is proven authentic:

1. `executor_id` resolves to a registration `R`.
2. `R.status == "active"` (evaluated at **ingest time** — a `paused`/`revoked`
   registration rejects new events immediately, independent of the event's
   `occurred_at`; signature key-validity, by contrast, is evaluated at
   `occurred_at`).
3. `event.project_id ∈ R.allowed_projects`. An **empty** `allowed_projects` means
   **no project is authorized** (deny-by-default) — authorization is always an
   explicit grant, never implicit.
4. `event.org_id == R.owner_org_id` (same-org), **or** a cross-org grant:
   `{org_id: event.org_id, project_id: event.project_id} ∈ R.cross_org_grants`
   **and** `R.trust_level == first_party`. The cross-org grant relaxes **only** this
   org check — clause 3 still applies, so the `project_id` must be in
   `allowed_projects` regardless. A cross-org event with no matching grant, or a
   grant on a non-`first_party` executor, is rejected (`org_mismatch`).

Otherwise the event is **rejected**: the whole event is discarded (no partial
record state), the rejection is idempotent, and it is recorded for audit with a
stable reason code. Reason codes:

| reason code             | condition                                             |
| ----------------------- | ----------------------------------------------------- |
| `unregistered_executor` | no registration resolves for `executor_id`            |
| `executor_not_active`   | `R.status != active`                                  |
| `project_not_allowed`   | `event.project_id ∉ R.allowed_projects` (incl. empty) |
| `org_mismatch`          | `event.org_id != R.owner_org_id` (no cross-org grant) |

Reason codes are evaluated in **clause order (1→4); the first failing clause is the
reason**, so the outcome is deterministic even when an event fails several clauses.
`executor_not_active` covers `pending`/`paused`/`revoked` alike (the audit record
carries the actual `status`). `trust_level` is a condition of clause 4's **cross-org**
branch (only a `first_party` executor can use a `cross_org_grants[]` grant); it does
not affect the same-org accept decision. A signature that fails verification is
rejected by signature/auth (it sits between clauses 2 and 3 in the pipeline), not by
one of these four scope codes. The hash `executor_id` carries no tenancy itself —
isolation is the `allowed_projects` + `owner_org_id` (+ `cross_org_grants[]`) grant,
checked per event.

**Signature trust root (key validity).** `event.signature.key_id` resolves to the
executor's registered key — a `signing_keys[]` entry whose `[valid_from, valid_to)`
window covers the event's `occurred_at` (falling back to the scalar
`log_ingest_key_id` while both fields exist). Unlike registration `status` (clause 2,
evaluated at **ingest** time), key validity is evaluated at **`occurred_at`**, so a
rotated key still verifies events it signed while valid; a `signing_keys[]` entry
with `status: revoked` rejects events signed under it.

## Precedence reject codes (auth & signature)

Two reject codes are emitted by the ingestion-precedence steps that **bracket** the
Tenant Scope-Check (auth before it, signature between its two halves), so they are
not scope-clause codes:

| reason code         | step               | condition                                                                                | HTTP |
| ------------------- | ------------------ | ---------------------------------------------------------------------------------------- | ---- |
| `unauthenticated`   | auth (step 1)      | missing, malformed, or invalid caller bearer token                                       | 401  |
| `invalid_signature` | signature (step 3) | `signature.value` fails verify, or no `signing_keys[]` entry resolves `signature.key_id` | 403  |

`invalid_signature` covers every signature failure: `signature.value` fails
`iplan_canonical.verify`; or no `signing_keys[]` entry resolves `signature.key_id`
(non-revoked, its `[valid_from, valid_to)` window covering `occurred_at`, and its
`algorithm` matching `signature.algorithm`); or the ed25519 `public_key` is absent or
not raw-32 bytes.

`unauthenticated` is **shape-only / reserved**: its only implementation is the D-2
fake static verifier; the real OIDC/JWKS validation (D-0017) is a later plan, and the
caller↔`executor_id` binding is deferred (auth is an on/off gate). The full
ingestion precedence and its HTTP status mapping: `unauthenticated` → 401;
`unregistered_executor` / `executor_not_active` / `invalid_signature` /
`project_not_allowed` / `org_mismatch` → 403; `timestamp_skew` → 400; `schema_invalid`
→ 400 (the D-1 body-validation code).

**ed25519 `public_key` encoding.** A `signing_keys[]` entry with `algorithm: ed25519`
stores `public_key` as **base64 of the raw 32-byte public key** — the encoding
`iplan_canonical.verify` consumes (it calls `Ed25519PublicKey.from_public_bytes`,
which requires 32 raw bytes, **not** SPKI-DER). This is also the self-certification
input (`sha256(public_key) == executor_id`). An
`hmac-sha256` entry has `public_key: null`; its shared secret is resolved out-of-band
(keyed by `signature.key_id`), never stored in the registration — so an ed25519
signature with no matching entry has no key material and is `invalid_signature`.

**`received_at` on accept.** An accepted event is appended to the outbox with the
**server-stamped `received_at`** (the ingest overwrite, below), so downstream
projection reads the ingest instant. The signature is verified over `signing_payload`,
which **excludes** `received_at`, so the stored (overwritten) value never conflicts
with the verified bytes. The schema currently marks `received_at` required on input
yet ingest overwrites it; making it server-authored is a tracked schema follow-up.

## Clock-Skew Window

Event timestamps are checked in two parts (the timestamp step of the ingestion
precedence):

1. **`received_at` overwrite.** Ingestion **overwrites `received_at` with its own
   ingest timestamp**; any executor-supplied value is replaced. (This is why the
   signed payload excludes `received_at` — see Signature & hash coverage, D-0021.)
   The check compares the signed `occurred_at` against the ingest-stamped
   `received_at`.
2. **Accepted window.** The event passes iff **both** hold:
   - `occurred_at <= received_at + FUTURE_SKEW` (an event may not occur
     meaningfully in the future — clock-ahead tolerance);
   - `received_at − occurred_at <= MAX_AGE` (an event older than the window is
     stale).

Defaults: `FUTURE_SKEW = 300s` (5-minute clock drift), `MAX_AGE = 86400s`
(24-hour late-delivery / replay tolerance); both configurable. Failure returns the
reject reason `timestamp_skew`, **retryable** when the executor's clock can be
corrected. An offline conformance event that sets `received_at = occurred_at`
(skew 0) is within the window; at live ingest `received_at` is re-stamped and the
real executor→ingest delay is evaluated.

## Inter-Plan Handoff

An Inter-Plan Handoff defines how one IPLAN in a chain transfers context,
evidence, artifacts, or approval state to another IPLAN before target work may
start.

Every handoff must define:

- source plan, step, and work order;
- target plan, step, and work order;
- handoff type;
- required context;
- required evidence;
- acceptance gate;
- fallback behavior for missing context or rejected evidence.

Dependencies define ordering. Inter-plan handoffs define the concrete payload
and acceptance gate needed to move from source work to target work.

## Temporary Plan Separation

A TMP-IPLAN is a temporary execution artifact, not a permanent IPLAN version.
It uses `tmp_iplan_id`, `tmp_kind`, `expires_at`, and `promotion_policy`
instead of `iplan_id`, `plan_version`, and permanent plan lifecycle fields.

TMP-IPLANs are used for bounded corrections, investigations, hotfixes, and
spikes that are opened from an approved IPLAN execution context. They must not
silently change the approved IPLAN's intent, scope, commands, or evidence
requirements. If temporary work expands beyond the approved boundary, it must
be promoted into a permanent IPLAN version or abandoned.

Temporary work must declare a `mutation_policy`:

- `read_only` for investigations and discovery work;
- `bounded_write` for scoped corrections;
- `approval_required` when writes or tool actions need an explicit gate before
  execution.

## IPLAN To TMP-IPLAN Handoff

An IPLAN to TMP-IPLAN handoff opens temporary work from a specific source
`iplan_id`, `plan_version_id`, `step_id`, and `work_order_id`. It records the
trigger, allowed scope, whether the standard IPLAN must pause, and the return
contract that decides whether the source IPLAN can resume.

The source handoff must define:

- `handoff_id`;
- `source_iplan_ref`;
- `trigger`;
- `allowed_scope`;
- `pause_standard_iplan`;
- `return_contract`.

The permanent IPLAN's `navigation.temporary_handoffs` list must record the same
handoff so an operator can see why the run branched and what evidence is
expected back.

## TMP-IPLAN Return Handoff

A TMP-IPLAN return handoff defines the planned return gate for the temporary
branch. It must target the original `iplan_id`, `plan_version_id`, `step_id`,
and `work_order_id`.

The return handoff must define:

- `handoff_id`;
- `target_iplan_ref`;
- `return_gate`;
- `allowed_resume_actions`;
- `promotion_rules`.

Valid return actions are `resume_standard_iplan`, `keep_blocked`,
`promote_to_permanent_iplan`, and `abandon_tmp`. The standard IPLAN may resume
only after the return gate passes.

`return_result` is runtime state, not a planning prerequisite. It records the
actual `outcome`, `evidence_refs`, `resume_action`, `promotion_decision`, and
completion time after temporary execution finishes.

## Evidence Manifest

An evidence manifest is the immutable list of evidence records included in a
bundle seal. Each manifest entry carries an artifact reference, artifact type,
and canonical hash.

The evidence bundle seal hash must cover the canonical payload and the evidence
manifest. The signature signs that canonical hash.

## Signature & hash coverage

All hashes and signatures use `iplan-canonical-json` then `sha256`
(`IPLAN-CANONICALIZATION.md`, D-0021). Each signed/hashed surface covers exactly:

| Surface | Covered payload | Excluded |
| --- | --- | --- |
| `execution-event` signature | the event object, drop-null normalized | `signature`; `received_at` (ingest-stamped) |
| evidence bundle `seal` | the canonical payload **and** the `evidence_manifest` | `seal.signature`, `seal.sealed_at` |
| `iplan-version` `canonical_hash` | the imported plan content (`content_ref`) | record metadata (mutable fields) |
| chain version `canonical_hash` | the imported chain content | record metadata |
| recorded-hash carriers (`iplan-comparison`, `iplan-validation-report`, `iplan-lifecycle-event`, `iplan-import-result`, chain `plans[]`) | **carry** a referenced version's `canonical_hash` | — they never recompute a distinct hash |

`execution-event.signature.value` and `seal.signature.value` are lowercase hex of
the raw signature bytes (`hmac-sha256` digest, or the `ed25519` signature). The
`received_at` exclusion makes signatures survive ingest, which stamps/overwrites
`received_at` independently of the executor.

## Initialization Gate

An Initialization Gate defines whether Iplanic may create runtime records for
an IPLAN or IPLAN chain. Initialization happens before task dispatch.

For a single IPLAN, initialization requires an approved version, validation
report, approval event, approved hash, execution record creation, task payload
creation, and evidence-store readiness.

For an IPLAN chain, initialization also requires approved plan versions, matching
approved hashes, passing validation reports, a valid dependency graph, resolved
handoff definitions, and chain execution records.

## Start Conditions

Start Conditions define whether initialized work may be dispatched to
executors. They are evaluated after initialization and before the first
`task.assigned` event.

Start conditions must cover:

- required plan or chain state;
- readiness result;
- executor and resource availability;
- policy checks;
- context and MCP availability;
- start events expected from the runtime.

## Completion Gate

A Completion Gate defines whether an IPLAN or IPLAN chain may move to a final
completed state.

For a single IPLAN, completion requires terminal required steps, accepted
required events, accepted required artifacts, passing verification commands,
policy gates, and an evidence bundle when required.

For an IPLAN chain, completion additionally requires tier exit gates, plan
completion gates, required inter-plan handoffs, chain evidence, and final chain
evidence bundle sealing.

## Comparison Impact

`impact` is the summary classification for a comparison. The nested
`approval_impact` and `execution_impact` blocks are the actionable detail.

Authoritative fields:

- `impact.severity` decides review priority.
- `approval_impact.approval_required` decides whether approval must run.
- `execution_impact.rerun_required` decides whether existing execution state is
  invalidated.
- `execution_impact.affected_steps`, `affected_work_orders`, and
  `affected_files` define the rerun scope.

Changes to intent, scope, commands, executor work, evidence requirements,
policy, or chain order should be treated as at least `review_required`.

## Temporary IPLAN

A temporary IPLAN is executable only when it includes the same operational
minimums as a permanent IPLAN step: executor context, executor work, concrete
TODOs, reporting rules, evidence requirements, failure handling, verification,
source handoff, return handoff, runtime handoff, and closure rules.

Temporary IPLANs must expire, close, or promote to permanent IPLANs. They are
not a bypass for approval, evidence, or policy controls.
