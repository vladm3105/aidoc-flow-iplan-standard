"""Contract tests: the canonical status projection (PLAN-002, backlog #2).

The projection vector (`status_projection/projection.json`) is the source of
truth for how a signed `execution-event` projects onto execution-record status,
and how the record task status corresponds to the document/TODO-plane step
status. These tests pin the vector to the live schema enums and to the normative
table in `IPLAN-DEFINITIONS.md`, so the doc, the schemas, and the vector can
never silently drift.
"""

import json
import pathlib
import re
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
SCHEMA_DIR = REPO_ROOT / "schemas"
DEFS_DOC = REPO_ROOT / "docs" / "standards" / "IPLAN-DEFINITIONS.md"
VECTOR = pathlib.Path(__file__).parent / "status_projection" / "projection.json"


def _enum_at(schema, *path):
    node = schema
    for key in path:
        node = node[key]
    return node["enum"]


def _find_enum(node, *required):
    """Return the first ``enum`` array that contains all ``required`` members."""
    req = set(required)
    if isinstance(node, dict):
        enum = node.get("enum")
        if isinstance(enum, list) and req.issubset(set(enum)):
            return enum
        for value in node.values():
            found = _find_enum(value, *required)
            if found is not None:
                return found
    elif isinstance(node, list):
        for value in node:
            found = _find_enum(value, *required)
            if found is not None:
                return found
    return None


def _load(name):
    return json.loads((SCHEMA_DIR / name).read_text())


VEC = json.loads(VECTOR.read_text())
EVENT = _load("execution-event.schema.json")
RECORD = _load("iplan-execution-record.schema.json")
DOCUMENT = _load("iplan-document.schema.json")

EVENT_TYPE_ENUM = _enum_at(EVENT, "properties", "event_type")
EVENT_STATUS_ENUM = _enum_at(EVENT, "properties", "status")
RECORD_TASK_STATUS_ENUM = _enum_at(RECORD, "properties", "tasks", "items", "properties", "status")
DOC_STEP_ENUM = _enum_at(DOCUMENT, "properties", "plan", "properties", "steps", "items", "properties", "status")

FIRST_CODE = re.compile(r"`([^`]+)`")


def _doc_projection_pairs():
    """Parse the (event_type -> record task status) pairs from the normative
    'Runtime: event -> execution record' table in IPLAN-DEFINITIONS.md."""
    lines = DEFS_DOC.read_text().splitlines()
    pairs = set()
    in_section = False
    for line in lines:
        if line.startswith("### Runtime: event"):
            in_section = True
            continue
        if in_section and line.startswith("#"):
            break
        if in_section and line.startswith("|"):
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if len(cells) < 3:
                continue
            et = FIRST_CODE.search(cells[0])
            rs = FIRST_CODE.search(cells[2])
            if et and rs and et.group(1) in EVENT_TYPE_ENUM:
                pairs.add((et.group(1), rs.group(1)))
    return pairs


class TestStatusProjection(unittest.TestCase):
    def test_event_types_and_statuses_are_in_schema_enums(self):
        for row in VEC["event_to_record"]:
            with self.subTest(event_type=row["event_type"]):
                self.assertIn(row["event_type"], EVENT_TYPE_ENUM)
                self.assertIn(row["event_status"], EVENT_STATUS_ENUM)

    def test_record_task_status_targets_are_in_schema_enum(self):
        for row in VEC["event_to_record"]:
            with self.subTest(event_type=row["event_type"]):
                self.assertIn(row["record_task_status"], RECORD_TASK_STATUS_ENUM)

    def test_projection_is_total_over_all_event_types(self):
        mapped = {row["event_type"] for row in VEC["event_to_record"]}
        self.assertEqual(mapped, set(EVENT_TYPE_ENUM))
        self.assertEqual(len(VEC["event_to_record"]), len(EVENT_TYPE_ENUM))  # no dup rows

    def test_doc_table_matches_vector(self):
        vector_pairs = {(r["event_type"], r["record_task_status"]) for r in VEC["event_to_record"]}
        self.assertEqual(_doc_projection_pairs(), vector_pairs)

    def test_document_step_correspondence(self):
        # document-step targets are valid document step statuses (or the
        # pre-dispatch 'Not Started', which no record status maps to).
        allowed_doc_steps = set(DOC_STEP_ENUM) | {"Not Started"}
        for record_status, doc_step in VEC["document_step_correspondence"].items():
            with self.subTest(record_status=record_status):
                self.assertIn(record_status, RECORD_TASK_STATUS_ENUM)
                self.assertIn(doc_step, allowed_doc_steps)
        # the terminal completion link is normative: task.completed -> Completed,
        # consistent with the document's completion_event const.
        completed_rows = [r for r in VEC["event_to_record"] if r["event_type"] == "task.completed"]
        self.assertEqual(completed_rows[0]["record_task_status"], "Completed")
        self.assertEqual(VEC["document_step_correspondence"]["Completed"], "Completed")
        self.assertEqual(_completion_event_const(), "task.completed")


def _completion_event_const(node=DOCUMENT):
    if isinstance(node, dict):
        if "completion_event" in node and isinstance(node["completion_event"], dict):
            const = node["completion_event"].get("const")
            if const is not None:
                return const
        for value in node.values():
            found = _completion_event_const(value)
            if found is not None:
                return found
    elif isinstance(node, list):
        for value in node:
            found = _completion_event_const(value)
            if found is not None:
                return found
    return None


if __name__ == "__main__":
    unittest.main()
