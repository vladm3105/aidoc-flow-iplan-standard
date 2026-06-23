# IPLAN Canonicalization

> Normative definition of `iplan-canonical-json` — the canonicalization algorithm
> every IPLANIC `canonical_hash` and signature is computed over. Any
> implementation (IPLANIC, iplan-runner, an ingestion adapter) that follows this document
> reproduces byte-identical canonical forms, hashes, and signatures.

## 1. Two-part model

A `canonical_hash` is produced in two steps:

1. **Canonicalize** the JSON value with `iplan-canonical-json` → a deterministic
   byte string.
2. **Hash** those bytes with SHA-256.

```text
canonical_hash.value = lowercasehex( sha256( iplan-canonical-json(value) ) )
canonical_hash.algorithm = "sha256"          # the hash function
canonicalization.algorithm = "iplan-canonical-json"   # the serialization (this doc)
canonicalization.version   = "1.0"
```

The schema field `canonical_hash.algorithm: "sha256"` names the **hash**; the
`canonicalization` block (`iplan-version.immutability.canonicalization`) names the
**serialization** and pins its version. They are different layers and both are
required to reproduce a hash.

## 2. `iplan-canonical-json` v1.0

`iplan-canonical-json` **v1.0** is **RFC 8785 JSON Canonicalization Scheme (JCS)**
applied to a UTF-8 JSON value, with one IPLANIC pre-processing rule (§3).

JCS (RFC 8785) fixes every serialization degree of freedom:

- **Object member order** — lexicographic by UTF-16 code unit of the member name.
- **Whitespace** — none (no insignificant whitespace between tokens).
- **Strings** — minimal escaping; `\uXXXX` only where RFC 8785 requires; UTF-8 output.
- **Numbers** — ECMAScript `Number.prototype.toString` / shortest round-trip form.
- **Literals** — `true`, `false`, `null` verbatim.

The output is a UTF-8 byte string; the hash is computed over those bytes.

> **Implementation:** use a conformant RFC 8785 library
> (reference impl uses the `rfc8785` package). Do **not** hand-roll number
> canonicalization — the ECMAScript number form is the error-prone part.

## 3. Absent-vs-null normalization (signed payloads)

JCS canonicalizes whatever value it is given, but it does **not** decide whether an
optional field that is *absent* is the same as one explicitly set to `null`. Two
producers emitting the semantically-identical event — one omitting an optional
field, the other sending it as `null` — would otherwise yield different bytes and
different hashes.

**Rule (v1.0):** before canonicalizing a value for hashing or signing, **recursively
drop every object member whose value is `null`.** After this normalization, "absent"
and "explicit `null`" collapse to the same canonical form.

This applies to nullable optional fields such as `protocol_plan_id` and
`protocol_agent_id` on `execution-event` (`payload` is object-or-absent, never
`null`, so the rule is a no-op for it).

## 4. Version semantics

`canonicalization.version` (string, e.g. `"1.0"`) pins the algorithm revision. A
change that alters output bytes for any input (e.g. a different null rule or a JCS
revision) **MUST** bump this version. A hash is only reproducible against the
version it was produced under; verifiers select the algorithm by the recorded
version. v1.0 is defined by this document.

## 5. Worked example

Input JSON (member order as written):

```json
{"event_type": "task.completed", "status": "succeeded", "org_id": "org-1", "task_id": "T-9"}
```

`iplan-canonical-json` output (UTF-8 bytes shown as text):

```text
{"event_type":"task.completed","org_id":"org-1","status":"succeeded","task_id":"T-9"}
```

`canonical_hash`:

```text
sha256 = 43b7af813374fd5b49224d377825b2af8f887d837d76b5d21c8194274dc2900c
```

(Members reordered lexicographically; whitespace removed; SHA-256 over the
canonical bytes, lowercase hex.)

## 6. Per-surface coverage

Which fields each hash/signature covers is defined in §"Signature & hash coverage"
of [`IPLAN-DEFINITIONS.md`](IPLAN-DEFINITIONS.md) and summarized here once specified
(see `PLAN-001` Task 4). In brief: `execution-event` signs the event minus
`{signature, received_at}` (after §3 normalization); the evidence `seal` hash covers
the canonical payload plus the evidence manifest; `iplan-version` / chain-version
cover the imported content; recorded-hash carriers carry a referenced version's
hash rather than recomputing one.

## 7. References

- RFC 8785 — JSON Canonicalization Scheme (JCS).
- `schemas/iplan-version.schema.json` — `immutability.canonicalization` (`algorithm`,
  `version`) and `canonical_hash` (`sha256`, hex64).
- `docs/standards/IPLAN-MANAGEMENT.md` — import pipeline (normalize → canonical hash).
- `docs/DECISIONS.md` — D-0021 (adopt RFC 8785 JCS).
