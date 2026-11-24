"""RCS-85 — tests de la synthèse TP05 (coût/succès, émissions, risques, décision)."""
from __future__ import annotations

import hashlib
import tempfile
import unittest
from pathlib import Path

from tools.rcs85_synthese_tp05 import (
    ACCEPTANCE_REL,
    DOC_REL,
    MEASURES_REL,
    ND,
    SOURCE_DOC_REL,
    STRATEGIES,
    build_report,
    check_outputs,
    render_doc,
    serialize,
    write_outputs,
)

HEADER = (
    "case_id,run_id,strategy,model_version,model_source,status_success,latency_s,p95_s,"
    "calls,retries,input_tokens,output_tokens,variable_cost_eur,allocated_cost_eur,"
    "cost_per_success_eur,energy_kwh,co2e_kg,measurement_status,boundary,source_url,"
    "source_date,notes"
)


def write_measures(directory: Path, rows: list[str] | None = None) -> Path:
    path = directory / MEASURES_REL
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join([HEADER] + (rows or [])) + "\n", encoding="utf-8")
    return path


def write_doc(directory: Path, result: str = ND) -> Path:
    path = directory / SOURCE_DOC_REL
    path.parent.mkdir(parents=True, exist_ok=True)
    risks = [
        "Hallucination ou citation absente",
        "Injection indirecte de document",
        "Données patient et droits",
        "Décision de maintenance autonome",
    ]
    lines = [
        "# TP05",
        "",
        "## 4 — Éthique (55–75 min)",
        "",
        "| Risque (personnes touchées) | Test/preuve prévu | Résultat |",
        "|---|---|---|",
    ]
    lines += [f"| {name} | test prévu | {result} |" for name in risks]
    lines += ["", "## 5 — Synthèse (75–90 min)", "", "| Question | Réponse |", "|---|---|"]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def measure_row(strategy: str, **overrides: str) -> str:
    values = {
        "case_id": "T01", "run_id": "run-1", "strategy": strategy,
        "model_version": "v1", "model_source": "fournisseur autorisé",
        "status_success": "success", "latency_s": "1.2", "p95_s": "1.5",
        "calls": "2", "retries": "0", "input_tokens": "100", "output_tokens": "40",
        "variable_cost_eur": "0.10", "allocated_cost_eur": "0.05",
        "cost_per_success_eur": "", "energy_kwh": "0.01", "co2e_kg": "0.005",
        "measurement_status": "mesuré", "boundary": "local_cpu",
        "source_url": "https://example.invalid/tarif", "source_date": "2026-11-24",
        "notes": "mesure de test",
    }
    values.update(overrides)
    return ",".join(values[key] for key in HEADER.split(","))


class Rcs85SyntheseTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_shipped_csv_is_header_only_and_all_values_nd(self) -> None:
        report = build_report(Path(__file__).resolve().parents[1])
        self.assertEqual(report["inputs"]["rows"], 0)
        self.assertEqual(report["decision"], "À TESTER")
        self.assertEqual(report["risque_principal"], ND)
        for name in STRATEGIES:
            metrics = report["comparatif"][name]
            self.assertEqual(metrics["cout_par_succes_eur"], ND)
            self.assertEqual(metrics["source"], ND)
            self.assertEqual(metrics["co2e_kg"], ND)
            self.assertEqual(metrics["statut_emissions"], ND)

    def test_input_hash_is_real_and_not_fabricated(self) -> None:
        path = write_measures(self.root)
        report = build_report(self.root)
        normalized = path.read_bytes().replace(b"\r\n", b"\n")
        self.assertEqual(report["inputs"]["sha256"], hashlib.sha256(normalized).hexdigest())
        self.assertEqual(report["inputs"]["path"], MEASURES_REL.as_posix())
        path.write_bytes(normalized)  # checkout Linux (LF) : même hash
        self.assertEqual(build_report(self.root)["inputs"]["sha256"], report["inputs"]["sha256"])

    def test_cost_per_success_is_computed_with_source(self) -> None:
        write_measures(self.root, [measure_row(name) for name in STRATEGIES])
        write_doc(self.root)
        report = build_report(self.root)
        for name in STRATEGIES:
            item = report["detail_couts"][name]
            self.assertEqual(item["succes"], 1)
            self.assertEqual(item["cout_par_succes_eur"], "0.150000")
            self.assertEqual(item["statut"], "calculé")
            self.assertEqual(item["source"], "https://example.invalid/tarif")
            self.assertEqual(item["source_date"], "2026-11-24")

    def test_zero_success_missing_costs_and_missing_source_are_nd(self) -> None:
        write_measures(self.root, [
            measure_row("mono-A", status_success="refused"),
            measure_row("mono-B", variable_cost_eur=""),
            measure_row("V2", source_url=ND),
        ])
        report = build_report(self.root)
        for name in STRATEGIES:
            self.assertEqual(report["detail_couts"][name]["cout_par_succes_eur"], ND)
            self.assertEqual(report["detail_couts"][name]["statut"], ND)

    def test_emissions_use_weakest_status_and_never_zero(self) -> None:
        write_measures(self.root, [
            measure_row("mono-A", measurement_status="mesuré"),
            measure_row("mono-B", measurement_status="estimé"),
            measure_row("V2", energy_kwh="", co2e_kg=""),
        ])
        report = build_report(self.root)
        self.assertEqual(report["detail_emissions"]["mono-A"]["statut"], "mesuré")
        self.assertEqual(report["detail_emissions"]["mono-A"]["co2e_kg"], "0.005000")
        self.assertEqual(report["detail_emissions"]["mono-B"]["statut"], "estimé")
        self.assertEqual(report["detail_emissions"]["V2"]["energie_kwh"], ND)
        self.assertEqual(report["detail_emissions"]["V2"]["co2e_kg"], ND)

    def test_risks_come_from_tp05_doc_with_nd_results(self) -> None:
        write_measures(self.root)
        write_doc(self.root)
        report = build_report(self.root)
        self.assertEqual(len(report["risques_residuels"]), 4)
        self.assertEqual({risk["resultat"] for risk in report["risques_residuels"]}, {ND})
        self.assertEqual(report["risque_principal"], ND)
        self.assertEqual(report["decision"], "À TESTER")

    def test_fail_risk_is_no_go_and_all_pass_can_reach_go(self) -> None:
        write_measures(self.root, [measure_row(name) for name in STRATEGIES])
        write_doc(self.root, result="FAIL")
        self.assertEqual(build_report(self.root)["decision"], "NO_GO")

        write_doc(self.root, result="PASS")
        report = build_report(self.root, reviewer="Omar")
        self.assertEqual(report["decision"], "GO")
        write_measures(self.root, [
            measure_row(name, measurement_status="estimé") for name in STRATEGIES
        ])
        self.assertEqual(build_report(self.root, reviewer="Omar")["decision"], "À TESTER")
        write_outputs(self.root, report)
        ok, reasons = check_outputs(self.root, report)
        self.assertTrue(ok, reasons)

    def test_go_without_reviewer_is_rejected(self) -> None:
        write_measures(self.root, [measure_row(name) for name in STRATEGIES])
        write_doc(self.root, result="PASS")
        report = build_report(self.root, reviewer="Omar")
        report["reviewer"] = ND  # tentative de falsification d'un GO
        write_outputs(self.root, report)
        ok, reasons = check_outputs(self.root, report)
        self.assertFalse(ok)
        self.assertTrue(any("relecteur" in reason for reason in reasons))

    def test_missing_measure_file_is_reported(self) -> None:
        with self.assertRaises(ValueError):
            build_report(self.root)

    def test_write_check_deterministic_and_tamper(self) -> None:
        write_measures(self.root)
        write_doc(self.root)
        report = build_report(self.root)
        write_outputs(self.root, report)
        first = (self.root / ACCEPTANCE_REL).read_text(encoding="utf-8")
        doc = (self.root / DOC_REL).read_text(encoding="utf-8")
        self.assertEqual(first, serialize(report))
        self.assertIn("À TESTER", doc)
        write_outputs(self.root, build_report(self.root))
        self.assertEqual(first, (self.root / ACCEPTANCE_REL).read_text(encoding="utf-8"))
        self.assertEqual(doc, (self.root / DOC_REL).read_text(encoding="utf-8"))
        ok, reasons = check_outputs(self.root, report)
        self.assertTrue(ok, reasons)
        (self.root / ACCEPTANCE_REL).write_text("{}\n", encoding="utf-8")
        ok, reasons = check_outputs(self.root, report)
        self.assertFalse(ok)
        self.assertTrue(any("obsolète" in reason for reason in reasons))

    def test_rendered_doc_cites_versioned_files(self) -> None:
        write_measures(self.root)
        report = build_report(self.root)
        doc = render_doc(report)
        for path in report["fichiers_versionnes"]:
            self.assertIn(path, doc)
        self.assertNotIn("0.15", doc)


if __name__ == "__main__":
    unittest.main()
