# IPLAN Assurance (DRAFT / Proposed)

> **Status:** DRAFT — proposed, **non-normative**. Targets a future `iplan/v0.x`
> minor. Ratification follows aidoc-flow governance (CHG / GATE-SPEC in the
> framework repo); until ratified, nothing here is a conformance requirement.
> **Date:** 2026-06-27.

This document specifies how the **Assurance** and **Lineage** pillars of IPLAN
(**I**ntent, **P**lan, **L**ineage, **A**ssurance, **N**avigation) are expressed
on the wire, so that **any** control plane, executor, or connector can verify
*who authored a plan* and *what an executor actually did* — not merely exchange
data. It is the trust contract that lets independent parties interoperate.

## Design principle: verifiable transparency, **not** blockchain

A blockchain bundles three things: a **verifiable append-only log**, **decentralized
consensus**, and **token incentives**. IPLAN assurance takes only the **first**.
All required properties — tamper-evidence, provenance, non-equivocation,
proof-of-existence, third-party verifiability — come from standard cryptography
(hash chains, Merkle trees, digital signatures, transparency logs), not from
consensus or a coin. This is the same family of mechanisms used by Certificate
Transparency (RFC 6962), Sigstore, and the Go checksum database. It is **not** a
blockchain and requires no chain, node, gas, or token.

The one property deliberately **not** provided is censorship resistance against a
fully adversarial log operator and trustless multi-party *writes* — those require
real decentralization and are out of scope (see §7).

## 1. Assurance Levels (conformance tiers)

A consumer **declares** the assurance level it produces/accepts. Levels are
cumulative. This lets the standard span experimentation through regulated
deployment without forcing cryptographic machinery on simple adopters.

| Level | Name | Guarantee added | Primitive |
|------|------|-----------------|-----------|
| **L0** | Unsigned | Byte integrity of the received artifact only | `sha256(file_bytes)` checksum (already in intake) |
| **L1** | Signed initiator | **Provenance** — the IPLAN was authored by an identified, authorized initiator and is unaltered | Detached signature over canonical IPLAN; initiator trust anchor |
| **L2** | Transparency-logged | **Non-equivocation + third-party verifiability** — execution evidence is in a public append-only log no single operator can rewrite, verifiable without trusting that operator | Merkle log + Signed Tree Head + (optional) witness cosign + (optional) external anchor |

Guarantees per level:

| Property | L0 | L1 | L2 |
|---|----|----|----|
| Artifact byte integrity | ✓ | ✓ | ✓ |
| Author provenance / authorization | — | ✓ | ✓ |
| Tamper-evident execution evidence | chain only | chain + sig | chain + sig |
| Non-equivocation (operator can't show two histories) | — | — | ✓ |
| Proof-of-existence at time *T* | — | — | ✓ (with anchor) |
| Verifiable without trusting the control-plane operator | — | — | ✓ |

## 2. L1 — initiator provenance

The **initiator** is the party that authored/authorized the IPLAN for execution
(distinct from the *runtime actor* that executes it — that is the executor
identity, governed separately).

- **Signed payload:** the IPLAN canonicalized per `IPLAN-CANONICALIZATION.md`
  (RFC 8785 JCS, recursive drop-null) **with the whole `intake_control` excluded**,
  reusing the normative `iplan_canonical` reference signer (`ed25519` preferred;
  `hmac-sha256` for symmetric trust). Excluding `intake_control` (not just the
  signature value) keeps the signed surface the plan content, stable under any
  intake-time wrapper.
- **Envelope:** a detached signature at `intake_control.provenance` —
  `{ initiator_key_id, algorithm, value (lowercase hex), signed_at }` (an optional,
  additive field on `iplan-document`; L0 omits it). Excluded from its own signed
  payload per the rule above.
- **Trust anchor:** the verifier resolves `initiator_key_id` to a public key via a
  configured **initiator keyring**. The conformant L1 baseline is a **signed
  authorized-initiator allowlist** (§9 R1); `initiator_key_id` resolution is an
  interface, so a referenced identity provider / keyless signing (§5) is an additive
  source later, not a breaking change.
- **Verification (at intake, before execution):** (1) canonicalize, (2) verify the
  signature, (3) confirm the initiator is authorized for the target
  `client_id`/`project_id` scope. Failure ⇒ **refuse to execute**.

### Validation rules (proposed category `INTAKE.PROVENANCE`)

| Rule | Triggers when |
|------|---------------|
| `INTAKE.PROVENANCE_UNSIGNED` | L1+ required but no initiator signature present |
| `INTAKE.PROVENANCE_BAD_SIGNATURE` | signature does not verify over the canonical IPLAN |
| `INTAKE.PROVENANCE_UNKNOWN_INITIATOR` | `initiator_key_id` not resolvable in the keyring |
| `INTAKE.PROVENANCE_UNAUTHORIZED_INITIATOR` | initiator resolved but not authorized for the plan's scope |

These compose with — and do not replace — existing `INTAKE-001` rules. They are
pure/deterministic except for keyring lookup.

## 3. Evidence attestation (binds plan → execution)

The `iplan-evidence-bundle` SHOULD carry an **attestation** binding the
**signed plan** to the **signed execution ledger**, so the custody chain is
end-to-end checkable:

```text
signed IPLAN (initiator)  →  isolated execution  →  signed hash-chained ledger  →  evidence bundle
```

The attestation is an **in-toto Statement v1** with an **IPLAN-native
`predicateType`** (§9 R3): subject = the IPLAN canonical digest; predicate = the
execution ledger head and gate outcome. The in-toto Statement envelope gives
interoperable, already-credible tooling; the predicate is **not**
`slsa.dev/provenance/v1` because SLSA provenance's `subject` is the build *output*
(inputs live in `resolvedDependencies`), whereas here the `subject` is the IPLAN —
the *input/recipe* — so the SLSA predicate would subject-invert and misrepresent
conformance.

## 4. L2 — transparency log

For deployments where evidence must be verifiable **without trusting the
control-plane operator** (e.g. third-party executors, external auditors):

- **Log:** a Merkle tree over accepted `execution-event`s (anchored on the
  existing hash-chain `event_hash`).
- **Signed Tree Head (STH):** the operator periodically publishes a signed
  `{ tree_size, root_hash, timestamp }` commitment.
- **Proofs served on request:** Merkle **inclusion** proof (an event is in the
  log) and **consistency** proof (the log only appended, never rewrote).
- **Witness cosigning (OPTIONAL — §9 R2):** one or more independent parties cosign
  each STH. This makes operator equivocation publicly **detectable** — the
  non-blockchain substitute for consensus. Single-operator L2 is conformant; the
  design admits a future tier that makes witness cosigning REQUIRED without breaking
  L2 verifiers.
- **External anchor (optional):** the STH MAY be timestamped against an external
  append-only authority (e.g. RFC 3161 TSA or OpenTimestamps) for
  proof-of-existence at time *T*.

**Verifier procedure:** fetch the STH (+ any witness cosignatures), verify the
target event's inclusion proof against the STH root, and verify a consistency
proof between two STHs. Trust derives from the proofs, not from the operator.

## 5. Key management direction (informative)

Long-lived initiator keys are the primary operational failure mode. The
recommended direction is **keyless / identity-bound signing** (Sigstore-style):
bind the initiator signature to the deployment's existing workload/agent identity
(short-lived certs), so there are no long-lived keys to manage and "who authored
the plan" unifies with "who is acting" under one identity fabric. L1 does not
*require* this; the keyring model is the conformant baseline.

## 6. Conformance

Each level is pinned by golden vectors in `tests/contract/`: a signed-plan
fixture set (L1) and a log/STH/inclusion/consistency fixture set (L2). A consumer
states the maximum level it produces and the minimum it accepts; conformance is
checked per level, consistent with the existing canonicalization golden-vector
approach.

## 7. Out of scope

- **Consensus, nodes, tokens, gas** — not used; this is not a blockchain.
- **Economic / settlement layer** (escrow, incentives, payment on verified
  completion). The evidence bundle defined here is the **verifiable-completion
  primitive** such a system would build on, but the standard specifies
  *verification*, not economics. Any marketplace/settlement design is a separate,
  non-standard concern.
- **Censorship resistance against a fully adversarial operator** and **trustless
  multi-party writes** — require real decentralization; not provided.

## 8. Relationship to existing specs

Builds on `IPLAN-CANONICALIZATION.md` (the normative signer), and the
`execution-event`, `executor-registration`, and `iplan-evidence-bundle` schemas.
Adds the assurance-level vocabulary, the `intake_control` provenance envelope, the
`INTAKE.PROVENANCE` rules, and the L2 transparency-log contract.

**Interchange compliance (informative).** The `execution-event` and
`iplan-evidence-bundle` schemas are also carried, unchanged, as **payloads** of
the Interlog log-interchange envelope (`experience-event`), referenced by
`payload_type` — never `$ref`-ed by the envelope. The interchange contract is
owned by `aidoc-flow-interlog`
([`docs/standards/DATA-INTERCHANGE.md`](https://github.com/vladm3105/aidoc-flow-interlog/blob/main/docs/standards/DATA-INTERCHANGE.md));
these IPLAN domain shapes **conform to** that envelope but do not depend on it,
and it does not depend on them. Assurance verification always resolves against
the assurance path here, never against the interchange.

## 9. Resolved decisions (ratification gate)

Resolved 2026-06-28 to unblock L1 ratification. The stance throughout: ship the
**simple conformant baseline now, designed forward-compatible** so the stronger
option slots in additively (a MINOR bump), never a breaking rewrite.

- **R1 — L1 keyring (was: inline allowlist vs. referenced IdP).** The conformant
  L1 **baseline is the inline signed authorized-initiator allowlist**. The envelope
  and keyring resolution MUST be designed so a **referenced identity provider /
  keyless identity-bound signing** (§5, Sigstore-style) can be added later as an
  additive trust-anchor source — i.e. `initiator_key_id` resolution is an interface
  with the allowlist as one implementation, not the only one. No long-lived-key
  assumption is baked into the wire envelope.
- **R2 — L2 witness cosigning (was: OPTIONAL vs. REQUIRED).** Witness cosigning is
  **OPTIONAL** at L2; single-operator L2 is conformant. The STH/log design MUST
  admit **REQUIRED** witness cosigning as an additive top-tier policy (a future
  higher tier), so making it mandatory later does not break L2 verifiers.
- **R3 — attestation predicate (was: SLSA v1 vs. IPLAN-native). Resolved
  IPLAN-native (amended 2026-06-28).** The evidence attestation is an **in-toto
  Statement v1** with an **IPLAN-native `predicateType`** (subject = the IPLAN
  canonical digest; predicate = the execution ledger head + gate outcome). The
  in-toto Statement envelope keeps interoperable, credible tooling; the predicate is
  **not** `slsa.dev/provenance/v1` because SLSA provenance's `subject` is the build
  *output* while here it is the IPLAN (the *input/recipe*) — claiming the SLSA
  predicate would subject-invert. (Supersedes the earlier SLSA-v1 wording; matches
  the first conformant producer, iplanic A4 / D-0109.)

**Landed (this version):** the `intake_control.provenance` envelope is an additive
optional field on `iplan-document`, and the L1 signed-plan golden vectors live in
`tests/contract/provenance/vectors/` (`accept_ed25519`, `accept_hmac`,
`reject_tampered`) with `test_provenance.py` pinning schema-validity + signature
verification. **Remaining before ratification (governance, not open design):**
ratify L1 via the framework CHG / GATE-SPEC, then consumers (iplanic, iplan-runner)
re-pin and enforce. The keyless direction (§5) and the REQUIRED-witness tier remain
informative/future, not L1 conformance requirements.
