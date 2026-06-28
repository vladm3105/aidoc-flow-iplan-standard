# Changelog

All notable changes to the IPLAN standard are recorded here. The standard ships
independently semver-tagged (`iplan/vX.Y.Z`); consumers pin a tag.

## [Unreleased]

Additive schema field + L1 conformance vectors (no breaking change). Part of the
**IPLAN Assurance** ratification gate (see `docs/standards/IPLAN-ASSURANCE.md`).

### Added

- **`iplan-document.intake_control.provenance`** (optional) — the **L1 initiator
  provenance envelope** (`{ initiator_key_id, algorithm, value, signed_at }`): a
  detached signature over the canonical IPLAN with `intake_control` excluded.
  Optional/additive — L0 documents omit it (backward-compatible; `schema_version`
  unchanged, consistent with the `dispatch_token_id` precedent). The verifier
  resolves `initiator_key_id` via a configured initiator keyring (baseline: a signed
  allowlist; §9 R1).
- **L1 signed-plan golden vectors** — `tests/contract/provenance/vectors/`
  (`accept_ed25519`, `accept_hmac`, `reject_tampered`) with real signatures from the
  `iplan_canonical` reference signer, pinned by `test_provenance.py` (schema-validity
  + signature verification + L0-without-envelope still valid).
- **`IPLAN-ASSURANCE.md` §9 resolved** — the three open questions ratified (R1 inline
  allowlist baseline / IdP-ready; R2 witness OPTIONAL / REQUIRED-ready; R3 SLSA v1
  predicate).

Remaining for L1: ratify via the framework CHG / GATE-SPEC, then consumers re-pin.

## [0.3.0] — 2026-06-23

Additive schema field (no breaking change; consumers may pin `iplan/v0.3.0`).

### Added

- **`executor-registration.dispatch_token_id`** (optional) — a handle for the bearer
  token a management plane sends as `Authorization` on task dispatch, resolved
  out-of-band (env/vault) so the raw token is never stored in the registration.
  Mirrors the existing `log_ingest_key_id` handle pattern; absent ⇒ no header
  (backward-compatible). Enables authenticated dispatch to a receiver that mandates
  a bearer.

## [0.2.0] — 2026-06-23

Adds the curated, vendor-neutral prose for the **ecosystem roles**, the **transport
& integration** contract, and the **plan-ingestion adapter** pattern — the design
notes held back from `0.1.0` for a curation pass. Additive (no schema or
`iplan_canonical` change); consumers may pin `iplan/v0.2.0` to reference them.

### Added

- **`docs/standards/IPLAN-ECOSYSTEM.md`** — the **author → manage → execute** role
  separation and the principle that the IPLAN standard is an intentionally-richer
  **hub that does not converge** to the source authoring formats it ingests
  (bridged by ingestion adapters; the executor edge consumes a dispatched task
  payload + pinned mirror).
- **`docs/standards/TRANSPORT-INTEGRATION.md`** — the two integration edges (import;
  execute), per-surface A2A/MCP channel mapping, executor onboarding + key
  enrollment, delivery/failure/retry + the ingestion rejection response, the
  artifact request→PUT→confirm→verify byte path, idempotency-as-contract, wire
  security (TLS/replay/scope), and the broker-ready scale option.
- **`docs/standards/PLAN-INGESTION-ADAPTERS.md`** — the per-source adapter contract
  (detection, mapping, enrichment/defaults, provenance, readiness gating, loss
  report) that converts any authoring or AI-agent plan into the IPLAN standard.

### Notes

- Curated for neutral publication: the old engineering codename, internal status
  banners, cross-references to unpublished internal docs, and internal decision/
  backlog identifiers were removed or restated as the standard's own positions.
- 63 conformance tests unchanged (the additions are prose only).

## [0.1.0] — 2026-06-23

Initial extraction of the IPLAN standard into its own neutral, versioned repo
(previously authored inside iplanic).

### Added

- **Schemas** (`schemas/`, 17) — the normative JSON Schemas: `iplan-document`,
  `iplan-chain`, `task`, `execution-event`, `executor-registration`,
  `iplan-comparison`, `iplan-validation-report`, `iplan-evidence-bundle`,
  `iplan-import-result`, `iplan-lifecycle-event`, the record/version schemas, and
  `tmp-iplan`.
- **Canonicalization reference** (`iplan_canonical/`) — RFC 8785 / JCS canonical
  JSON, the signing payload, and signature verify (ed25519 / hmac-sha256).
- **Conformance suite** (`tests/contract/`, 63 tests) — schema/template/fixture
  validation, canonicalization golden vectors, scope-check, and status-projection
  contracts; runnable standalone.
- **Spec docs** (`docs/standards/`) — `IPLAN-STANDARD`, `IPLAN-DEFINITIONS`,
  `IPLAN-CANONICALIZATION`, `IPLAN-MANAGEMENT`,
  `VERSIONING`, and `templates/`.
- MIT license; conformance CI (Python 3.11 / 3.12 on `ubuntu-latest`).

### Notes

- The transport/ecosystem prose specs (the A2A/MCP narrative + plan-ingestion-adapters) are being curated
  for a neutral public release and will land in a later minor; the
  machine-readable transport contracts (`task`, `execution-event`,
  `executor-registration`) are already included.
- The `IOPS` codename (the former name of `iplan-runner`) was normalized to
  `iplan-runner` throughout the moved docs.
