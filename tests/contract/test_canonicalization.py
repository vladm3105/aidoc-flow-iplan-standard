"""Contract tests: the iplan_canonical reference module must reproduce the
golden canonicalization + signature vectors (PLAN-001).

Vectors are the source of truth (RFC 8785 JCS + sha256 + hmac/ed25519); the
module under test must produce byte-identical canonical forms, hashes, and
signatures.
"""

import json
import pathlib
import unittest

import iplan_canonical as ic

VEC_DIR = pathlib.Path(__file__).parent / "canonicalization" / "vectors"


def load(name):
    return json.loads((VEC_DIR / f"{name}.json").read_text())


class TestCanonicalization(unittest.TestCase):
    def test_canonical_vectors(self):
        for path in sorted(VEC_DIR.glob("canon_*.json")):
            v = json.loads(path.read_text())
            with self.subTest(vector=path.stem):
                self.assertEqual(ic.canonicalize(v["input"]), v["canonical"].encode("utf-8"))
                self.assertEqual(ic.canonical_hash(v["input"]), v["sha256"])

    def test_absent_vs_null_normalization(self):
        v = load("normalize_omit_vs_null")
        self.assertEqual(
            ic.canonical_hash(v["input_omit"]),
            ic.canonical_hash(v["input_null"]),
        )
        self.assertEqual(ic.canonical_hash(v["input_omit"]), v["sha256"])

    def test_signing_payload_excludes_signature_and_received_at(self):
        v = load("sig_hmac")
        payload = ic.signing_payload(v["event"])
        self.assertNotIn("signature", payload)
        self.assertNotIn("received_at", payload)
        self.assertNotIn("protocol_plan_id", payload)  # null dropped
        self.assertEqual(payload, v["signing_payload"])

    def test_signing_payload_omit_vs_null_identical(self):
        base = {"org_id": "o", "task_id": "t", "event_type": "task.completed"}
        with_null = {**base, "protocol_plan_id": None}
        self.assertEqual(ic.signing_payload(base), ic.signing_payload(with_null))
        self.assertEqual(
            ic.canonical_hash(ic.signing_payload(base)),
            ic.canonical_hash(ic.signing_payload(with_null)),
        )

    def test_hmac_signature_vector(self):
        v = load("sig_hmac")
        value = ic.sign(
            ic.signing_payload(v["event"]),
            algorithm="hmac-sha256",
            key=bytes.fromhex(v["key_hex"]),
        )
        self.assertEqual(value, v["value"])
        self.assertTrue(
            ic.verify(
                ic.signing_payload(v["event"]),
                value,
                algorithm="hmac-sha256",
                key=bytes.fromhex(v["key_hex"]),
            )
        )

    def test_ed25519_signature_vector(self):
        v = load("sig_ed25519")
        value = ic.sign(
            ic.signing_payload(v["event"]),
            algorithm="ed25519",
            key=bytes.fromhex(v["ed25519_seed_hex"]),
        )
        self.assertEqual(value, v["value"])
        self.assertTrue(
            ic.verify(
                ic.signing_payload(v["event"]),
                value,
                algorithm="ed25519",
                key=bytes.fromhex(v["ed25519_public_hex"]),
            )
        )

    def test_evidence_seal_hash_covers_payload_and_manifest(self):
        v = load("seal_hash")
        self.assertEqual(
            ic.evidence_seal_hash(v["payload"], v["evidence_manifest"]),
            v["sha256"],
        )


REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
SCHEMA_DIR = REPO_ROOT / "schemas"
SPEC_DOC = REPO_ROOT / "docs" / "standards" / "IPLAN-CANONICALIZATION.md"
HEX64 = "^[a-fA-F0-9]{64}$"


def _find(node, key):
    """Yield every dict value stored under ``key`` anywhere in ``node``."""
    if isinstance(node, dict):
        for k, v in node.items():
            if k == key and isinstance(v, dict):
                yield v
            yield from _find(v, key)
    elif isinstance(node, list):
        for v in node:
            yield from _find(v, key)


class TestSchemaCanonicalHashConsistency(unittest.TestCase):
    """Every canonical_hash across the schemas is sha256 over iplan-canonical-json."""

    def test_every_canonical_hash_is_sha256_hex64(self):
        seen = 0
        for path in sorted(SCHEMA_DIR.glob("*.json")):
            schema = json.loads(path.read_text())
            for ch in _find(schema, "canonical_hash"):
                props = ch.get("properties")
                if not props:  # a $ref-style or value usage, not the object def
                    continue
                seen += 1
                with self.subTest(schema=path.name):
                    self.assertEqual(props["algorithm"].get("enum"), ["sha256"])
                    self.assertEqual(props["value"].get("pattern"), HEX64)
        self.assertGreaterEqual(seen, 7)  # >=1 per the 7 carrier schemas

    def test_canonicalization_block_names_iplan_canonical_json(self):
        version_schema = json.loads((SCHEMA_DIR / "iplan-version.schema.json").read_text())
        blocks = list(_find(version_schema, "canonicalization"))
        self.assertTrue(blocks)
        for block in blocks:
            self.assertEqual(block["properties"]["algorithm"].get("enum"), ["iplan-canonical-json"])

    def test_spec_doc_exists_and_version_matches_module(self):
        self.assertTrue(SPEC_DOC.exists(), "IPLAN-CANONICALIZATION.md missing")
        text = SPEC_DOC.read_text()
        self.assertIn("iplan-canonical-json", text)
        self.assertIn(ic.CANONICALIZATION_VERSION, text)  # module pin appears in spec


if __name__ == "__main__":
    unittest.main()
