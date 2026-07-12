# CLAUDE.md — iplan-standard

Operating notes for Claude Code sessions in this repo. Read first.

## What this repo is

The **IPLAN standard** — canonical schemas + IPLAN Assurance framework. Docs +
JSON schemas + test fixtures. Consumed by `iplan-runner` (OSS execute) and
downstream product code.

## Where things are

- `iplan_canonical/` — canonical IPLAN structures
- `schemas/` — JSON schemas (the normative machine-readable spec)
- `docs/standards/` — the prose spec (IPLAN-STANDARD, IPLAN-ASSURANCE,
  VERSIONING, etc.). **Substantive standard changes evolve here**
  through the framework CHG / GATE-SPEC ratification process.
- `GOVERNANCE.md` — pointer to the framework governance model
  (CHG / GATE-SPEC) + local OPS-NNNN deltas. NOT the substantive
  standard content.
- `CONTRIBUTING.md` — how to contribute
- `CHANGELOG.md` — chronological index of changes
- `HANDOFF.md` / `DECISIONS.md` / `ROADMAP.md` / `plans/` — workspace-
  canon durable governance surfaces (PLAN-003 §4.2; see
  `## Per-repo governance` below). Track **repo-level operational +
  workspace-standard-adoption** decisions, distinct from substantive
  standard evolution in `docs/standards/`.

## Per-repo governance — this repo owns its own continuity

The `aidoc-flow` workspace is **multi-repo**. Each repo governs its own
activity tracking; cross-session continuity is per-repo. The durable
surfaces for **this** repo:

| Surface | Path (in this repo) |
| --- | --- |
| Live HANDOFF | `HANDOFF.md` |
| TODO / backlog | Not adopted — `HANDOFF.md` open threads + `plans/` per-initiative plans serve as the backlog |
| Decisions log | `DECISIONS.md` |
| Plans | `plans/` |
| Changelog | `CHANGELOG.md` |
| Roadmap | `ROADMAP.md` |
| _(repo-specific rows below — same table, optional)_ | |
| Framework-governance pointer + local OPS-NNNN deltas | `GOVERNANCE.md` |

`GOVERNANCE.md` is a POINTER to the workspace-wide governance model
maintained in the framework repo (CHG / GATE-SPEC ratification), plus
local OPS-NNNN adoption deltas. It is NOT a substantive-standard-decision
log. Substantive standard evolution lives in `docs/standards/*.md`
under CHG / GATE-SPEC; repo-level operational + workspace-standard
adoption decisions log in `DECISIONS.md`.

Never in `tmp/` (transient). Never in the umbrella `aidoc-flow/` (holds
no dev). Cross-repo coordination captured here references siblings by
path (`../<repo>/`), never relocates their state.

## GitHub operations

Use the **GitHub CLI (`gh`)** as the default for all GitHub operations — PRs,
issues, reviews, releases, repo queries — not the GitHub MCP servers
(`github-tt`, `github-vl`) or raw API calls. If `gh` is unauthenticated, run
`gh auth login` rather than falling back to MCP/API.

## Multi-agent automated review (aidoc-flow standard — OPS-0065 + OPS-0067)

This repo follows the **aidoc-flow standard** for author-side multi-agent
review BEFORE push/commit. The canonical rules + diff-class → agents table +
parameterized prompt templates live in `aidoc-flow-operations`:

- **Rules:** `aidoc-flow-operations/CLAUDE.md` → "Multi-agent automated review
  (OPS-0065 — generalizes the CI ai-reviewer pattern to ALL internal flow)"
  section.
- **Prompt templates:** `aidoc-flow-operations/.claude/agents/review-prompts/`
  — diff-class skeletons (`workflow-yaml.md` / `governance-docs.md` /
  `docs.md` / `scripts.md` / `cross-repo.md` / `adversarial-judge.md` +
  `INDEX.md`).
- **Empirical default (OPS-0067):** 3-agent parallel dispatch + single fold
  cycle for ≤300-line diffs. Re-dispatch only on NEW load-bearing surfaces
  or structural pivots. Cap at 3 cycles per OPS-0066 circuit-breaker.
- **Standard scope:** all aidoc-flow workspace repos — this one included.

The CI `ai-review.yml` gate (merge-side) is unchanged; multi-agent review
strengthens the author-side review pattern.

**Skip discipline:** Stop using `SKIP_LOCAL_AI_REVIEW=1` indiscriminately
per OPS-0065. Acceptable cases: (a) mechanical content (pin bumps with no
logic edits); (b) AI-side review already done via dispatched agent (commit-
message audit-trail line names the agents + verdict); (c) explicit founder
OK per governance PR-discipline Rule 2.

**Origin:** OPS-0065/0067 in `aidoc-flow-operations` `ops/DECISIONS.md`;
cross-repo rollout runbook at
`aidoc-flow-operations` `ops/inbox/2026-06-30_cto-platform_ops-0067-multi-agent-review-rollout.md`.
