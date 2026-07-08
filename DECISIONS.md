# DECISIONS — iplan-standard

Durable, ISO-stamped, **append-only** record of load-bearing decisions
for the iplan-standard repo (the neutral, versioned source of truth for
the IPLAN standard).

**ID prefix:** `IS-NNNN`. Never reuse a retired ID.

**Scope:** repo-level operational + workspace-standard-adoption
decisions. **NOT for** substantive standard evolution — those go
through the framework CHG / GATE-SPEC process referenced by
`GOVERNANCE.md`, with the ratified content landing in
`docs/standards/*.md`. `GOVERNANCE.md` itself is a POINTER to the
framework governance model + local OPS-NNNN adoption deltas, not a
decision log.

## IS-0001: PLAN-003 Wave 1b canon adoption (2026-07-08)

**Context**

`aidoc-flow-ci@ci/v1.6.0` shipped the PLAN-003 project-governance file
canon (see `aidoc-flow-ci#72` plan; `aidoc-flow-ci#73`/`#74`,
`aidoc-flow-operations#217`, `aidoc-flow-ci#75` = PR-V1/V2/V3/V4).
Workspace audit had this repo missing 4 of 6 required governance
surfaces (HANDOFF / DECISIONS / ROADMAP / plans/) — biggest gap in the
non-paused workspace repo set. Per PLAN-003 §5.4c iplan-standard row +
§5.5 Wave 1: adopt in Wave 1b (the "b" sub-designation distinguishes
this rollout from framework's Wave 1a in `aidoc-flow-framework#273`;
PLAN-003 §5.5 defines Wave 1 as the pair — the a/b split is per-PR
sequencing convention).

**Decision**

Create all 4 missing governance files from `aidoc-flow-ci/install/
templates/*.template` skeletons; add `## Per-repo governance` H2 section
to `CLAUDE.md` declaring the paths. 6-surface bundle above OPS-0061
Rule 1 ≤3 default authorized by explicit founder OK 2026-07-08
(analogous to `aidoc-flow-ci#73` 11-surface PR-V1 bundle per PLAN-002
§5.4 dogfood-in-canon-PR precedent).

**Consequences**

- Governance drift on `CLAUDE.md#per-repo-governance` closes; `bash
  ../aidoc-flow-ci/install/apply-standards.sh --check` reports exit 0.
- This DECISIONS log seeds with this entry (`IS-0001`); future entries
  append here + never rewrite history.
- This repo now participates as a consumer of PLAN-003 project-governance
  canon (previously only PLAN-002 CI + governance-workflow canon).
- Substantive IPLAN standard evolution remains routed through the
  framework CHG / GATE-SPEC process referenced by `GOVERNANCE.md` +
  landing in `docs/standards/*.md`. This decision is workspace-standard
  adoption, not standard-content evolution.

**Origin**

Founder direction 2026-07-08: "continue with Wave 1b: iplan-standard".
PLAN-003 §5.5 Wave 1 sequencing + §5.4c iplan-standard row scope.

<!-- Append new entries above this line; append-only. Never rewrite
history; if a decision is reversed, add a NEW entry citing the reversal
and update the superseded entry's "Consequences" section to reference
the reversal ID. -->
