# IPLAN Standard

The open specification for **IPLAN** — **Intent, Plan, Lineage, Assurance, Navigation** — the
plan-centered contract for AI software delivery: the schemas, canonicalization, and the
A2A / MCP / signed-log-ingestion contracts that lets any control plane, executor, or connector
interoperate.

This repository is the **neutral, versioned source of truth** for the standard. It is consumed by:

- **[`iplan-runner`](https://github.com/vladm3105/aidoc-flow-iplan-runner)** — the OSS remote execution
  worker (an executor), and
- **iplanic** — the hosted execution control plane,

and by any third-party executor, connector, or control surface that speaks the IPLAN contracts.

## What's here

| Path | What |
| --- | --- |
| `schemas/` | The normative JSON Schemas (17) — `iplan-document`, `iplan-chain`, `task`, `execution-event`, `executor-registration`, `iplan-comparison`, `iplan-validation-report`, `iplan-evidence-bundle`, the record/version schemas, … |
| `docs/standards/` | The prose spec — `IPLAN-STANDARD`, `IPLAN-DEFINITIONS`, `IPLAN-CANONICALIZATION`, `IPLAN-MANAGEMENT`, `VERSIONING`, and `templates/` |
| `iplan_canonical/` | The **reference implementation** of IPLAN canonical JSON (RFC 8785 / JCS) + the signing payload + signature verify (ed25519 / hmac-sha256) — the normative algorithm both sides sign and verify with |
| `tests/contract/` | The **conformance suite** — every schema validates its template/fixtures, the canonicalization is pinned by golden vectors, and the scope-check / status-projection contracts are replayed |

## Conformance

```bash
PYTHONPATH=. python -m unittest discover -s tests/contract
```

A consumer conforms if its inputs/outputs validate against `schemas/` and its canonical hashing +
signatures match the `iplan_canonical` reference (the golden vectors in
`tests/contract/canonicalization/vectors/`).

## Versioning

The standard ships **independently semver-tagged** — `iplan/vX.Y.Z`. Consumers **pin** a tag rather than
vendoring a copy. Backward-compatible schema/field additions bump the minor; a breaking change bumps the
major. See [`docs/standards/VERSIONING.md`](docs/standards/VERSIONING.md).

## Status

`iplan/v0.1.0` — initial extraction of the stable schema + canonicalization + conformance surface. The
transport/ecosystem prose specs (the A2A/MCP narrative) are being curated for a neutral public release and
will land in a subsequent minor; the machine-readable transport contracts (`task`, `execution-event`,
`executor-registration` schemas) are already here.

## License

[MIT](LICENSE).
