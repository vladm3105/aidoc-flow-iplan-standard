# Data & Log Interchange (DRAFT / Investigation)

> **Status:** DRAFT — investigation, **non-normative**. This document captures
> the interchange model under active evaluation. Nothing here is a conformance
> requirement; the target schema lands as an additive change to the schema set
> only after the model is confirmed. Ratification follows aidoc-flow governance
> (CHG / GATE-SPEC in the framework repo).
> **Date:** 2026-07-05.

This document specifies how the projects of an IPLAN ecosystem — plan
authoring, management, execution, memory, CI, operations — exchange **data and
logs** with each other so the ecosystem forms a continuous-improvement loop:

```text
plan formation → execution → published events → distilled knowledge → next plan formation
```

The IPLAN pipeline (`author → manage → execute`, IPLAN-ECOSYSTEM.md) already
contracts the *downward* flow of plans and the *assurance* flow of signed
evidence. This document adds the missing arc: an ecosystem-wide **learning
interchange** that any project can publish into and any project can learn from.

The normative body is written in **role** terms (producer, consumer, steward,
exchange, memory plane) so the contract stays deployment-neutral. §6 maps the
roles onto the aidoc-flow workspace as the **informative reference
deployment**.

## 1. Scope test and interchange governance

In scope: **plan-lifecycle learning interchange** — events *about* plan
formation, validation, review, execution, and their outcomes, exchanged for
continuous improvement.

Out of scope: a generic message bus for arbitrary application traffic.
Admission is governed, not self-served:

- The **event-kind registry** (§4) is gated by the **interchange steward**
  role (§5 Roles): new kinds enter only by steward approval against the scope
  test above.
- **Split trigger (countable):** if the steward rejects three or more kind
  proposals in a rolling quarter for being outside plan-lifecycle scope,
  recurring demand exists outside the scope — the interchange contract is
  then split into its own standard rather than widened here.

## 2. Log tiers (per project)

Every project keeps several layers of logs. Only one crosses project
boundaries:

| Tier | Name | Content | Visibility |
|------|------|---------|------------|
| **private** | Own full logs | Complete execution detail: full ledgers, raw CI run logs, session transcripts, debug output | Never leaves the owning project |
| **exchange** | Published events | Curated, envelope-conformant events the project chooses to publish (§4) | Ecosystem-wide via the exchange (§5) |
| **distilled** | Knowledge | Lessons extracted from exchange-tier history | The memory plane |

Naming note: the tiers are deliberately **named, not numbered**. `L0/L1/L2`
already denote assurance levels in this standard (IPLAN-ASSURANCE.md §1), and
`L0–L3` denote the reference memory plane's internal layers (knowledge base,
working memory, long-term memory, per-agent identity — see §8). A third
numbered scale would collide with both.

Publishing is an explicit, per-project **curation step** — a project promotes
selected facts from its private tier into the exchange tier. The exchange
never sees the private tier. This boundary is the access-control and
secrets-hygiene line: exchange-tier producers MUST NOT publish secrets,
credentials, or personal data, and producer CI SHOULD run secret detection
over emitted events.

## 3. Purpose separation (what this interchange is NOT)

Three families of records exist in the ecosystem; only the third is carried by
this interchange:

| Family | Purpose | Owner / contract | Carried here? |
|---|---|---|---|
| Assurance logs | Tamper-evident proof of what happened | Signed hash-chained ledger + evidence bundles (`execution-event`, `iplan-evidence-bundle` schemas; IPLAN-ASSURANCE.md) | No — referenced by origin, never replaced |
| Operational telemetry | Observe running systems | OpenTelemetry / SLOs (executor Monitor), CI run status | No |
| Learning / experience data | Continuous improvement | **This document** | Yes — the exchange tier |

The exchange is **never the system-of-record** for assurance. An
exchange-tier event may *reference* signed evidence (by origin), but
verification always resolves against the assurance path.

## 4. The envelope: `experience-event` (sketch)

One envelope for every published event; payloads stay **federated** — each
producer domain owns its payload schema and the envelope references it by
type. Target schema: `schemas/experience-event.schema.json` (not yet present;
lands only at ratification).

Not to be confused with `execution-event` (an execution-plane *payload* shape,
schemas/execution-event.schema.json): an `experience-event` is the exchange
envelope; an `execution-event` is one thing it can carry.

```json
{
  "event_id": "uuid — producer-generated; THE dedup key at the exchange tier",
  "occurred_at": "RFC 3339 timestamp",
  "source": {
    "project": "free-form string — validated against the deployment's producer registry, not a schema enum",
    "producer": "free-form component id, e.g. 'review', 'gate', 'session'"
  },
  "kind": "registry-governed taxonomy, e.g. plan.authored, review.verdict, execution.completed, gate.failed, decision.recorded, lesson.proposed",
  "origin": {
    "repo": "owner/name — REQUIRED",
    "commit": "SHA (optional)",
    "pr": "number (optional)",
    "plan_id": "IPLAN id (optional)",
    "run_id": "execution run id (optional)"
  },
  "assurance_level": "L0 | L1 | L2 — exchange-scoped guarantees, see mapping below",
  "visibility": "org | public",
  "payload_type": "URI or registered id, e.g. 'iplanic:execution-event', 'review:verdict'",
  "payload": { "…domain-owned…" }
}
```

Design rules:

- **Origin is mandatory and typed.** `origin.repo` plus at least one typed
  reference (`commit | pr | plan_id | run_id`; enforced via `anyOf` at schema
  landing). `commit`/`pr` MUST resolve within the deployment's code hosting;
  `plan_id`/`run_id` resolve against the management plane where deployed —
  producers SHOULD prefer a resolvable `commit`/`pr` alongside plane-local
  ids so distilled lessons remain traceable without the management plane.
  (The field is named `origin`, not `provenance`, to avoid collision with the
  assurance standard's `intake_control.provenance` signature envelope.)
- **Payloads are reused, not reinvented.** The execution plane publishes its
  existing contracted shapes as payloads: `execution-event`
  (schemas/execution-event.schema.json) and `iplan-evidence-bundle`
  (schemas/iplan-evidence-bundle.schema.json). Producers never translate
  their facts into a foreign vocabulary.
- **One dedup key at the exchange tier.** Consumers dedup on `event_id`. Keys
  inside payloads (e.g. `execution-event.idempotency_key`) are payload-internal
  and do not govern exchange-tier dedup. This adapts the ship-time idempotency
  pattern of TRANSPORT-INTEGRATION.md §6 to the exchange surface.
- **Envelope `kind` and payload-internal type fields are independent
  taxonomies.** `kind` is the exchange-tier classification; a payload's own
  `event_type` (etc.) is payload-internal. Any mapping is registered per
  `payload_type`; no cross-field consistency is required by the envelope.
- **The kind taxonomy is registry-governed** (§1). New kinds are additive;
  renames are breaking (VERSIONING.md rules apply once the schema lands).

**Assurance-level mapping (exchange-scoped).** The envelope reuses the
IPLAN-ASSURANCE.md §1 level *vocabulary* by analogy, but the attachment point
(a per-event field, not a declared conformance tier) and the guarantees
differ; the exchange-scoped meanings are:

| Level | Exchange-tier guarantee | Primitive |
|---|---|---|
| `L0` | Byte integrity of the event as stored/carried | Content hash of the carrying medium (e.g. git object hashes); weaker than assurance-L0 intake checksums — history rewrite is possible on the medium |
| `L1` | Producer authenticity — the event was published by an identified producer and is unaltered | Detached signature over canonical JSON (`iplan_canonical/` reference implementation); NOT the assurance-L1 initiator-authorization semantics |
| `L2` | Non-equivocation of the exchange history | Transparency log over the exchange store; machinery not yet specified for the exchange tier |

## 5. Exchange models considered

| Model | Shape | Assessment |
|---|---|---|
| **A — Memory plane as exchange** | Producers write directly into the memory plane's ingestion API | Rejected: couples transport to one consumer; a second consumer (dashboards, compliance, analytics) would have to read through the memory plane; the reference memory plane has no ingestion API today |
| **B — Dedicated exchange service** | ingest + store + query/subscribe API speaking the envelope | **Target.** Correct layering; justified once event volume and consumer count require a running service |
| **C — Shared exchange repo (git-native, no runtime)** | All producers commit envelope events into ONE dedicated git repository; consumers pull it | **Start.** Zero services; single point of discovery; git history is the cursor and the ordered record |
| Federated per-producer publishing | Each producer publishes events in its own repo; consumers poll N repos | Rejected: consumers must discover and cursor N producers; completeness is unverifiable |
| Code-hosting native eventing (webhooks / repository dispatch) | Push notifications from the hosting platform | Rejected as the record: delivery is ephemeral, there is no durable queryable store; MAY complement C/B as a notification trigger |
| Execution ledger / management-plane store as exchange | Reuse the executor's assurance ledger or the management plane's system-of-record as the exchange store | Rejected: the ledger's hash chain is single-writer and IPLAN-bound, mixing learning events pollutes the proof surface, and full ledgers are private-tier (§2); the management plane is optional (executors are local-first), so standalone producers could not publish. Patterns and content are reused, never the artifact — see `docs/adr/ADR-0001_exchange-storage-independent-of-execution-ledger.md` |

**Direction (investigation): B as target, C as the start, one repo housing
both.** This follows the standard's governing principle — *contract above
transport* (TRANSPORT-INTEGRATION.md §1) — and its broker precedent: design
broker-ready, ship on the simple transport first, add the heavier transport
at scale with no schema change (TRANSPORT-INTEGRATION.md §8).

**Minimal C contract** (what makes C a specified transport):

- **Layout convention:** `events/<project>/<YYYY-MM>/<event_id>.json` (or
  batched JSONL per period) in the exchange repo.
- **Discovery:** the exchange repo itself — one clone, all producers.
- **Cursor:** consumer-recorded last-read commit; git history is the ordered,
  append-only read surface. Ordering guarantee is per-producer commit order
  only.
- **Admission:** producer CI validates envelope conformance + secret
  detection before commit; non-conformant events are rejected at PR/push
  time.
- **Backfill at B cutover:** the service imports the repo history it already
  co-locates with — pre-service events remain queryable.

**Migration statement:** C → B involves **no schema migration** — the
envelope is identical — but consumer *transport bindings* are rewritten (git
pull + commit-cursor → service query/subscribe). Producers switch from
commit-to-repo to publish-to-API. The claim is envelope stability, not zero
integration work.

**B architecture: store + notify.** The exchange service is two layers, of
which only the first is required — and only the first is the record:

- **The store (normative):** an append-only, replayable record of every
  admitted envelope event. A consumer that subscribes late — months after
  events were published — MUST be able to read the full history from the
  beginning. This is the property the interchange exists for; the store is
  the exchange.
- **The notify layer (optional):** pub/sub delivery that pushes new events to
  live subscribers so they do not poll. **Pub/sub is a transport, not
  storage**: managed pub/sub services bound message retention to a window of
  days, so a late subscriber cannot rely on the broker for history. Even
  where a broker retains longer (e.g. a log-based broker with extended
  retention), the design stance is unchanged: the broker is never the
  record. A deployment that used pub/sub *as* the exchange would silently
  violate the late-consumer property above.

Admission order is store-first: an event is admitted when durably written to
the store; notification follows. A consumer must be able to reconcile
against the store regardless of notification delivery.

**B implementation options.** The service contract is broker-neutral, per the
same §8 precedent (a transactional-outbox store serves the no-broker
deployment; a broker is added at scale). For the notify layer, managed cloud
pub/sub — GCP Pub/Sub, Azure Service Bus / Event Grid — or self-hosted
NATS/Kafka are all admissible; the broker family is already anticipated by
TRANSPORT-INTEGRATION.md §8 (NATS / Kafka / Pub-Sub). The broker choice is
deferred to the B phase; the storage recommendation is in §7.6.

### Roles

- **The standard (this repo)** — owns the documentation and contracts: this
  document, the `experience-event` schema, the kind-registry rules,
  conformance fixtures. No runtime code.
- **The exchange repo** — a separate implementation repo: the C-phase event
  store, publisher/consumer reference libraries, and later the B-phase
  service. References this standard; never redefines it.
- **The memory plane** — a *subscriber*. Consumes exchange-tier events, owns
  the distilled tier (reflection/consolidation). It is not the exchange.
- **Producers** — every project, via its own curation policy (§2).
- **The interchange steward** — a second management layer, distinct from
  execution management (the IPLAN control plane manages plan execution; the
  steward manages the learning loop): gates the kind registry (§1), approves
  producer curation policies, **monitors the loop** (runs the reader that
  watches exchange-tier flow, flags stalled producers and unconsumed events),
  and owns the split trigger.

## 6. Reference deployment (informative — aidoc-flow workspace)

Non-normative mapping of roles to the aidoc-flow workspace; removed or moved
to deployment docs at ratification.

| Role | Workspace assignment |
|---|---|
| Standard | `iplan-standard` (this repo) |
| Exchange repo | `aidoc-flow-exchange` (to be created; naming §7.4) |
| Memory plane | `engramory` (its `docs/MEMORY_DESIGN.md` defines the distilled tier internally) |
| First producers | `aidoc-flow-operations` (decisions, handoffs, review verdicts — the author-side multi-agent review standard already emits a structured verdict shape) and `aidoc-flow-ci` (`ai-review/verdict.schema.json` — emission automatable in-workflow) |
| Later producers | `iplanic` / `iplan-runner` (execution plane; Iplanic's built-in workers already include connector sync), `framework` (authoring outcomes) |
| Interchange steward | `aidoc-flow-operations` — the operations AI team is both a producer and the loop's monitoring/management layer |

**Minimal viability condition** (before ratification blesses the model): the
reference memory plane is at project-initiation phase and is not yet a
running consumer. The loop must not launch as producers-without-tooling
feeding a consumer-that-does-not-exist. The first slice is therefore:
automated in-workflow emission from `aidoc-flow-ci` (the one producer with a
natural forcing function) plus the steward's scripted reader — proving
publish → store → read end-to-end before any service or memory-plane
integration is built.

## 7. Open questions and working recommendations

Recommendations recorded for ratification review; none are locked.

### 7.1 Retention

**Recommendation:** the exchange tier is append-only and the record retains
full history — the late-consumer property (§5) requires it. During the
investigation/MVP phase everything is retained as-is (volume is small). When
the exchange-service phase begins, per-kind retention decisions govern
**tier placement** — which events stay in the hot store versus move to the
archival tier (§7.6) — not whether history exists; the full record remains
readable across tiers. Deleting a kind's history is possible only by an
explicit, steward-approved waiver of the late-consumer property for that
kind, recorded in the kind registry. The assurance path (§3) remains the
durable proof regardless — the exchange record serves learning, not
compliance.

### 7.2 Signing

**Recommendation:** no new signing scheme; use the exchange-scoped
assurance-level mapping (§4). MVP: `L0`. Execution-plane payloads retain
their existing signatures regardless of envelope level. Producers move to
`L1` (detached signature over canonical JSON, `iplan_canonical/` reference
implementation) when the exchange-service phase begins or when events cross
an organizational trust boundary, whichever is first.

### 7.3 Access control

**Recommendation:** single-organization deployment ⇒ exchange content is
org-internal; every event carries `visibility: org | public` from day one
(low cost now, enforced later). Publishing is opt-in per project via its
curation step (§2); consumers read all org-visible events. Per-project ACLs
are deferred until a multi-tenant or external-consumer scenario exists.

### 7.4 Exchange repo naming

**Recommendation:** `aidoc-flow-exchange`. It matches this document's
vocabulary (exchange tier, interchange) and stays truthful at both phases —
"bus"/"broker" names would over-promise delivery semantics the C-phase
transport does not provide. ("Hub" is avoided: IPLAN-ECOSYSTEM.md already
uses *hub* for the management-plane standard itself.)

### 7.5 Improvement metrics (loop verification)

**Recommendation:** define one measurable signal per plane so "continuous
improvement" is testable: execution plane — predicted readiness
(`exec_ready_score`) vs. actual gate outcome over time; operations — repeat
findings rate (same lesson re-learned) and reviewer findings per PR trend.
Metric definitions belong to the consuming analytics, not this contract; the
contract only guarantees the events needed to compute them. Metrics are
computable only after the §6 minimal viability condition is met (that
condition moves to deployment docs together with §6 at ratification).

### 7.6 Storage and broker choice (B phase)

**Storage recommendation (the record, §5 store+notify):**

- **C phase:** the exchange repo itself — git already is an append-only,
  replayable, content-hashed store; no additional storage is stood up.
- **B phase primary store:** an append-only event table in **PostgreSQL**.
  The transport standard already establishes PostgreSQL as its no-broker
  baseline (transactional outbox, TRANSPORT-INTEGRATION.md §8); the exchange
  adapts that pattern with one deliberate divergence — the event table is
  the permanent record, not a pruned relay staging table. Store-first
  admission (§5) follows when the event row and the notification intent
  commit in one transaction and a relay publishes after commit.
- **Archival / analytics tier (optional):** object storage (e.g. GCS or
  Azure Blob) for cold history, and a columnar warehouse for metric queries
  (§7.5). On managed clouds this tier can be fed directly by the notify
  layer (e.g. broker export/capture subscriptions) rather than by custom
  glue — informative, not contracted.

**Broker recommendation (the notify layer only):** defer the provider. The
envelope and service contract are broker-neutral (§5); GCP Pub/Sub and Azure
Service Bus / Event Grid are both admissible, and the reference memory
plane's portability principle (self-hosted dev → GCP or Azure as an adapter
swap) suggests the same posture: choose per deployment at the B phase,
encode nothing provider-specific in the contract. Whatever the choice, the
broker is never the record — retention windows on managed pub/sub are
measured in days, and the late-consumer property (§5) holds regardless of
provider choice.

### 7.7 Versioning axis at schema landing

VERSIONING.md permits an additive MINOR (`1.3-draft` → `1.4-draft`), but the
repo's demonstrated practice for additive changes has been to ride the
`iplan/vX.Y.Z` release tag without bumping `schema_version` (the
`dispatch_token_id` precedent). **Recommendation:** the new schema file rides
a repo minor release; whether `schema_version` bumps is recorded as an
explicit decision at landing. Whether `experience-event` carries
`schema_version` in its own metadata (joining the document-level artifact
list in VERSIONING.md) is decided at the same time.

## 8. Relationship to existing specs

- **IPLAN-ECOSYSTEM.md** — the author/manage/execute pipeline this loop
  closes; source of the *hub* term this document deliberately does not reuse.
- **IPLAN-ASSURANCE.md** — level vocabulary adapted (with shifted, explicitly
  mapped guarantees) by §4; the assurance path referenced (never replaced)
  by §3.
- **TRANSPORT-INTEGRATION.md** — governing principle (§1), idempotency
  pattern (§6), and the broker-ready/ship-simple precedent (§8) this model
  follows.
- **VERSIONING.md** — versioning rules governing the schema landing (§7.7).
- **Engramory `docs/MEMORY_DESIGN.md`** — the distilled tier's internal model
  (L0–L3 memory layers, reflection/consolidation loop) in the reference
  deployment.

## Appendix A — Claim ledger (investigation evidence)

Retained while this document is DRAFT; removed at ratification. Citations are
relative to this repo unless prefixed with a sibling-repo directory (resolved
against the workspace root).

| # | Claim | Symbol | Citation |
|---|-------|--------|----------|
| 1 | `L0/L1/L2` already denote assurance levels in this standard | `Assurance Levels (conformance tiers)` | docs/standards/IPLAN-ASSURANCE.md:29 |
| 2 | Engramory uses `L0–L3` for its memory layers | `Per-agent identity (L3)` | engramory/README.md:33 |
| 3 | Engramory's distillation loop turns raw experience into reusable lessons | `Distillation loop` | engramory/README.md:34 |
| 4 | The pipeline `author → manage → execute` is contracted | `author → manage` | docs/standards/IPLAN-ECOSYSTEM.md:22 |
| 5 | "Contract above transport" is the standard's governing principle | `The governing principle: contract above transport` | docs/standards/TRANSPORT-INTEGRATION.md:10 |
| 6 | Broker-ready / ship-simple-first precedent, "No schema change needed later" | `Scale option — message broker (broker-ready, A2A-first)` | docs/standards/TRANSPORT-INTEGRATION.md:224 |
| 7 | Idempotency is a ship-time contract, not a broker feature | `Idempotency (ship-time contract, not a broker feature)` | docs/standards/TRANSPORT-INTEGRATION.md:194 |
| 8 | The schema set versions together as one unit | `versioned **together**` | docs/standards/VERSIONING.md:11 |
| 9 | Current schema-set version is `1.3-draft` | `1.3-draft` | docs/standards/VERSIONING.md:19 |
| 10 | Individual schemas do not version themselves | `Individual schemas do not version themselves` | docs/standards/VERSIONING.md:24 |
| 11 | `execution-event` payload schema exists in this repo | `Iplanic Execution Event` | schemas/execution-event.schema.json:4 |
| 12 | `iplan-evidence-bundle` payload schema exists in this repo | `IPLAN Evidence Bundle` | schemas/iplan-evidence-bundle.schema.json:4 |
| 13 | Operations already emits a structured review-verdict shape | `Multi-agent review verdict — author-side` | operations/.claude/agents/review-prompts/verdict-schema.json:3 |
| 14 | aidoc-flow-ci emits a structured verdict shape (automatable producer) | `"required": ["decision", "summary", "findings"]` | aidoc-flow-ci/ai-review/verdict.schema.json:4 |
| 15 | Iplanic's built-in workers include connector sync | `connector sync` | iplanic/README.md:13 |
| 16 | The executor ledger is append-only and hash-chained (private-tier example) | `Ledger` | iplan-runner/README.md:22 |
| 17 | Operational telemetry is owned by the runner Monitor (OpenTelemetry) | `Monitor` | iplan-runner/README.md:25 |
| 18 | The broker family NATS / Kafka / Pub-Sub is already anticipated | `NATS / Kafka / Pub-Sub` | docs/standards/TRANSPORT-INTEGRATION.md:230 |
| 19 | The reference memory plane is at project-initiation phase | `Project initiation` | engramory/README.md:76 |
| 20 | Memory-plane portability: self-hosted dev → GCP or Azure adapter swap | `Self-hosted for dev, portable to GCP or Azure` | engramory/README.md:42 |
| 21 | A PostgreSQL transactional outbox is the standard's no-broker baseline | `PostgreSQL transactional outbox` | docs/standards/TRANSPORT-INTEGRATION.md:239 |
| 22 | The executor ledger chain is strictly sequential (one writer per scope) | `event.get("sequence") != index + 1` | iplan-runner/platforms/hermes/src/iplan_hermes/ledger/store.py:28 |
| 23 | A ledger binds to one source IPLAN by id + version + checksum | `` `id` + `version` + `checksum` `` | iplan-runner/README.md:28 |
| 24 | Every management-plane store has a PostgreSQL adapter | `has a PostgreSQL adapter` | iplanic/README.md:77 |

## Appendix B — Review log

### Pass 1 - 2026-07-05 - author self-check

Draft assembled against the claim ledger; all citations opened and verified
during drafting. Naming collision with assurance levels and Engramory memory
layers identified and resolved (named tiers, §2). Versioning recommendation
corrected from "separate version track" to "additive change to the single
set" after reading VERSIONING.md.

### Pass 2 - 2026-07-05 - independent (3-agent parallel per OPS-0067)

Three fresh-context agents: citation verifier, standards-consistency
reviewer, adversarial architecture judge. Citation verifier: 15/15 ledger
rows accurate, zero load-bearing findings. Consistency reviewer: 1 blocker
(workspace-internal specifics in a neutral standard body), 6 warnings
(assurance-level semantic drift, signed-JSONL vs L0 inconsistency,
versioning-axis conflation, "hub" term collision, missing ratification-path
sentence, missing CHANGELOG entry), 3 nits. Architecture judge: 1 blocker
("C→B is not a migration" overstated; Model C underspecified), 6 warnings
(missing shared-exchange-repo model, hardcoded project enum, assurance-level
redefinition, untyped origin refs, vague scope test, consumer-not-ready
failure mode), 2 nits. All findings folded in this revision: normative body
made role-based with an informative §6 reference-deployment mapping; Model C
respecified as the shared git-native exchange repo with a minimal transport
contract and an honest migration statement; `source.project` made free-form
against a registry; `provenance` renamed `origin` with typed refs;
exchange-scoped assurance mapping table added; "hub" term dropped; scope test
given a steward gatekeeper and countable split trigger; minimal viability
condition added; ratification path added to the header; CHANGELOG entry
added; ledger extended to 20 rows.

### Pass 3 - 2026-07-05 - independent

Fresh-context re-verification of the folded revision: every Pass-2 finding
confirmed addressed in the body; all 20 ledger citations re-opened and
verified; all internal §-pointers resolve; no new contradictions; normative
body confirmed free of workspace-internal identifiers outside the informative
§6 and Appendices. Zero load-bearing findings; five cosmetic minors
(placeholder wording in envelope examples, an unmarked informative aside,
CHANGELOG preamble coverage, three rhetorical phrasings, a §7.5 pointer note)
— all fixed in this revision. **Result:** ready

### Amendment - 2026-07-05 - store + notify

Post-merge amendment (founder-directed): §5 gains the **store + notify**
architecture for the B-phase exchange service — pub/sub is a transport, not
storage; the append-only replayable store is the normative record
(late-consumer property), notification is an optional layer, admission is
store-first. §7.6 retitled "Storage and broker choice" with the storage
recommendation (C: the exchange repo; B: PostgreSQL append-only event table
adapting the transport standard's transactional-outbox baseline; optional
object storage / warehouse archival tier). §7.1 reconciled with the
late-consumer property: per-kind retention governs tier placement, not
existence; deletion only via steward-approved waiver. Ledger row 21 added.
Pre-push adversarial review (1 agent, docs-class): 1 blocker (§5 ↔ §7.1
retention contradiction), 1 warn (outbox inference read as sourced), 3 nits
— all fixed in this amendment.

### Amendment - 2026-07-05 - ADR-0001 (exchange storage independence)

Founder-confirmed decision recorded as
`docs/adr/ADR-0001_exchange-storage-independent-of-execution-ledger.md`:
neither the executor's assurance ledger nor the management-plane
system-of-record serves as the exchange store; patterns (append-only +
hash-chain, canonical signing) and content (curated ledger projections as
payloads) are reused, never the artifact. §5 models table gains the
corresponding rejected row; ledger rows 22–24 added.
