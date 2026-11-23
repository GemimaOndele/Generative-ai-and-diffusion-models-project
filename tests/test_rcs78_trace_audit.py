"""RCS-78: tests without private, clinical or real model outputs."""
import json
import tempfile
import unittest
from pathlib import Path
from tools.rcs78_trace_audit import audit_traces


class TraceAuditTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / "traces.jsonl"

    def write(self, records):
        self.path.write_text("\n".join(json.dumps(x) for x in records), encoding="utf-8")

    def record(self, case="T01", strategy="mono_a", **kw):
        return {"trace_id": "dummy-1", "case_id": case,
                "strategy": strategy, "status": "ok", "latency_ms": 12,
                "variant": "default", "score": 1, "models": ["local-a"],
                "cost_eur": None, **kw}

    def test_metadata_no_raw_answers(self):
        one = self.record()
        one["answer"] = "PRIVATE TEXT THAT MUST NEVER BE COPIED"
        one["raw_prompt"] = "DO NOT EXPORT"
        self.write([one, self.record("T02")])
        result = audit_traces(self.path)
        report = json.dumps(result)
        self.assertNotIn("PRIVATE TEXT", report)
        self.assertNotIn("DO NOT EXPORT", report)
        self.assertTrue(result["human_review_required"])
        self.assertFalse(result["clinical_validation"])
        self.assertEqual(result["summary"]["mono_a:default"]["unique_cases"], 2)
        self.assertEqual(result["quality_checks"]["potential_sensitive_field_rows"], 1)
        self.assertEqual(result["quality_checks"]["missing_or_invalid_cost_count"], 2)

    def test_duplicate_and_invalid_latency_are_reported(self):
        first = self.record()
        second = self.record()
        second["latency_ms"] = "-5"
        self.write([first, second])
        result = audit_traces(self.path)
        self.assertEqual(result["quality_checks"]["duplicate_case_strategy_variant"], 1)
        self.assertEqual(result["quality_checks"]["invalid_latency_count"], 1)

    def test_missing_metadata_refused(self):
        self.write([{"strategy": "mono_a"}])
        with self.assertRaises(ValueError):
            audit_traces(self.path)

    def test_empty_file_stays_blocked(self):
        self.write([])
        self.assertEqual(audit_traces(self.path)["decision"], "BLOCKED")

    def test_bad_json_fails(self):
        self.path.write_text("{broken", encoding="utf-8")
        with self.assertRaises(ValueError):
            audit_traces(self.path)

    def test_p95_nearest_rank(self):
        self.write([dict(self.record(f"T{i:02d}"), latency_ms=i * 100)
                    for i in range(1, 11)])
        result = audit_traces(self.path)
        self.assertEqual(result["summary"]["mono_a:default"]["p95_latency_ms"], "1000")


if __name__ == "__main__":
    unittest.main()
