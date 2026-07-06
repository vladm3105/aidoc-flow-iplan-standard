# ADR-0001 — Exchange storage is independent of the execution ledger and the management-plane store

> **Status:** Accepted (2026-07-05, founder-confirmed). Scoped to the
> DATA-INTERCHANGE model (DRAFT); revisited automatically if that document
> fails ratification.
> **Relates to:** `docs/standards/DATA-INTERCHANGE.md` §3 (purpose
> separation), §5 (exchange models), §7.6 (storage and broker choice).

## Context

The ecosystem already has two mature record stores on the execution plane:

- The **executor ledger** (iplan-runner) — an append-only, hash-chained,
  isolation-scoped execution log. The chain is strictly sequential per
  scope: each event's `sequence` must equal `index + 1` and reference the
  single previous event's hash (`verify_chain`,
  `platforms/hermes/src/iplan_hermes/ledger/store.py`). A ledger binds to
  one source IPLAN by `id` + `version` + `checksum`, and its integrity is
  what the Gate's well-formedness veto verifies.
- The **management-plane store** (Iplanic) — the PostgreSQL-backed
  system-of-record that ingests ledger flushes (`sync`) and execution
  records.

The DATA-INTERCHANGE model (DRAFT) requires an append-only, replayable
store for exchange-tier `experience-event`s. The question examined here:
reuse one of the existing stores as that exchange store, or create
independent storage?

## Decision

**Independent storage.** The exchange store is its own artifact — the
exchange repo (git) in the C phase, a dedicated PostgreSQL append-only
event table in the B phase (DATA-INTERCHANGE §7.6). Neither the executor
ledger nor the management-plane store serves as the exchange store.

## Rationale

Reusing the **ledger** fails on five grounds:

1. **One chain means one writer.** The chain math assumes a single
   sequential history per scope. The exchange has N independent producers
   with no global order: funneling them through one chain-writer fabricates
   an ordering that does not exist; per-producer chains would no longer be
   "the ledger" but a new store borrowing its hash chain.
2. **Wrong identity model.** A ledger binds to an IPLAN
   `id`/`version`/`checksum`; most exchange events (decisions, review
   verdicts, CI outcomes) have no IPLAN to bind to.
3. **Proof-surface pollution.** The ledger is the assurance record; the
   Gate verifies its integrity as evidence. Mixing curated learning events
   into it burdens every verification with non-assurance content —
   DATA-INTERCHANGE §3 already contracts that the exchange references the
   assurance path and never replaces it; the reverse holds symmetrically.
4. **Tier inversion.** Full ledgers are private-tier by the interchange's
   own taxonomy (§2): they never leave the owning project. Making the
   ledger the exchange inverts the curation boundary that is the model's
   access-control line.
5. **Conflicting lifecycles.** Ledger retention is proof-driven; exchange
   retention is learning-driven (tier placement, steward waivers, §7.1).
   Two policies cannot govern one artifact.

Reusing the **management-plane store** fails on the same layering ground as
Model A (memory-plane-as-exchange) in §5 — coupling the interchange to a
single consumer/product — with an additional ground: the management plane is
deliberately optional; executors can run standalone/local-first without ever
contacting it (IPLAN-ECOSYSTEM.md), so producers in standalone deployments
could not publish.

## What IS reused

The independence is of the *artifact*, not the engineering:

1. **Content.** Execution-plane producers publish curated projections of
   ledger facts into the exchange as payloads (`execution-event`,
   `iplan-evidence-bundle`). The executor's existing `sync` flush to the
   management plane is the natural later hook for exchange emission.
2. **Machinery.** The exchange store adopts the ledger's append-only +
   hash-chain pattern and the `iplan_canonical/` signing reference — as
   *per-producer* chains matching exchange semantics. This is the concrete
   implementation path to exchange-scoped `L2` (transparency log,
   DATA-INTERCHANGE §4) if ever required.
3. **Infrastructure posture.** The management plane's PostgreSQL-adapter
   pattern validates the B-phase storage choice: same engine and
   operational skills, **separate database** — never a shared instance or
   schema.

## Consequences

- A third record store exists in the ecosystem (assurance ledger,
  management-plane store, exchange store), each with a single purpose;
  DATA-INTERCHANGE §3 is the map of which record answers which question.
- The exchange store's integrity mechanisms can evolve independently of
  Gate verification semantics.
- Execution-plane exchange emission is deferred until the projection hook
  lands in the executor's sync path; until then the execution plane
  publishes nothing (consistent with the first-producers sequencing in
  DATA-INTERCHANGE §6).
