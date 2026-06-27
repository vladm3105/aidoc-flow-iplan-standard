# Governance

This repository follows the **aidoc-flow project governance**, which is
maintained as a single source of truth in the framework repository and
referenced here, never copied:

→ <https://github.com/vladm3105/aidoc-flow-framework/blob/main/framework/governance/README.md>

Governance changes are proposed and ratified there through the CHG / GATE-SPEC
process; consuming repositories do not fork or copy these documents.

## Repo-specific deltas

### OPS-0062 (2026-06-27) — AI agent auto-merge default (applies to ALL AI agents)

This repo adopts the operations OPS-0062 governance rule. Canonical record:
`aidoc-flow-operations` `ops/DECISIONS.md` OPS-0062 (PR
[vladm3105/aidoc-flow-operations#152](https://github.com/vladm3105/aidoc-flow-operations/pull/152),
merged 2026-06-27 commit `dcc4692`).

**Rule (applies to ALL AI agents — Claude, Codex, Gemini, GitHub Copilot,
etc., not just one model):** for PRs the AI agent opens itself in this
repository:

1. **Auto-watch + auto-merge when green** — after opening a PR, AI watches
   the PR's check rollup until all checks complete; if
   `mergeStateStatus = CLEAN` AND all required checks are SUCCESS, AI
   attempts `gh pr merge --squash --delete-branch` without per-PR
   authorization prompt.
2. **Escalate to human at 10 attempts** — after 10 distinct merge-or-recovery
   actions, AI STOPS + requests human confirmation.

**One attempt** = each distinct merge-or-recovery action (`gh pr merge` /
`skip-ai-review` label-cycle / `gh run rerun` / `gh workflow run`
retrigger). Polling does not count. Counter is per-PR cumulative.

**Visibility:** AI announces each merge attempt in-session.

**Exceptions (AI never auto-merges these; always asks the human first):**

- 🟡 / 🔴 actions per operations autonomy tiers.
- Spec / governance tier PRs (per framework GOVERNANCE referenced above).
- Cross-repo coordinated changes.
- PRs touching this repo's `GOVERNANCE.md`, `CONTRIBUTING.md`, schemas,
  or `.github/` configuration.

**Why this is a delta and not a framework gate weakening:** OPS-0062 is
operations-side AI agent behavioral discipline, not a framework spec
governance gate. It strengthens (doesn't weaken) the framework's adversarial-
review + governance-merge requirements by adding a 10-attempt escalation
ceiling that prevents AI looping on stuck PRs.

A delta must never weaken a framework gate (see `ADAPTATION.md` in the
source above). Add additional repo-local deltas below as needed.
