import os
import unittest

from src.model_config import BenchmarkPolicy, ModelSpec
from src.orchestrator import CaseInput, DemoClient, Orchestrator


class CountingClient(DemoClient):
    """Client de test qui compte les appels réseau et les bornes reçues."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.calls = []
        self.max_output_tokens_seen = []

    def generate(self, prompt, *, timeout_s, max_output_tokens=None):
        self.calls.append(prompt)
        self.max_output_tokens_seen.append(max_output_tokens)
        return super().generate(
            prompt, timeout_s=timeout_s, max_output_tokens=max_output_tokens
        )


def priced_spec(label, name, price=0.01):
    return ModelSpec(
        label=label, model_name=name, provider="demo", version="1",
        is_demo=True, data_transfer_authorized=True,
        price_in_eur_per_1k_input=price, price_in_eur_per_1k_output=price,
    )


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

    def test_cascade_respects_max_calls_per_case(self):
        policy = BenchmarkPolicy(max_calls_per_case=1)
        a = CountingClient("a", behavior={"case_id=T08": "invalid"})
        b = CountingClient("b")
        spec_b = ModelSpec(
            label="B", model_name="b", provider="demo", version="1",
            is_demo=False, data_transfer_authorized=True, usage_rights_verified=True,
        )
        orch = Orchestrator(a, b, policy=policy, spec_b=spec_b)
        case = CaseInput(case_id="T08", task="qa", input="conflict", category="contradiction")
        res = orch.run_cascade(case)
        self.assertEqual(res.status, "abstain")
        self.assertEqual(res.reason, "max_calls_per_case_reached")
        self.assertEqual(len(a.calls), 1)
        self.assertEqual(len(b.calls), 0)
        self.assertEqual(res.traces[0].call_count, 1)

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

    def test_cascade_emergency_budget_stop_makes_zero_calls(self):
        a, b = CountingClient("a"), CountingClient("b")
        orch = Orchestrator(a, b)
        case = CaseInput(case_id="T01", task="summarize", input="alarme", category="usual")
        os.environ["TP04_BUDGET_EXCEEDED"] = "1"
        try:
            res = orch.run_cascade(case)
        finally:
            os.environ.pop("TP04_BUDGET_EXCEEDED", None)
        self.assertEqual(res.status, "abstain")
        self.assertEqual(res.reason, "budget_exceeded")
        self.assertEqual(len(res.traces), 1)
        self.assertEqual(res.traces[0].call_count, 0)
        self.assertEqual(res.traces[0].notes, "blocked_before_call")
        self.assertEqual(a.calls, [])
        self.assertEqual(b.calls, [])

    def test_mono_and_routing_emergency_budget_stop_make_zero_calls(self):
        for run in ("mono", "routing"):
            with self.subTest(run=run):
                a, b = CountingClient("a"), CountingClient("b")
                orch = Orchestrator(a, b)
                case = CaseInput(case_id="T01", task="summarize", input="alarme", category="usual")
                os.environ["TP04_BUDGET_EXCEEDED"] = "1"
                try:
                    res = orch.run_mono(case, "A") if run == "mono" else orch.run_routing(case)
                finally:
                    os.environ.pop("TP04_BUDGET_EXCEEDED", None)
                self.assertEqual(res.status, "abstain")
                self.assertEqual(res.reason, "budget_exceeded")
                self.assertEqual(a.calls, [])
                self.assertEqual(b.calls, [])

    def test_budget_cap_blocks_before_first_call_when_forecast_exceeds_it(self):
        policy = BenchmarkPolicy(
            max_cost_eur_per_case=0.001,
            max_input_tokens_per_call=100,
            max_output_tokens_per_call=100,
        )
        a, b = CountingClient("a"), CountingClient("b")
        orch = Orchestrator(
            a, b, policy=policy,
            spec_a=priced_spec("A", "a"), spec_b=priced_spec("B", "b"),
        )
        case = CaseInput(case_id="T01", task="summarize", input="alarme", category="usual")
        res = orch.run_cascade(case)
        self.assertEqual(res.status, "abstain")
        self.assertEqual(res.reason, "budget_exceeded_forecast")
        self.assertEqual(a.calls, [])
        self.assertEqual(b.calls, [])

    def test_budget_cap_blocks_before_first_call_when_tariffs_are_nd(self):
        policy = BenchmarkPolicy(max_cost_eur_per_case=1.0)
        spec_a = ModelSpec(
            label="A", model_name="a", provider="demo", version="1",
            is_demo=True, data_transfer_authorized=True,
        )
        spec_b = ModelSpec(
            label="B", model_name="b", provider="demo", version="1",
            is_demo=True, data_transfer_authorized=True,
        )
        a, b = CountingClient("a"), CountingClient("b")
        orch = Orchestrator(a, b, policy=policy, spec_a=spec_a, spec_b=spec_b)
        case = CaseInput(case_id="T01", task="summarize", input="alarme", category="usual")
        res = orch.run_cascade(case)
        self.assertEqual(res.status, "abstain")
        self.assertEqual(res.reason, "cost_nd_with_cap")
        self.assertEqual(a.calls, [])
        self.assertEqual(b.calls, [])

    def test_calls_respect_token_bounds_before_network(self):
        policy = BenchmarkPolicy(
            max_cost_eur_per_case=1.0,
            max_input_tokens_per_call=60,
            max_output_tokens_per_call=7,
        )
        a, b = CountingClient("a"), CountingClient("b")
        orch = Orchestrator(
            a, b, policy=policy,
            spec_a=priced_spec("A", "a", price=0.0001),
            spec_b=priced_spec("B", "b", price=0.0001),
        )
        case = CaseInput(
            case_id="T99", task="reason", input="x" * 500, category="usual"
        )
        res = orch.run_cascade(case)
        self.assertEqual(res.status, "ok")
        self.assertLessEqual(len(a.calls[0].encode("utf-8")), 60)
        self.assertEqual(a.max_output_tokens_seen[0], 7)
        self.assertIn("prompt_truncated_to_token_budget", res.traces[0].notes)


if __name__ == "__main__":
    unittest.main()
