# Changelog

All notable changes to the IPLAN standard are recorded here. The standard ships
independently semver-tagged (`iplan/vX.Y.Z`); consumers pin a tag.

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
