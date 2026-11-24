"""Tests de cohérence du squelette GitHub RCS. Ne valide PAS les modèles IA."""
import csv
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]

class TestStructure(unittest.TestCase):
    def test_dossiers_et_documents_de_reference(self):
        required = [
            "README.md", "CONTRIBUTING.md", ".gitignore", ".env.example",
            "docs/03_preuve_technique.md", "docs/05_tp04_architecture_v2.md",
            "docs/05_tp04_benchmark.md", "data/manifest.md",
            "experiments/results.csv", "experiments/test_cases.jsonl",
            "src/orchestrator.py", "tests/cases.csv",
            ".github/pull_request_template.md",
        ]
        for rel in required:
            with self.subTest(path=rel):
                self.assertTrue((ROOT / rel).is_file(), f"Fichier manquant : {rel}")

    def test_en_tete_cas_de_tests_c3(self):
        with (ROOT / "tests/cases.csv").open(newline="", encoding="utf-8") as fh:
            cols = next(csv.reader(fh))
        for field in ("case_id", "type", "expected_behavior", "check_mode"):
            self.assertIn(field, cols)

    def test_resultats_non_inventes(self):
        path = ROOT / "experiments/results.csv"
        with path.open(newline="", encoding="utf-8") as fh:
            rows = list(csv.reader(fh))
        self.assertEqual(len(rows), 1, "Aucune mesure scientifique n'est encore revendiquée")

    def test_fichier_jsonl_compatible_vide(self):
        # À remplacer par des tests sur données figées lors du TP04.
        text = (ROOT / "experiments/test_cases.jsonl").read_text(encoding="utf-8")
        self.assertEqual(text.strip(), "")

if __name__ == "__main__":
    unittest.main()
