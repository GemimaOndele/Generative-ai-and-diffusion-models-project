"""RCS-79 — tests de la décision benchmark V2 (GO/NO-GO sans preuve inventée)."""
from __future__ import annotations

import json
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path

from tools.rcs79_benchmark_decision import (
    ACCEPTANCE_REL,
    DOC_REL,
    ND,
    STRATEGIES,
    build_report,
    check_outputs,
    serialize,
    write_outputs,
)

SHA = "a" * 40
CATEGORY_SEQUENCE = (
    ["usual"] * 4
    + ["complex"] * 2
    + [
        "stress_source_absente",
        "stress_source_contradictoire",
        "stress_injection_indirecte",
        "stress_donnee_sensible",
    ]
)


def write_manifest(directory: Path, frozen: bool = True) -> Path:
    path = directory / "cases.csv"
    rows = ["case_id,category,expected_behavior,approval_state,freeze_commit"]
    for index, category in enumerate(CATEGORY_SEQUENCE, start=1):
        rows.append(
            f"T{index:02d},{category},comportement attendu de test,"
            f"{'frozen' if frozen else 'pending'},{SHA if frozen else ''}"
        )
    path.write_text("\n".join(rows) + "\n", encoding="utf-8")
    return path


def model_payload() -> dict:
    base = {
        "provider": "demo-provider",
        "license": "licence vérifiée en test",
        "region": "eu-test",
        "retention_policy": "aucune rétention",
        "validated": True,
        "usage_rights_verified": True,
        "data_transfer_authorized": True,
    }
    return {
        "A": {**base, "model_name": "modele-a", "version": "1.0"},
        "B": {**base, "model_name": "modele-b", "version": "2.0"},
    }


def results_payload() -> dict:
    metrics = {
        "quality": 0.70,
        "p95_ms": 800,
        "cost_eur": 0.20,
        "co2e_kg": 0.01,
        "energy_status": "mesuré",
    }
    return {
        "execution_mode": "live",
        "cases_count": 10,
        "strategies": {
            "mono-A": {**metrics, "quality": 0.60},
            "mono-B": {**metrics, "quality": 0.62},
            "V2": {**metrics, "quality": 0.80, "p95_ms": 1500, "cost_eur": 0.50},
        },
        "approved_thresholds": {
            "quality_delta": 0.10,
            "p95_ms": 2000,
            "cost_eur": 1.00,
        },
    }


def write_json(directory: Path, name: str, payload: dict) -> Path:
    path = directory / name
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


class Rcs79BenchmarkDecisionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.manifest = write_manifest(self.root)
        self.models = write_json(self.root, "models.json", model_payload())
        self.results = write_json(self.root, "results.json", results_payload())

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def report(self, **kwargs) -> dict:
        options = {
            "manifest": str(self.manifest),
            "models": str(self.models),
            "results": str(self.results),
            "reviewer": "Omar",
            "commit": SHA,
        }
        options.update(kwargs)
        return build_report(self.root, **options)

    def test_default_report_is_no_go_and_all_metrics_nd(self) -> None:
        report = build_report(self.root)
        self.assertEqual(report["decision"], "NO_GO")
        self.assertFalse(report["gates"]["cas_geles"])
        self.assertFalse(report["gates"]["modeles_ab_valides"])
        for name in STRATEGIES:
            for value in report["comparatif"][name].values():
                self.assertEqual(value, ND)
        self.assertGreaterEqual(len(report["blocking_reasons"]), 5)

    def test_shipped_manifest_is_not_frozen(self) -> None:
        report = build_report(Path(__file__).resolve().parents[1])
        self.assertEqual(report["decision"], "NO_GO")
        self.assertFalse(report["gates"]["cas_geles"])

    def test_frozen_cases_and_models_but_no_live_results_stays_a_tester(self) -> None:
        report = self.report(results=None)
        self.assertTrue(report["gates"]["cas_geles"])
        self.assertTrue(report["gates"]["modeles_ab_valides"])
        self.assertFalse(report["gates"]["resultats_live_reels"])
        self.assertEqual(report["decision"], "A_TESTER")

    def test_demo_results_are_never_accepted(self) -> None:
        payload = results_payload()
        payload["execution_mode"] = "demo"
        path = write_json(self.root, "demo.json", payload)
        report = self.report(results=str(path))
        self.assertFalse(report["gates"]["resultats_live_reels"])
        self.assertEqual(report["decision"], "A_TESTER")

    def test_all_gates_valid_produce_go_with_reviewer_and_commit(self) -> None:
        report = self.report()
        for name, value in report["gates"].items():
            self.assertTrue(value, name)
        self.assertEqual(report["decision"], "GO")
        self.assertEqual(report["reviewer"], "Omar")
        self.assertEqual(report["commit"], SHA)
        self.assertEqual(report["comparatif"]["V2"]["quality"], 0.80)
        write_outputs(self.root, report)
        ok, reasons = check_outputs(self.root, report)
        self.assertTrue(ok, reasons)

    def test_quality_latency_and_cost_thresholds_are_enforced(self) -> None:
        cases = [
            ("qualite_v2_superieure", lambda p: p["strategies"]["V2"].update(quality=0.65)),
            ("latence_conforme", lambda p: p["strategies"]["V2"].update(p95_ms=3000)),
            ("cout_conforme", lambda p: p["strategies"]["V2"].update(cost_eur=2.0)),
        ]
        for gate, mutate in cases:
            with self.subTest(gate=gate):
                payload = results_payload()
                mutate(payload)
                path = write_json(self.root, f"{gate}.json", payload)
                report = self.report(results=str(path))
                self.assertFalse(report["gates"][gate])
                self.assertEqual(report["decision"], "A_TESTER")

    def test_energy_and_human_review_are_required(self) -> None:
        payload = results_payload()
        payload["strategies"]["mono-A"]["energy_status"] = ND
        path = write_json(self.root, "energy.json", payload)
        report = self.report(results=str(path), reviewer=ND)
        self.assertFalse(report["gates"]["energie_documentee"])
        self.assertFalse(report["gates"]["revue_humaine"])
        self.assertEqual(report["decision"], "A_TESTER")

    def test_models_must_be_distinct_validated_and_authorized(self) -> None:
        payload = model_payload()
        payload["B"]["model_name"] = payload["A"]["model_name"]
        payload["B"]["version"] = payload["A"]["version"]
        path = write_json(self.root, "same-models.json", payload)
        self.assertEqual(self.report(models=str(path))["decision"], "NO_GO")

        payload = model_payload()
        payload["A"]["validated"] = False
        path = write_json(self.root, "unvalidated.json", payload)
        self.assertEqual(self.report(models=str(path))["decision"], "NO_GO")

        payload = model_payload()
        del payload["B"]["retention_policy"]
        path = write_json(self.root, "incomplete.json", payload)
        self.assertEqual(self.report(models=str(path))["decision"], "NO_GO")

    def test_invalid_commit_blocks_go(self) -> None:
        report = self.report(commit="abcxyz")
        self.assertFalse(report["gates"]["commit_reference"])
        self.assertEqual(report["decision"], "A_TESTER")

    def test_missing_manifest_is_reported_not_fabricated(self) -> None:
        report = self.report(manifest=str(self.root / "absent.csv"))
        self.assertFalse(report["gates"]["cas_geles"])
        self.assertEqual(report["decision"], "NO_GO")
        self.assertTrue(any("Manifeste" in reason for reason in report["blocking_reasons"]))

    def test_write_check_deterministic_and_tamper(self) -> None:
        report = self.report()
        write_outputs(self.root, report)
        first = (self.root / ACCEPTANCE_REL).read_text(encoding="utf-8")
        doc = (self.root / DOC_REL).read_text(encoding="utf-8")
        self.assertEqual(first, serialize(report))
        write_outputs(self.root, self.report())
        self.assertEqual(first, (self.root / ACCEPTANCE_REL).read_text(encoding="utf-8"))
        self.assertEqual(doc, (self.root / DOC_REL).read_text(encoding="utf-8"))
        ok, reasons = check_outputs(self.root, report)
        self.assertTrue(ok, reasons)
        (self.root / ACCEPTANCE_REL).write_text("{}\n", encoding="utf-8")
        ok, reasons = check_outputs(self.root, report)
        self.assertFalse(ok)
        self.assertTrue(any("obsolète" in reason for reason in reasons))

    def test_no_go_without_all_gates_even_if_tampered(self) -> None:
        report = self.report()
        tampered = deepcopy(report)
        tampered["decision"] = "GO"
        tampered["gates"]["resultats_live_reels"] = False
        ok, reasons = check_outputs(self.root, tampered)
        self.assertFalse(ok)
        self.assertTrue(any("GO sans toutes les portes" in reason for reason in reasons))


if __name__ == "__main__":
    unittest.main()
