# Changelog

All notable changes to the IPLAN standard are recorded here. The standard ships
independently semver-tagged (`iplan/vX.Y.Z`); consumers pin a tag.

## [Unreleased]

Additive schema field + L1 conformance vectors (no breaking change), part of the
**IPLAN Assurance** ratification gate (see `docs/standards/IPLAN-ASSURANCE.md`).
The DRAFT **Data & Log Interchange** document + `ADR-0001` **moved out** to
`aidoc-flow-interlog` (below).

### Added — Wave 1 governance-tier adoption of aidoc-flow-ci canon (PLAN-002 §5.5) (2026-07-08)

Self-adopts the workspace-wide standards canon from `aidoc-flow-ci@ci/v1.6.0`
per PLAN-002 §5.5 Wave 1 (governance tier). Adds mechanical OPS-0069 audit-trail
enforcement + workspace-baseline governance surfaces. 9 file surfaces + this
CHANGELOG entry (atomic canon-adoption bundle per PLAN-002 §5.5 explicit
exemption to OPS-0061 Rule 1's ≤3-surface cap; same precedent as PR-U4 on
aidoc-flow-ci):

- **`scripts/pre_push_check.sh`** (NEW) — canon self-review script from
  `aidoc-flow-ci/install/templates/pre_push_check.sh` at `ci/v1.6.0`. Runs 5
  checks pre-push: markdownlint / yamllint / actionlint / shellcheck (all
  skipped-with-notice if absent) + OPS-0069 audit-trail phrase check
  (mandatory).
- **`.pre-commit-config.yaml`** (NEW) — canon fragment wiring the pre-push
  hook via `default_install_hook_types: [pre-commit, pre-push]`. Carries
  the `# CANON: aidoc-flow-ci pre_push_check` idempotency marker so future
  `install.sh` re-runs no-op.
- **`.github/CODEOWNERS`** (NEW) — canon shape per `REPO_STANDARDS.md` §7
  (single-owner phase; all patterns route to `@vladm3105`).
- **`.github/pull_request_template.md`** (NEW) — canon PR template per
  `REPO_STANDARDS.md` §8 (Summary + Files-touched Rule 1 self-check +
  Multi-agent self-review + Cross-refs + tier-guarded test plan).
- **`.github/dependabot.yml`** (NEW) — FULL canon per `REPO_STANDARDS.md`
  §6 (5 ecosystems; Dependabot silently skips ecosystems with no matching
  manifests).
- **`.gitignore`** (edit) — merged canon baseline lines per
  `REPO_STANDARDS.md` §10.1 (subset semantics; existing entries retained).
- **`.gitattributes`** (NEW) — canon baseline per `REPO_STANDARDS.md`
  §10.2.
- **`.github/workflows/audit-trail.yml`** (NEW) — consumer caller wiring
  the `audit-trail-check.yml` reusable at `@ci/v1.6.0`. Check-name renders
  as `call / verify`. Adds mechanical OPS-0069 audit-trail enforcement to
  every PR on this repo.
- **`.github/workflows/standards-drift.yml`** (NEW) — weekly `schedule:
  cron` job that fetches `sync/check-standards-drift.sh` from
  aidoc-flow-ci canon at runtime and runs it with `--tier governance`.
  Warning-only per canon §3.1b (script always exits 0).

**Server-side follow-up:** adding `call / verify` to branch-protection
`contexts` on `main` requires a founder-run `bash install/apply-standards.sh
--apply --repo vladm3105/aidoc-flow-iplan-standard --tier governance --ci-tag
ci/v1.6.0 --yes` per `REPO_STANDARDS.md` §14.3 (governance tier). F5
blast-radius; not in this PR.

**Origin:** `aidoc-flow-ci/plans/PLAN-002_workspace-standards-rollout.md`
§5.5 Wave 1 (governance tier). Sibling Wave 1 rollout: `aidoc-flow-framework`.

### Changed — Data & Log Interchange moved to Interlog (2026-07-06, interlog PLAN-002 PR-4)

- **`docs/standards/DATA-INTERCHANGE.md` and `docs/adr/ADR-0001`** are now
  **pointer stubs** — the interchange/logging standard and its
  storage-independence ADR are owned by `aidoc-flow-interlog`, which a
  founder-directed pivot made the owner of the ecosystem's horizontal logging
  concern (private logging + monitoring + learning; interlog `docs/adr/ADR-0002`).
  `iplan-standard` no longer defines the interchange contract.
- **`docs/standards/IPLAN-ASSURANCE.md` §8** — added an informative interchange-
  compliance note: `execution-event` / `iplan-evidence-bundle` are carried
  unchanged as Interlog-envelope *payloads* (by `payload_type`, never `$ref`),
  conforming to but not depending on the interchange contract. No schema change.

### Changed

- **`DATA-INTERCHANGE.md` §6/§7.4** — exchange reference-deployment repo named:
  `aidoc-flow-interlog`, project name **Interlog** (functional, brand deferred).
  Replaces the `aidoc-flow-exchange` placeholder.

### Added

- **`docs/standards/DATA-INTERCHANGE.md`** (DRAFT / Investigation, non-normative) —
  the ecosystem data & log interchange model: per-project log tiers
  (private/exchange/distilled), the `experience-event` envelope sketch (schema NOT
  yet landed; arrives as an additive change only at ratification, §7.7), exchange
  models (shared git-native exchange repo → dedicated exchange service,
  broker-neutral), roles (producer / consumer / memory plane / interchange
  steward), and open-question recommendations (retention, signing via an
  exchange-scoped assurance mapping, access control, naming, metrics, storage +
  broker choice — store+notify: pub/sub is a transport, not storage; the
  append-only store is the record).
- **`docs/adr/ADR-0001_exchange-storage-independent-of-execution-ledger.md`** —
  decision record: the exchange store is independent of the executor's
  assurance ledger (single-writer chain semantics, IPLAN-bound identity,
  proof-surface separation, private-tier boundary, conflicting lifecycles)
  and of the management-plane system-of-record (layering + the plane is
  optional); ledger patterns and curated content projections are reused,
  never the artifact.

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
  allowlist baseline / IdP-ready; R2 witness OPTIONAL / REQUIRED-ready; R3
  **IPLAN-native** in-toto predicate — amended 2026-06-28 from the initial SLSA-v1
  wording: SLSA provenance subject-inverts the IPLAN; matches iplanic A4 / D-0109).

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
