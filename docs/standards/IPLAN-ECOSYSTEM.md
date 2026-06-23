# IPLAN Ecosystem — Roles, Pipeline & Contract Divergence

A conceptual note on the three roles the IPLAN concept spans — **author**,
**manage**, **execute** — the pipeline between them, and why the management
plane's IPLAN standard is an intentionally-richer hub that does not converge to
the source authoring formats it ingests.

## Roles

The IPLAN lifecycle separates three responsibilities. Any concrete deployment may
map them to one or several systems; the roles are distinct regardless of packaging.

| Role | Responsibility |
| --- | --- |
| **Author** | Turns an upstream specification into an approved implementation plan (`IPLAN-NN`). A framework Layer 8 authoring flow is one such author; any AI-agent planner (Claude Code, Gemini, Copilot, Codex) is another. |
| **Manage** | The control plane (**Iplanic** is the reference implementation): import, immutable hash-bound versioning, validation, approval, executor dispatch, completion gate, signed evidence. Standard: [`IPLAN-STANDARD.md`](IPLAN-STANDARD.md). |
| **Execute** | A remote execution worker (**iplan-runner** is the OSS reference executor): runs the plan, produces an append-only ledger + independent gate + handover receipt, emits signed facts. |

Intended pipeline:

```text
author → manage (version / dispatch / gate)
       → execute → manage (record evidence, gate completion)
```

The management plane is **optional — the executor is local-first.** A compliant
executor can run an approved IPLAN straight from the authoring output (file intake)
with a fully local, signed, append-only ledger + independent gate + handover, and
never contact the management plane (**standalone** mode, including fully
**offline**). Management-plane dispatch and evidence relay are **additive** — used
when the management plane owns the lifecycle as the system-of-record. The two hops
through the management plane above describe the **managed** mode; standalone is just
`author → execute (local ledger / gate / handover)`.

## Contract divergence

All three roles stamp `document_type: iplan-document`, but the shapes differ. The
authoring format is intentionally thin; the managed standard is intentionally rich;
the executor consumes a narrow runtime slice.

| Aspect | author (framework L8) | manage (IPLAN standard) | execute (runtime intake) |
| --- | --- | --- | --- |
| schema_version | 1.0 | 1.3-draft | intake 1.0 |
| sections | 6 | 13 | 4 (its own `iplan-intake`) |
| unit of work | `file_manifest` (files) | `step → work_order → todo` | flat `task_graph` |
| executor ctx | — | `executor_context` (forbidden_paths, mcp_tools, secrets_policy) | `isolation_scope.allowed_roots` |
| readiness | "IPLAN-Ready ≥90" (TDD-layer score, not in doc) | `verification.exec_ready_score` + EXEC-Ready gate | `intake_control.exec_ready_score ≥ 90` |
| completion gate | — (status only) | `completion_gate` (management-owned) | ledger well-formedness veto |
| resume | `session_handoff.sessions[]` | `handoff` + `navigation` | `run_state` + idempotent `resume` |
| identity | `iplan_id`, `source_spec` | org/project/iplan/plan_version/run/task/step/executor + aliases | client/project/allowed_roots, source_iplan, agent_id |
| TMP-IPLAN | yes (bugfix, disposable) | yes (first-class: return_gate, promotion) | none |
| signing | — | ed25519 / hmac-sha256 (execution-event, evidence seal) | hmac-sha256 over a hash-chained ledger |

Two consequences:

1. **The managed standard is intentionally richer than the authoring template it
   ingests.** The 13-section standard (step/work_order/todo, executor_context,
   completion_gate, runtime task payload, chains, evidence bundles, protocols) is a
   far richer artifact than a 6-section authoring template. They share the name and
   a few concepts (file ordering, traceability/lineage, TMP-IPLAN, session/handoff)
   but not the structure.
2. **A naive executor intake assumes a shape that matches neither edge exactly.** An
   idealized intake mapping may read `document_control.iplan_id` (matching an L8
   author) yet expect `exec_ready.score`, `tasks[]`, and `isolation_scope` fields
   that are present in neither a real 6-section authoring template nor the managed
   standard's top-level shape. The bridge must be explicit, not assumed.

## Resolved direction — the hub does not converge

The original options were:

1. Declare the management plane's IPLAN standard the **canonical Layer 8** and
   regenerate the authoring template + executor intake mapping from it.
2. Keep the authoring template canonical for authoring; have the management plane
   define an explicit **import/normalization** from the thin authoring format into
   its richer internal model.
3. Pin the executor's intake to the management plane's **dispatched task payload**.

**Resolution: option 2, generalized.** The IPLAN standard is the **canonical,
intentionally-richer hub**; it does **not** converge to any source. Each source —
a framework Layer 8 plan **and any AI-agent plan** (Claude Code, Gemini, Copilot,
Codex, OpenRouter) — is bridged by a **pluggable ingestion adapter** that
maps/enriches it into the IPLAN standard and runs the existing import pipeline
(`iplan-import-result`, `source_framework` provenance). The executor side consumes
the dispatched task payload (option 3) and vendors a pinned mirror — so **neither
edge converges the standard**; the hub stays the hub. The adapter-layer contract
and source set are specified in
[`PLAN-INGESTION-ADAPTERS.md`](PLAN-INGESTION-ADAPTERS.md).

## Cross-references

- [`IPLAN-STANDARD.md`](IPLAN-STANDARD.md) — the canonical IPLAN standard.
- [`IPLAN-MANAGEMENT.md`](IPLAN-MANAGEMENT.md) — the management profile + import pipeline.
- [`PLAN-INGESTION-ADAPTERS.md`](PLAN-INGESTION-ADAPTERS.md) — the pluggable ingestion adapter layer.
- [`TRANSPORT-INTEGRATION.md`](TRANSPORT-INTEGRATION.md) — the import and execute transport edges.
