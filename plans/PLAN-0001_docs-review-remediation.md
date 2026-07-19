# PLAN-0001 — Documentation review remediation

- **Status:** READY (verified-planning: 3 passes, 2 independent, final pass zero load-bearing findings)
- **Date:** 2026-07-19
- **Owner:** iplan-standard repo
- **Origin:** four-agent documentation review (internal consistency /
  docs↔schemas+templates / docs↔code+tests+CI / standards best-practices)
  run 2026-07-19 over `docs/`, `schemas/`, `iplan_canonical/`,
  `tests/contract/`, root docs, and `.github/workflows/`. Every finding
  below was re-verified against source by the plan author before entering
  this plan (see Claim ledger).

## 1. Problem statement

The IPLAN standard's machine surface is healthy — the conformance suite
passes (67 tests + 203 subtests), templates/fixtures cover all 17 schemas
with a closed-set guarantee, and the canonicalization reference
implementation matches its spec byte-for-byte (worked-example hash
reproduces). The documentation layer around it has drifted:

1. **Release truth is stale.** Tags exist through `iplan/v0.4.0` and the
   framework ratified IPLAN-Assurance L1 (GD-04, 2026-06-28, pinning
   `iplan/v0.4.0`), but README/HANDOFF/ROADMAP still claim `iplan/v0.1.0`,
   CHANGELOG has no `[0.4.0]` section, IPLAN-ASSURANCE.md still carries a
   DRAFT/non-normative banner, and ROADMAP plans a "next `iplan/v0.2.0`"
   that would collide with the existing tag.
2. **Schema-contract defects.** The same field (`exec_ready_status`) has
   two incompatible enums in different schemas; a chain import result
   cannot carry its chain id; the documented first lifecycle transition is
   unrepresentable; the closed-schema policy contradicts the "minor =
   additive, no consumer action" versioning contract.
3. **Prose inconsistencies.** Two conflicting ingestion reject-code
   vocabularies; dead references (`docs/DECISIONS.md`, `§2.2`,
   `PLAN-001`); iplanic-internal decision IDs that resolve nowhere; stale
   "deferred/backlog" notes for work that already landed; a false
   `sha256(public_key) == executor_id` equality.
4. **Standards-practice gaps.** No BCP 14 normative-language convention,
   no per-document status banners (8 of 10 specs), no conformance clause,
   no docs index, golden-vector gaps on exactly the canonicalization rules
   the spec calls error-prone.

## 2. Findings register (consolidated, deduplicated)

Severity: **B** blocker, **M** major, **m** minor. Citations in the Claim
ledger (referenced as C-n).

| ID | Sev | Finding | Claims |
| --- | --- | --- | --- |
| F-01 | B | README/HANDOFF/ROADMAP claim `iplan/v0.1.0`; tags reach `iplan/v0.4.0`; ROADMAP plans an already-taken `v0.2.0` | C-1..C-5 |
| F-02 | B | CHANGELOG has no `[0.4.0]` section; shipped L1 content sits under `[Unreleased]` | C-6, C-7 |
| F-03 | B | IPLAN-ASSURANCE.md banner says DRAFT/non-normative and §9 says "remaining before ratification", but GD-04 ratified L1 at `iplan/v0.4.0` on 2026-06-28 | C-1, C-8, C-9 |
| F-04 | M | `exec_ready_status` split into two incompatible enums: chain doc `passed/passed_with_warnings` vs version records `not_ready/ready/ready_with_warnings`; prose sides with the `ready` family; chain template + init-check use `passed` | C-10..C-14 |
| F-05 | M | `iplan-import-result.iplan_id` pattern rejects chain ids while MANAGEMENT mandates chain imports produce import results; sibling schema already widened per D-0043 | C-15..C-18 |
| F-06 | M | Lifecycle entry transition unrepresentable: `from_status` required + non-nullable, but the lifecycle starts at `Imported` with no predecessor | C-19..C-22 |
| F-07 | M | Closed schemas (`additionalProperties: false`, all 17) contradict VERSIONING's "minor = additive; pinned consumer accepts any newer minor"; no unknown-field/forward-compat policy exists | C-23..C-25 |
| F-08 | M | Two conflicting ingestion reject-code vocabularies (TRANSPORT §5.1 vs DEFINITIONS ingestion codes); DEFINITIONS' HTTP mapping omits `idempotency_replay`; neither vocabulary is in any schema | C-26..C-28 |
| F-09 | M | Dead refs in normative docs: `docs/DECISIONS.md` D-0021, VERSIONING "§2.2", `PLAN-001` Task 4; iplanic-internal D-NNNN IDs resolve nowhere in this repo | C-29..C-31 |
| F-10 | M | False self-certification equality `sha256(public_key) == executor_id` — `executor_id` is the `exec:<base32(sha256(...))>` form | C-32, C-33 |
| F-11 | M | Stale claims: DEFINITIONS says `format` not asserted (tests assert it, #14 resolved); DEFINITIONS defers retry cross-mapping that IPLAN-STANDARD now defines; MANAGEMENT "chain registry record when it is introduced" (it exists); IPLAN-STANDARD retains internal-workstream/"Iplanic standard package" framing | C-34..C-39 |
| F-12 | M | HANDOFF/ROADMAP open threads direct next-session work at already-landed items (provenance envelope + L1 vectors); only consumer re-pin/enforce remains | C-5, C-9, C-40 |
| F-13 | M | Golden-vector gaps on canonicalization rules the spec calls error-prone: numbers vector covers only small ints; no literals/null-in-array, string-escaping, or non-ASCII key-order vectors | C-41..C-43 |
| F-14 | M | No BCP 14 / RFC 2119 convention in any spec; normative keywords lowercase/informal (verified-absent; see Claim ledger) | — |
| F-15 | M | 8 of 10 specs carry no status/normativity banner (ASSURANCE + DATA-INTERCHANGE stub are the only labeled ones) | C-8 |
| F-16 | M | No conformance clause defining conformance classes (document / producer / control plane / executor / validator); README's two lines are the only conformance definition | C-44 |
| F-17 | M | Version surfaces uncorrelated: `iplan/vX.Y.Z` tags vs `schema_version 1.3-draft` vs package `0.1.0`; VERSIONING never mentions the tag scheme | C-45, C-46 |
| F-18 | m | Status-vocabulary gaps: DEFINITIONS Status Families has no chain-registry-record row and no EXEC-Ready row; `rolled_back` lifecycle event is schema-only; `Not Started` shown in an "execution-record transitions" diagram though it is document-plane | C-47..C-51 |
| F-19 | m | Import path mismatch: MANAGEMENT `POST /projects/{project_id}/iplans/import` vs TRANSPORT `POST /iplans/import` | C-52, C-53 |
| F-20 | m | Artifact types `coverage_report`/`lint_report`/`drift_report` exist only in the artifact enum — absent from `task.required_artifacts` enum and all prose | C-54, C-55 |
| F-21 | m | `sig_ed25519.json` embedded event says `"algorithm": "hmac-sha256"` in an ed25519 vector | C-56 |
| F-22 | m | Stale CI pin refs: README canon `ci/v1.6.0`; `standards-drift.yml` curls the drift script from `ci/v1.6.0` (missed by the v1.9.5 re-pin — raw URL, not `uses:`); `links.yml` header comment says v1.9.4 | C-57, C-58, C-69 |
| F-23 | m | README misc: conformance command fails on fresh clone (no install step); docs list omits IPLAN-ASSURANCE; CLAUDE.md anchor contains a literal em dash (unresolvable fragment) | C-59, C-60, C-70 |
| F-24 | m | ASSURANCE terminology: `client_id` (canonical is `org_id`); `INTAKE-001` referenced without a pointer (iplan-runner rule family) | C-61, C-62 |
| F-25 | m | CHANGELOG hygiene: unqualified `docs/WORKFLOWS.md` refs (file lives in aidoc-flow-ci); orphan L1 paragraph detached under an unrelated entry; ROADMAP interlog-extraction date 2026-07-07 vs CHANGELOG 2026-07-06 | C-4, C-63..C-65 |
| F-26 | m | HANDOFF `## Current state` heading dated 2026-07-08 while recording a 2026-07-12 event | C-66 |
| F-27 | m | No docs/standards index or reading order; no tests/contract vector-format README; canonicalization vectors lack `description` fields (verified-absent; see Claim ledger) | — |
| F-28 | m | No SECURITY.md and no Security Considerations in the crypto-bearing spec (verified-absent; see Claim ledger) | — |
| F-29 | m | Reference verifier ed25519 path raises `ValueError` on malformed hex instead of returning False (hmac path returns False) | C-67 |

## 3. Work plan

Routing key: **[repo]** = repo-level/editorial PR (normal flow);
**[CHG]** = substantive standard change — lands via the framework
CHG / GATE-SPEC process per `plans/README.md` §Substantive
standard-changes, with the plan tracking sequencing only. Every PR
follows OPS-0065 pre-push multi-agent review; governance-class PRs
(.github/, CLAUDE.md, DECISIONS) stay ≤3 doc surfaces.

### Wave 1 — Release-truth sync (F-01, F-02, F-03, F-12, F-22, F-23, F-25, F-26)

Executing already-ratified GD-04 state, not making new standard decisions.

- **W1.1 [repo]** CHANGELOG: cut `## [0.4.0] — 2026-06-28` from the
  `[Unreleased]` L1/assurance entries (content per the tag message +
  GD-04); qualify the two `docs/WORKFLOWS.md` refs as
  `aidoc-flow-ci docs/WORKFLOWS.md`; reattach the orphan L1 paragraph.
- **W1.2 [repo]** IPLAN-ASSURANCE.md: flip the banner to
  ratified-at-L1 (GD-04, 2026-06-28, pins `iplan/v0.4.0`; L1 normative
  for consumers declaring `assurance ≥ L1`; §5 keyless + witness tiers
  remain informative); rewrite §9 "Remaining before ratification" to
  post-ratification state (remaining: consumers re-pin + enforce);
  reword §6's L2 fixture-set claim to future tense (F-11 overlap).
- **W1.3 [repo]** README: Status → current tag (add "see CHANGELOG"
  so it can't silently rot); drop the "will land in a subsequent
  minor" transport-prose sentence (landed in v0.2.0); add
  IPLAN-ASSURANCE to the docs table; governance pin ref v1.6.0 →
  v1.9.5; fix the CLAUDE.md anchor slug; add `pip install -e ".[dev]"`
  before the conformance command.
- **W1.4 [repo]** HANDOFF + ROADMAP: version refs → `iplan/v0.4.0`;
  open threads rewritten to "consumers (iplanic, iplan-runner) re-pin +
  enforce L1"; ROADMAP "Next phase" section rewritten (not just
  renamed) — the planned `v0.2.0` content (L1 vectors + schema
  additions) already shipped in v0.2.0–v0.4.0; the next release
  (`v0.5.0`) is the Wave-3 `1.4-draft` change set; interlog date →
  2026-07-06; HANDOFF heading date refreshed.
- **W1.5 [repo, governance-class — own PR]** `.github/workflows/`:
  `standards-drift.yml` curl URL `ci/v1.6.0` → `ci/v1.9.5` (version-only
  edit per the re-pin rule); `links.yml` header comment → v1.9.5.

### Wave 2 — Normative-prose consistency (F-08..F-11, F-18, F-19, F-24, F-21)

Editorial repairs of self-contradictions; no intended semantic change
(exception: W2.1, which is a wire-semantics choice and rides the Wave 3
CHG change set). Batch per doc; ≤3 surfaces per PR.

- **W2.1 [CHG]** Reject codes: rewrite TRANSPORT §5.1 to use the
  DEFINITIONS ingestion code set as the single vocabulary (declare the
  §5.1 names as retry-category groupings if kept), and add
  `idempotency_replay` to the DEFINITIONS HTTP mapping (or explicitly
  scope it out with a sentence). Routed [CHG] because resolving two
  conflicting vocabularies is choosing a wire semantics, even though
  neither vocabulary is schema-encoded (C-26..C-28); rides the Wave 3
  change set.
- **W2.2 [repo]** Dead refs: CANONICALIZATION `docs/DECISIONS.md`
  D-0021 bullet → qualify as the iplanic-internal decision log (or
  drop); drop the `PLAN-001` Task 4 parenthetical; drop VERSIONING's
  "§2.2"; qualify inline D-NNNN mentions where they appear (D-NNNN =
  upstream iplanic decision log; IS-NNNN = this repo). The shared
  "Decision-ID provenance" paragraph lands later with the docs index
  (W4.4) — W2.2 must not depend on it.
- **W2.3 [repo]** Self-certification wording in DEFINITIONS and
  VERSIONING: `sha256(public_key) == executor_id` → "the base32
  encoding of `sha256(public_key)` in the `exec:` form must equal
  `executor_id`".
- **W2.4 [repo]** Stale claims: DEFINITIONS format sentence → "format
  `date-time` IS asserted (test_date_time_format_checker_is_active)";
  DEFINITIONS attempt-result deferral note → cross-ref IPLAN-STANDARD
  §Retry & Attempt Cap; MANAGEMENT "when it is introduced" clause
  dropped; IPLAN-STANDARD §349-354 workstream/"Iplanic standard
  package" framing → neutral standard voice.
- **W2.5 [repo]** Status vocabulary: add "Chain registry record" and
  "EXEC-Ready" rows to DEFINITIONS Status Families; re-caption the
  IPLAN-STANDARD execution diagram (`Not Started` = document plane,
  pointer to Status Projection); document `rolled_back` / `completed` /
  `archived` lifecycle-event planes+transitions in MANAGEMENT
  §Lifecycle; align the import path (MANAGEMENT project-scoped form is
  canonical; TRANSPORT notes the same pipeline). The path alignment
  stays editorial: both docs describe the same Management API endpoint,
  neither path is schema-encoded, and TRANSPORT's form is annotated as
  abbreviated rather than changed.
- **W2.6 [repo]** ASSURANCE terms: `client_id` → `org_id`;
  `INTAKE-001` gets a pointer sentence (iplan-runner intake rules).
- **W2.7 [repo]** `sig_ed25519.json` embedded `algorithm` →
  `"ed25519"` (signature field is excluded from the signed payload, so
  golden hashes unchanged — conformance suite must stay green).

### Wave 3 — Schema-contract fixes (F-04..F-07, F-20)

W3.1–W3.4 form one CHG-routed change set; per `-draft` semantics these ride a MINOR
bump: `schema_version` `1.3-draft` → `1.4-draft` with migration notes
in VERSIONING (D-0031 pattern).

- **W3.1 [CHG]** Unify `exec_ready_status` on the `ready` family:
  chain schema enum → `not_ready`/`ready`/`ready_with_warnings`
  (binding-level `passed` values migrate to `ready`); rename init check
  `all_exec_ready_statuses_passed` → `all_exec_ready_statuses_ready`;
  update IPLAN-CHAIN-TEMPLATE (3 value sites + check name); migration
  note.
- **W3.2 [CHG]** Widen `iplan-import-result.iplan_id` pattern to
  `^IPLAN(-CHAIN)?-[0-9]{2,}$` with the D-0043 "chain id carried in
  iplan_id" description (additive-leaning but rides the same bump).
- **W3.3 [CHG]** Make `iplan-lifecycle-event.from_status` nullable
  (`null` = entry/creation transition); document the entry transition
  in MANAGEMENT §Lifecycle + DEFINITIONS Management row.
- **W3.4 [CHG]** Forward-compatibility policy in VERSIONING: state
  explicitly that schemas are closed (`additionalProperties: false`)
  and a validating consumer MUST re-pin the schema set before accepting
  documents from a newer minor; record the open-schema
  ("must-ignore-unknown") alternative as an explicitly deferred
  decision. Add a Deprecation subsection (deprecate in MINOR via
  `description` + CHANGELOG; remove only in MAJOR).
- **W3.5 [repo]** One sentence in DEFINITIONS (artifact section):
  `coverage_report`/`lint_report`/`drift_report` are
  voluntary-submission artifact types, deliberately absent from
  `task.required_artifacts` (no schema change).
- **W3.6 [CHG]** `schema_version` bump blast radius (rides the same
  change set): bump the pinned `schema_version: "1.3-draft"` in all 7
  metadata-bearing templates (C-71) and the hardcoded snippet in
  `test_schema_contracts.py` (C-72); update the `1.3-draft` row in the
  IPLAN-ECOSYSTEM version table (C-74); the 3 L1 provenance vectors
  embed `"schema_version": "1.3-draft"` inside **signed** documents
  (C-73) — they stay at 1.3-draft to preserve signatures (the field is
  pattern-validated, so they remain schema-valid; note this in the
  migration note). Also bump the "Current value" line in VERSIONING
  itself (C-45) per the D-0031 precedent.

### Wave 4 — Standards-quality upgrades (F-13..F-17, F-27..F-29)

- **W4.1 [CHG]** BCP 14 pass: add the RFC 2119/RFC 8174 boilerplate
  (once, in the docs index, referenced per doc) and uppercase the
  load-bearing requirements in IPLAN-CANONICALIZATION, IPLAN-STANDARD,
  IPLAN-DEFINITIONS, TRANSPORT-INTEGRATION.
- **W4.2 [repo]** Status banners on the 8 unlabeled specs (pattern:
  the IPLAN-ASSURANCE banner — Status / normativity / Since-version /
  Date).
- **W4.3 [CHG]** Conformance section in IPLAN-STANDARD: classes
  (conforming IPLAN document / producer / control plane / executor /
  validator), 2–4 MUST-level requirements each, each pointing at the
  `tests/contract/` surface that demonstrates it.
- **W4.4 [repo]** `docs/standards/README.md`: annotated index +
  reading order + BCP 14 boilerplate + decision-ID provenance note
  (hosts W2.2/W4.1 shared text).
- **W4.5 [repo]** VERSIONING "Version surfaces" table: `iplan/vX.Y.Z`
  release tag ↔ `schema_version` wire contract ↔ `iplan-canonical`
  package version, with the mapping per release and a sentence that the
  package versions independently.
- **W4.6 [repo]** Conformance-vector hardening: add `description`
  fields to existing canonicalization vectors (hash-preserving —
  verify goldens unchanged); add 4 vectors: numbers-hard (floats,
  exponent forms, `-0`, large ints), literals + null-in-array
  preservation, string escaping (control chars/quote/backslash),
  non-ASCII/astral key ordering; add `tests/contract/README.md`
  documenting each vector family's format and pass criteria.
- **W4.7 [repo]** Root `SECURITY.md` (reporting channel) + "Security
  Considerations" section in IPLAN-CANONICALIZATION (key handling,
  hmac-vs-ed25519 trust asymmetry, canonicalization-confusion risks).
- **W4.8 [repo]** `iplan_canonical/signing.py`: ed25519 verify catches
  `ValueError` from `bytes.fromhex` and returns False (parity with the
  hmac path) + regression test.

### PR sequencing

W1 = 3 PRs (W1.1+W1.2; W1.3+W1.4; W1.5 alone). W2 = 2–3 PRs grouped by
doc. W3 = single CHG-routed change set for W3.1–W3.4 + W3.6 + W2.1
(framework GATE-SPEC entry first, then the schema PR); W3.5 rides one
of the W2 repo PRs. W4 = W4.2+W4.4+W4.5 as one PR; W4.6 and
W4.7+W4.8 as separate PRs; W4.1+W4.3 ride the CHG route (can batch
with W3's GATE-SPEC entry or a second one). Waves 1–2 (except W2.1,
which rides the W3 change set) have no dependency on 3–4 and land
first.

## 4. Out of scope / deferred (founder decision or low value now)

- **`$id` base-URI policy** — all 17 schemas use unversioned
  `https://iplanic.ai/schemas/...` (C-68): neutrality question
  (standard hosted on the commercial control-plane's domain), version
  segment, dereferenceability. Founder decision; park in ROADMAP.
- **Template filename separator** split (`-TEMPLATE.yaml` vs
  `.TEMPLATE.yaml`) — rename churn touches the test map + external
  refs; low value.
- **License/IPR posture** (MIT has no patent grant) — founder decision.
- **Rendered spec site / GitHub Pages, `schemas/index.json` machine
  registry, `py.typed`** — deferred until external-implementer demand.

## 5. Acceptance criteria

1. `python3 -m pytest tests/contract -q` green after every wave
   (goldens unchanged except W4.6 additions).
2. `grep -rn 'iplan/v0.1.0' README.md HANDOFF.md ROADMAP.md` empty;
   `grep -rn 'ci/v1.6.0' README.md .github/` empty.
3. CHANGELOG contains `## [0.4.0] — 2026-06-28`; ASSURANCE banner
   reflects GD-04.
4. Each [CHG] item has a framework GATE-SPEC/CHG record before its
   schema/prose PR merges; migration notes in VERSIONING for W3.
   After W3, `grep -rn '1\.3-draft' docs/ schemas/ tests/` returns only
   the 3 signed provenance vectors and the VERSIONING migration-note
   history.
5. links + markdown-lint CI gates green on every PR.
6. This plan passes `check_plan.py` with zero UNVERIFIED rows and the
   review log shows ≥2 passes, ≥1 independent, final pass zero
   load-bearing findings.

## Claim ledger

| # | Claim | Symbol | Citation |
| --- | --- | --- | --- |
| C-1 | GD-04 ratified IPLAN-ASSURANCE L1, Accepted 2026-06-28, pins `iplan/v0.4.0` (tag existence also verified via `git tag`) | `GD-04` | ../framework/framework/governance/DECISIONS.md:152 |
| C-2 | README claims status `iplan/v0.1.0` | `iplan/v0.1.0` | README.md:43 |
| C-3 | ROADMAP status line claims `iplan/v0.1.0` | `iplan/v0.1.0` | ROADMAP.md:20 |
| C-4 | ROADMAP plans "next `iplan/v0.2.0` minor release" (tag already exists) | `iplan/v0.2.0` | ROADMAP.md:46 |
| C-5 | HANDOFF claims "currently at `iplan/v0.1.0`" | `iplan/v0.1.0` | HANDOFF.md:5 |
| C-6 | CHANGELOG jumps from `[Unreleased]` (line 6) to `[0.3.0]` — no `[0.4.0]` section | `[0.3.0]` | CHANGELOG.md:233 |
| C-7 | L1/assurance content sits under `[Unreleased]` | `intake_control.provenance` | CHANGELOG.md:215 |
| C-8 | ASSURANCE banner: "DRAFT — proposed, non-normative … until ratified, nothing here is a conformance requirement" | `non-normative` | docs/standards/IPLAN-ASSURANCE.md:3 |
| C-9 | ASSURANCE §9 still says "Remaining before ratification … ratify L1 via the framework CHG / GATE-SPEC" | `Remaining before ratification` | docs/standards/IPLAN-ASSURANCE.md:207 |
| C-10 | Chain schema `exec_ready_status` enum is `["passed","passed_with_warnings"]` | `exec_ready_status` | schemas/iplan-chain.schema.json:93 |
| C-11 | Chain init check named `all_exec_ready_statuses_passed` | `all_exec_ready_statuses_passed` | schemas/iplan-chain.schema.json:295 |
| C-12 | Version-record `exec_ready_status` enum is `["not_ready","ready","ready_with_warnings"]` (same in iplan-chain-version.schema.json:64) | `exec_ready_status` | schemas/iplan-version.schema.json:64 |
| C-13 | Prose defines the `ready` family bands (`exec_ready_score ≥ 90 → ready`) | `exec_ready_score` | docs/standards/IPLAN-STANDARD.md:295 |
| C-14 | Chain template uses `exec_ready_status: "passed"` (also lines 49, 67; check name line 188) | `exec_ready_status` | docs/standards/templates/IPLAN-CHAIN-TEMPLATE.yaml:31 |
| C-15 | `iplan-import-result.iplan_id` pattern `^IPLAN-[0-9]{2,}$` rejects chain ids | `^IPLAN-[0-9]{2,}$` | schemas/iplan-import-result.schema.json:35 |
| C-16 | `iplan_id` is in the import-result `required` array | `iplan_id` | schemas/iplan-import-result.schema.json:12 |
| C-17 | Chain import uses the same Import Pipeline, producing chain Version + Registry records | `same Import Pipeline` | docs/standards/IPLAN-MANAGEMENT.md:82 |
| C-18 | Sibling schema already widened to `^IPLAN(-CHAIN)?-[0-9]{2,}$` (D-0043 precedent) | `IPLAN(-CHAIN)` | schemas/iplan-lifecycle-event.schema.json:30 |
| C-19 | `from_status` is in lifecycle-event `required` | `from_status` | schemas/iplan-lifecycle-event.schema.json:13 |
| C-20 | `from_status` enum has 11 statuses, no null | `from_status` | schemas/iplan-lifecycle-event.schema.json:48 |
| C-21 | Lifecycle starts at `Imported` with no predecessor | `Imported -> Validated` | docs/standards/IPLAN-MANAGEMENT.md:133 |
| C-22 | Each transition emits a Lifecycle Event with source status | `source status` | docs/standards/IPLAN-MANAGEMENT.md:148 |
| C-23 | Schemas are closed: `additionalProperties: false` (top level; pattern repeated across all 17 schemas, verified by grep) | `additionalProperties` | schemas/iplan-document.schema.json:6 |
| C-24 | VERSIONING: MINOR = "Additive, backward-compatible" | `Additive, backward-compatible` | docs/standards/VERSIONING.md:31 |
| C-25 | VERSIONING: consumer pinned to `MAJOR.m` accepts any `MINOR >= m` | `MAJOR.m` | docs/standards/VERSIONING.md:34 |
| C-26 | TRANSPORT §5.1 reject vocabulary incl. `auth_failed`, `scope_denied`, `idempotency_replay` | `idempotency_replay` | docs/standards/TRANSPORT-INTEGRATION.md:184 |
| C-27 | DEFINITIONS ingestion reject codes incl. `unregistered_executor`, `executor_not_active`, `project_not_allowed`, `org_mismatch` | `unregistered_executor` | docs/standards/IPLAN-DEFINITIONS.md:165 |
| C-28 | DEFINITIONS full HTTP mapping lists codes without `idempotency_replay` | `timestamp_skew` | docs/standards/IPLAN-DEFINITIONS.md:211 |
| C-29 | Dead ref: "`docs/DECISIONS.md` — D-0021" (no such file; root DECISIONS.md is IS-NNNN) | `docs/DECISIONS.md` | docs/standards/IPLAN-CANONICALIZATION.md:109 |
| C-30 | Dead ref: "(see `PLAN-001` Task 4)" — plans/ has no PLAN-001 | `PLAN-001` | docs/standards/IPLAN-CANONICALIZATION.md:97 |
| C-31 | Dead ref: "for self-certification, §2.2" — no §2.2 exists in VERSIONING or sibling docs | `§2.2` | docs/standards/VERSIONING.md:67 |
| C-32 | DEFINITIONS states literal `sha256(public_key) == executor_id` | `sha256(public_key) == executor_id` | docs/standards/IPLAN-DEFINITIONS.md:219 |
| C-33 | `executor_id` is the encoded form `^exec:[a-z2-7]{16,}$` | `^exec:[a-z2-7]{16,}$` | docs/standards/VERSIONING.md:59 |
| C-34 | DEFINITIONS claims format "is **not** assert[ed]" / tracked as backlog item 14 | `backlog item` | docs/standards/IPLAN-DEFINITIONS.md:21 |
| C-35 | Test asserts the date-time format checker is active (resolves #14) | `test_date_time_format_checker_is_active` | tests/contract/test_schema_contracts.py:450 |
| C-36 | DEFINITIONS defers attempt-result cross-mapping to "backlog #11 (retry policy)" | `backlog #11` | docs/standards/IPLAN-DEFINITIONS.md:62 |
| C-37 | IPLAN-STANDARD normatively defines Retry & Attempt Cap (final failed attempt → terminal `Failed` at line 336) | `Retry & Attempt Cap` | docs/standards/IPLAN-STANDARD.md:322 |
| C-38 | MANAGEMENT: "the chain registry record when it is introduced" — but the record exists and is specified live at lines 76-84 | `introduced` | docs/standards/IPLAN-MANAGEMENT.md:43 |
| C-39 | IPLAN-STANDARD retains "this workstream … This Iplanic standard package is a draft" framing | `Iplanic standard package` | docs/standards/IPLAN-STANDARD.md:350 |
| C-40 | HANDOFF open thread directs next work at "L1 golden-vector coverage + `intake_control.provenance` additive field" (already landed per ASSURANCE §9 "Landed (this version)" at docs/standards/IPLAN-ASSURANCE.md:204) | `intake_control.provenance` | HANDOFF.md:37 |
| C-41 | Numbers vector covers only small ints (42, -7, 0) | `neg` | tests/contract/canonicalization/vectors/canon_numbers.json:4 |
| C-42 | Spec: "Do **not** hand-roll number canonicalization — the ECMAScript number form is the error-prone part" | `error-prone` | docs/standards/IPLAN-CANONICALIZATION.md:45 |
| C-43 | Spec rules for strings/numbers/literals that lack vectors (minimal escaping; ECMAScript form; literals verbatim) | `minimal escaping` | docs/standards/IPLAN-CANONICALIZATION.md:37 |
| C-44 | README's two-line conformance definition is the only conformance clause | `A consumer conforms` | README.md:31 |
| C-45 | `schema_version` current value `1.3-draft` | `1.3-draft` | docs/standards/VERSIONING.md:19 |
| C-46 | Package `iplan-canonical` version `0.1.0` while tags reach v0.4.0 | `version = "0.1.0"` | pyproject.toml:7 |
| C-47 | Status Families table (rows at 51-63) has no chain-registry-record row and no EXEC-Ready row | `Registry record` | docs/standards/IPLAN-DEFINITIONS.md:53 |
| C-48 | Chain-record status = chain lifecycle states + registry-only `Archived` (documented only in MANAGEMENT) | `Archived` | docs/standards/IPLAN-MANAGEMENT.md:80 |
| C-49 | `rolled_back` exists in the lifecycle-event schema (no prose doc mentions it — grep verified) | `rolled_back` | schemas/iplan-lifecycle-event.schema.json:45 |
| C-50 | Execution diagram starts `Not Started -> Queued` | `Not Started -> Queued` | docs/standards/IPLAN-STANDARD.md:262 |
| C-51 | Diagram captioned "These Title-Case execution-record transitions"; DEFINITIONS puts `Not Started` in the Document-step family (docs/standards/IPLAN-DEFINITIONS.md:55) | `execution-record transitions` | docs/standards/IPLAN-STANDARD.md:269 |
| C-52 | MANAGEMENT import endpoint: `POST /projects/{project_id}/iplans/import` | `/iplans/import` | docs/standards/IPLAN-MANAGEMENT.md:196 |
| C-53 | TRANSPORT import endpoint: `POST /iplans/import` | `/iplans/import` | docs/standards/TRANSPORT-INTEGRATION.md:46 |
| C-54 | Artifact enum includes `coverage_report`/`lint_report`/`drift_report` (lines 31-35) | `coverage_report` | schemas/artifact.schema.json:31 |
| C-55 | `task.required_artifacts` enum has only 6 values (no coverage/lint/drift report) | `required_artifacts` | schemas/task.schema.json:55 |
| C-56 | ed25519 vector's embedded event signature says `"algorithm": "hmac-sha256"` (vector-level algorithm at line 43 is `ed25519`) | `hmac-sha256` | tests/contract/canonicalization/vectors/sig_ed25519.json:22 |
| C-57 | standards-drift workflow curls the drift script from `ci/v1.6.0` | `ci/v1.6.0` | .github/workflows/standards-drift.yml:30 |
| C-58 | links workflow header comment says `@ci/v1.9.4` while `uses:` lines pin v1.9.5 (lines 25, 33) | `ci/v1.9.4` | .github/workflows/links.yml:1 |
| C-59 | README conformance command has no dependency-install step | `unittest discover` | README.md:28 |
| C-60 | README docs list omits IPLAN-ASSURANCE | `PLAN-INGESTION-ADAPTERS` | README.md:21 |
| C-61 | ASSURANCE uses `client_id` (non-canonical; tenancy is org_id/project_id) | `client_id` | docs/standards/IPLAN-ASSURANCE.md:75 |
| C-62 | ASSURANCE references "existing `INTAKE-001` rules" with no pointer | `INTAKE-001` | docs/standards/IPLAN-ASSURANCE.md:86 |
| C-63 | CHANGELOG cites "docs/WORKFLOWS.md §2.1" unqualified (also line 19; file exists only in ../aidoc-flow-ci/docs/WORKFLOWS.md) | `docs/WORKFLOWS.md` | CHANGELOG.md:15 |
| C-64 | Orphan L1 paragraph detached under an unrelated entry | `Additive schema field` | CHANGELOG.md:64 |
| C-65 | ROADMAP says interlog extraction 2026-07-07; CHANGELOG:176 says 2026-07-06 | `2026-07-07` | ROADMAP.md:39 |
| C-66 | HANDOFF heading "## Current state (2026-07-08)" precedes a 2026-07-12 event | `Current state` | HANDOFF.md:8 |
| C-67 | ed25519 verify calls `bytes.fromhex(value)` unguarded (raises on malformed hex) | `bytes.fromhex` | iplan_canonical/signing.py:64 |
| C-68 | Schema `$id`s are unversioned on `iplanic.ai` (pattern across all 17, verified by grep) | `iplanic.ai` | schemas/artifact.schema.json:3 |
| C-69 | README governance section pins canon at `ci/v1.6.0` | `ci/v1.6.0` | README.md:51 |
| C-70 | README CLAUDE.md anchor contains a literal em dash (unresolvable fragment) | `per-repo-governance` | README.md:52 |
| C-71 | Templates pin `schema_version: "1.3-draft"` (same at line 5 of all 7 metadata-bearing templates) | `1.3-draft` | docs/standards/templates/IPLAN-TEMPLATE.yaml:5 |
| C-72 | Test hardcodes the `schema_version: "1.3-draft"` snippet for the chain template | `1.3-draft` | tests/contract/test_schema_contracts.py:666 |
| C-73 | L1 provenance vectors embed `"schema_version": "1.3-draft"` inside signed documents (all 3 vectors) | `1.3-draft` | tests/contract/provenance/vectors/accept_ed25519.json:5 |
| C-74 | IPLAN-ECOSYSTEM version table cites `1.3-draft` | `1.3-draft` | docs/standards/IPLAN-ECOSYSTEM.md:43 |

### Verified-absent claims (grep evidence, no line to cite)

- No `RFC 2119` / `BCP 14` / `RFC 8174` match anywhere in
  `docs/standards/` (F-14).
- No `docs/standards/README.md`, no `tests/contract/README.md`, no
  root/`.github/` `SECURITY.md`, no `Security Considerations` heading
  in any spec (F-27, F-28).
- No `description` key in `canon_*.json` vectors;
  `normalize_omit_vs_null.json` uses `note` (F-27).
- `rolled_back` absent from all `docs/standards/*.md` (F-18).
- Conformance suite baseline: `python3 -m pytest tests/contract -q` →
  67 passed, 203 subtests passed (run 2026-07-19).

## Review log

### Pass 1 - 2026-07-19 - author self-check

Findings folded: (1) Wave 3 heading blanket-labeled [CHG] though W3.5
is repo-level — heading corrected, per-item routing tags authoritative;
(2) W2.2 depended on the W4.4 docs index that lands in a later wave —
reworded to inline qualification with the shared paragraph deferred to
W4.4; (3) C-46 pyproject version citation verified first-hand and
symbol sharpened; (4) C-17 symbol re-pointed after the gate flagged a
split-phrase symbol. All ledger citations re-run through `check_plan.py
--root ..`.

### Pass 2 - 2026-07-19 - independent

Fresh-context adversarial review (Agent tool). Verified all 68 ledger
rows against source (incl. cross-repo C-1 against the framework GD-04
record), reproduced the conformance baseline, and hard-checked the fix
directions (F-03 banner-is-stale direction, W3.1 `-draft` bump
legality, W2.7 golden-hash safety, W1.5 target existence). 2
load-bearing findings + 3 nits, all folded: (1) W3 `schema_version`
bump blast radius was unstated (7 template pins, hardcoded test
snippet, signed provenance vectors, ECOSYSTEM table) → new W3.6 +
C-71..C-74; (2) W2.1 reject-code unification is a wire-semantics
choice, not editorial → re-routed [CHG] onto the Wave 3 change set,
with the W2.5 path-alignment editorial justification stated in-text;
(nits) C-2 split into C-2/C-69, PR-sequencing paragraph aligned with
W3.5's [repo] tag, F-23's anchor claim got ledger row C-70.

### Pass 3 - 2026-07-19 - independent

Second fresh-context adversarial review (Agent tool). Re-verified the
Pass-2 fold-ins (whole-repo `1.3-draft` grep confirming W3.6's blast
radius, W2.1/W2.5 routing justifications, C-69..C-74), spot-verified
ledger rows across C-1..C-68 for substance, reproduced the conformance
baseline, and confirmed complete F→wave mapping. **Zero load-bearing
findings.** 4 nits, all folded: W3.6 now names the VERSIONING
current-value line; the Wave-2 chapeau and sequencing sentence carve
out W2.1; the dead "§7" internal refs point at the Claim ledger; W1.4
rewrites (not renames) the ROADMAP next-phase content; acceptance
criterion 4 gained a stale-`1.3-draft` grep backstop.

**Result:** ready
