import json
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from src.model_config import BenchmarkPolicy, CostLedger, ModelSpec, load_config, validate_pair


def demo_spec(label, name):
    return ModelSpec(
        label=label, model_name=name, provider="demo", version="1",
        is_demo=True, data_transfer_authorized=True,
    )


def live_spec(label, name):
    return ModelSpec(
        label=label, model_name=name, provider="fournisseur-" + label.lower(), version="1",
        license="license-verify", usage_rights_verified=True, region="EU",
        retention_policy="aucune rétention", data_transfer_authorized=True,
        base_url="https://example.invalid/v1", api_key_env=f"LLM_{label}_API_KEY",
        price_in_eur_per_1k_input=0.001, price_in_eur_per_1k_output=0.002,
    )


class ModelConfigTests(unittest.TestCase):
    def test_demo_pair_distinct_ok(self):
        validate_pair(demo_spec("A", "demo-a"), demo_spec("B", "demo-b"), live=False)

    def test_same_model_rejected(self):
        with self.assertRaises(ValueError):
            validate_pair(demo_spec("A", "modele-x"), demo_spec("B", "modele-x"), live=False)

    def test_same_model_under_two_providers_rejected(self):
        a = live_spec("A", "modele-x")
        b = live_spec("B", "modele-x")
        with self.assertRaises(ValueError):
            validate_pair(a, b, live=True)

    def test_live_requires_rights_and_license(self):
        spec = replace(live_spec("A", "a"), license="")
        with self.assertRaises(ValueError):
            spec.validate(live=True)

    def test_policy_rejects_invalid_pattern(self):
        with self.assertRaises(ValueError):
            BenchmarkPolicy(v2_pattern="magie").validate(live=False)

    def test_policy_requires_explicit_consent_in_live(self):
        with self.assertRaises(ValueError):
            BenchmarkPolicy().validate(live=True)

    def test_cost_ledger_uses_only_known_tariffs(self):
        ledger = CostLedger(max_cost_eur=1.0)
        spec = live_spec("A", "a")
        cost, note = ledger.record(spec, 1000, 500)
        self.assertAlmostEqual(cost, 0.002)
        self.assertIsNone(note)
        allowed, _ = ledger.can_spend()
        self.assertTrue(allowed)

    def test_cost_ledger_never_invents_cost(self):
        ledger = CostLedger(max_cost_eur=1.0)
        spec = demo_spec("A", "demo-a")
        cost, note = ledger.record(spec, 1000, 500)
        self.assertIsNone(cost)
        self.assertEqual(note, "cost_nd")
        allowed, reason = ledger.can_spend()
        self.assertFalse(allowed)
        self.assertEqual(reason, "cost_nd_with_cap")

    def test_cost_ledger_reserves_forecast_then_settles_actual(self):
        ledger = CostLedger(max_cost_eur=1.0)
        spec = live_spec("A", "a")
        allowed, reason, reserved = ledger.reserve(spec, 1000, 500)
        self.assertTrue(allowed)
        self.assertIsNone(reason)
        self.assertAlmostEqual(reserved, 0.002)
        self.assertAlmostEqual(ledger.reserved_eur, 0.002)
        allowed, _ = ledger.can_spend()
        self.assertTrue(allowed)
        cost, note = ledger.record(spec, 500, 250, reserved)
        self.assertAlmostEqual(cost, 0.001)
        self.assertIsNone(note)
        self.assertAlmostEqual(ledger.spent_eur, 0.001)
        self.assertAlmostEqual(ledger.reserved_eur, 0.0)

    def test_cost_ledger_flags_cost_above_reservation(self):
        ledger = CostLedger(max_cost_eur=1.0)
        spec = live_spec("A", "a")
        _, _, reserved = ledger.reserve(spec, 100, 100)
        cost, note = ledger.record(spec, 1000, 1000, reserved)
        self.assertAlmostEqual(cost, 0.003)
        self.assertEqual(note, "cost_above_forecast")

    def test_cost_ledger_rejects_forecast_above_cap(self):
        ledger = CostLedger(max_cost_eur=0.001)
        spec = live_spec("A", "a")
        allowed, reason, reserved = ledger.reserve(spec, 1000, 500)
        self.assertFalse(allowed)
        self.assertEqual(reason, "budget_exceeded_forecast")
        self.assertAlmostEqual(reserved, 0.002)
        self.assertEqual(ledger.calls, 0)

    def test_benchmark_policy_requires_positive_token_bounds(self):
        with self.assertRaises(ValueError):
            BenchmarkPolicy(max_output_tokens_per_call=0).validate(live=False)

    def test_load_config_validates_file(self):
        payload = {
            "models": {
                "A": {
                    "model_name": "modele-a", "provider": "p-a", "version": "v1",
                    "license": "licence", "usage_rights_verified": True, "region": "EU",
                    "retention_policy": "0j", "data_transfer_authorized": True,
                    "base_url": "https://a.invalid/v1", "api_key_env": "LLM_A_API_KEY",
                },
                "B": {
                    "model_name": "modele-b", "provider": "p-b", "version": "v1",
                    "license": "licence", "usage_rights_verified": True, "region": "EU",
                    "retention_policy": "0j", "data_transfer_authorized": True,
                    "base_url": "https://b.invalid/v1", "api_key_env": "LLM_B_API_KEY",
                },
            },
            "policy": {"allow_paid_calls": True, "v2_pattern": "cascade"},
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "models.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            spec_a, spec_b, policy = load_config(path)
        self.assertEqual(spec_a.model_name, "modele-a")
        self.assertEqual(spec_b.model_name, "modele-b")
        self.assertTrue(policy.allow_paid_calls)
        self.assertNotIn("api_key_env", spec_a.public_dict())


if __name__ == "__main__":
    unittest.main()
