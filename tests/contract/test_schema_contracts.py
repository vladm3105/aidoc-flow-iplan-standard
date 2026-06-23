from __future__ import annotations

import json
import unittest
from pathlib import Path

import jsonschema
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_ROOT = REPO_ROOT / "schemas"
STANDARD_TEMPLATE_ROOT = REPO_ROOT / "docs" / "standards" / "templates"
FIXTURE_ROOT = Path(__file__).resolve().parent / "fixtures"

# Templates that double as schema-valid reference instances (PLAN-005 / #9). The
# distinct schema *values* (7) are the template-covered set; every other schema is
# template-less and is instead covered by a fixture in FIXTURE_ROOT (PLAN-009).
TEMPLATE_TO_SCHEMA = {
    "IPLAN-CHAIN-TEMPLATE.yaml": "iplan-chain.schema.json",
    "IPLAN-COMPARISON.TEMPLATE.yaml": "iplan-comparison.schema.json",
    "IPLAN-EVIDENCE-BUNDLE.TEMPLATE.yaml": "iplan-evidence-bundle.schema.json",
    "IPLAN-EXECUTION-RECORD.TEMPLATE.yaml": "iplan-execution-record.schema.json",
    "IPLAN-TASK-TEMPLATE.yaml": "task.schema.json",
    "IPLAN-TEMPLATE.yaml": "iplan-document.schema.json",
    "TMP-IPLAN-CORRECTION.TEMPLATE.yaml": "tmp-iplan.schema.json",
    "TMP-IPLAN-INVESTIGATION.TEMPLATE.yaml": "tmp-iplan.schema.json",
    "TMP-IPLAN-TEMPLATE.yaml": "tmp-iplan.schema.json",
}

# One schema-valid instance per template-less schema (PLAN-009, Phase A). Keyed by
# fixture filename under FIXTURE_ROOT, valued by the schema it must validate against.
FIXTURE_TO_SCHEMA = {
    "artifact.json": "artifact.schema.json",
    "execution-event.json": "execution-event.schema.json",
    "executor-registration.json": "executor-registration.schema.json",
    "iplan-import-result.json": "iplan-import-result.schema.json",
    "iplan-lifecycle-event.json": "iplan-lifecycle-event.schema.json",
    "iplan-record.json": "iplan-record.schema.json",
    "iplan-validation-report.json": "iplan-validation-report.schema.json",
    "iplan-version.json": "iplan-version.schema.json",
    "iplan-chain-version.json": "iplan-chain-version.schema.json",
    "iplan-chain-record.json": "iplan-chain-record.schema.json",
}


class SchemaContractTests(unittest.TestCase):
    def test_remote_executor_contract_schemas_exist_and_are_structured(self) -> None:
        expected = {
            "artifact.schema.json",
            "executor-registration.schema.json",
            "execution-event.schema.json",
            "iplan-chain.schema.json",
            "iplan-chain-record.schema.json",
            "iplan-chain-version.schema.json",
            "iplan-comparison.schema.json",
            "iplan-document.schema.json",
            "iplan-evidence-bundle.schema.json",
            "iplan-execution-record.schema.json",
            "iplan-import-result.schema.json",
            "iplan-lifecycle-event.schema.json",
            "iplan-record.schema.json",
            "iplan-validation-report.schema.json",
            "iplan-version.schema.json",
            "task.schema.json",
            "tmp-iplan.schema.json",
        }

        for schema_name in expected:
            with self.subTest(schema=schema_name):
                schema_path = SCHEMA_ROOT / schema_name
                self.assertTrue(schema_path.exists(), f"Missing schema: {schema_path}")

                schema = json.loads(schema_path.read_text(encoding="utf-8"))
                self.assertEqual(schema["type"], "object")
                self.assertIsInstance(schema["required"], list)
                self.assertIsInstance(schema["properties"], dict)

    def test_execution_event_schema_requires_protocol_fields(self) -> None:
        schema_path = SCHEMA_ROOT / "execution-event.schema.json"
        schema = json.loads(schema_path.read_text(encoding="utf-8"))

        required_fields = set(schema["required"])
        expected_fields = {
            "org_id",
            "project_id",
            "iplan_id",
            "plan_version_id",
            "run_id",
            "task_id",
            "step_id",
            "executor_id",
            "trace_id",
            "event_id",
            "idempotency_key",
            "event_type",
            "occurred_at",
            "received_at",
            "status",
            "artifact_refs",
            "signature",
        }

        self.assertTrue(
            expected_fields.issubset(required_fields),
            f"Execution event schema missing fields: {sorted(expected_fields - required_fields)}",
        )

    def test_execution_event_taxonomy_uses_task_completion_events(self) -> None:
        schema_path = SCHEMA_ROOT / "execution-event.schema.json"
        schema = json.loads(schema_path.read_text(encoding="utf-8"))

        event_types = set(schema["properties"]["event_type"]["enum"])

        self.assertTrue(
            {"task.blocked", "task.completed", "task.failed"}.issubset(event_types),
            "Execution events must expose task lifecycle completion events.",
        )
        self.assertFalse(
            {"agent.blocked", "agent.completed", "agent.failed"} & event_types,
            "Execution event schema should use executor/task terminology, not agent lifecycle events.",
        )

    def test_protocol_schemas_use_executor_identity(self) -> None:
        for schema_name in {
            "artifact.schema.json",
            "execution-event.schema.json",
            "executor-registration.schema.json",
            "task.schema.json",
        }:
            with self.subTest(schema=schema_name):
                schema = json.loads((SCHEMA_ROOT / schema_name).read_text(encoding="utf-8"))
                required_fields = set(schema["required"])
                properties = set(schema["properties"])

                self.assertIn("executor_id", required_fields)
                self.assertIn("executor_id", properties)
                self.assertNotIn("agent_id", required_fields)
                self.assertNotIn("assigned_agent_id", required_fields)

    def test_executor_id_enforces_hash_form_pattern(self) -> None:
        # executor_id is the self-certifying hash identity (D-0031): every schema
        # that carries it constrains it with ^exec:[a-z2-7]{16,}$, so a free string
        # like the legacy "exec-hermes-01" can never validate. Covers all six field
        # sites across the five carrier schemas: four single-occurrence schemas +
        # three in iplan-execution-record (tasks / assignments / events) = seven.
        pattern = "^exec:[a-z2-7]{16,}$"
        sites = 0

        def executor_id_schemas(node: object):
            if isinstance(node, dict):
                for key, value in node.items():
                    if key == "executor_id" and isinstance(value, dict):
                        yield value
                    else:
                        yield from executor_id_schemas(value)
            elif isinstance(node, list):
                for item in node:
                    yield from executor_id_schemas(item)

        for schema_name in (
            "artifact.schema.json",
            "execution-event.schema.json",
            "executor-registration.schema.json",
            "task.schema.json",
            "iplan-execution-record.schema.json",
        ):
            schema = json.loads((SCHEMA_ROOT / schema_name).read_text(encoding="utf-8"))
            for definition in executor_id_schemas(schema):
                sites += 1
                with self.subTest(schema=schema_name):
                    self.assertEqual(definition.get("pattern"), pattern)

        self.assertEqual(sites, 7, "expected seven executor_id field sites across the five schemas")

        # A non-conforming legacy id is rejected; a conforming one is accepted.
        registration = json.loads((SCHEMA_ROOT / "executor-registration.schema.json").read_text(encoding="utf-8"))
        validator = jsonschema.Draft202012Validator(registration)
        self.assertFalse(validator.is_valid({"executor_id": "exec-hermes-01"}))
        self.assertTrue(
            all(e.validator != "pattern" for e in validator.iter_errors({"executor_id": "exec:hermes2zqf7kx3a4b5c6d"}))
        )

    def test_iplan_document_schema_requires_operational_sections(self) -> None:
        schema_path = SCHEMA_ROOT / "iplan-document.schema.json"
        schema = json.loads(schema_path.read_text(encoding="utf-8"))

        required_fields = set(schema["required"])
        expected_fields = {
            "metadata",
            "intent",
            "lineage",
            "scope",
            "initialization",
            "start_conditions",
            "plan",
            "files",
            "verification",
            "evidence_requirements",
            "completion_gate",
            "handoff",
            "navigation",
        }

        self.assertTrue(
            expected_fields.issubset(required_fields),
            f"IPLAN document schema missing fields: {sorted(expected_fields - required_fields)}",
        )

    def test_iplan_document_schema_enforces_exec_ready_shape(self) -> None:
        schema_path = SCHEMA_ROOT / "iplan-document.schema.json"
        schema = json.loads(schema_path.read_text(encoding="utf-8"))

        properties = schema["properties"]
        step_schema = properties["plan"]["properties"]["steps"]["items"]

        self.assertFalse(schema["additionalProperties"])
        self.assertGreaterEqual(properties["files"]["minItems"], 1)
        self.assertGreaterEqual(properties["plan"]["properties"]["steps"]["minItems"], 1)
        self.assertTrue(
            {
                "step_id",
                "title",
                "intent",
                "dependencies",
                "executor_capabilities",
                "target_files",
                "commands",
                "expected_outputs",
                "evidence_required",
                "status",
            }.issubset(set(step_schema["required"]))
        )
        self.assertTrue(
            {"exec_ready_score", "required_commands", "completion_criteria"}.issubset(
                set(properties["verification"]["required"])
            )
        )
        self.assertTrue(
            {"current_state", "resume_from_step", "blockers", "sessions"}.issubset(
                set(properties["handoff"]["required"])
            )
        )

    def test_iplan_document_schema_defines_initialization_start_and_completion_gates(self) -> None:
        schema = json.loads((SCHEMA_ROOT / "iplan-document.schema.json").read_text(encoding="utf-8"))

        initialization_schema = schema["properties"]["initialization"]
        start_schema = schema["properties"]["start_conditions"]
        completion_schema = schema["properties"]["completion_gate"]

        self.assertTrue(
            {
                "required_status",
                "version_record_ref",
                "validation_report_id",
                "approval_event_id",
                "approved_hash",
                "runtime_records",
            }.issubset(set(initialization_schema["required"]))
        )
        self.assertTrue(
            {
                "required_state",
                "required_readiness",
                "required_resources",
                "policy_checks",
                "context_checks",
                "start_events",
            }.issubset(set(start_schema["required"]))
        )
        self.assertTrue(
            {
                "criteria",
                "required_events",
                "required_artifacts",
                "evidence_bundle_required",
                "final_state",
            }.issubset(set(completion_schema["required"]))
        )

    def test_iplan_chain_schema_enforces_dependency_and_tier_shape(self) -> None:
        schema_path = SCHEMA_ROOT / "iplan-chain.schema.json"
        schema = json.loads(schema_path.read_text(encoding="utf-8"))

        dependency_schema = schema["properties"]["dependencies"]["items"]
        tier_schema = schema["properties"]["execution_path"]["properties"]["tiers"]["items"]

        self.assertTrue(
            {"dependency_id", "from", "to", "type", "gate", "reason"}.issubset(set(dependency_schema["required"]))
        )
        self.assertEqual({"blocks", "informs", "optional"}, set(dependency_schema["properties"]["type"]["enum"]))
        self.assertTrue(
            {
                "tier",
                "label",
                "entry_gate",
                "plan_sequence",
                "parallel_safe",
                "dispatch_policy",
                "exit_gate",
            }.issubset(set(tier_schema["required"]))
        )
        self.assertGreaterEqual(tier_schema["properties"]["plan_sequence"]["minItems"], 1)

    def test_iplan_chain_schema_binds_immutable_plan_versions(self) -> None:
        schema_path = SCHEMA_ROOT / "iplan-chain.schema.json"
        schema = json.loads(schema_path.read_text(encoding="utf-8"))

        plan_schema = schema["properties"]["plans"]["items"]
        canonical_hash_schema = plan_schema["properties"]["canonical_hash"]

        self.assertTrue(
            {
                "iplan_id",
                "plan_version",
                "plan_version_id",
                "title",
                "status",
                "file_path",
                "artifact_ref",
                "canonical_hash",
                "exec_ready_status",
                "approved_at",
            }.issubset(set(plan_schema["required"]))
        )
        self.assertTrue({"algorithm", "value"}.issubset(set(canonical_hash_schema["required"])))

    def test_iplan_chain_schema_models_cross_plan_work_order_dependencies(self) -> None:
        schema_path = SCHEMA_ROOT / "iplan-chain.schema.json"
        schema = json.loads(schema_path.read_text(encoding="utf-8"))

        dependency_schema = schema["properties"]["dependencies"]["items"]
        from_ref_schema = dependency_schema["properties"]["from"]
        to_ref_schema = dependency_schema["properties"]["to"]

        expected_ref_fields = {"iplan_id", "step_id", "work_order_id"}
        self.assertTrue(expected_ref_fields.issubset(set(from_ref_schema["required"])))
        self.assertTrue(expected_ref_fields.issubset(set(to_ref_schema["required"])))
        self.assertEqual(
            {"completion_required", "evidence_required", "approval_required", "context_available"},
            set(dependency_schema["properties"]["gate"]["enum"]),
        )

    def test_iplan_chain_schema_defines_ordered_dispatch_and_gates(self) -> None:
        schema_path = SCHEMA_ROOT / "iplan-chain.schema.json"
        schema = json.loads(schema_path.read_text(encoding="utf-8"))

        execution_path_schema = schema["properties"]["execution_path"]
        tier_schema = execution_path_schema["properties"]["tiers"]["items"]
        sequence_schema = tier_schema["properties"]["plan_sequence"]["items"]

        self.assertIn("strategy", execution_path_schema["required"])
        self.assertEqual({"tiered_dag"}, set(execution_path_schema["properties"]["strategy"]["enum"]))
        self.assertTrue(
            {"sequence", "iplan_id", "dispatch_mode", "required_work_orders"}.issubset(set(sequence_schema["required"]))
        )
        self.assertTrue(
            {"required_dependencies", "required_approvals"}.issubset(
                set(tier_schema["properties"]["entry_gate"]["required"])
            )
        )
        self.assertTrue(
            {"required_events", "required_artifacts", "require_evidence_bundle"}.issubset(
                set(tier_schema["properties"]["exit_gate"]["required"])
            )
        )

    def test_iplan_chain_schema_requires_context_evidence_completion_and_semantic_rules(self) -> None:
        schema_path = SCHEMA_ROOT / "iplan-chain.schema.json"
        schema = json.loads(schema_path.read_text(encoding="utf-8"))

        required_sections = set(schema["required"])
        self.assertTrue(
            {
                "chain_context",
                "evidence_requirements",
                "completion_gate",
                "initialization",
                "start_conditions",
                "handoff",
                "semantic_rules",
            }.issubset(required_sections)
        )

        policy_schema = schema["properties"]["policy"]
        completion_gate_schema = schema["properties"]["completion_gate"]
        initialization_schema = schema["properties"]["initialization"]
        start_schema = schema["properties"]["start_conditions"]
        semantic_rules_schema = schema["properties"]["semantic_rules"]

        self.assertIn("resource_conflict_policy", policy_schema["required"])
        self.assertTrue(
            {
                "criteria",
                "required_events",
                "required_artifacts",
                "required_handoffs",
                "chain_evidence_bundle_required",
                "final_state",
            }.issubset(set(completion_gate_schema["required"]))
        )
        self.assertTrue(
            {
                "required_status",
                "plan_version_checks",
                "graph_checks",
                "handoff_checks",
                "runtime_records",
            }.issubset(set(initialization_schema["required"]))
        )
        self.assertTrue(
            {
                "first_tier",
                "required_resources",
                "policy_checks",
                "context_checks",
                "start_events",
            }.issubset(set(start_schema["required"]))
        )
        self.assertTrue(
            {
                "unique_plan_ids_required",
                "references_must_resolve",
                "acyclic_dependencies_required",
                "tiers_must_cover_declared_plans",
                "work_order_refs_must_resolve",
            }.issubset(set(semantic_rules_schema["required"]))
        )

    def test_evidence_bundle_schema_requires_verifiable_seal(self) -> None:
        schema_path = SCHEMA_ROOT / "iplan-evidence-bundle.schema.json"
        schema = json.loads(schema_path.read_text(encoding="utf-8"))

        seal_schema = schema["properties"]["seal"]
        canonical_hash_schema = seal_schema["properties"]["canonical_hash"]
        signature_schema = seal_schema["properties"]["signature"]

        self.assertTrue({"sealed_at", "canonical_hash", "signature"}.issubset(set(seal_schema["required"])))
        self.assertTrue({"algorithm", "value"}.issubset(set(canonical_hash_schema["required"])))
        self.assertTrue({"key_id", "algorithm", "value"}.issubset(set(signature_schema["required"])))

    def test_all_schemas_are_valid_meta_schema(self) -> None:
        # check_schema catches a malformed schema (bad keyword, wrong type) that
        # instance validation would otherwise mask.
        for schema_path in sorted(SCHEMA_ROOT.glob("*.json")):
            with self.subTest(schema=schema_path.name):
                schema = json.loads(schema_path.read_text(encoding="utf-8"))
                jsonschema.Draft202012Validator.check_schema(schema)

    def test_date_time_format_checker_is_active(self) -> None:
        # Guard: jsonschema only checks `date-time` when rfc3339-validator is
        # installed. Without it, the format_checker below silently passes every
        # timestamp. This assertion makes a missing dependency fail loudly (#14).
        self.assertIn("date-time", jsonschema.Draft202012Validator.FORMAT_CHECKER.checkers)

    def test_standard_templates_validate_against_their_schema(self) -> None:
        # Real JSON Schema validation (replaces the former substring check, which
        # let structural drift inside a section pass silently). Templates are
        # schema-valid reference instances. Format is asserted (date-time, #14) via
        # the FORMAT_CHECKER; the guard test above ensures the checker is active.
        for template_name, schema_name in TEMPLATE_TO_SCHEMA.items():
            with self.subTest(template=template_name):
                instance = yaml.safe_load((STANDARD_TEMPLATE_ROOT / template_name).read_text(encoding="utf-8"))
                schema = json.loads((SCHEMA_ROOT / schema_name).read_text(encoding="utf-8"))

                errors = sorted(
                    jsonschema.Draft202012Validator(
                        schema, format_checker=jsonschema.Draft202012Validator.FORMAT_CHECKER
                    ).iter_errors(instance),
                    key=lambda e: list(e.path),
                )
                self.assertEqual(
                    [],
                    [f"{list(e.path)}: {e.message}" for e in errors],
                    f"{template_name} does not validate against {schema_name}",
                )

    def test_template_less_schemas_have_validated_fixtures(self) -> None:
        # The eight schemas with no authoring template (PLAN-005 deferred them to
        # check_schema-only) get an instance fixture validated the same way templates
        # are — real JSON Schema validation with the format checker active (#14), so
        # date-time fields are genuinely enforced (PLAN-009).
        for fixture_name, schema_name in FIXTURE_TO_SCHEMA.items():
            with self.subTest(fixture=fixture_name):
                instance = json.loads((FIXTURE_ROOT / fixture_name).read_text(encoding="utf-8"))
                schema = json.loads((SCHEMA_ROOT / schema_name).read_text(encoding="utf-8"))

                errors = sorted(
                    jsonschema.Draft202012Validator(
                        schema, format_checker=jsonschema.Draft202012Validator.FORMAT_CHECKER
                    ).iter_errors(instance),
                    key=lambda e: list(e.path),
                )
                self.assertEqual(
                    [],
                    [f"{list(e.path)}: {e.message}" for e in errors],
                    f"{fixture_name} does not validate against {schema_name}",
                )

    def test_every_schema_is_covered_by_a_template_or_a_fixture(self) -> None:
        # Closed-set guarantee: every schema is validated by an instance — either a
        # template (TEMPLATE_TO_SCHEMA) or a fixture (FIXTURE_TO_SCHEMA), with no
        # overlap and nothing left at check_schema-only. A future schema added
        # without either fails here loudly (PLAN-009).
        all_schemas = {path.name for path in SCHEMA_ROOT.glob("*.json")}
        template_covered = set(TEMPLATE_TO_SCHEMA.values())
        fixture_covered = set(FIXTURE_TO_SCHEMA.values())

        self.assertEqual(
            set(),
            template_covered & fixture_covered,
            "A schema is covered by both a template and a fixture; pick one.",
        )
        self.assertEqual(
            fixture_covered,
            all_schemas - template_covered,
            "FIXTURE_TO_SCHEMA must cover exactly the template-less schemas "
            f"(missing fixtures: {sorted(all_schemas - template_covered - fixture_covered)}; "
            f"unexpected: {sorted(fixture_covered - (all_schemas - template_covered))}).",
        )

    def test_iplanic_runtime_schemas_separate_plan_from_execution_state(self) -> None:
        for schema_name in {
            "iplan-execution-record.schema.json",
            "iplan-evidence-bundle.schema.json",
        }:
            with self.subTest(schema=schema_name):
                schema_path = SCHEMA_ROOT / schema_name
                schema = json.loads(schema_path.read_text(encoding="utf-8"))

                self.assertIn("plan_ref", schema["required"])
                self.assertIn("metadata", schema["required"])

    def test_iplan_steps_define_remote_executor_work_orders(self) -> None:
        schema_path = SCHEMA_ROOT / "iplan-document.schema.json"
        schema = json.loads(schema_path.read_text(encoding="utf-8"))

        step_schema = schema["properties"]["plan"]["properties"]["steps"]["items"]
        step_required = set(step_schema["required"])
        step_properties = step_schema["properties"]

        self.assertTrue(
            {"executor_context", "executor_work", "failure_handling"}.issubset(step_required),
            "IPLAN steps must be dispatchable work orders for remote executors.",
        )

        work_schema = step_properties["executor_work"]
        todo_schema = work_schema["properties"]["todos"]["items"]
        todo_required = set(todo_schema["required"])

        self.assertGreaterEqual(work_schema["properties"]["todos"]["minItems"], 1)
        self.assertTrue(
            {
                "todo_id",
                "description",
                "type",
                "priority",
                "allowed_actions",
                "acceptance_criteria",
                "evidence_required",
                "status",
            }.issubset(todo_required),
        )
        self.assertGreaterEqual(todo_schema["properties"]["acceptance_criteria"]["minItems"], 1)
        self.assertGreaterEqual(todo_schema["properties"]["evidence_required"]["minItems"], 1)

    def test_iplan_steps_require_executor_context_and_failure_handling(self) -> None:
        schema_path = SCHEMA_ROOT / "iplan-document.schema.json"
        schema = json.loads(schema_path.read_text(encoding="utf-8"))

        step_schema = schema["properties"]["plan"]["properties"]["steps"]["items"]
        context_schema = step_schema["properties"]["executor_context"]
        failure_schema = step_schema["properties"]["failure_handling"]

        self.assertTrue(
            {
                "repository",
                "workspace",
                "knowledge_refs",
                "mcp_tools",
                "secrets_policy",
                "forbidden_paths",
            }.issubset(set(context_schema["required"]))
        )
        self.assertTrue(
            {
                "on_blocker",
                "on_ambiguity",
                "on_test_failure",
                "on_policy_denial",
                "on_partial_completion",
            }.issubset(set(failure_schema["required"]))
        )

    def test_iplan_step_commands_are_executor_ready(self) -> None:
        schema_path = SCHEMA_ROOT / "iplan-document.schema.json"
        schema = json.loads(schema_path.read_text(encoding="utf-8"))

        command_schema = schema["properties"]["plan"]["properties"]["steps"]["items"]["properties"]["commands"]
        execute_schema = command_schema["properties"]["execute"]["properties"]["items"]
        verify_schema = command_schema["properties"]["verify"]["properties"]["items"]

        self.assertGreaterEqual(execute_schema["minItems"], 1)
        self.assertGreaterEqual(verify_schema["minItems"], 1)

    def test_runtime_task_schema_carries_bound_work_order_and_reporting_contract(self) -> None:
        schema_path = SCHEMA_ROOT / "task.schema.json"
        schema = json.loads(schema_path.read_text(encoding="utf-8"))

        required_fields = set(schema["required"])
        self.assertTrue(
            {"iplan_id", "work_order", "context_package", "reporting", "failure_handling"}.issubset(required_fields)
        )
        self.assertNotIn("plan_id", required_fields)
        self.assertNotIn("plan_id", schema["properties"])
        self.assertIn("protocol_plan_id", schema["properties"])
        self.assertIn("null", schema["properties"]["protocol_agent_id"]["type"])

        work_order = schema["properties"]["work_order"]
        reporting = schema["properties"]["reporting"]
        self.assertTrue({"work_order_id", "todos", "commands", "acceptance_criteria"}.issubset(work_order["required"]))
        self.assertGreaterEqual(work_order["properties"]["todos"]["minItems"], 1)
        self.assertTrue(
            {
                "required_events",
                "required_artifacts",
                "artifact_manifest_required",
                "final_summary_required",
            }.issubset(reporting["required"])
        )

    def test_iplan_template_exposes_executor_todos_context_and_reporting(self) -> None:
        template_text = (STANDARD_TEMPLATE_ROOT / "IPLAN-TEMPLATE.yaml").read_text(encoding="utf-8")

        for expected_snippet in {
            "initialization:",
            "start_conditions:",
            "completion_gate:",
            "required_status:",
            "required_readiness:",
            "evidence_bundle_required:",
            "executor_context:",
            "executor_work:",
            "todos:",
            'todo_id: "TODO-001"',
            "acceptance_criteria:",
            "failure_handling:",
            "on_blocker:",
            "reporting:",
        }:
            with self.subTest(snippet=expected_snippet):
                self.assertIn(expected_snippet, template_text)

    def test_task_template_uses_canonical_iplan_identity_and_nullable_protocol_aliases(self) -> None:
        template_text = (STANDARD_TEMPLATE_ROOT / "IPLAN-TASK-TEMPLATE.yaml").read_text(encoding="utf-8")

        self.assertIn('iplan_id: "IPLAN-01"', template_text)
        self.assertIn("protocol_plan_id: null", template_text)
        self.assertIn("protocol_agent_id: null", template_text)
        self.assertNotIn("\nplan_id:", f"\n{template_text}")

    def test_iplan_chain_template_exposes_complete_execution_order(self) -> None:
        template_text = (STANDARD_TEMPLATE_ROOT / "IPLAN-CHAIN-TEMPLATE.yaml").read_text(encoding="utf-8")

        for expected_snippet in {
            'schema_version: "1.3-draft"',
            "plan_version_id:",
            "canonical_hash:",
            "exec_ready_status:",
            "plan_sequence:",
            "sequence: 1",
            "required_work_orders:",
            "work_order_id:",
            "initialization:",
            "start_conditions:",
            "entry_gate:",
            "dispatch_policy:",
            "exit_gate:",
            "chain_context:",
            "evidence_requirements:",
            "completion_gate:",
            "required_handoffs:",
            "inter_plan_handoffs:",
            "semantic_rules:",
        }:
            with self.subTest(snippet=expected_snippet):
                self.assertIn(expected_snippet, template_text)

    def test_iplan_chain_template_declares_all_referenced_plans(self) -> None:
        template_text = (STANDARD_TEMPLATE_ROOT / "IPLAN-CHAIN-TEMPLATE.yaml").read_text(encoding="utf-8")
        plan_list_text = template_text.split("\ndependencies:", maxsplit=1)[0]

        declared_plan_ids = set()
        all_referenced_plan_ids = set()

        for line in plan_list_text.splitlines():
            stripped = line.strip()
            if stripped.startswith("- iplan_id:"):
                declared_plan_ids.add(stripped.split('"')[1])

        for line in template_text.splitlines():
            stripped = line.strip()
            if stripped.startswith("iplan_id:") or stripped.startswith("- iplan_id:"):
                all_referenced_plan_ids.add(stripped.split('"')[1])

        self.assertTrue(declared_plan_ids)
        self.assertTrue(
            all_referenced_plan_ids.issubset(declared_plan_ids),
            f"Template references undeclared plans: {sorted(all_referenced_plan_ids - declared_plan_ids)}",
        )

    def test_iplan_chain_schema_binds_management_evidence_and_inter_plan_handoffs(self) -> None:
        schema = json.loads((SCHEMA_ROOT / "iplan-chain.schema.json").read_text(encoding="utf-8"))

        plan_schema = schema["properties"]["plans"]["items"]
        handoff_schema = schema["properties"]["inter_plan_handoffs"]["items"]

        self.assertIn("inter_plan_handoffs", schema["required"])
        self.assertTrue(
            {
                "version_record_ref",
                "validation_report_id",
                "approval_event_id",
                "approved_hash",
            }.issubset(set(plan_schema["required"]))
        )
        self.assertTrue(
            {
                "handoff_id",
                "from",
                "to",
                "handoff_type",
                "required_context",
                "required_evidence",
                "acceptance_gate",
                "fallback",
            }.issubset(set(handoff_schema["required"]))
        )

    def test_iplan_chain_template_defines_clear_handoff_steps_between_plans(self) -> None:
        template_text = (STANDARD_TEMPLATE_ROOT / "IPLAN-CHAIN-TEMPLATE.yaml").read_text(encoding="utf-8")

        for expected_snippet in {
            "inter_plan_handoffs:",
            'handoff_id: "HANDOFF-001"',
            "handoff_type:",
            "required_context:",
            "required_evidence:",
            "acceptance_gate:",
            "fallback:",
            "version_record_ref:",
            "validation_report_id:",
            "approval_event_id:",
            "approved_hash:",
        }:
            with self.subTest(snippet=expected_snippet):
                self.assertIn(expected_snippet, template_text)

    def test_tmp_iplan_schema_and_template_are_executor_ready(self) -> None:
        schema = json.loads((SCHEMA_ROOT / "tmp-iplan.schema.json").read_text(encoding="utf-8"))
        template_text = (STANDARD_TEMPLATE_ROOT / "TMP-IPLAN-TEMPLATE.yaml").read_text(encoding="utf-8")

        self.assertTrue(
            {
                "metadata",
                "intent",
                "scope",
                "plan",
                "verification",
                "evidence_requirements",
                "source_iplan_handoff",
                "return_handoff",
                "handoff",
                "closure",
            }.issubset(set(schema["required"]))
        )

        step_schema = schema["properties"]["plan"]["properties"]["steps"]["items"]
        self.assertTrue(
            {"executor_context", "executor_work", "failure_handling"}.issubset(set(step_schema["required"]))
        )

        for expected_snippet in {
            "executor_context:",
            "executor_work:",
            "todos:",
            "reporting:",
            "failure_handling:",
            "evidence_requirements:",
            "handoff:",
        }:
            with self.subTest(snippet=expected_snippet):
                self.assertIn(expected_snippet, template_text)

    def test_tmp_iplan_schema_separates_temporary_from_standard_plans(self) -> None:
        schema = json.loads((SCHEMA_ROOT / "tmp-iplan.schema.json").read_text(encoding="utf-8"))

        metadata_schema = schema["properties"]["metadata"]
        source_handoff_schema = schema["properties"]["source_iplan_handoff"]
        return_handoff_schema = schema["properties"]["return_handoff"]

        self.assertIn("tmp_kind", metadata_schema["required"])
        self.assertIn("promotion_policy", metadata_schema["required"])
        self.assertIn("expires_at", metadata_schema["required"])
        self.assertNotIn("iplan_id", metadata_schema["required"])
        self.assertNotIn("iplan_id", metadata_schema["properties"])
        self.assertNotIn("plan_version", metadata_schema["properties"])
        self.assertEqual(
            {"correction", "investigation", "hotfix", "spike"},
            set(metadata_schema["properties"]["tmp_kind"]["enum"]),
        )

        self.assertTrue(
            {
                "handoff_id",
                "source_iplan_ref",
                "trigger",
                "allowed_scope",
                "pause_standard_iplan",
                "return_contract",
            }.issubset(set(source_handoff_schema["required"]))
        )
        self.assertTrue(
            {
                "handoff_id",
                "target_iplan_ref",
                "return_gate",
                "allowed_resume_actions",
                "promotion_rules",
            }.issubset(set(return_handoff_schema["required"]))
        )
        self.assertEqual(
            {
                "resume_standard_iplan",
                "keep_blocked",
                "promote_to_permanent_iplan",
                "abandon_tmp",
            },
            set(return_handoff_schema["properties"]["allowed_resume_actions"]["items"]["enum"]),
        )

    def test_tmp_iplan_return_result_is_separate_from_planned_return_handoff(self) -> None:
        schema = json.loads((SCHEMA_ROOT / "tmp-iplan.schema.json").read_text(encoding="utf-8"))
        template_text = (STANDARD_TEMPLATE_ROOT / "TMP-IPLAN-TEMPLATE.yaml").read_text(encoding="utf-8")

        return_handoff_schema = schema["properties"]["return_handoff"]
        return_result_schema = schema["properties"]["return_result"]

        self.assertIn("return_result", schema["properties"])
        self.assertNotIn("outcome", return_handoff_schema["required"])
        self.assertNotIn("evidence_refs", return_handoff_schema["required"])
        self.assertTrue(
            {"handoff_id", "target_iplan_ref", "return_gate", "allowed_resume_actions", "promotion_rules"}.issubset(
                set(return_handoff_schema["required"])
            )
        )
        self.assertTrue(
            {"outcome", "evidence_refs", "resume_action", "promotion_decision", "completed_at"}.issubset(
                set(return_result_schema["required"])
            )
        )

        self.assertIn("return_result:", template_text)
        self.assertIn("outcome: null", template_text)
        self.assertIn("evidence_refs: []", template_text)

    def test_tmp_iplan_schema_tightens_executor_ready_step_shape(self) -> None:
        schema = json.loads((SCHEMA_ROOT / "tmp-iplan.schema.json").read_text(encoding="utf-8"))

        step_schema = schema["properties"]["plan"]["properties"]["steps"]["items"]
        target_file_schema = step_schema["properties"]["target_files"]["items"]
        command_schema = step_schema["properties"]["commands"]
        context_schema = step_schema["properties"]["executor_context"]
        work_schema = step_schema["properties"]["executor_work"]
        todo_schema = work_schema["properties"]["todos"]["items"]
        reporting_schema = work_schema["properties"]["reporting"]

        self.assertTrue({"path", "action"}.issubset(set(target_file_schema["required"])))
        self.assertEqual(
            {"create", "modify", "delete", "read", "verify"}, set(target_file_schema["properties"]["action"]["enum"])
        )
        for command_group in {"setup", "execute", "verify"}:
            with self.subTest(command_group=command_group):
                self.assertTrue(
                    {"items", "not_applicable_reason"}.issubset(
                        set(command_schema["properties"][command_group]["required"])
                    )
                )

        self.assertTrue(
            {"url", "default_branch", "base_ref"}.issubset(set(context_schema["properties"]["repository"]["required"]))
        )
        self.assertTrue(
            {"working_directory", "write_scope", "read_only_paths"}.issubset(
                set(context_schema["properties"]["workspace"]["required"])
            )
        )
        self.assertTrue(
            {
                "todo_id",
                "description",
                "type",
                "priority",
                "allowed_actions",
                "acceptance_criteria",
                "evidence_required",
                "status",
            }.issubset(set(todo_schema["required"]))
        )
        self.assertTrue(
            {"progress_events", "completion_event", "artifact_manifest_required", "final_summary_required"}.issubset(
                set(reporting_schema["required"])
            )
        )

    def test_tmp_iplan_schema_enforces_mode_specific_scope_rules(self) -> None:
        schema = json.loads((SCHEMA_ROOT / "tmp-iplan.schema.json").read_text(encoding="utf-8"))

        conditional_rules = json.dumps(schema["allOf"])

        self.assertIn('"tmp_kind": {"const": "investigation"}', conditional_rules)
        self.assertIn('"mutation_policy": {"const": "read_only"}', conditional_rules)
        self.assertIn('"tmp_kind": {"enum": ["correction", "hotfix"]}', conditional_rules)
        self.assertIn('"mutation_policy": {"enum": ["bounded_write", "approval_required"]}', conditional_rules)
        self.assertIn('"correction_scope"', conditional_rules)
        self.assertIn('"investigation_questions"', conditional_rules)

    def test_tmp_templates_cover_correction_and_investigation_modes(self) -> None:
        expected_templates = {
            "TMP-IPLAN-CORRECTION.TEMPLATE.yaml": {
                'tmp_kind: "correction"',
                "source_iplan_handoff:",
                "return_handoff:",
                "return_result:",
                "allowed_resume_actions:",
                "allowed_scope:",
                "correction_scope:",
                'mutation_policy: "bounded_write"',
            },
            "TMP-IPLAN-INVESTIGATION.TEMPLATE.yaml": {
                'tmp_kind: "investigation"',
                "source_iplan_handoff:",
                "return_handoff:",
                "return_result:",
                "allowed_resume_actions:",
                "investigation_questions:",
                'mutation_policy: "read_only"',
            },
        }

        for template_name, snippets in expected_templates.items():
            with self.subTest(template=template_name):
                template_path = STANDARD_TEMPLATE_ROOT / template_name
                self.assertTrue(template_path.exists())
                template_text = template_path.read_text(encoding="utf-8")

                for snippet in snippets:
                    self.assertIn(snippet, template_text)

    def test_standard_iplan_tracks_temporary_handoffs(self) -> None:
        schema = json.loads((SCHEMA_ROOT / "iplan-document.schema.json").read_text(encoding="utf-8"))
        template_text = (STANDARD_TEMPLATE_ROOT / "IPLAN-TEMPLATE.yaml").read_text(encoding="utf-8")

        navigation_schema = schema["properties"]["navigation"]
        temporary_handoff_schema = navigation_schema["properties"]["temporary_handoffs"]["items"]

        self.assertIn("temporary_handoffs", navigation_schema["required"])
        self.assertTrue(
            {
                "handoff_id",
                "tmp_iplan_id",
                "direction",
                "source_ref",
                "target_ref",
                "reason",
                "status",
                "expected_return",
            }.issubset(set(temporary_handoff_schema["required"]))
        )
        self.assertEqual(
            {"iplan_to_tmp", "tmp_to_iplan"},
            set(temporary_handoff_schema["properties"]["direction"]["enum"]),
        )
        self.assertTrue(
            {"artifact_type", "artifact_id"}.issubset(
                set(temporary_handoff_schema["properties"]["source_ref"]["required"])
            )
        )
        self.assertTrue(
            {"artifact_type", "artifact_id"}.issubset(
                set(temporary_handoff_schema["properties"]["target_ref"]["required"])
            )
        )
        direction_rules = json.dumps(temporary_handoff_schema["allOf"])
        self.assertIn('"direction": {"const": "iplan_to_tmp"}', direction_rules)
        self.assertIn('"direction": {"const": "tmp_to_iplan"}', direction_rules)
        self.assertIn('"artifact_type": {"const": "IPLAN"}', direction_rules)
        self.assertIn('"artifact_type": {"const": "TMP-IPLAN"}', direction_rules)

        for expected_snippet in {
            "temporary_handoffs:",
            'tmp_iplan_id: "TMP-IPLAN-2026-06-01-example"',
            'direction: "iplan_to_tmp"',
            'direction: "tmp_to_iplan"',
            "expected_return:",
        }:
            with self.subTest(snippet=expected_snippet):
                self.assertIn(expected_snippet, template_text)

    def test_runtime_audit_schemas_are_typed_and_closed(self) -> None:
        execution_schema = json.loads((SCHEMA_ROOT / "iplan-execution-record.schema.json").read_text(encoding="utf-8"))
        evidence_schema = json.loads((SCHEMA_ROOT / "iplan-evidence-bundle.schema.json").read_text(encoding="utf-8"))

        self.assertFalse(execution_schema["additionalProperties"])
        self.assertFalse(evidence_schema["additionalProperties"])

        task_item_schema = execution_schema["properties"]["tasks"]["items"]
        event_item_schema = execution_schema["properties"]["events"]["properties"]["accepted"]["items"]
        verification_schema = execution_schema["properties"]["verification"]
        execution_evidence_schema = evidence_schema["properties"]["execution_evidence"]
        assurance_schema = evidence_schema["properties"]["assurance"]
        seal_schema = evidence_schema["properties"]["seal"]

        self.assertTrue(
            {"task_id", "step_id", "work_order_id", "status", "executor_id", "lease_id", "attempts"}.issubset(
                set(task_item_schema["required"])
            )
        )
        self.assertTrue(
            {"event_id", "event_type", "task_id", "executor_id", "status", "occurred_at"}.issubset(
                set(event_item_schema["required"])
            )
        )
        self.assertTrue(
            {"commands_run", "evidence_status", "completion_gate", "required_evidence"}.issubset(
                set(verification_schema["required"])
            )
        )
        self.assertTrue(
            {
                "signed_events",
                "executor_assignments",
                "command_results",
                "test_results",
                "artifacts",
                "policy_decisions",
                "approvals",
            }.issubset(set(execution_evidence_schema["required"]))
        )
        self.assertTrue(
            {
                "required_evidence_satisfied",
                "verification_passed",
                "drift_findings",
                "open_deferred_items",
                "reviewer_notes",
            }.issubset(set(assurance_schema["required"]))
        )
        self.assertIn("evidence_manifest", seal_schema["required"])

    def test_iplan_management_schemas_exist_and_cover_system_of_record(self) -> None:
        expected = {
            "iplan-record.schema.json": {"org_id", "project_id", "iplan_id", "status", "current_version_id"},
            "iplan-version.schema.json": {
                "plan_version_id",
                "iplan_id",
                "plan_version",
                "canonical_hash",
                "approval",
                "immutable",
            },
            "iplan-import-result.schema.json": {
                "import_id",
                "status",
                "artifact_type",
                "canonical_hash",
                "validation_report_id",
            },
            "iplan-validation-report.schema.json": {
                "validation_report_id",
                "subject_ref",
                "schema_validation",
                "semantic_validation",
                "readiness",
                "findings",
            },
            "iplan-comparison.schema.json": {
                "comparison_id",
                "base_ref",
                "target_ref",
                "summary",
                "section_diffs",
                "impact",
            },
            "iplan-lifecycle-event.schema.json": {
                "event_id",
                "iplan_id",
                "event_type",
                "from_status",
                "to_status",
                "actor",
                "occurred_at",
            },
            "iplan-chain-version.schema.json": {
                "chain_version_id",
                "chain_id",
                "chain_version",
                "canonical_hash",
                "approval",
                "immutable",
            },
            "iplan-chain-record.schema.json": {
                "org_id",
                "project_id",
                "chain_id",
                "status",
                "current_version_id",
                "record_version",
            },
        }

        for schema_name, required_fields in expected.items():
            with self.subTest(schema=schema_name):
                schema = json.loads((SCHEMA_ROOT / schema_name).read_text(encoding="utf-8"))
                self.assertEqual(schema["type"], "object")
                self.assertTrue(required_fields.issubset(set(schema["required"])))

    def test_iplan_version_schema_requires_immutability_hash_and_approval(self) -> None:
        schema = json.loads((SCHEMA_ROOT / "iplan-version.schema.json").read_text(encoding="utf-8"))

        canonical_hash_schema = schema["properties"]["canonical_hash"]
        approval_schema = schema["properties"]["approval"]
        supersession_schema = schema["properties"]["supersession"]

        self.assertTrue({"algorithm", "value"}.issubset(set(canonical_hash_schema["required"])))
        self.assertTrue(
            {
                "decision",
                "approved_by",
                "approved_at",
                "approved_hash",
                "policy_result",
                "exceptions",
            }.issubset(set(approval_schema["required"]))
        )
        self.assertTrue(
            {"supersedes_version_id", "superseded_by_version_id"}.issubset(supersession_schema["properties"])
        )
        self.assertIn(True, schema["properties"]["immutable"]["enum"])

    def test_iplan_validation_report_schema_models_semantic_rules(self) -> None:
        schema = json.loads((SCHEMA_ROOT / "iplan-validation-report.schema.json").read_text(encoding="utf-8"))

        semantic_schema = schema["properties"]["semantic_validation"]
        readiness_schema = schema["properties"]["readiness"]

        self.assertTrue(
            {
                "duplicate_ids",
                "unresolved_references",
                "placeholder_fields",
                "command_evidence_coverage",
                "file_conflicts",
                "chain_graph_integrity",
            }.issubset(set(semantic_schema["required"]))
        )
        self.assertTrue({"exec_ready_score", "result", "blocking_findings"}.issubset(set(readiness_schema["required"])))

    def test_iplan_comparison_schema_models_review_and_execution_impact(self) -> None:
        schema = json.loads((SCHEMA_ROOT / "iplan-comparison.schema.json").read_text(encoding="utf-8"))

        impact_schema = schema["properties"]["impact"]
        section_diff_schema = schema["properties"]["section_diffs"]["items"]

        # impact is the summary classification only (severity); the actionable
        # detail lives in the top-level approval_impact / execution_impact objects.
        self.assertEqual(["severity"], impact_schema["required"])
        self.assertNotIn("change_severity", impact_schema["properties"])
        self.assertTrue({"approval_impact", "execution_impact"}.issubset(set(schema["required"])))
        self.assertIn("approval_required", schema["properties"]["approval_impact"]["properties"])
        self.assertIn("rerun_required", schema["properties"]["execution_impact"]["properties"])
        self.assertEqual(
            {
                "intent",
                "scope",
                "lineage",
                "plan_steps",
                "executor_work",
                "commands",
                "evidence",
                "handoff",
                "navigation",
                "chain_order",
                "policy",
            },
            set(section_diff_schema["properties"]["section"]["enum"]),
        )

    def test_iplan_lifecycle_event_schema_enforces_controlled_transitions(self) -> None:
        schema = json.loads((SCHEMA_ROOT / "iplan-lifecycle-event.schema.json").read_text(encoding="utf-8"))

        event_types = set(schema["properties"]["event_type"]["enum"])
        status_enum = set(schema["properties"]["to_status"]["enum"])

        self.assertTrue(
            {
                "imported",
                "validated",
                "submitted_for_review",
                "approved",
                "rejected",
                "superseded",
                "abandoned",
                "rolled_back",
            }.issubset(event_types)
        )
        self.assertTrue({"Draft", "Review", "Approved", "Rejected", "Superseded", "Abandoned"}.issubset(status_enum))

