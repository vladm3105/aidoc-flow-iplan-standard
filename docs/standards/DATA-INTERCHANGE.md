# Data & Log Interchange — MOVED to Interlog

> **Status:** Moved (2026-07-06, PLAN-002 PR-1/PR-4). This standard is no longer
> owned by `iplan-standard`.

The Data & Log Interchange standard — the `experience-event` envelope, the
event-kind registry, the tier taxonomy, conformance fixtures, and (under the
expanded charter) the private-logging + operational-monitoring standard — is now
**owned by Interlog** (`aidoc-flow-interlog`), the owner of the ecosystem's
horizontal logging concern.

- **Standard:** [`aidoc-flow-interlog` → `docs/standards/DATA-INTERCHANGE.md`](https://github.com/vladm3105/aidoc-flow-interlog/blob/main/docs/standards/DATA-INTERCHANGE.md)
- **Storage-independence decision:** [`docs/adr/ADR-0001`](https://github.com/vladm3105/aidoc-flow-interlog/blob/main/docs/adr/ADR-0001_exchange-storage-independent-of-execution-ledger.md)
- **Charter-expansion decision:** [`docs/adr/ADR-0002`](https://github.com/vladm3105/aidoc-flow-interlog/blob/main/docs/adr/ADR-0002_logging-hub-charter-expansion.md)

## What stays in `iplan-standard`

`iplan-standard` owns the IPLAN **domain shapes** that the interchange carries as
payloads — `execution-event` (`schemas/execution-event.schema.json`) and
`iplan-evidence-bundle` (`schemas/iplan-evidence-bundle.schema.json`). These
**comply with** the Interlog envelope (referenced by `payload_type`, never
`$ref`-ed by it) — see `docs/standards/IPLAN-ASSURANCE.md` §8. The dependency is
one-way: IPLAN domain shapes conform to the Interlog envelope; Interlog does not
depend on `iplan-standard` for its contract.

The full DRAFT history of this document before the move is preserved in this
repo's git history and in the Interlog copy linked above.
