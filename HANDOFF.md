# HANDOFF — iplan-standard

Live cross-session resume point for the iplan-standard repo — the
neutral, versioned source of truth for the IPLAN standard (currently
at `iplan/v0.1.0`, in additive-only maintenance). Read at session start;
refresh at milestones and before context compaction.

## Current state (2026-07-08)

**CI gate stack complete (2026-07-12):** ai-review + composition activated
(reviewer App provisioned; `APP_REVIEWER_1_BOT_ID` var set), joining the
content-check surface (secret-scan / links / markdown-lint / labeler /
docs-sync) + pre-commit + audit-trail + auto-merge already adopted from
`aidoc-flow-ci`.

**PLAN-003 Wave 1b adoption** — first substantive governance-file
adoption on this repo. Prior state: only `CHANGELOG.md` and a small
`CLAUDE.md`; no HANDOFF / DECISIONS / ROADMAP / plans dir. Wave 1b
creates all 4 from `aidoc-flow-ci@ci/v1.6.0` canon templates + declares
them in `CLAUDE.md ## Per-repo governance` table. 6-surface bundle
above OPS-0061 Rule 1 ≤3 default authorized by explicit founder OK
2026-07-08.

**Active surfaces** (independent of the Wave 1b adoption):

- **IPLAN Assurance L1 ratification** — additive schema field +
  L1 conformance vectors under way in `[Unreleased]` per the
  ratification gate (see `docs/standards/IPLAN-ASSURANCE.md §9 R1/R2/R3`).
- **Interlog extraction** — DRAFT Data & Log Interchange doc + `ADR-0001`
  moved out to `aidoc-flow-interlog` (per CHANGELOG); this repo tracks
  the remaining interchange-compliance note only.

## Open threads

- **IPLAN-Assurance L1 ratification** — advance the R1/R2/R3 ratification
  scoped in `docs/standards/IPLAN-ASSURANCE.md §9`. Next concrete step:
  L1 golden-vector coverage + `intake_control.provenance` additive
  field. No blocker; ready when a session picks it up.
- **PLAN-003 §5.4c workspace-standards link-summary retrofit** —
  deferred from this Wave 1b PR (see `ROADMAP.md § Deferred / parked`).
  Follow-up PR converts the current `## Multi-agent automated review`
  block to the canonical `## Workspace standards` shape per §4.3 +
  §4.2 H5 link-summary mechanism.
- **Wave 2+ cascade** — this repo's downstream consumers (`iplanic`,
  `iplan-runner`) proceed in Waves 2/3 per PLAN-003 §5.5; Wave 2+ is
  independent of this repo's ongoing work.

## Next-session start-here

1. Read `CLAUDE.md ## Per-repo governance` table to locate durable
   surfaces (this file + `DECISIONS.md` + `ROADMAP.md` + `plans/`).
2. If picking up the IPLAN-Assurance L1 ratification: read
   `docs/standards/IPLAN-ASSURANCE.md §9` (R1/R2/R3) + top of
   `CHANGELOG.md [Unreleased]` for the additive schema field +
   golden-vector scope.
3. Check `ROADMAP.md` for phase sequence.

## Recent decisions

- 2026-07-08 — `IS-0001` (see `DECISIONS.md`): Wave 1b adoption of
  PLAN-003 canon; 4 governance files created + `CLAUDE.md ## Per-repo
  governance` section added.

_No prior entries in this log — this HANDOFF began at Wave 1b. Older
history lives in `CHANGELOG.md` + git commit log._

---

**Maintenance protocol:**

- Update `Current state` on every PR that changes what this repo is
  actively working on.
- Move resolved `Open threads` to `Recent decisions` (with `IS-NNNN`
  entry ID if load-bearing) or to git commit history.
- Prune `Recent decisions` — entries older than 4 weeks belong only in
  `DECISIONS.md`.
