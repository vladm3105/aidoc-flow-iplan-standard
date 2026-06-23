# Plan Ingestion Adapters

How Iplanic converts plans from **any source** — a framework Layer 8 plan and
**any AI-agent plan** (Claude Code, Gemini CLI, Copilot, Codex, OpenRouter) — into
its own, intentionally-richer IPLAN standard. The IPLAN standard is the
**canonical hub**; it does **not** converge to a source. Companion to
[`IPLAN-ECOSYSTEM.md`](IPLAN-ECOSYSTEM.md),
[`IPLAN-MANAGEMENT.md`](IPLAN-MANAGEMENT.md) (the import pipeline), and
[`IPLAN-STANDARD.md`](IPLAN-STANDARD.md).

## 1. Principle

The IPLAN standard is a **superset** of any authoring format, because its job is
managing the execution + lifecycle of many IPLANs and chains (step→work_order→todo,
`executor_context`, `completion_gate`, runtime task payload, chains, evidence,
versioning/registry). A source plan is almost always **thinner**. So ingestion is
not a rename — it is **map + enrich + readiness-gate**, performed by a per-source
**adapter** in front of the existing import pipeline. No source standard is altered;
the IPLAN standard stays the hub.

## 2. Where adapters sit

```text
source plan ──adapter(source)──▶ iplan-document (+ chain) ──IMPORT PIPELINE──▶ records
   (L8 / Claude / Gemini / …)        (IPLAN standard)      normalize→hash→
                                                           validate→registry+version
                                                           →iplan-import-result
```

The adapter produces a candidate `iplan-document`/chain in the IPLAN standard; the
**unchanged** import pipeline ([`IPLAN-MANAGEMENT.md`](IPLAN-MANAGEMENT.md):
normalize → canonical-hash → validate → registry/version records →
`iplan-import-result`) then owns it. Adapters are a **front-end**, not a
replacement for the pipeline.

## 3. Adapter contract (per source)

Each adapter MUST define:

1. **Source detection** — how a payload is recognized as this source (explicit
   `source_kind` parameter and/or a signature/shape sniff).
2. **Mapping** — source fields/structure → `iplan-document` fields (e.g. prose or
   markdown tasks → `work_order` → `todos`; source ids → `iplan_id` candidate).
3. **Enrichment / defaults** — the standard-only fields the source lacks
   (`executor_context`, `completion_gate`, the `work_order` skeleton, `verification`)
   filled with **defined, documented defaults**, never silently guessed.
4. **Provenance** — stamp `source_framework` / `source_framework_version`
   (`iplan-document.metadata`) + a source-plan reference, for lineage.
5. **Readiness gating** — a converted thin plan is typically
   **`ready_with_warnings`**, not `ready`: the adapter records which control-plane
   fields are defaulted/missing so the `exec_ready_score` gate blocks dispatch until
   an author completes them. **Conversion ≠ approval.**
6. **Loss report** — what in the source could not be represented (returned in the
   import result `warnings`), so nothing is dropped silently.

A source whose minimum required fields cannot be mapped is **rejected** with a
typed reason (mirrors the import pipeline's accept/reject), not force-fitted.

## 4. Source set (framework-L8 first)

| Source | Shape | Adapter status |
| --- | --- | --- |
| framework L8 | 6-section L8 (`file_manifest`, `document_control`) | **first** — the reference adapter |
| Claude Code plan | markdown / prose task plan | planned |
| Gemini CLI / Copilot / Codex / OpenRouter | varied agent plan formats | planned |

The framework-L8 adapter is the reference implementation because the divergence is
already mapped (see [`IPLAN-ECOSYSTEM.md`](IPLAN-ECOSYSTEM.md) "Contract
divergence": L8 6 sections / `file_manifest` vs the standard's 13 sections /
`step→work_order→todo`).

## 5. Boundaries

- **Authoring stays upstream.** Adapters convert *approved/authored* plans into the
  managed standard; they do not author plans or invent execution intent beyond
  documented defaults.
- **No source-standard changes.** The source authoring formats are read-only;
  adapters live entirely in Iplanic.
- **Executor side is separate.** The remote executor consumes Iplanic's *dispatched
  task payload* and vendors a pinned mirror (see
  [`IPLAN-ECOSYSTEM.md`](IPLAN-ECOSYSTEM.md)); that edge is not an adapter.

## 6. Open questions

- **Default policy depth** — how much may an adapter default vs. how much MUST an
  author supply before `ready`? Tie the line to the `exec_ready_score ≥ 90` gate.
- **Markdown/prose plans** — extraction strategy for unstructured agent plans
  (LLM-assisted mapping vs. strict structured input only).
- **Chain inference** — can an adapter emit an IPLAN *chain* from a multi-plan
  source, or only single IPLANs initially?
- **Adapter versioning** — pinning the adapter ↔ standard-version compatibility
  (ties to schema versioning).

## 7. Implementation step

An implementation step defines the adapter-layer contract as a schema/interface +
implements the **framework-L8 reference adapter** with golden conversion vectors
(L8 input → expected `iplan-document` + import result), following a
verified-planning + golden-vector discipline.

## 8. Cross-references

- [`IPLAN-ECOSYSTEM.md`](IPLAN-ECOSYSTEM.md) — roles, divergence, the hub + adapter resolution.
- [`IPLAN-MANAGEMENT.md`](IPLAN-MANAGEMENT.md) — the import pipeline + `iplan-import-result`.
- [`IPLAN-STANDARD.md`](IPLAN-STANDARD.md) — the target standard adapters map into.
