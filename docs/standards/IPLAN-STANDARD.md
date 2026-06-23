# IPLAN Standard

## Slogan

**IPLAN:** Intent. Plan. Lineage. Assurance. Navigation.

**IPLANIC:** Intent. Plan. Lineage. Assurance. Navigation. Intelligence.
Control.

Iplanic is the Intelligence and Control layer for IPLAN execution: intent to
evidence, under intelligent control.

## Purpose

An IPLAN is a versioned, machine-readable implementation plan. It translates
approved intent into ordered execution steps, files, commands, verification, and
evidence requirements.

The standard exists so AIDoc Flow can create IPLAN artifacts and Iplanic can
import, operate, monitor, and prove those artifacts without changing their
meaning.

## Core Responsibilities

| Term | Responsibility |
| --- | --- |
| Intent | State the approved outcome, scope, assumptions, and non-goals |
| Plan | Define ordered steps, target files, commands, dependencies, and gates |
| Lineage | Link upstream requirements and downstream code, artifacts, and evidence |
| Assurance | Define verification commands, required evidence, approvals, and completion criteria |
| Navigation | Preserve execution order, plan-chain dependencies, blockers, deferred work, and resume state |

## Artifact Family

| Artifact | Owner | Mutable During Execution | Purpose |
| --- | --- | --- | --- |
| IPLAN document | AIDoc Flow / framework authoring flow | No after approval | Canonical approved implementation plan |
| IPLAN chain | AIDoc Flow / Iplanic import flow | Versioned | Ordered set of dependent IPLANs |
| IPLAN record | Iplanic | Yes, metadata only | Registry entry for one logical plan |
| IPLAN version | Iplanic | No content mutation | Immutable imported plan content and canonical hash |
| Import result | Iplanic | No | Outcome of an import attempt, including errors and warnings |
| Validation report | Iplanic | No | Schema, semantic, and EXEC-Ready validation outcome |
| IPLAN comparison | Iplanic | No | Version or chain diff with approval and execution impact |
| Lifecycle event | Iplanic | No | Append-only transition record for plan management |
| Temporary IPLAN | AIDoc Flow / project maintainer | Yes until closed | Small correction, bugfix, or investigation |
| Task payload | Iplanic | No after dispatch | Runtime work order sent to a remote executor |
| Execution record | Iplanic | Yes, append-only state transitions | Runtime run, task, executor, event, and artifact state |
| Evidence bundle | Iplanic | No after sealing | Audit package proving what happened |

## Management Records

Iplanic manages IPLANs as registry records plus immutable version records. The
registry points to the current and latest versions. Version content is locked by
canonical hash; approval is valid only for the exact hash that was reviewed.

Import results, validation reports, comparison records, and lifecycle events are
append-only evidence for plan management. They answer four operational
questions:

- Which plan content was imported?
- Did the content pass schema, semantic, and EXEC-Ready validation?
- What changed from the previous version?
- Which actor or policy allowed the lifecycle transition?

The detailed management profile lives in `IPLAN-MANAGEMENT.md`.
Shared identifier, status, handoff, evidence, and comparison terminology lives
in `IPLAN-DEFINITIONS.md`.

## Plan State vs Execution State

The approved IPLAN document is canonical plan intent. It should not be mutated
by remote executors during a run.

Iplanic stores execution state separately:

- `plan_version_id` identifies the approved imported IPLAN.
- `run_id` identifies one execution attempt against that plan version.
- `task_id` identifies assigned work.
- `executor_id` identifies the remote executor assigned to a task.
- `work_order_id` identifies the dispatchable step work package.
- a work order's `dispatchable` flag decides whether it is sent to a remote
  executor: `true` dispatches it as a runtime task; `false` marks a work order
  that is part of the plan but not dispatched (a human gate, manual, or
  platform-internal step) — Iplanic tracks it but dispatch skips remote
  assignment.
- `todo_id` identifies one concrete executor TODO inside a work order.
- `protocol_agent_id` may store a protocol-native A2A agent identifier, but it
  maps to `executor_id` before Iplanic updates canonical state.
- signed events and artifacts prove what happened.

## Implementation Gates

Implementation must not start only because an IPLAN document exists. Iplanic
starts work in three explicit phases:

1. Initialization creates runtime records only after approval, validation,
   approved-hash, and evidence-store prerequisites pass.
2. Start conditions dispatch tasks only after executor capacity, resource
   availability, policy checks, context checks, and expected start events are
   ready.
3. Completion gates close execution only after required events, artifacts,
   verification, policy, handoff, and evidence-bundle requirements pass.

The same model applies to IPLAN chains, with additional graph, tier, and
inter-plan handoff checks.

## Executor Work Orders

Every executable IPLAN step must include an `executor_work` block. This block is
the bridge between an approved plan and a remote executor task. It must define:

- a stable `work_order_id`;
- one or more ordered `todos`;
- concrete allowed actions for each TODO;
- TODO-level acceptance criteria;
- TODO-level evidence requirements;
- required progress and completion reporting.

Every executable step must also include an `executor_context` package describing
the repository, workspace write scope, knowledge references, MCP tools, secrets
policy, and forbidden paths. A remote executor should not infer missing context
from outside the task payload.

Iplanic converts the approved step into a runtime task payload using
`IPLAN-TASK-TEMPLATE.yaml`. The payload binds plan intent to runtime identifiers
such as `task_id`, `run_id`, `executor_id`, lease expiry, grants, work order,
context package, reporting requirements, and failure-handling instructions.

## Temporary IPLAN Execution

A TMP-IPLAN is a temporary execution artifact opened from an approved IPLAN
execution context. It is not a permanent IPLAN version and does not use
`iplan_id` or `plan_version` as its own identity. Its canonical identifier is
`tmp_iplan_id`.

TMP-IPLANs are appropriate for bounded corrections, read-only investigations,
hotfixes, and spikes. They must declare:

- `tmp_kind`;
- expiration and promotion policy;
- mutation policy;
- source IPLAN handoff;
- planned return handoff;
- runtime return result;
- executor-ready steps, TODOs, reporting, verification, and evidence;
- closure result.

The source handoff opens the temporary branch from a specific `iplan_id`,
`plan_version_id`, `step_id`, and `work_order_id`. It defines the trigger,
allowed scope, pause behavior, and return contract.

The return handoff defines the gate and allowed decisions for returning to the
source IPLAN. Runtime outcome data belongs in `return_result`, not in the draft
handoff. The source IPLAN can resume only when the TMP-IPLAN `return_gate`
passes and `return_result.resume_action` is `resume_standard_iplan`. If the
temporary work expands the approved intent or scope, the return action must be
`promote_to_permanent_iplan` or the temporary plan must be abandoned.

Permanent IPLANs track temporary branches in
`navigation.temporary_handoffs`. That list records both `iplan_to_tmp` and
`tmp_to_iplan` directions so operators can see why execution left the standard
plan and what evidence is required before it resumes.

## IPLAN Chain Execution Order

An IPLAN chain is an ordered execution graph over immutable approved IPLAN
versions. A chain must not rely on mutable file paths alone. Every chain plan
entry must bind:

- `iplan_id`;
- `plan_version`;
- `plan_version_id`;
- approved artifact reference;
- canonical payload hash;
- `EXEC-Ready` status;
- approval timestamp.

Chain execution order is defined in three layers:

1. `dependencies` define cross-plan work-order edges. Each edge must reference
   source and target `iplan_id`, `step_id`, and `work_order_id`, with an
   explicit gate such as completion, evidence, approval, or context
   availability.
2. `execution_path.tiers` define tier order. Tiers execute in ascending numeric
   order after their `entry_gate` passes.
3. `plan_sequence` defines dispatch order inside a tier. Sequence values run in
   ascending order. Plans in the same sequence may run together only when the
   tier is marked `parallel_safe` and dispatch policy permits it.

Every tier must define:

- entry dependencies and approvals;
- plan sequence and required work orders;
- parallel-safety flag;
- dispatch limits for plans, tasks, and executors;
- exit evidence required before the next tier may start.

Every cross-plan transfer of context, artifacts, or evidence must also define
an `inter_plan_handoffs` entry. Dependencies define ordering; handoffs define
what must be available to the target plan, which evidence proves it, which gate
accepts it, and what fallback runs when the handoff cannot be satisfied.

Chain completion requires the chain `completion_gate` to pass. At minimum this
means all required dependencies are satisfied, tier exit gates pass, plan
completion gates pass, required evidence is accepted, and a chain evidence
bundle is generated when required.

Chain semantic validation must reject duplicate plan IDs, unresolved plan
references, unresolved work-order references, dependency cycles, and execution
tiers that do not cover all declared plans.

## Required IPLAN Sections

Every permanent IPLAN document must contain:

1. `metadata`
2. `intent`
3. `lineage`
4. `scope`
5. `initialization`
6. `start_conditions`
7. `plan`
8. `files`
9. `verification`
10. `evidence_requirements`
11. `completion_gate`
12. `handoff`
13. `navigation`

## Required Identifiers

| Identifier | Format | Notes |
| --- | --- | --- |
| `iplan_id` | `IPLAN-NN` | Sequential and never reused inside a project |
| `tmp_iplan_id` | `TMP-IPLAN-YYYY-MM-DD-slug` | Temporary and bounded correction or investigation plan |
| `plan_version` | semantic version | Increment when approved plan content changes |
| `chain_id` | `IPLAN-CHAIN-NN` | Required when multiple IPLANs execute together |
| `dependency_id` | `DEP-NNN` | Cross-plan dependency edge inside one chain |
| `handoff_id` | `HANDOFF-NNN` or `TMP-HANDOFF-NNN` | Inter-plan or temporary branch handoff |
| `step_id` | `STEP-NNN` | Unique inside one IPLAN |
| `work_order_id` | `WORK-NNN` | Unique dispatchable work package inside one IPLAN |
| `todo_id` | `TODO-NNN` | Unique inside one work order |
| `run_id` | generated by Iplanic | Runtime only |
| `task_id` | generated by Iplanic | Runtime only |
| `executor_id` | registered in Iplanic | Runtime assignment identity |
| `protocol_plan_id` | protocol-native | Optional alias mapped to `iplan_id` at gateway boundary |
| `protocol_agent_id` | protocol-native | Optional alias mapped to `executor_id` at gateway boundary |

## Lifecycle

Plan status:

```text
Draft -> Review -> Approved -> Superseded
Draft -> Abandoned
Approved -> Superseded
```

Execution status:

```text
Not Started -> Queued -> Running -> Blocked -> Completed
Running -> Failed
Running -> Cancelled
Blocked -> Running
Blocked -> Abandoned
```

These Title-Case execution-record transitions are driven by projected runtime
events, not written directly by executors. The authoritative event-to-record
projection (e.g. `task.completed` / `succeeded` → `Completed`) is in
[`IPLAN-DEFINITIONS.md`](IPLAN-DEFINITIONS.md) (Status Projection).

## Readiness Gates

`IPLAN-Ready` belongs to the upstream authoring flow. It confirms SPEC/TDD input
quality before an IPLAN is created.

`EXEC-Ready` belongs to the IPLAN standard. It confirms that the IPLAN can be
executed by Iplanic or another compliant runtime.

Minimum `EXEC-Ready` requirements:

- Approved IPLAN version.
- Complete intent, scope, lineage, and non-goals.
- Ordered steps with dependencies.
- Step-level executor work orders with concrete TODOs.
- Step-level executor context, allowed actions, and failure instructions.
- Test-first file plan where applicable.
- Exact execution and verification commands.
- Evidence requirements for every executable TODO and step.
- Resume instructions and known blockers.
- No unresolved placeholder fields.

`exec_ready_score` (integer 0–100) maps to `required_readiness` by these bands:

- `exec_ready_score >= 90` → `ready` (the `ready ⇔ exec_ready_score ≥ 90`
  boundary; matches iplan-runner `exec_ready_min = 90`);
- `70 <= exec_ready_score < 90` → `ready_with_warnings`;
- `exec_ready_score < 90` is not `ready`; below `70` the plan is not
  execution-ready and must not be dispatched.

The score is a plan-level gate; it is never carried in the dispatched task payload.

## Completion Rules

An IPLAN run is complete only when:

- all required steps are completed or explicitly deferred;
- required signed execution events are accepted;
- required artifacts are accepted;
- required verification commands pass or approved exceptions are recorded;
- evidence requirements are satisfied;
- policy gates and human approvals pass where required.

Executor self-reporting is not enough to complete a plan.

An IPLAN chain is complete only when every required plan run reaches its
completion gate, every tier exit gate passes, every chain evidence requirement
is accepted, and the chain completion gate reaches `Completed`.

## Retry & Attempt Cap

A task may be attempted more than once; each attempt is recorded in
`execution-record.tasks[].attempts[]` with its `result`. Retries are bounded:

- **Attempt cap.** A configured `max_attempts` (integer ≥ 1) bounds retries; the
  recorded `attempts[]` length never exceeds it. The default is conservative —
  `max_attempts = 1` (no automatic retry) — and is configurable upward. A
  `pending` entry is the single in-flight attempt; a new attempt is appended only
  after it resolves to `failed` and the cap still allows.
- **Per-`result` classification** (all five attempt `result` values):
  - `pending` — non-terminal, the attempt is still open; not a retry trigger and
    not terminal;
  - `failed` — transient; may be retried until `attempts` reaches `max_attempts`;
    on the final failed attempt the task status becomes terminal `Failed`;
  - `blocked` — not auto-retried; it resumes via a blocker resolution, not a new
    attempt;
  - `succeeded` and `cancelled` — terminal.
- **Backoff.** Retries use exponential backoff with a configured base, applied by
  the executor. The standard specifies the policy; the executor owns the timing
  (a remote executor such as iplan-runner injects its own `backoff_base`).

The retry policy is a plan-level config, like `exec_ready_score`; it is not
carried in the dispatched task payload.

## Framework Boundary

`aidoc-flow-framework` is the upstream reference for Layer 8 IPLAN concepts. In
this workstream it is read-only. This Iplanic standard package is a draft
operational profile for how Iplanic imports and operates IPLANs.

Framework adoption should happen only after an explicit instruction to modify
the framework repository.
