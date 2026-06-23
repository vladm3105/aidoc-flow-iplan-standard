# Contributing

Thanks for your interest in the **IPLAN standard**. This repo is the neutral,
versioned source of truth for the IPLAN contracts — the schemas,
canonicalization, and the prose spec — consumed by iplanic, `iplan-runner`, and
third parties.

## Scope

This repo holds the **contract**, not any implementation runtime. Changes here:

- **Schemas** (`schemas/`) — the normative shapes. Additive, optional changes are
  backward-compatible (minor); removing/renaming a required field, tightening a
  type, or changing an enum is **breaking** (major).
- **Canonicalization** (`iplan_canonical/`) — the reference RFC 8785 algorithm +
  signing. Any change here is contract-affecting; the golden vectors in
  `tests/contract/canonicalization/vectors/` are the gate.
- **Spec docs** (`docs/standards/`) — keep neutral: describe the contract, not
  any one product's internals.

## The conformance suite is the gate

```bash
pip install -e ".[dev]"
PYTHONPATH=. python -m unittest discover -s tests/contract
ruff check iplan_canonical tests
```

Every schema must validate its template/fixtures; canonicalization must match the
golden vectors. A change that alters a vector or a required field needs a
**version bump** (see `docs/standards/VERSIONING.md`) and a CHANGELOG entry.

## Versioning & release

The standard ships independently semver-tagged — `iplan/vX.Y.Z`. Consumers pin a
tag. Cut a tag after a logical contract change; record it in `CHANGELOG.md`.
