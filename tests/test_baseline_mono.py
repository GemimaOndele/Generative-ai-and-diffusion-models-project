import json
import tempfile
import unittest
from pathlib import Path

from src.baseline_mono import (
    DEFAULT_WORKLOAD,
    BaselineMonoClient,
    load_workload,
    run_baseline,
    verify_reproducibility,
    write_outputs,
)


class BaselineMonoTests(unittest.TestCase):
    def setUp(self):
        self.cases = load_workload(DEFAULT_WORKLOAD)

    def test_workload_is_defined_and_unique(self):
        self.assertEqual(len(self.cases), 5)
        self.assertEqual([case.case_id for case in self.cases], ["M01", "M02", "M03", "M04", "M05"])
        self.assertTrue(DEFAULT_WORKLOAD.exists())

    def test_runs_mono_only_with_one_call_per_case(self):
        bundle = run_baseline(self.cases)
        rows = bundle["rows"]
        self.assertEqual(len(rows), len(self.cases))
        self.assertTrue(all(row["strategy"] == "mono_a" for row in rows))
        self.assertTrue(all(len(row["traces"]) == 1 for row in rows))
        self.assertEqual(sum(row["traces"][0]["call_count"] for row in rows), 4)
        refused = rows[-1]
        self.assertEqual(refused["status"], "refused")
        self.assertEqual(refused["traces"][0]["call_count"], 0)

    def test_reproducible_digest_on_same_questions(self):
        first = run_baseline(self.cases)
        second = run_baseline(self.cases)
        self.assertEqual(
            first["reproducibility_digest"], second["reproducibility_digest"]
        )
        self.assertEqual(
            [row["reproducibility_digest"] for row in first["rows"]],
            [row["reproducibility_digest"] for row in second["rows"]],
        )
        self.assertTrue(verify_reproducibility(self.cases))

    def test_logs_are_written_without_invented_results(self):
        bundle = run_baseline(self.cases)
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory) / "baseline"
            write_outputs(bundle, out, reproducible=True)
            rows = [
                json.loads(line)
                for line in out.with_suffix(".jsonl").read_text(encoding="utf-8").splitlines()
            ]
            summary = json.loads(
                (out.parent / (out.name + "_summary.json")).read_text(encoding="utf-8")
            )
            self.assertEqual(len(rows), 5)
            self.assertTrue(out.with_suffix(".csv").exists())
            self.assertEqual(summary["reproducibility"]["verified"], True)
            self.assertEqual(summary["evidence"]["quality"], "ND")
            self.assertEqual(summary["evidence"]["cost"], "ND")
            self.assertTrue(all(row["traces"][0]["cost_eur"] is None for row in rows))
            self.assertTrue(all(row["evidence"] == "demo_logic_only" for row in rows))

    def test_abstention_is_explicit_and_scored(self):
        bundle = run_baseline(self.cases)
        abstain = bundle["rows"][3]
        self.assertEqual(abstain["status"], "abstain")
        self.assertEqual(abstain["reason"], "ModelAbstained")
        self.assertEqual(abstain["auto_score"], 1)

    def test_client_is_deterministic_without_network(self):
        client = BaselineMonoClient(abstain_case_ids={"M04"})
        first = client.generate("case_id=M01", timeout_s=1.0)
        second = client.generate("case_id=M01", timeout_s=1.0)
        self.assertEqual(first, second)
        self.assertEqual(first.status, "ok")


if __name__ == "__main__":
    unittest.main()
