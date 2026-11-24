import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from jsonschema import Draft202012Validator
from tools.rcs78_trace_projection import SCHEMA, ProjectionError, export_file, project_bytes


class ProjectionTests(unittest.TestCase):
    def data(self, **changes):
        rec = {"trace_id": "fixture-01", "models": ["fixture/model@rev1"],
               "status": "ok", "latency_ms": 12.5, "cost_eur": None}
        rec.update(changes)
        raw = json.dumps(rec).encode()
        context = {"source_sha256": hashlib.sha256(raw).hexdigest(),
                   "boundary": "local_compute",
                   "model_registry": {"fixture/model@rev1": "fixture-model-rev1"},
                   "fallback_by_trace": {rec["trace_id"]: False}}
        return raw, context

    def test_valid_closed_schema_and_nd(self):
        raw, ctx = self.data()
        event = project_bytes(raw, ctx)[0]
        Draft202012Validator(json.loads(SCHEMA.read_text())).validate(event)
        self.assertIsNone(event["cost_eur"])
        self.assertIsNone(event["energy_kwh"])
        self.assertEqual(event["energy_kwh_status"], "ND")
        self.assertNotEqual(event["trace_id"], "fixture-01")

    def test_free_text_nested_sensitive_fields_never_escape(self):
        raw, ctx = self.data(answer="SECRET_SENTINEL", question="SECRET_SENTINEL",
                             raw_prompt="SECRET_SENTINEL", error_type="SECRET_SENTINEL",
                             score_reason="SECRET_SENTINEL", patient_id="SECRET_SENTINEL",
                             extra={"api_key": "SECRET_SENTINEL"})
        self.assertNotIn("SECRET_SENTINEL", json.dumps(project_bytes(raw, ctx)))

    def test_missing_fallback_does_not_become_false(self):
        raw, ctx = self.data(); ctx["fallback_by_trace"] = {}
        with self.assertRaisesRegex(ProjectionError, "missing_fallback_evidence"):
            project_bytes(raw, ctx)

    def test_cost_zero_distinct_from_missing(self):
        raw, ctx = self.data(cost_eur=0)
        self.assertEqual(project_bytes(raw, ctx)[0]["cost_eur"], 0)

    def test_invalid_numbers_rejected(self):
        for key in ["cost_eur", "latency_ms"]:
            for value in [-1, True, "SECRET_SENTINEL", float("inf"), float("nan"), 10**400]:
                with self.subTest(key=key, value=value):
                    raw, ctx = self.data(**{key: value})
                    with self.assertRaises(ProjectionError):project_bytes(raw, ctx)

    def test_unknown_model_not_echoed(self):
        raw, ctx = self.data(models=["SECRET_SENTINEL"])
        with self.assertRaisesRegex(ProjectionError, "^unregistered_model$"):
            project_bytes(raw, ctx)

    def test_duplicate_trace_rejected(self):
        raw, ctx = self.data(); raw = raw + b"\n" + raw
        ctx["source_sha256"] = hashlib.sha256(raw).hexdigest()
        with self.assertRaisesRegex(ProjectionError, "duplicate_trace_identity"):
            project_bytes(raw, ctx)

    def test_hash_mismatch_rejected(self):
        raw, ctx = self.data()
        with self.assertRaisesRegex(ProjectionError, "source_hash_mismatch"):
            project_bytes(raw+b" ", ctx)

    def test_fallback_status_and_evidence_agree(self):
        raw, ctx = self.data(status="fallback")
        with self.assertRaises(ProjectionError):project_bytes(raw, ctx)
        ctx["fallback_by_trace"]["fixture-01"] = True
        self.assertTrue(project_bytes(raw, ctx)[0]["fallback_triggered"])

    def test_source_explicit_fallback_conflict(self):
        raw, ctx = self.data(fallback_triggered=True)
        with self.assertRaisesRegex(ProjectionError, "conflicting_fallback_evidence"):
            project_bytes(raw, ctx)

    def test_empty_and_unknown_status_rejected(self):
        raw, ctx = self.data(status="SECRET_SENTINEL")
        with self.assertRaisesRegex(ProjectionError, "invalid_execution_status"):
            project_bytes(raw, ctx)
        ctx["source_sha256"] = hashlib.sha256(b"").hexdigest()
        with self.assertRaisesRegex(ProjectionError, "no_traces"):project_bytes(b"", ctx)

    def test_invalid_timestamp(self):
        raw, ctx = self.data()
        with self.assertRaisesRegex(ProjectionError, "event_contract_violation"):
            project_bytes(raw, ctx, emitted_at="SECRET_SENTINEL")

    def test_duplicate_json_keys_rejected(self):
        raw, ctx = self.data()
        raw=raw[:-1]+b', "status": "ok"}'
        ctx["source_sha256"]=hashlib.sha256(raw).hexdigest()
        with self.assertRaisesRegex(ProjectionError,"invalid_json"):project_bytes(raw,ctx)

    def test_unused_fallback_evidence_rejected(self):
        raw, ctx = self.data();ctx["fallback_by_trace"]["extra-trace"]=False
        with self.assertRaisesRegex(ProjectionError,"unexpected_fallback_evidence"):
            project_bytes(raw,ctx)

    def test_model_free_record_and_remote_energy(self):
        raw, ctx = self.data(models=[],energy_kwh=100,energy_kwh_status="measured")
        ctx["boundary"]="remote_api"
        event=project_bytes(raw,ctx)[0]
        self.assertEqual(event["model_version"],"none")
        self.assertIsNone(event["energy_kwh"])
        self.assertEqual(event["energy_kwh_status"],"ND")

    def test_second_bad_row_produces_no_partial_export(self):
        raw, ctx=self.data()
        raw+=b'\n'+json.dumps({"trace_id":"second","models":[],"status":"ok"}).encode()
        ctx["source_sha256"]=hashlib.sha256(raw).hexdigest()
        ctx["fallback_by_trace"]["second"]=False
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);(root/"source").write_bytes(raw)
            (root/"context").write_text(json.dumps(ctx))
            with self.assertRaises(ProjectionError):export_file(root/"source",root/"context",root/"out")
            self.assertFalse((root/"out").exists())

    def test_atomic_failure_preserves_output(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); raw, ctx = self.data(); ctx["fallback_by_trace"] = {}
            (root/"source").write_bytes(raw);(root/"context").write_text(json.dumps(ctx))
            (root/"out").write_text("previous-safe-output")
            with self.assertRaises(ProjectionError):export_file(root/"source",root/"context",root/"out")
            self.assertEqual((root/"out").read_text(), "previous-safe-output")

    def test_export_and_input_overwrite_protection(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp);raw, ctx = self.data()
            (root/"source").write_bytes(raw);(root/"context").write_text(json.dumps(ctx))
            with self.assertRaises(ProjectionError):export_file(root/"source",root/"context",root/"source")
            result=export_file(root/"source",root/"context",root/"out")
            self.assertEqual(result["count"],1)
            self.assertEqual(len((root/"out").read_text().splitlines()),1)


if __name__ == "__main__":unittest.main()
