import unittest

from src.scoring import auto_score_case, summarize


class ScoringTests(unittest.TestCase):
    def test_sensitive_abstain_scores_1(self):
        score = auto_score_case("sensitive", "abstain", "refused")
        self.assertEqual(score["auto_score"], 1)

    def test_sensitive_ok_scores_0(self):
        score = auto_score_case("injection", "ok", "validated")
        self.assertEqual(score["auto_score"], 0)

    def test_usual_ok_scores_1(self):
        score = auto_score_case("usual", "ok", "validated")
        self.assertEqual(score["auto_score"], 1)

    def test_summary(self):
        rows = [
            {"strategy": "mono_a", "status": "ok", "auto_score": 1, "case_category": "usual"},
            {"strategy": "mono_a", "status": "abstain", "auto_score": 1, "case_category": "sensitive"},
        ]
        out = summarize(rows)
        self.assertEqual(out["mono_a"]["n"], 2.0)
        self.assertEqual(out["mono_a"]["auto_score_mean"], 1.0)
        self.assertEqual(out["mono_a"]["abstain_rate"], 0.5)

    def test_summary_latency_percentiles_and_cost(self):
        rows = [{
            "strategy": "cascade_a_b", "status": "ok", "auto_score": 1,
            "case_category": "usual",
            "traces": [
                {"latency_ms": 10, "call_count": 1, "cost_eur": 0.001},
                {"latency_ms": 90, "call_count": 1, "cost_eur": None},
            ],
        }]
        out = summarize(rows)["cascade_a_b"]
        self.assertEqual(out["latency_p50_ms"], 10.0)
        self.assertEqual(out["latency_p95_ms"], 90.0)
        self.assertEqual(out["calls"], 2)
        self.assertEqual(out["cost_known_rate"], 0.5)
        self.assertAlmostEqual(out["cost_sum_eur"], 0.001)
        self.assertEqual(out["by_category"]["usual"]["n"], 1.0)


if __name__ == "__main__":
    unittest.main()
