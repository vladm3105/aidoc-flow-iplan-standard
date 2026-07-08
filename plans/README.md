# plans/ — iplan-standard

Per-initiative plans for the iplan-standard repo. Naming convention +
verified-planning-skill contract per the workspace canon at
`../aidoc-flow-ci/install/templates/plans-README.md.template`.

## Naming convention

`PLAN-NNNN_<descriptive-slug>.md` where `NNNN` is a 4-digit
monotonically increasing sequence local to this repo. Never reuse a
retired ID.

**Alternate prefixes** for scoped plan types (per
`aidoc-flow-ci/docs/REPO_STANDARDS.md` — `PLAN-NNNN` default; `IPLAN`
for session-execution plans; `TPLAN`/`DPLAN`/`MPLAN`/`RPLAN`/`CPLAN`/
`SPLAN` for the reserved scoped types).

Small bug fixes / work items do NOT need a plan — commit + PR body
suffices.

## Structure

Every plan follows the `verified-planning` skill contract (Claim
ledger + Review log; ≥2 review passes with ≥1 independent). Canonical
skill lives at `../operations/.claude/skills/verified-planning/`. Run
`python3 ../operations/.claude/skills/verified-planning/check_plan.py
<plan>` gate before declaring a plan ready.

## Cross-repo plan references

Cite files in sibling repos via `../<repo>/<path>` form. The
`check_plan.py` gate accepts cross-repo citations via `--root
<umbrella-dir>` — typically `--root ..` (the aidoc-flow umbrella).

## Backlog

Larger backlog items that aren't ready for a plan yet live in this
repo's `HANDOFF.md ## Open threads` or (once volume warrants) a
dedicated TODO file. Small + speculative items don't need durable
capture — if they surface again, they get a plan then.

## Substantive standard-changes

Substantive changes to the IPLAN standard (schemas, canonicalization,
prose specs) evolve through the framework **CHG / GATE-SPEC** ratification
process referenced by `GOVERNANCE.md`, landing in `docs/standards/*.md`
— NOT through `plans/`. `plans/` here tracks repo-level operational +
tooling + workspace-standard-adoption work.
