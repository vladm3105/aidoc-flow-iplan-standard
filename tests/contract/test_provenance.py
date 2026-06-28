"""Contract tests: L1 initiator-provenance (IPLAN-ASSURANCE.md §2).

The golden vectors under ``provenance/vectors/`` are the source of truth that both
Iplanic (import-time verify) and a remote executor (intake provenance gate)
validate against. Each vector carries a real signature produced by the normative
``iplan_canonical`` reference signer over the **canonical IPLAN with
``intake_control`` excluded** (the envelope cannot sign itself).

These tests pin three things so the rule, the schema, and the signer can never
silently drift: (1) every vector document is schema-valid against
``iplan-document.schema.json`` (exercising the additive ``intake_control``
field), (2) the reference verification reproduces each vector's ``expected``
outcome, and (3) an L0 document (no ``intake_control``) stays schema-valid
(the field is optional/backward-compatible).
"""

from __future__ import annotations

import json
import pathlib
import unittest

import jsonschema

from iplan_canonical.canonical import drop_null
from iplan_canonical.signing import verify

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
SCHEMA_DIR = REPO_ROOT / "schemas"
VEC_DIR = pathlib.Path(__file__).parent / "provenance" / "vectors"

_DOC_SCHEMA = json.loads((SCHEMA_DIR / "iplan-document.schema.json").read_text())
VECTORS = sorted(VEC_DIR.glob("*.json"))


def provenance_signing_payload(document: dict) -> dict:
    """Reference L1 signed-payload view: the IPLAN minus ``intake_control``,
    drop-null normalized (IPLAN-ASSURANCE.md §2). Mirrors ``signing_payload`` for
    execution-events (the signed surface excludes the envelope that carries it)."""
    return drop_null({k: v for k, v in document.items() if k != "intake_control"})


def verify_provenance(document: dict, keyring: dict) -> bool:
    """Reference L1 verification: resolve ``initiator_key_id`` in the keyring and
    verify the detached signature over the canonical signed payload."""
    env = document["intake_control"]["provenance"]
    entry = keyring[env["initiator_key_id"]]
    key = bytes.fromhex(entry["public_key"] if env["algorithm"] == "ed25519" else entry["secret_hex"])
    return verify(provenance_signing_payload(document), env["value"], algorithm=env["algorithm"], key=key)


class ProvenanceVectorTests(unittest.TestCase):
    def test_vectors_present(self) -> None:
        self.assertTrue(VECTORS, "no L1 provenance vectors found")

    def test_documents_are_schema_valid(self) -> None:
        for path in VECTORS:
            v = json.loads(path.read_text())
            with self.subTest(vector=path.name):
                jsonschema.validate(v["document"], _DOC_SCHEMA)  # exercises the additive intake_control

    def test_verification_matches_expected(self) -> None:
        for path in VECTORS:
            v = json.loads(path.read_text())
            with self.subTest(vector=path.name):
                self.assertEqual(verify_provenance(v["document"], v["keyring"]), v["expected"]["verifies"])

    def test_l0_document_without_intake_control_is_valid(self) -> None:
        # backward-compatibility: intake_control is optional, so an L0 document omitting it still validates.
        any_doc = json.loads(VECTORS[0].read_text())["document"]
        l0 = {k: x for k, x in any_doc.items() if k != "intake_control"}
        jsonschema.validate(l0, _DOC_SCHEMA)


if __name__ == "__main__":
    unittest.main()
