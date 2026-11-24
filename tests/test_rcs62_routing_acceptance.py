"""RCS-62 — tests du protocole d'acceptation du routage Multi-LLM."""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tools.rcs62_routing_acceptance import (
    ROUTE_CASES,
    build_orchestrator,
    build_report,
    check_outputs,
    serialize,
    write_outputs,
)


class Rcs62RoutingAcceptanceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.report = build_report()

    def test_report_requires_three_distinct_route_cases(self) -> None:
        self.assertEqual(len(self.report["cases"]), 3)
        self.assertEqual(
            [row["category"] for row in self.report["cases"]],
            ["usual", "complex", "sensitive"],
        )
        self.assertEqual(len({row["case_id"] for row in self.report["cases"]}), 3)
        self.assertEqual(ROUTE_CASES[0]["case_id"], "T01")
        self.assertEqual(ROUTE_CASES[2]["category"], "sensitive")

    def test_two_distinct_models_and_default_guards(self) -> None:
        self.assertTrue(self.report["checks"]["deux_modeles_distincts"])
        self.assertTrue(self.report["checks"]["garde_fous_actifs"])
        orch = build_orchestrator()
        self.assertNotEqual(orch.spec_a.identity(), orch.spec_b.identity())
        self.assertEqual(orch.policy.max_calls_per_case, 2)
        self.assertFalse(orch.policy.allow_paid_calls)

    def test_route_uses_category_not_expected_behavior(self) -> None:
        by_id = {row["case_id"]: row for row in self.report["cases"]}
        self.assertEqual(by_id["T01"]["route_observee"], "A")
        self.assertEqual(by_id["T05"]["route_observee"], "B")
        self.assertEqual(by_id["T10"]["route_observee"], "A")
        for row in self.report["cases"]:
            self.assertEqual(row["route_observee"], row["route_avec_expected_modifie"])
        self.assertTrue(self.report["checks"]["selection_par_categorie_uniquement"])

    def test_sensitive_case_refused_before_any_call(self) -> None:
        sensible = [row for row in self.report["cases"] if row["category"] == "sensitive"]
        self.assertEqual(len(sensible), 1)
        self.assertEqual(sensible[0]["routing"]["status"], "refused")
        self.assertEqual(sensible[0]["routing"]["call_count"], 0)
        self.assertTrue(self.report["checks"]["cas_sensible_refuse_sans_appel"])

    def test_mono_comparison_present_for_each_case(self) -> None:
        for row in self.report["cases"]:
            self.assertIn(row["mono_a"]["status"], {"ok", "abstain", "refused"})
            self.assertIn(row["mono_b"]["status"], {"ok", "abstain", "refused"})
            self.assertEqual(row["mono_a"]["strategy"], "mono_a")
            self.assertEqual(row["mono_b"]["strategy"], "mono_b")
            self.assertEqual(row["routing"]["strategy"], "routing_a_b")
        self.assertTrue(self.report["checks"]["comparaison_mono_presente"])

    def test_report_has_no_prompt_secret_or_expected_behavior(self) -> None:
        data = json.dumps(self.report, ensure_ascii=False)
        self.assertNotIn("expected_behavior", data)
        self.assertNotIn("cas fictif de maintenance", data)
        self.assertNotIn("sk-", data)
        self.assertTrue(self.report["checks"]["traces_sans_secret_ni_expected"])

    def test_live_decision_stays_no_go(self) -> None:
        self.assertEqual(self.report["demo_gate"], "PASS")
        self.assertEqual(self.report["live_decision"], "NO_GO")
        self.assertFalse(self.report["qualite_llm_mesuree"])
        self.assertGreaterEqual(len(self.report["blocking_reasons"]), 3)

    def test_write_and_check_are_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_outputs(root, self.report)
            first = (root / "governance/rcs62/acceptance.json").read_text(encoding="utf-8")
            second = (root / "docs/44_rcs62_routing_multillm.md").read_text(encoding="utf-8")
            write_outputs(root, build_report())
            self.assertEqual(first, (root / "governance/rcs62/acceptance.json").read_text(encoding="utf-8"))
            self.assertEqual(second, (root / "docs/44_rcs62_routing_multillm.md").read_text(encoding="utf-8"))
            ok, reasons = check_outputs(root, self.report)
            self.assertTrue(ok, reasons)
            self.assertEqual(first, serialize(self.report))

    def test_check_detects_tampered_or_missing_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ok, reasons = check_outputs(root, self.report)
            self.assertFalse(ok)
            self.assertTrue(any("absent" in reason for reason in reasons))
            write_outputs(root, self.report)
            path = root / "governance/rcs62/acceptance.json"
            path.write_text(path.read_text(encoding="utf-8").replace("NO_GO", "GO"), encoding="utf-8")
            ok, reasons = check_outputs(root, self.report)
            self.assertFalse(ok)
            self.assertTrue(any("obsolète" in reason for reason in reasons))


if __name__ == "__main__":
    unittest.main()
