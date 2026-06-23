"""Contract tests: the tenant scope-check rule (PLAN-003, backlog #3, D-0023).

`scope_decision` is the reference spec implementation of the accept-iff rule in
`IPLAN-DEFINITIONS.md` (Tenant Scope-Check). The golden vectors under
`scope_check/vectors/` are the source of truth that both Iplanic ingestion and a
remote executor (iplan-runner) validate against. These tests pin the predicate to the
vectors, the vector reason codes to the normative DEFINITIONS reject table, and
the field names to the live schemas — so the rule, the doc, and the schemas can
never silently drift.

Scope of the predicate: clauses 1-4 only. Signature verification sits between
clauses 2 and 3 in the runtime ingestion pipeline and is out of scope here
(vectors carry no signature).
"""

import json
import pathlib
import re
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
SCHEMA_DIR = REPO_ROOT / "schemas"
DEFS_DOC = REPO_ROOT / "docs" / "standards" / "IPLAN-DEFINITIONS.md"
VEC_DIR = pathlib.Path(__file__).parent / "scope_check" / "vectors"


def scope_decision(event, registrations):
    """Reference implementation of the Tenant Scope-Check accept-iff rule.

    Returns ``(accept: bool, reason: str | None)``. Clauses are evaluated in
    order; the first failing clause is the reason (deterministic).
    """
    registration = next((r for r in registrations if r["executor_id"] == event["executor_id"]), None)
    if registration is None:  # clause 1
        return (False, "unregistered_executor")
    if registration["status"] != "active":  # clause 2 (ingest-time status)
        return (False, "executor_not_active")
    if event["project_id"] not in registration["allowed_projects"]:  # clause 3 (empty => deny)
        return (False, "project_not_allowed")
    if event["org_id"] != registration["owner_org_id"]:  # clause 4 (org): same-org or cross-org grant
        # A first_party executor may serve a cross-org (org_id, project_id) named in
        # cross_org_grants[]. The grant relaxes only the org check — project_id is
        # still required in allowed_projects (clause 3, above). Failing clause 4
        # stays org_mismatch (no new reason code).
        granted = {"org_id": event["org_id"], "project_id": event["project_id"]} in registration.get(
            "cross_org_grants", []
        )
        if not (granted and registration.get("trust_level") == "first_party"):
            return (False, "org_mismatch")
    return (True, None)


def _load_schema(name):
    return json.loads((SCHEMA_DIR / name).read_text())


EVENT_SCHEMA = _load_schema("execution-event.schema.json")
REGISTRATION_SCHEMA = _load_schema("executor-registration.schema.json")
VECTORS = sorted(VEC_DIR.glob("*.json"))

FIRST_CODE = re.compile(r"`([^`]+)`")
REASON_CODE = re.compile(r"^[a-z]+(?:_[a-z]+)+$")


def _doc_reason_codes():
    """Reason codes from the DEFINITIONS 'Tenant Scope-Check' reject table."""
    lines = DEFS_DOC.read_text().splitlines()
    codes = set()
    in_section = False
    for line in lines:
        if line.startswith("## Tenant Scope-Check"):
            in_section = True
            continue
        if in_section and line.startswith("## "):
            break
        if in_section and line.startswith("|"):
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            m = FIRST_CODE.search(cells[0]) if cells else None
            if m and REASON_CODE.match(m.group(1)):
                codes.add(m.group(1))
    return codes


class TestScopeCheck(unittest.TestCase):
    def test_vectors(self):
        self.assertTrue(VECTORS, "no scope-check vectors found")
        for path in VECTORS:
            v = json.loads(path.read_text())
            accept, reason = scope_decision(v["event"], v["registrations"])
            with self.subTest(vector=path.stem):
                self.assertEqual(accept, v["expected"]["accept"])
                self.assertEqual(reason, v["expected"]["reason"])

    def test_every_reject_reason_has_a_vector_and_vice_versa(self):
        doc_reasons = _doc_reason_codes()
        self.assertEqual(
            doc_reasons,
            {"unregistered_executor", "executor_not_active", "project_not_allowed", "org_mismatch"},
        )
        vector_reasons = set()
        for path in VECTORS:
            reason = json.loads(path.read_text())["expected"]["reason"]
            if reason is not None:
                vector_reasons.add(reason)
        self.assertEqual(vector_reasons, doc_reasons)  # one-to-one, no orphan either way

    def test_clause_precedence_is_deterministic(self):
        # an event failing both clause 3 (project) and clause 4 (org) reports the
        # earlier clause's reason.
        both = {"org_id": "org-x", "project_id": "nope", "executor_id": "exec:pppppppppppppppp"}
        regs = [
            {
                "executor_id": "exec:pppppppppppppppp",
                "owner_org_id": "org-y",
                "allowed_projects": ["yes"],
                "status": "active",
            }
        ]
        self.assertEqual(scope_decision(both, regs), (False, "project_not_allowed"))

    def test_predicate_field_names_exist_in_schemas(self):
        event_props = EVENT_SCHEMA["properties"]
        for field in ("org_id", "project_id", "executor_id"):
            self.assertIn(field, event_props)
        reg_props = REGISTRATION_SCHEMA["properties"]
        for field in ("owner_org_id", "allowed_projects", "status"):
            self.assertIn(field, reg_props)

    def test_active_is_the_only_accepting_status(self):
        # every non-active status in the registration enum must reject (clause 2).
        statuses = REGISTRATION_SCHEMA["properties"]["status"]["enum"]
        base_event = {"org_id": "o", "project_id": "p", "executor_id": "exec:ssssssssssssssss"}
        for status in statuses:
            regs = [
                {
                    "executor_id": "exec:ssssssssssssssss",
                    "owner_org_id": "o",
                    "allowed_projects": ["p"],
                    "status": status,
                }
            ]
            accept, reason = scope_decision(base_event, regs)
            with self.subTest(status=status):
                if status == "active":
                    self.assertTrue(accept)
                else:
                    self.assertEqual((accept, reason), (False, "executor_not_active"))


if __name__ == "__main__":
    unittest.main()
