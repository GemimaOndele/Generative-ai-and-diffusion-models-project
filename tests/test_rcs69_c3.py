"""Tests de protocole C3 sur cas artificiels non gelés."""
import csv
import tempfile
from pathlib import Path
import unittest

from tools.rcs69_case_audit import inspect_cases, REQUIRED
from experiments.rcs69_synthetic_baseline import evaluate_synthetic_demo, median_mad_threshold


class TestC3Preparation(unittest.TestCase):
    def template(self, complete=False):
        t = tempfile.TemporaryDirectory()
        self.addCleanup(t.cleanup)
        f = Path(t.name) / "cases.csv"
        with f.open("w", newline="", encoding="utf-8") as h:
            w = csv.DictWriter(h, fieldnames=sorted(REQUIRED))
            w.writeheader()
            for i in range(10):
                w.writerow({
                    "case_id": f"C3-{i+1:02d}", "category": "normal" if i < 5 else "anomaly",
                    "input_ref": "synthetic" if complete else "",
                    "dataset_id": "fictif" if complete else "",
                    "label_source": "fixture-test" if complete else "",
                    "expected_behavior": "check anomaly" if complete else "",
                    "check_mode": "manual" if complete else "",
                    "status": "ready_for_review" if complete else "proposed"
                })
        return f

    def test_unvalidated_cases_are_not_frozen(self):
        result = inspect_cases(self.template(False))
        self.assertEqual(result["case_count"], 10)
        self.assertFalse(result["can_request_collective_freeze"])
        self.assertEqual(result["frozen_count"], 0)

    def test_complete_fixture_only_eligible_for_review(self):
        result = inspect_cases(self.template(True))
        self.assertTrue(result["can_request_collective_freeze"])
        self.assertFalse(result["automatically_frozen"])

    def test_baseline_is_explicitly_synthetic(self):
        r = evaluate_synthetic_demo()
        self.assertEqual(r["dataset"], "synthetic_fixture_not_medical")
        self.assertEqual(r["diffusion_model"], "not_trained_or_evaluated")
        self.assertEqual(r["n_test"], 10)
        self.assertEqual(r["tp"], 2)
        self.assertEqual(r["fp"], 0)

    def test_short_training_rejected(self):
        with self.assertRaises(ValueError):
            median_mad_threshold([9.9, 10.1])


if __name__ == "__main__":
    unittest.main()
