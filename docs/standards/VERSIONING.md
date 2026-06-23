# Schema Versioning & Migration

## Purpose

This document defines how the IPLAN schema set is versioned and how consumers
(including remote executors such as iplan-runner, which pin vendored schema mirrors)
manage compatibility and migration.

## Version scheme

The schema set is versioned **together** as one unit by `schema_version`:

```text
MAJOR.MINOR[-draft]
```

- `MAJOR` and `MINOR` are non-negative integers.
- The optional `-draft` suffix marks a pre-stable version.
- Current value: `1.3-draft`.

Document-level artifacts carry `schema_version` in their `metadata`
(`iplan-document`, `iplan-chain`, `iplan-execution-record`,
`iplan-evidence-bundle`, `tmp-iplan`). The field is validated against
`^[0-9]+\.[0-9]+(-draft)?$`. Individual schemas do not version themselves; the set
version is the single source of truth.

## Compatibility

| Bump | Meaning | Examples |
| --- | --- | --- |
| `MINOR` | Additive, backward-compatible | new optional field; appended enum value; new `description`; relaxed constraint |
| `MAJOR` | Breaking | removed or renamed required field; removed enum value; tightened constraint; changed semantics of an existing field |

A consumer pinned to `MAJOR.m` accepts any `MINOR >= m` within the same `MAJOR`
(additive changes only). A consumer must not accept a different `MAJOR` without an
explicit migration.

## `-draft` semantics

A `MAJOR.MINOR-draft` version is pre-stable: it **may** introduce breaking changes
between minor versions without a `MAJOR` bump. Consumers pinning a `-draft` version
must expect to re-pin on each minor change. The `-draft` suffix is removed when the
set is declared stable.

## Migration

- A `MINOR` bump requires no consumer action (additive only).
- A `MAJOR` bump requires a **migration note** added to this document describing
  the breaking change, the affected schemas, and the field-by-field upgrade steps.
- Mirror-pinning consumers (iplan-runner vendored mirrors) pin a specific `MAJOR.MINOR` and
  upgrade deliberately after reading the migration note.

## Migration notes

### `1.2-draft` → `1.3-draft` — `executor_id` hash form (D-0031)

**Breaking** (a tightened constraint). `executor_id` changes from a free
`string (minLength 1)` to the self-certifying hash form
`^exec:[a-z2-7]{16,}$` (`exec:<base32(sha256(...))>`).

- **Affected schemas (5):** `artifact`, `execution-event`, `executor-registration`,
  `task`, `iplan-execution-record` (the last at `tasks[].executor_id` — nullable,
  `null` still valid — `executor_assignments[].executor_id`, and
  `events[].executor_id`).
- **Upgrade step:** rewrite every `executor_id` to the `exec:` hash form. A
  trusted/first-party executor's `executor_id` is `exec:<base32(sha256(public_key))>`
  (it must equal `sha256(public_key)` for self-certification, §2.2); a sandbox
  executor's is `exec:<base32(sha256(registration claim))>`.
- **Mirror-pinning consumers (iplan-runner):** re-pin the vendored
  `execution-event`/`executor-registration` mirrors to this commit, tighten the
  mirror copies, and rewrite emitted + test `executor_id`s to the `exec:` form.

This is the first breaking change in the `-draft` series; per the `-draft`
semantics above it rides a `MINOR` bump (no `MAJOR`), and consumers re-pin.
