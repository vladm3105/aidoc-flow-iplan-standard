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
  (RFC 8785 JCS, recursive drop-null), reusing the normative `iplan_canonical`
  reference signer (`ed25519` preferred; `hmac-sha256` for symmetric trust).
- **Envelope:** a detached signature carried in `intake_control` —
  `{ initiator_key_id, algorithm, value (lowercase hex), signed_at }` — excluded
  from its own signed payload.
- **Trust anchor:** the verifier resolves `initiator_key_id` to a public key via a
  configured **initiator keyring** (an authorized-initiator allowlist). Single-admin
  deployments use a signed allowlist; see §5 for the keyless direction.
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

```
signed IPLAN (initiator)  →  isolated execution  →  signed hash-chained ledger  →  evidence bundle
```

The attestation format SHOULD follow the **in-toto / SLSA** provenance shape
(subject = the IPLAN canonical digest; predicate = the execution ledger head and
gate outcome). Aligning to that ecosystem gives interoperable, already-credible
tooling rather than a bespoke format.

## 4. L2 — transparency log

For deployments where evidence must be verifiable **without trusting the
control-plane operator** (e.g. third-party executors, external auditors):

- **Log:** a Merkle tree over accepted `execution-event`s (anchored on the
  existing hash-chain `event_hash`).
- **Signed Tree Head (STH):** the operator periodically publishes a signed
  `{ tree_size, root_hash, timestamp }` commitment.
- **Proofs served on request:** Merkle **inclusion** proof (an event is in the
  log) and **consistency** proof (the log only appended, never rewrote).
- **Witness cosigning (optional):** one or more independent parties cosign each
  STH. This makes operator equivocation publicly **detectable** — the
  non-blockchain substitute for consensus.
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

## 9. Open questions

- Keyring distribution/rotation format for L1 (inline allowlist vs. referenced
  identity provider).
- Whether L2 witness cosigning is OPTIONAL or REQUIRED at the top tier.
- Canonical attestation predicate fields for the evidence bundle (align to SLSA
  v1 predicate vs. a minimal IPLAN-native predicate).
