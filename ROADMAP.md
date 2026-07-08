# ROADMAP — iplan-standard

Forward-looking view of the iplan-standard repo (the neutral, versioned
source of truth for the IPLAN standard).

Sequenced by phase, not by month. Update in place when a phase closes;
deferred items belong in `plans/` per-initiative plans or `HANDOFF.md`
open threads.

**Scope note:** this ROADMAP tracks the repo-level operational +
release phases (workspace-standard adoption, tooling upgrades, release
cadence, ratification-in-progress). Substantive standard evolution
(schema changes, spec authoring) is routed through the framework
CHG / GATE-SPEC process referenced by `GOVERNANCE.md`, landing in
`docs/standards/*.md`. This roadmap references the ratification-in-
progress but does not decide the substantive content.

## Current phase — additive maintenance + IPLAN-Assurance L1 ratification

Status: `iplan/v0.1.0` in additive-only maintenance. Active surface:
IPLAN-Assurance L1 ratification (see `docs/standards/IPLAN-ASSURANCE.md
§9 R1/R2/R3`) + workspace-standard adoption cascade.

**In flight:**

- **Wave 1b PLAN-003 adoption** — this PR: creates HANDOFF / DECISIONS
  / ROADMAP / plans/ + declares `## Per-repo governance` table in
  CLAUDE.md.
- **IPLAN-Assurance L1 ratification** — additive schema field +
  L1 conformance vectors (see CHANGELOG `[Unreleased]`).

**Recently landed:**

- 2026-07-08 — 2 dependabot bumps merged (this repo #14/#15) as part
  of the session-wide green-PR sweep.
- 2026-07-08 — Aligned with `aidoc-flow-ci@ci/v1.6.0` workspace CI +
  governance-workflow canon per PLAN-002 rollout (`.github/workflows/`
  callers pinned).
- 2026-07-07 — DRAFT `DATA-INTERCHANGE.md` + `ADR-0001` extracted to
  `aidoc-flow-interlog` (per CHANGELOG history).

---

## Next phase — post-Assurance-L1 minor release

Once IPLAN-Assurance L1 ratifies + the additive schema field lands, the
next `iplan/v0.2.0` minor release will bundle the L1 vectors + related
schema additions. Subsequent phases follow driver-planned schema
additions (transport/ecosystem prose curation for public release per
README `## Status`).

**Planned initiatives:**

- IPLAN-Assurance L1 conformance vector set completion (draft in
  `docs/standards/IPLAN-ASSURANCE.md §9`).
- Public curation of the transport/ecosystem prose specs (per README
  `## Status`).

---

## Deferred / parked

- **PLAN-003 §5.4c workspace-standards link-summary retrofit** — the
  `## Multi-agent automated review (aidoc-flow standard — OPS-0065 +
  OPS-0067)` section in `CLAUDE.md` will be renamed to the canonical
  `## Workspace standards` block per PLAN-003 §4.3 required section #5,
  with content retrofitted to the §4.2 H5 path-with-summary format
  (one-sentence summary + explicit path pointer, not duplicated body).
  Deferred to keep Wave 1b within the 6-surface founder-OK budget.

---

**Maintenance protocol:**

- When a phase closes, promote "Next phase" to "Current phase"; move
  landed items to git commit history (or DECISIONS.md if the phase
  outcome was itself a load-bearing decision).
- Do NOT accumulate — a roadmap that grows longer every quarter is a
  backlog in disguise.
