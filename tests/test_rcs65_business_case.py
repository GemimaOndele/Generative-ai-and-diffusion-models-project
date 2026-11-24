"""RCS-65 — tests du business case ROI (formules et garde-fous)."""
from __future__ import annotations

import json
import tempfile
import unittest
from dataclasses import replace
from decimal import Decimal
from pathlib import Path

from tools.rcs65_business_case import (
    HYPOTHESES,
    ND,
    SCENARIOS,
    build_report,
    check_outputs,
    compute_scenario,
    load_assumptions,
    render_doc,
    scenario_ready,
    serialize,
    template_scenario,
    write_outputs,
)

ACCEPTANCE_PATH = Path("governance/rcs65/business_case.json")
DOC_PATH = Path("docs/45_rcs65_business_case_roi.md")

VALUES = {
    "H-01": "100", "H-02": "0.10", "H-03": "15", "H-04": "25",
    "H-05": "0.08", "H-06": "180", "H-07": "2000", "H-08": "12",
}


def sourced_scenario(**overrides: str) -> dict:
    scenario = template_scenario()
    merged = {**VALUES, **overrides}
    for key, raw in merged.items():
        scenario[key] = replace(
            scenario[key], value=Decimal(raw), status="hypothèse",
            source="hypothèse explicite de test", source_date="2026-11-24",
        )
    scenario["H-09"] = replace(
        scenario["H-09"], value=Decimal("1"), status="hypothèse",
        source="périmètre vérifié", source_date="2026-11-24",
    )
    if "H-09" in overrides:
        scenario["H-09"] = replace(
            scenario["H-09"], value=Decimal(overrides["H-09"]),
        )
    return scenario


class Rcs65BusinessCaseTests(unittest.TestCase):
    def test_template_has_three_scenarios_all_nd(self) -> None:
        report = build_report()
        self.assertEqual(tuple(report["scenarios"]), SCENARIOS)
        self.assertFalse(report["claim_ready"])
        self.assertFalse(report["financial_claim"])
        self.assertEqual(report["decision"], ND)
        for scenario in report["scenarios"].values():
            for item in scenario["hypotheses"].values():
                self.assertEqual(item["value"], ND)
                self.assertEqual(item["status"], ND)
            self.assertEqual(scenario["result"]["roi"], ND)

    def test_formulas_are_exact_and_verifiable(self) -> None:
        result = compute_scenario(sourced_scenario())
        self.assertEqual(result["cout_variable_mensuel_eur"], "8.00")
        self.assertEqual(result["cout_total_mensuel_eur"], "188.00")
        self.assertEqual(result["cout_total_annuel_eur"], "4256.00")
        self.assertEqual(result["benefice_annuel_brut_valorise_eur"], "750.00")
        self.assertEqual(result["gain_net_annuel_eur"], "-3506.00")
        self.assertEqual(result["roi"], "-0.82")
        self.assertEqual(result["payback_mois"], ND)

    def test_unsourced_values_never_become_claims(self) -> None:
        scenario = template_scenario()
        for key, raw in VALUES.items():
            scenario[key] = replace(scenario[key], value=Decimal(raw), status="hypothèse")
        scenario["H-09"] = replace(scenario["H-09"], value=Decimal("1"), status="hypothèse")
        self.assertFalse(scenario_ready(scenario))
        result = compute_scenario(scenario)
        self.assertEqual(result["roi"], ND)
        self.assertIn("non sourcées", result["raison"])

    def test_assumptions_file_computes_without_automatic_go(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "assumptions.json"
            payload = {
                "scenarios": {
                    name: {
                        key: {
                            "value": VALUES[key], "status": "hypothèse",
                            "source": "source explicite de test",
                            "source_date": "2026-11-24",
                        }
                        for key in HYPOTHESES if key != "H-09"
                    }
                    | {"H-09": {"value": True, "status": "hypothèse",
                                "source": "périmètre vérifié", "source_date": "2026-11-24"}}
                    for name in SCENARIOS
                }
            }
            path.write_text(json.dumps(payload), encoding="utf-8")
            report = build_report(str(path), reviewer="Omar")
            self.assertTrue(report["claim_ready"])
            self.assertEqual(report["decision"], "À VALIDER")
            self.assertEqual(report["reviewer"], "Omar")
            self.assertFalse(report["financial_claim"])
            self.assertEqual(report["scenarios"]["central"]["result"]["roi"], "-0.82")
            self.assertNotEqual(report["decision"], "GO")

    def test_double_counting_flag_blocks_claim(self) -> None:
        scenario = sourced_scenario(**{"H-09": "0"})
        self.assertFalse(scenario_ready(scenario))
        self.assertEqual(compute_scenario(scenario)["cout_total_annuel_eur"], ND)

    def test_double_counting_requires_sourced_strict_boolean(self) -> None:
        scenario = sourced_scenario()
        scenario["H-09"] = replace(scenario["H-09"], source=ND)
        self.assertFalse(scenario_ready(scenario))
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "assumptions.json"
            for flag in ("false", "true", 1, []):
                path.write_text(json.dumps({"scenarios": {"central": {
                    "H-09": {"value": flag, "status": "hypothèse"}
                }}}), encoding="utf-8")
                with self.assertRaisesRegex(ValueError, "booléen JSON"):
                    load_assumptions(str(path))

    def test_fraction_date_and_annual_horizon_are_validated(self) -> None:
        self.assertFalse(scenario_ready(sourced_scenario(**{"H-02": "1.2"})))
        scenario = sourced_scenario()
        scenario["H-01"] = replace(scenario["H-01"], source_date="2026-02-30")
        self.assertFalse(scenario_ready(scenario))
        result = compute_scenario(sourced_scenario(**{"H-08": "24"}))
        self.assertEqual(result["roi"], ND)
        self.assertIn("12 mois", result["raison"])

    def test_zero_horizon_and_zero_cost_do_not_divide(self) -> None:
        zero_horizon = compute_scenario(sourced_scenario(**{"H-08": "0"}))
        self.assertEqual(zero_horizon["roi"], ND)
        self.assertIn("division par zéro", zero_horizon["raison"])
        zero_cost = compute_scenario(sourced_scenario(**{
            "H-05": "0", "H-06": "0", "H-07": "0",
        }))
        self.assertEqual(zero_cost["roi"], ND)
        self.assertEqual(zero_cost["payback_mois"], ND)

    def test_positive_payback_is_computed(self) -> None:
        result = compute_scenario(sourced_scenario(**{
            "H-01": "1000", "H-02": "0.20", "H-03": "30", "H-04": "30",
            "H-05": "0.01", "H-06": "10", "H-07": "100",
        }))
        self.assertEqual(result["payback_mois"], "0.03")
        self.assertNotEqual(result["roi"], ND)

    def test_write_check_deterministic_and_tamper(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            report = build_report()
            write_outputs(root, report)
            doc = (root / DOC_PATH).read_text(encoding="utf-8")
            self.assertEqual((root / ACCEPTANCE_PATH).read_text(encoding="utf-8"), serialize(report))
            write_outputs(root, build_report())
            self.assertEqual(doc, (root / DOC_PATH).read_text(encoding="utf-8"))
            ok, reasons = check_outputs(root, report)
            self.assertTrue(ok, reasons)
            (root / ACCEPTANCE_PATH).write_text("{}\n", encoding="utf-8")
            ok, reasons = check_outputs(root, report)
            self.assertFalse(ok)
            self.assertTrue(any("obsolète" in reason for reason in reasons))

    def test_shipped_doc_has_no_invented_financial_value(self) -> None:
        report = build_report()
        doc = render_doc(report)
        for forbidden in ("18 750", "93 333", "500", "2 000", "232,4%"):
            self.assertNotIn(forbidden, doc)
        self.assertIn("ND", doc)
        self.assertIn("À VALIDER" if report["claim_ready"] else "ND", doc)


if __name__ == "__main__":
    unittest.main()
