"""RCS-79 — tests stricts de la décision benchmark (relecture de 5a1cf06).

Chaque porte ajoutée après la relecture possède au moins un test négatif :
booléens/infini/bornes, ND/espaces dans les identités, résultats autoproclamés live,
lien manifeste/config/run/commit, antériorité des seuils, revue indépendante
attestée et interdiction d'un GO automatisé.
"""
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
    SCHEMA_DECISION,
    SCHEMA_MODELS,
    SCHEMA_RESULTS,
    SCHEMA_REVIEW,
    STRATEGIES,
    _number,
    build_report,
    check_outputs,
    manifest_fingerprint,
    models_valid,
    results_valid,
    review_valid,
    serialize,
    write_outputs,
)
from tools.rcs81_evaluate import IDS

SHA = "a" * 40
CONFIG_SHA = "b" * 64
RUN_ID = "run-20261124"
COMMIT = "c" * 40
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


def model_payload(manifest_sha: str) -> dict:
    base = {
        "provider": "demo-provider",
        "license": "licence vérifiée en test",
        "region": "eu-test",
        "retention_policy": "aucune rétention",
        "validated": True,
        "usage_rights_verified": True,
        "data_transfer_authorized": True,
        "validation_source": "https://example.invalid/model-card",
        "validation_date": "2026-11-20",
    }
    return {
        "schema": SCHEMA_MODELS,
        "config_sha256": CONFIG_SHA,
        "manifest_sha256": manifest_sha,
        "A": {**base, "model_name": "modele-a", "version": "1.0"},
        "B": {**base, "model_name": "modele-b", "version": "2.0"},
    }


def results_payload(manifest_sha: str, commit: str = COMMIT) -> dict:
    metrics = {
        "quality": 0.70,
        "p95_ms": 800,
        "cost_eur": 0.20,
        "co2e_kg": 0.01,
        "energy_status": "mesuré",
    }
    return {
        "schema": SCHEMA_RESULTS,
        "execution_mode": "live",
        "cases_count": 10,
        "executed_at": "2026-11-24T10:00:00Z",
        "manifest_sha256": manifest_sha,
        "config_sha256": CONFIG_SHA,
        "run_id": RUN_ID,
        "commit": commit,
        "run_evidence": "https://example.invalid/run-logs",
        "cases": [{"case_id": case_id, "freeze_commit": SHA} for case_id in IDS],
        "strategies": {
            name: {
                **metrics,
                "run_id": RUN_ID,
                "quality": 0.80 if name == "V2" else (0.60 if name == "mono-A" else 0.62),
                "p95_ms": 1500 if name == "V2" else 800,
                "cost_eur": 0.50 if name == "V2" else 0.20,
                "trace_evidence": f"https://example.invalid/trace-{name}",
            }
            for name in STRATEGIES
        },
        "approved_thresholds": {
            "quality_delta": 0.10,
            "p95_ms": 2000,
            "cost_eur": 1.00,
            "approved_at": "2026-11-23",
            "approved_by": "Aminata",
            "evidence": "https://example.invalid/seuils-approuves",
        },
    }


def review_payload(commit: str = COMMIT, reviewer: str = "Omar") -> dict:
    return {
        "schema": SCHEMA_REVIEW,
        "reviewer": reviewer,
        "role": "independent",
        "reviewed_at": "2026-11-24",
        "decision": "GO_WITH_RESERVATIONS",
        "signature": "signature-attestee-20261124",
        "commit": commit,
        "authors": ["Aminata", "Gémima"],
    }


def write_json(directory: Path, name: str, payload: dict) -> Path:
    path = directory / name
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return path


class Rcs79BenchmarkDecisionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.manifest = write_manifest(self.root)
        self.manifest_sha = manifest_fingerprint(self.manifest)
        assert self.manifest_sha is not None
        self.models = write_json(self.root, "models.json", model_payload(self.manifest_sha))
        self.results = write_json(self.root, "results.json", results_payload(self.manifest_sha))
        self.review = write_json(self.root, "review.json", review_payload())

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def report(self, **kwargs) -> dict:
        options = {
            "manifest": str(self.manifest),
            "models": str(self.models),
            "results": str(self.results),
            "review_evidence": str(self.review),
            "reviewer": "Omar",
            "commit": COMMIT,
        }
        options.update(kwargs)
        return build_report(self.root, **options)

    def replace_json(self, path: Path, mutate) -> Path:
        payload = json.loads(path.read_text(encoding="utf-8"))
        mutate(payload)
        return write_json(self.root, path.name, payload)

    # --- Validations de base -------------------------------------------------
    def test_default_report_is_no_go_and_all_metrics_nd(self) -> None:
        report = build_report(self.root)
        self.assertEqual(report["decision"], "NO_GO")
        self.assertFalse(report["gates"]["cas_geles"])
        for name in STRATEGIES:
            for value in report["comparatif"][name].values():
                self.assertEqual(value, ND)
        self.assertTrue(any("Autorisation collective" in reason for reason in report["blocking_reasons"]))

    def test_shipped_manifest_is_not_frozen(self) -> None:
        report = build_report(Path(__file__).resolve().parents[1])
        self.assertEqual(report["decision"], "NO_GO")
        self.assertFalse(report["gates"]["cas_geles"])

    def test_all_valid_inputs_only_produce_recommendation(self) -> None:
        report = self.report()
        for name, value in report["gates"].items():
            if name != "autorisation_collective":
                self.assertTrue(value, name)
        self.assertFalse(report["gates"]["autorisation_collective"])
        self.assertEqual(report["decision"], "RECOMMANDATION_A_RATIFIER")
        self.assertEqual(report["schema"], SCHEMA_DECISION)
        write_outputs(self.root, report)
        ok, reasons = check_outputs(self.root, report)
        self.assertTrue(ok, reasons)

    # --- Nombres stricts et bornés ------------------------------------------
    def test_number_rejects_bool_non_finite_string_and_out_of_bounds(self) -> None:
        for value in (True, False, "0.8", float("inf"), float("-inf"), float("nan"), -1, ND, None):
            with self.subTest(value=value):
                self.assertIsNone(_number(value, "quality"))
        self.assertIsNone(_number(1.2, "quality"))
        self.assertIsNone(_number(86_400_001, "p95_ms"))
        self.assertEqual(_number(0.8, "quality"), 0.8)
        self.assertEqual(_number(2000, "p95_ms"), 2000.0)

    def test_boolean_quality_in_results_is_rejected(self) -> None:
        path = self.replace_json(self.results, lambda p: p["strategies"]["V2"].update(quality=True))
        report = self.report(results=str(path))
        self.assertFalse(report["gates"]["resultats_live_reels"])
        self.assertEqual(report["decision"], "A_TESTER")

    def test_infinite_and_out_of_bounds_metrics_are_rejected(self) -> None:
        payload = json.loads(self.results.read_text(encoding="utf-8"))
        payload["strategies"]["V2"]["cost_eur"] = float("inf")
        # JSON standard n'a pas d'infini : on teste directement le validateur.
        self.assertIsNone(_number(payload["strategies"]["V2"]["cost_eur"], "cost_eur"))
        path = self.replace_json(self.results, lambda p: p["strategies"]["V2"].update(quality=1.5))
        self.assertFalse(self.report(results=str(path))["gates"]["resultats_live_reels"])

    # --- Modèles stricts -----------------------------------------------------
    def test_models_reject_nd_none_and_uncanonical_identity(self) -> None:
        base = model_payload(self.manifest_sha)
        for value in (ND, None, " modele-a", "modele-a "):
            with self.subTest(value=value):
                broken = deepcopy(base)
                broken["A"]["model_name"] = value
                self.assertFalse(models_valid(broken, self.manifest_sha))
        broken = deepcopy(base)
        broken["B"]["provider"] = "demo provider"
        self.assertFalse(models_valid(broken, self.manifest_sha))
        broken = deepcopy(base)
        broken["manifest_sha256"] = "d" * 64
        self.assertFalse(models_valid(broken, self.manifest_sha))
        broken = deepcopy(base)
        broken["A"]["validation_date"] = ND
        self.assertFalse(models_valid(broken, self.manifest_sha))
        self.assertTrue(models_valid(base, self.manifest_sha))

    def test_models_must_be_distinct_validated_and_authorized(self) -> None:
        path = self.replace_json(self.models, lambda p: (
            p["B"].update(model_name=p["A"]["model_name"], version=p["A"]["version"])
        ))
        self.assertEqual(self.report(models=str(path))["decision"], "NO_GO")
        path = self.replace_json(self.models, lambda p: p["A"].update(validated=False))
        self.assertEqual(self.report(models=str(path))["decision"], "NO_GO")
        path = self.replace_json(self.models, lambda p: p["B"].update(data_transfer_authorized=False))
        self.assertEqual(self.report(models=str(path))["decision"], "NO_GO")

    # --- Résultats liés au manifeste/config/run/commit -----------------------
    def test_self_proclaimed_live_without_case_evidence_is_rejected(self) -> None:
        path = self.replace_json(self.results, lambda p: p.update(cases=[], cases_count=10))
        self.assertFalse(results_valid(
            json.loads(path.read_text(encoding="utf-8")),
            rows=[{"case_id": case_id, "freeze_commit": SHA} for case_id in IDS],
            manifest_sha256=self.manifest_sha, config_sha256=CONFIG_SHA, commit=COMMIT,
        ))
        report = self.report(results=str(path))
        self.assertFalse(report["gates"]["preuves_manifeste_config_run"])
        self.assertEqual(report["decision"], "A_TESTER")

    def test_all_ten_case_ids_and_fingerprints_must_match_manifest(self) -> None:
        def tamper(p: dict) -> None:
            p["cases"][0]["case_id"] = "T11"
            p["cases"][1]["freeze_commit"] = "e" * 40
        path = self.replace_json(self.results, tamper)
        report = self.report(results=str(path))
        self.assertFalse(report["gates"]["preuves_manifeste_config_run"])
        self.assertFalse(report["gates"]["resultats_live_reels"])

    def test_manifest_config_run_and_commit_links_are_enforced(self) -> None:
        mutations = [
            ("manifest_sha256", "d" * 64),
            ("config_sha256", "d" * 64),
            ("run_id", "run-autre"),
            ("commit", "d" * 40),
            ("run_evidence", ND),
        ]
        for key, value in mutations:
            with self.subTest(key=key):
                path = self.replace_json(self.results, lambda p, k=key, v=value: p.update({k: v}))
                report = self.report(results=str(path))
                self.assertFalse(report["gates"]["preuves_manifeste_config_run"], key)
        path = self.replace_json(self.results, lambda p: p["strategies"]["V2"].update(run_id="run-autre"))
        self.assertFalse(self.report(results=str(path))["gates"]["preuves_manifeste_config_run"])

    def test_demo_results_are_never_accepted(self) -> None:
        path = self.replace_json(self.results, lambda p: p.update(execution_mode="demo"))
        report = self.report(results=str(path))
        self.assertFalse(report["gates"]["resultats_live_reels"])
        self.assertEqual(report["decision"], "A_TESTER")

    def test_extra_unknown_keys_break_strict_schema(self) -> None:
        path = self.replace_json(self.results, lambda p: p.update(champ_inattendu="valeur"))
        self.assertFalse(self.report(results=str(path))["gates"]["resultats_live_reels"])
        path = self.replace_json(self.models, lambda p: p.update(champ_inattendu="valeur"))
        self.assertEqual(self.report(models=str(path))["decision"], "NO_GO")

    # --- Seuils approuvés avant les résultats --------------------------------
    def test_thresholds_must_be_approved_before_execution(self) -> None:
        for approved_at in ("2026-11-24", "2026-11-25"):
            with self.subTest(approved_at=approved_at):
                path = self.replace_json(
                    self.results,
                    lambda p, value=approved_at: p["approved_thresholds"].update(approved_at=value),
                )
                report = self.report(results=str(path))
                self.assertFalse(report["gates"]["seuils_approuves_avant_resultats"])
                self.assertEqual(report["decision"], "A_TESTER")

    def test_threshold_provenance_is_required(self) -> None:
        for key in ("approved_by", "evidence"):
            with self.subTest(key=key):
                path = self.replace_json(
                    self.results, lambda p, k=key: p["approved_thresholds"].update({k: ND})
                )
                self.assertFalse(self.report(results=str(path))["gates"]["seuils_approuves_avant_resultats"])

    # --- Revue indépendante attestée ----------------------------------------
    def test_arbitrary_reviewer_name_without_attestation_is_rejected(self) -> None:
        report = self.report(review_evidence=None, reviewer="Nimportequi")
        self.assertFalse(report["gates"]["revue_independante_attestee"])
        self.assertEqual(report["decision"], "A_TESTER")
        self.assertEqual(report["reviewer"], "Nimportequi")  # nom canonique mais non attesté

    def test_review_attestation_must_be_independent_signed_and_current(self) -> None:
        mutations = [
            ("role", "pair"),
            ("reviewer", "Aminata"),
            ("signature", "trop-court"),
            ("commit", "d" * 40),
            ("reviewed_at", "2026-11-23"),
            ("decision", "ND"),
        ]
        for key, value in mutations:
            with self.subTest(key=key):
                path = self.replace_json(self.review, lambda p, k=key, v=value: p.update({k: v}))
                report = self.report(review_evidence=str(path))
                self.assertFalse(report["gates"]["revue_independante_attestee"], key)
                self.assertEqual(report["decision"], "A_TESTER")
        path = self.replace_json(self.review, lambda p: p.update(authors=["Omar", "Aminata"]))
        self.assertFalse(self.report(review_evidence=str(path))["gates"]["revue_independante_attestee"])

    # --- Commit et ratification ---------------------------------------------
    def test_commit_reference_requires_full_sha_and_run_match(self) -> None:
        short = self.report(commit="abcdef0")
        self.assertEqual(short["commit"], ND)
        self.assertFalse(short["gates"]["commit_reference"])
        self.assertNotEqual(short["decision"], "RECOMMANDATION_A_RATIFIER")
        mismatched = self.report(commit="d" * 40)
        self.assertFalse(mismatched["gates"]["commit_reference"])
        self.assertEqual(mismatched["decision"], "A_TESTER")

    def test_go_is_never_emitted_and_tampering_is_detected(self) -> None:
        report = self.report()
        self.assertEqual(report["decision"], "RECOMMANDATION_A_RATIFIER")
        write_outputs(self.root, report)
        tampered = deepcopy(report)
        tampered["decision"] = "GO"
        write_outputs(self.root, tampered)
        ok, reasons = check_outputs(self.root, tampered)
        self.assertFalse(ok)
        self.assertTrue(any("GO interdit" in reason for reason in reasons))

    def test_write_check_deterministic_and_tamper(self) -> None:
        report = self.report()
        write_outputs(self.root, report)
        first = (self.root / ACCEPTANCE_REL).read_text(encoding="utf-8")
        doc = (self.root / DOC_REL).read_text(encoding="utf-8")
        self.assertEqual(first, serialize(report))
        self.assertIn("RECOMMANDATION_A_RATIFIER", doc)
        write_outputs(self.root, self.report())
        self.assertEqual(first, (self.root / ACCEPTANCE_REL).read_text(encoding="utf-8"))
        self.assertEqual(doc, (self.root / DOC_REL).read_text(encoding="utf-8"))
        ok, reasons = check_outputs(self.root, report)
        self.assertTrue(ok, reasons)
        (self.root / ACCEPTANCE_REL).write_text("{}\n", encoding="utf-8")
        ok, reasons = check_outputs(self.root, report)
        self.assertFalse(ok)
        self.assertTrue(any("obsolète" in reason for reason in reasons))


if __name__ == "__main__":
    unittest.main()
