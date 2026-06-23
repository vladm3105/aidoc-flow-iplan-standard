# IPLAN Management Standard

## Purpose

IPLAN management is Iplanic's system of record for approved implementation
plans. It stores canonical IPLAN records, immutable versions, import results,
validation reports, lifecycle events, comparisons, and approval decisions.

The management layer does not execute code directly. It controls which plan
content is trusted, which version is active, what changed between versions, and
which execution or review actions are allowed.

## IPLAN Registry

The IPLAN Registry stores one durable record per logical plan inside a project.
The registry record owns:

- organization and project scope;
- stable `iplan_id`;
- current and latest version pointers;
- owner metadata;
- lifecycle state;
- timestamps and labels.

The registry record is mutable metadata. It must not contain mutable copies of
approved plan content. Approved plan content belongs to immutable IPLAN Version
records.

### Registry concurrency

Registry-record mutations use **optimistic concurrency**, scoped per
`(org_id, project_id, iplan_id)`. The record carries a monotonic `record_version`
token. A writer (for example, two imports racing to set `current_version_id`)
supplies the `record_version` it read; the write is a **compare-and-set**:

- if the stored `record_version` still matches, the write is applied and
  `record_version` is incremented;
- if it no longer matches, the write is **rejected**; the caller re-reads the
  record and retries against fresh state.

This prevents a stale writer from clobbering `current_version_id` or other mutable
pointers. The same rule applies to the chain registry record when it is
introduced.

## Version Control

Every imported plan artifact creates an IPLAN Version record. Version content is
immutable after import and is identified by `plan_version_id`,
`plan_version`, and a canonical `sha256` hash.

Mutable fields are limited to lifecycle state, validation status, approval
state, and supersession pointers. Any content change creates a new version.
Rollback is modeled by approving previously known content as a new version
event, not by mutating old content.

Required version controls (canonicalization defined in
[`IPLAN-CANONICALIZATION.md`](IPLAN-CANONICALIZATION.md), D-0021):

- canonical payload hash and canonicalization algorithm;
- source import reference;
- validation report link;
- approval decision and approved hash;
- immutable content lock;
- supersession links.

### Chain registry & version

Chains are managed by the same two-record split as plans (D-0029):

- An **IPLAN Chain Version** record (`iplan-chain-version`) holds immutable imported
  chain content, mirroring IPLAN Version: it is identified by `chain_version_id` and
  `chain_version`, and it carries the chain's **own** canonical `sha256` hash. The
  `iplan-chain` document has no self-hash; this record supplies it (closing the gap
  where only member `plans[].canonical_hash` existed). Mutable fields, approval,
  immutability, and supersession mirror IPLAN Version.
- An **IPLAN Chain Record** (`iplan-chain-record`) is the mutable registry pointer,
  mirroring IPLAN Record: `chain_id`, `current_version_id`, `latest_version_id`,
  `status`, `lifecycle`, `owner`, `record_version`. Its status vocabulary is the
  chain document's lifecycle states — which include `Completed` (chains complete;
  plans track completion in the execution plane) — plus the registry-only `Archived`.

The chain import path is the same Import Pipeline: a chain artifact produces a chain
Version record plus a chain Registry record (and a derived membership index,
introduced separately). Chain registry-record mutations use the **same** optimistic
`record_version` compare-and-set as the IPLAN registry, scoped per
`(org_id, project_id, chain_id)` — the one conflict rule shared by both registries.

## Import Pipeline

The Import Pipeline accepts IPLAN and IPLAN chain artifacts from AIDoc Flow,
manual upload, API clients, or connectors. Import must produce an import result
whether the artifact is accepted or rejected.

Import steps:

1. Normalize the payload to the canonical form.
2. Calculate the canonical hash.
3. Validate the declared schema.
4. Run semantic validation.
5. Create or reject the registry and version records.
6. Return an import result with errors, warnings, and validation report ID.

Accepted-with-warnings imports are allowed only when warnings are non-blocking
and the version remains unavailable for execution until approval rules pass.

## Validation

Validation has two layers.

Schema validation checks that the artifact matches the registered JSON schema.
Semantic validation checks whether the artifact can be operated safely by
Iplanic.

Semantic validation must check:

- duplicate IDs;
- unresolved references;
- placeholder fields;
- command-to-evidence coverage;
- file conflicts;
- chain graph integrity;
- unresolved work-order references;
- tier coverage for declared plans.

`EXEC-Ready` is derived from validation and readiness scoring. A plan cannot be
approved for execution when blocking findings remain.

## Lifecycle

The management lifecycle is append-only and event-driven.

```text
Imported -> Validated -> Review -> Approved -> Active -> Superseded
Review -> Rejected
Imported -> Abandoned
Validated -> Abandoned
Approved -> Superseded
```

`Active` is a **registry-record** state (`iplan-record.status`), not a version
status: it marks the approved version that is currently current. The
`Approved -> Active` transition is produced by the `activated` lifecycle event;
the immutable version status set is `Imported, Validated, Review, Approved,
Superseded, Rejected, Abandoned` (no `Active`). See `IPLAN-DEFINITIONS.md`
(Status Families: Management vs Registry record).

Each transition emits an IPLAN Lifecycle Event with the actor, reason,
canonical hash, policy result, source status, and target status.

## Approval Model

Approval is always bound to a canonical hash. If plan content changes after an
approval, the previous approval no longer applies to the new version.

Approval records must capture:

- decision;
- approver identity (`approved_by`);
- decision timestamp (`approved_at`);
- approved hash;
- policy result;
- exceptions.

Approval can be granted only for versions that pass schema validation and have
no blocking semantic or readiness findings.

Identifier and status definitions are centralized in `IPLAN-DEFINITIONS.md`.

## Comparison

IPLAN Comparison records explain what changed between two plan versions, chain
versions, or document artifacts. Comparisons are required before approval when a
new version supersedes an approved version.

The comparison contract must report:

- base and target references with canonical hashes;
- changed sections;
- change severity;
- approval impact;
- execution impact;
- affected steps, work orders, and files;
- rerun scope.

Breaking changes require review. Changes to executor work, commands, evidence,
scope, policy, or chain order usually require new approval and may require
partial or full rerun.

## Management API

The management API should expose plan operations separately from execution-run
operations.

Recommended endpoints:

- `POST /projects/{project_id}/iplans/import`
- `GET /projects/{project_id}/iplans`
- `GET /iplans/{iplan_id}`
- `GET /iplans/{iplan_id}/versions`
- `GET /iplans/{iplan_id}/versions/{plan_version_id}`
- `POST /iplans/{iplan_id}/versions/{plan_version_id}/validate`
- `POST /iplans/{iplan_id}/versions/{plan_version_id}/submit-review`
- `POST /iplans/{iplan_id}/versions/{plan_version_id}/approve`
- `POST /iplans/{iplan_id}/versions/{plan_version_id}/reject`
- `POST /iplans/{iplan_id}/versions/{plan_version_id}/compare`
- `POST /iplan-chains/import`
- `POST /iplan-chains/{chain_id}/compare`

API responses should return stable IDs for import results, validation reports,
version records, lifecycle events, and comparison records so callers can build
auditable workflows without scraping logs.
