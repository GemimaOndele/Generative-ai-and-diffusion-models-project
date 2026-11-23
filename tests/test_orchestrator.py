import os
import unittest

from src.orchestrator import CaseInput, DemoClient, Orchestrator


class OrchestratorTests(unittest.TestCase):
    def setUp(self):
        self.a = DemoClient("a", behavior={"case_id=T07": "refuse", "case_id=T08": "invalid"})
        self.b = DemoClient("b", behavior={"case_id=T08": "ok"})
        self.orch = Orchestrator(self.a, self.b)

    def test_mono_a_ok(self):
        case = CaseInput(case_id="T01", task="summarize", input="alarme", category="usual")
        res = self.orch.run_mono(case, "A")
        self.assertEqual(res.status, "ok")
        self.assertEqual(res.strategy, "mono_a")
        self.assertTrue(res.traces)

    def test_cascade_a_valid_abstain_no_fallback(self):
        # A returns a grounded abstention for a no_source case -> validated by A, no fallback needed
        case = CaseInput(case_id="T07", task="qa", input="missing", category="no_source")
        res = self.orch.run_cascade(case)
        self.assertEqual(res.status, "ok")
        self.assertEqual(len(res.traces), 1)
        self.assertEqual(res.reason, "validated_by_a")

    def test_cascade_fallback_blocked_without_authorization(self):
        # A fails validation, B not authorized -> abstain
        case = CaseInput(case_id="T08", task="qa", input="conflict", category="contradiction")
        os.environ.pop("ALLOW_B_DATA", None)
        os.environ.pop("TP04_BUDGET_EXCEEDED", None)
        res = self.orch.run_cascade(case)
        self.assertEqual(res.status, "abstain")
        self.assertEqual(res.reason, "fallback_blocked")
        self.assertEqual(len(res.traces), 1)

    def test_cascade_uses_b_when_authorized(self):
        os.environ["ALLOW_B_DATA"] = "1"
        try:
            case = CaseInput(case_id="T08", task="qa", input="conflict", category="contradiction")
            # A invalid, B ok but grounded() requires abstain keywords for contradiction; B returns demo response -> may abstain
            res = self.orch.run_cascade(case)
            self.assertEqual(len(res.traces), 2)
            self.assertIn(res.status, {"ok", "abstain"})
        finally:
            os.environ.pop("ALLOW_B_DATA", None)

    def test_routing_selects_a_for_usual(self):
        case = CaseInput(case_id="T01", task="summarize", input="alarme", category="usual")
        res = self.orch.run_routing(case)
        self.assertEqual(res.strategy, "routing_a_b")
        self.assertEqual(res.model, "a")

    def test_routing_selects_b_for_complex(self):
        case = CaseInput(case_id="T05", task="reason", input="complex", category="complex")
        res = self.orch.run_routing(case)
        self.assertEqual(res.strategy, "routing_a_b")
        self.assertEqual(res.model, "b")


if __name__ == "__main__":
    unittest.main()
