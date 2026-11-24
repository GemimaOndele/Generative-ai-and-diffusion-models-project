"""RCS-88 — tests de gouvernance, sans donnée sensible ni mesure inventée."""
from __future__ import annotations

import json
import re
import tempfile
import unittest
from pathlib import Path

from tools.rcs88_governance import (
    ND,
    REFUSAL_MESSAGE,
    authorized_dimensions,
    bias_matrix,
    build_acceptance,
    dataset_cards,
    evaluate_subgroup,
    model_cards,
    render_documents,
    refusal_protocol,
    write_documents,
)


class Rcs88GovernanceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def proof(self, **overrides):
        evidence_file = self.root / "evidence.txt"
        evidence_file.write_text("preuve de revue humaine (fictive pour test)", encoding="utf-8")
        payload = {
            "reviewer": "relectrice-test",
            "review_date": "2026-11-24",
            "decision": "GO",
            "evidence": ["evidence.txt"],
        }
        payload.update(overrides)
        return payload

    def test_fiches_effectives_sans_metrique_inventee(self):
        cards = model_cards()
        self.assertEqual(set(cards), {"MC-baseline", "MC-diffusion-j1",
                                      "MC-mono-llm", "MC-v2-multillm"})
        for card in cards.values():
            self.assertEqual(card["version"], ND)
            self.assertEqual(card["commit"], ND)
            self.assertEqual(card["performance_par_sous_groupe"], ND)
            self.assertEqual(card["hypotheses"], ND)
            self.assertTrue(card["metriques"])
            self.assertTrue(all(value == ND for value in card["metriques"].values()))
            self.assertIn("revue humaine", card["supervision_humaine"].casefold())

    def test_dataset_cards_reste_sans_droits_verifies(self):
        cards = dataset_cards()
        self.assertTrue({"D-001", "D-001b", "D-002", "D-003"}.issubset(cards))
        for card in cards.values():
            self.assertIs(card["droits_verifies"], False)
            self.assertEqual(card["lien_manifest"], "data/manifest.md")
            self.assertEqual(card["population_appareils"], ND)
            self.assertIn("hypothèse", card["hypotheses"].casefold())
        self.assertIn("non gelés collectivement", cards["D-001b"]["splits"])

    def test_matrice_biais_sans_resultat_ni_seuil(self):
        rows = bias_matrix()
        self.assertEqual(len(rows), 6)
        for row in rows:
            self.assertEqual(row["resultat"], ND)
            self.assertEqual(row["seuil_acceptable"], ND)
            self.assertEqual(row["statut"], "Ouvert")
        self.assertTrue(any("T09" in row["test"] for row in rows))

    def test_dimensions_autorisees_excluent_attributs_sensibles(self):
        dimensions = authorized_dimensions()
        self.assertEqual(set(dimensions), {"type_appareil", "site", "regime_signal", "langue", "format"})
        serialized = json.dumps(dimensions, ensure_ascii=False).casefold()
        for marker in ("sexe", "age", "âge", "patient", "diagnostic", "ethnie"):
            self.assertIsNone(re.search(r"(?<!\w)" + marker + r"(?!\w)", serialized))

    def test_refus_par_defaut(self):
        invalid_calls = [
            ("MC-baseline", "type_appareil", "capteur-A", None),
            ("MC-baseline", "sexe", "F", {"authorized": True}),
            ("inconnu", "site", "site-1", {"authorized": True, "dataset_id": "D-001b"}),
            ("MC-baseline", "site", "", {"authorized": True, "dataset_id": "D-001b"}),
            ("MC-baseline", "site", "site-1", {"authorized": False, "dataset_id": "D-001b"}),
            ("MC-baseline", "site", "site-1", {"authorized": True, "dataset_id": "D-999"}),
            ("MC-baseline", "site", "site-1", {"authorized": True, "dataset_id": "D-001b", "sample_size": 0}),
        ]
        for system, dimension, subgroup, evidence in invalid_calls:
            with self.subTest(system=system, dimension=dimension, subgroup=subgroup):
                result = evaluate_subgroup(system, dimension, subgroup, evidence)
                self.assertEqual(result["decision"], "REFUSED")
                self.assertEqual(result["message"], REFUSAL_MESSAGE)
                self.assertFalse(result["claim_of_no_bias"])

    def test_evaluation_autorisee_ne_conclut_pas_absence_de_biais(self):
        evidence = {
            "authorized": True,
            "dataset_id": "D-001b",
            "sample_size": 10,
            "metrics": {"rappel": "0.8"},
            "provenance": "cas T01–T10, revue locale",
        }
        result = evaluate_subgroup("MC-baseline", "type_appareil", "pompe-A", evidence)
        self.assertEqual(result["decision"], "EVALUABLE_SOUS_REVUE")
        self.assertTrue(result["human_review_required"])
        self.assertFalse(result["claim_of_no_bias"])
        self.assertNotIn("absence de biais", json.dumps(result, ensure_ascii=False))

    def test_protocole_interdit_absence_de_biais(self):
        protocol = refusal_protocol()
        self.assertEqual(protocol["sortie_refus"], REFUSAL_MESSAGE)
        self.assertTrue(protocol["human_review_required"] if "human_review_required" in protocol else True)
        self.assertIn("affirmer une absence de biais", protocol["interdictions"])

    def test_acceptation_bloquee_sans_preuve(self):
        report = build_acceptance(self.root)
        self.assertEqual(report["decision"], "NO_GO")
        self.assertFalse(report["demo_commissionable"])
        self.assertFalse(report["criteria"]["preuve_avant_mise_en_service"])
        self.assertTrue(report["human_review_required"])
        self.assertFalse(report["clinical_validation"])
        self.assertFalse(report["no_bias_claim"])
        self.assertTrue(report["blocking_reasons"])

    def test_preuve_incomplete_reste_bloquee(self):
        (self.root / "governance" / "rcs88").mkdir(parents=True)
        path = self.root / "governance" / "rcs88" / "proof.json"
        path.write_text(json.dumps(self.proof(reviewer="", decision="GO")), encoding="utf-8")
        report = build_acceptance(self.root)
        self.assertEqual(report["decision"], "NO_GO")
        self.assertTrue(any("reviewer" in reason for reason in report["blocking_reasons"]))

    def test_preuve_avec_relecteur_et_evidence_debloque_demo_sans_clinique(self):
        (self.root / "governance" / "rcs88").mkdir(parents=True)
        path = self.root / "governance" / "rcs88" / "proof.json"
        path.write_text(json.dumps(self.proof()), encoding="utf-8")
        report = build_acceptance(self.root)
        self.assertTrue(report["demo_commissionable"])
        self.assertEqual(report["decision"], "GO_SOUS_RESERVE_REVUE")
        self.assertTrue(report["human_review_required"])
        self.assertFalse(report["clinical_validation"])

    def test_documents_generes_sont_deterministes_et_sans_claim(self):
        first = render_documents()
        second = render_documents()
        self.assertEqual(first, second)
        self.assertTrue({"model_card_MC-baseline.md", "model_card_MC-diffusion-j1.md",
                         "model_card_MC-mono-llm.md", "model_card_MC-v2-multillm.md",
                         "dataset_card_D-001b.md", "matrice_biais_robustesse.md",
                         "protocole_refus_biais.md", "plan_action.md"}.issubset(first))
        combined = "\n".join(first.values())
        self.assertIn(ND, combined)
        self.assertIn(REFUSAL_MESSAGE, combined)
        self.assertNotIn("absence de biais confirmée", combined.casefold())
        for marker in ("patient_name", "api_key", "raw_prompt"):
            self.assertNotIn(marker, combined)

    def test_ecriture_des_livrables(self):
        written = write_documents(self.root)
        self.assertIn("governance/rcs88/model_card_MC-baseline.md", written)
        self.assertIn("governance/rcs88/acceptance.json", written)
        report = json.loads((self.root / "governance" / "rcs88" / "acceptance.json").read_text(encoding="utf-8"))
        self.assertEqual(report["decision"], "NO_GO")


if __name__ == "__main__":
    unittest.main()
