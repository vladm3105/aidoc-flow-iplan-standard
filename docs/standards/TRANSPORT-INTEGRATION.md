# Transport & Integration

How approved IPLANs flow **into** Iplanic (authoring flow → Iplanic import) and
how tasks/results flow **between** Iplanic and remote executors
(Iplanic ↔ iplan-runner). This standard expands the two integration edges with a
per-surface channel mapping and the **behavioral contracts** (onboarding,
delivery/failure/retry, the artifact byte path, liveness/cancellation,
idempotency/replay) — not just the topology.

## 1. The governing principle: contract above transport

The protocol layering is fixed by these rules:

- **The contract is the schema, not the wire.** `task`, `execution-event`,
  `artifact`, and the evidence `seal` are the real contract; A2A/MCP are carriers.
- **Signed log ingestion is the canonical telemetry path.** A2A/MCP can carry
  status, but history is recorded through normalized, signed events.
- **Protocol Boundary Rule.** Payloads are normalized at the gateway; core modules
  work with internal commands/events/records, never raw A2A/MCP payloads.

Consequence: transport is **per-edge, per-surface**, and reversible. Signatures
(the executor-identity model) ride inside the payload → transport-independent.
This is also why **replay defense is mandatory** (§7): a transport-independent
signed event is replayable on any channel unless dedup + a clock-skew window stop it.

## 2. The two integration edges

```text
author ──IMPORT──▶ Iplanic ──DISPATCH──▶ iplan-runner (execute)
                      ◀──REPORT (events/artifacts/evidence)──
```

| Edge | Direction | Nature | Surface |
| ---- | --------- | ------ | ------- |
| **Edge 1 — Import** | author → Iplanic | artifact submission | accepts from the authoring flow, manual upload, API clients, and connectors |
| **Edge 2 — Execute** | Iplanic ↔ iplan-runner | agent task delegation + signed reporting | A2A + MCP |

## 3. Edge 1 — Author → Iplanic (import)

Import is **not** task delegation; the authoring flow deposits an approved
IPLAN/chain for management.

| Option | Fit | Decision |
| ------ | --- | -------- |
| **MCP tool** (`import_iplan` / `import_chain`) | The authoring agent is already an MCP client. Agent-native, schema-validated at the boundary. | **Primary — agent path** |
| **REST** `POST /iplans/import`, `/iplan-chains/import` (Management API) | Universal: CI, manual upload, connectors, non-agent clients. Same pipeline. | **Primary — universal path** |
| **Git / GitOps + webhook connector** | The authoring flow commits approved IPLANs; Iplanic ingests on push. | Optional connector |
| **Event/message bus** | Decoupled/async; heavier infra. | Only if a bus exists |
| **A2A** | ✗ Mismatch — forces a task protocol onto a document push. | **Not used on this edge** |

**Decision (T1):** MCP (agent) + REST (universal) as twin front doors to one
Import Pipeline:

```text
normalize → canonical-hash (iplan-canonical-json) → schema validate →
semantic validate → create/reject registry + version records → import result
```

**Import idempotency (contract, not option).** Re-importing content whose
`iplan-canonical-json` hash equals an existing version is a **no-op that returns
the existing `plan_version_id`** with `import_result.status = unchanged` — never a
duplicate version. Both front doors MUST produce an `iplan-import-result`.

## 4. Edge 2 — Iplanic ↔ iplan-runner (execute)

A2A is the remote-executor task protocol; MCP is the tool/data/evidence protocol.
The four interop surfaces map to channels:

| Surface | Channel | Rationale |
| ------- | ------- | --------- |
| ① **dispatch** (`task`) | **A2A** — Iplanic as A2A *client* → executor `task_endpoint` | A2A's core use case |
| ② **events** — live | **A2A status + SSE streaming** | low-latency UX |
| ② **events** — canonical | **signed `execution-event` ingestion** (A2A or MCP, normalized at gateway) | durable, signed, transport-agnostic |
| ③ **artifacts** | **MCP request-upload → object storage (signed URL) → confirm** (§4.4) | keep bytes off the control plane |
| ④ **evidence bundle** | **MCP** evidence upload (sealed, signed `seal`) | sealed audit package |

`protocol_agent_id` records the A2A-native agent-card ID, mapped to the canonical
hash `executor_id` (a hash-derived identity over the executor's registered signing
key) before core state updates.

### 4.1 Iplanic as A2A server (not only client)

Iplanic supports **both** A2A roles. Beyond dispatch (client), Iplanic **as A2A
server** exposes control-plane tasks to trusted external systems — e.g. a customer
system querying run status, requesting a chain dispatch, or cancelling a run. The
server role is `trust_level`-gated (`trusted`/`first_party` only) and authenticated
per §7. Surface to expose: read run/chain status, request dispatch, request cancel.
(A detailed server-task catalog is a follow-on; the role is listed here so it is
not omitted.)

### 4.2 Onboarding & key enrollment (the trust bootstrap)

All signature verification depends on a registered key, so registration is the
**first** transport concern, not an afterthought. Lifecycle over the
`status` enum (`pending → active → paused → revoked`):

1. **Enroll** — executor submits an enrollment request (MCP `register_executor`
   or REST `POST /executors`) carrying a proposed Agent Card + public key
   material (`signing_keys[]`). Record created `status: pending`.
2. **Approve** — an **org admin** grants `trust_level`, `allowed_projects`,
   `owner_org_id` (these are **never self-asserted** — see §4.3) → `status: active`.
3. **Rotate** — add a new entry to `signing_keys[]` (new `key_id`, `valid_from`);
   old keys stay valid for their window so historical events still verify.
4. **Pause/Revoke** — admin or policy sets `status: paused` (transient, e.g.
   missed heartbeats §4.5) or `revoked` (terminal). Both stop new dispatch and
   reject new events; prior sealed evidence stays verifiable against historical keys.

### 4.3 Agent Card ↔ `executor-registration` mapping

An Agent Card may **propose** capabilities; trust and tenancy are **granted**,
never self-claimed:

| Registration field | Source |
| ------------------ | ------ |
| `capabilities`, `protocols_supported`, `max_parallel_tasks`, `task_endpoint`, `heartbeat_url`, `display_name` | **Card-derivable** (executor-proposed) |
| `trust_level`, `allowed_projects`, `owner_org_id`, `cross_org_grants[]`, `status` | **Admin-granted** (must not come from the Card) |
| `executor_id`, `signing_keys[]` | **Derived/registered** at enrollment (hash identity over the registered signing key) |

`cross_org_grants[]` and `signing_keys[]` extend `executor-registration` so that
key rotation, multi-key history, and cross-org grants are first-class. The
onboarding/rotation/cross-org narrative here depends on those fields being present
in the registration schema.

### 4.4 Artifact byte path (③) — request → PUT → confirm → verify

"Signed URL" expanded to an enforced sequence:

1. **Request** — executor calls MCP `request_artifact_upload(artifact_id, artifact_type, byte_size, media_type)`.
   `byte_size`/`media_type` here are **request arguments** (not the artifact
   record), so the policy gate works regardless of the schema. Iplanic rejects
   up-front if `byte_size > artifact_upload_policy.max_artifact_bytes` or
   `media_type ∉ allowed_media_types`; otherwise returns a short-lived signed PUT
   URL scoped to `artifact_id` + tenant prefix.
2. **PUT** — executor uploads bytes directly to object storage (off the control plane).
3. **Confirm** — executor submits the `artifact` record (`uri`, `sha256`,
   `byte_size`, `media_type`, `org_id`, `project_id`, `run_id`, `task_id`,
   `executor_id`).
4. **Verify** — Iplanic recomputes `sha256` from the stored object and **rejects**
   on mismatch, on `byte_size`/`media_type` policy violation, or on a tenant/scope
   failure (§7). Only a **verified** artifact counts toward the completion gate.

### 4.5 Liveness & cancellation

Wires the lease lifecycle to the wire:

- **Heartbeat** — executor pings `heartbeat_url` on a registered interval;
  Iplanic stamps `last_seen_at`. Missed beats beyond the timeout → `status: paused`
  and **in-flight tasks whose lease cannot be confirmed are reassigned**
  (re-`task.assigned` to another eligible executor).
- **Lease expiry** — `lease_expires_at` lapses without progress → reassignment or
  executor self-`task.cancelled`.
- **Cancellation** — A2A cancel (Iplanic- or chain-initiated, e.g.
  `conflict_strategy: cancel_lower_priority`) → emits `task.cancelled` (status
  `cancelled`) and **releases the lease**. Cancellation is idempotent (§6).

### 4.6 Backpressure & quotas (pre-broker)

Honored on the A2A/MCP-first path, not deferred to a broker: the dispatcher
**MUST NOT** exceed a registration's `max_parallel_tasks`; artifact uploads are
bounded by `artifact_upload_policy.max_artifact_bytes` (enforced at §4.4 step 1
and step 4). Over-limit dispatch is queued, not dropped.

## 5. Delivery, failure & retry (the A2A/MCP-first contract)

Every channel has stated delivery semantics **before** any broker exists.

| Channel | Delivery | On failure |
| ------- | -------- | ---------- |
| ① dispatch (A2A → `task_endpoint`) | at-least-once; lease makes re-dispatch safe | endpoint unreachable / NACK → retry with backoff; persistent failure → reassign (§4.5) |
| ② event ingestion | at-least-once + **idempotent** (§6) | ingestion returns a **rejection response** (§5.1); retryable vs terminal per reason |
| ③ artifact confirm | at-least-once + idempotent on `artifact_id` | sha256/policy/scope failure → terminal reject; transient → re-PUT + re-confirm |
| ④ evidence upload | at-least-once + idempotent on bundle id | seal/signature failure → terminal reject |

### 5.1 Ingestion rejection response

Ingestion rejects events on auth / signature / scope / timestamp / idempotency
failure, plus `schema_invalid` (payload validation) as a sixth category. The
rejection is **explicit**, not silent:

```text
{ accepted: false, event_id, reason, retryable }
reason ∈ { auth_failed, signature_invalid, scope_denied, timestamp_skew,
           idempotency_replay, schema_invalid }
```

- **Terminal (retryable=false):** `auth_failed`, `signature_invalid`,
  `scope_denied`, `schema_invalid` — fix and re-sign; blind retry is futile.
- **Benign (retryable=false):** `idempotency_replay` → already recorded; treat as success.
- **Transient (retryable=true):** `timestamp_skew` outside the window when the
  executor's clock can be corrected; server-side `unavailable`.

Accepted: `{ accepted: true, event_id, received_at }` (server stamps `received_at`).

## 6. Idempotency (ship-time contract, not a broker feature)

- **Events** — ingestion **deduplicates on `idempotency_key`** today, A2A/MCP-first;
  a duplicate returns success without re-recording. `idempotency_key` and
  `trace_id` are required on every event for exactly this.
- **Artifacts** — confirm is idempotent on `artifact_id` (re-confirm with matching
  `sha256` = no-op).
- **Import** — idempotent on canonical hash (§3).
- **Cancellation** — idempotent on `task_id`.

A broker (§8) reuses these keys; it does not introduce idempotency.

## 7. Security on the wire

- **TLS required** on every A2A/MCP/REST channel; no plaintext.
- **Authentication** — caller identity established before §5.1 checks. The baseline
  is OIDC/JWT for all callers, layered above the payload signature; mTLS is optional
  for `trusted`/`first_party` (see §9). TLS + an authenticated principal are
  mandatory regardless.
- **Replay defense** — because signatures are transport-independent, a captured
  signed event is replayable. Defense = **`idempotency_key` dedup (§6) +
  clock-skew window** (`received_at − occurred_at` bound). Both are required;
  neither alone suffices.
- **Scope/tenant isolation** — every event/artifact is accepted only if
  `{org_id, project_id}` is within the executor's `allowed_projects` /
  `owner_org_id` / `cross_org_grants[]`. Signed URLs (§4.4) are tenant-prefixed.
- **Webhook/push-notification callbacks** (`protocols_supported: webhook`) MUST
  authenticate Iplanic to the executor (signed callback) and carry only the hash
  `executor_id` + refs, never secrets.

## 8. Scale option — message broker (broker-ready, A2A-first)

A2A stays the control-plane protocol. The one place a different transport wins is
the **high-volume async surface** — the signed-event firehose and **pull-based
dispatch to a large/NAT'd fleet**:

- A **broker** (NATS / Kafka / Pub-Sub) adds durable at-least-once, **per-`run_id`
  ordering**, backpressure, replay, and a **work-queue pull model** (executors
  subscribe instead of exposing `task_endpoint`). Reuses the §6 idempotency keys.
- It **complements** A2A; gRPC bidi streaming is a possible under-the-hood
  optimization, not the contract.

**Decision (T5):** design event-ingestion + dispatch to be **broker-ready**
(idempotent, ordered, replayable — already true via §5/§6) but **ship on A2A/MCP
first**; add a broker only at fleet scale. No schema change needed later. The
baseline transport contract is broker-neutral: a PostgreSQL transactional outbox
serves the no-broker deployment, and a broker is added only at fleet scale.

## 9. Reference topology & decisions

```text
Author ──MCP / REST──▶ Iplanic Import Pipeline                       (Edge 1)
Executor ──MCP/REST enroll──▶ Iplanic (pending→active, keys)         onboarding §4.2
Iplanic ──A2A (client)──▶ iplan-runner                               dispatch ①
iplan-runner ──A2A status / SSE──▶ Iplanic                           live state ②
iplan-runner ──signed events (A2A | MCP, normalized)──▶ Iplanic      canonical telemetry ②
iplan-runner ──MCP request-upload + object-store + confirm──▶ Iplanic   artifacts / evidence ③④
External ──A2A (Iplanic as server)──▶ Iplanic                        control-plane tasks §4.1
        [scale]  signed events + pull-dispatch over a broker (NATS / Kafka / Pub-Sub)
```

| # | Decision |
| - | -------- |
| T1 | Edge 1 = MCP + REST twin front doors; A2A not used; import idempotent on canonical hash |
| T2 | Edge 2 = A2A (dispatch/status/stream/cancel/discovery) + MCP (tool/data/evidence/log) |
| T3 | Canonical telemetry = signed `execution-event` ingestion, transport-agnostic, normalized at gateway |
| T4 | Large artifacts → object storage via request→PUT→confirm→verify; control protocol carries only the ref |
| T5 | Event-ingestion + dispatch broker-ready; ship A2A-first; broker-neutral contract (v1 = PostgreSQL outbox, no broker) |
| T6 | All channels: TLS + authenticated principal; auth baseline = OIDC/JWT, mTLS optional for trusted/first_party; replay defense = idempotency + skew window |
| T7 | Onboarding admin-approved; trust/tenancy granted not self-asserted; keys via `signing_keys[]`; Agent Card maps to `executor-registration` against a pinned minimum A2A `protocolVersion` |

## 10. MCP tool catalog (Iplanic's MCP server)

| Tool | Surface / use |
| ---- | ------------- |
| `import_iplan`, `import_chain` | Edge-1 import |
| `register_executor`, `rotate_executor_key` | onboarding §4.2 |
| `get_plan`, `get_chain_context` | plan lookup / chain context |
| `search_knowledge` | knowledge-base search |
| `submit_event` | execution-log / event submission ② |
| `request_artifact_upload`, `confirm_artifact` | artifact byte path ③ §4.4 |
| `upload_evidence_bundle` | evidence ④ |
| `check_policy`, `run_validator` | policy checks / validator access |
| `get_repo_metadata` | connector-backed repository metadata |

## 11. Non-goals (explicit scope boundary)

- **Auth credential plumbing** — the *issuance* of mTLS/OIDC/SPIFFE creds (the §9
  open item); this standard mandates TLS + an authenticated principal but not the
  IdP wiring.
- **Broker product selection** — deferred until fleet scale (§8).
- **Detailed A2A-server task catalog** — §4.1 establishes the role; the full
  exposed-task list is follow-on.
- **Executor-side implementation** — the live A2A/MCP client is the remote
  executor's responsibility.
- **Wire-format SDK choices** — A2A/MCP library selection is implementation, not contract.

## 12. Open questions

Resolved positions adopted by this standard:

- **Wire auth:** OIDC/JWT baseline for all callers, layered above the payload
  signature; mTLS optional for `trusted`/`first_party`; SPIFFE deferred.
- **A2A version pin + Agent Card mapping:** pin a minimum A2A `protocolVersion`;
  map the Card to `executor-registration` with A2A skills normalized to the
  `capabilities` enum; trust/tenancy/keys admin-granted.
- **Broker selection:** broker-neutral contract; v1 = PostgreSQL transactional
  outbox (no broker); broker added only at fleet scale, per mode.

Still open:

- **Concrete A2A baseline version** — the specific minimum version to pin, set
  against the current A2A spec at implementation time.
- **A2A skill → `capabilities` normalization table** — the actual id/tag → enum map.
- **Payload `schema_version` negotiation** — executor sends e.g. `1.2-draft` vs the
  executor's vendored mirror; accept/reject rule (a future revision).
- **Deployment-specific providers** — concrete OIDC provider and object storage /
  eventual broker, pending the hosted-vs-self-managed target.
- **Heartbeat interval/timeout defaults** and the reassignment grace window.

## 13. Cross-references

- [`IPLAN-MANAGEMENT.md`](IPLAN-MANAGEMENT.md) — Import Pipeline + Management API.
- [`IPLAN-STANDARD.md`](IPLAN-STANDARD.md) — artifact family, executor work orders,
  the dispatched task payload, and execution state.
- [`IPLAN-ECOSYSTEM.md`](IPLAN-ECOSYSTEM.md) — author → manage → execute pipeline.
- [`PLAN-INGESTION-ADAPTERS.md`](PLAN-INGESTION-ADAPTERS.md) — converting source
  plans into the standard ahead of the import pipeline.
