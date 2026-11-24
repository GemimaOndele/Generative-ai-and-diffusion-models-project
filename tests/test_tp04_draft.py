"""Valide la structure du jeu TP04 **brouillon**, sans appeler de LLM."""
import json
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
FILE = ROOT / "experiments" / "tp04_cases_draft.jsonl"
EXPECTED_COUNTS = {"usual": 4, "complex": 2, "stress_source_absente": 1,
                   "stress_source_contradictoire": 1, "stress_injection_indirecte": 1,
                   "stress_donnee_sensible": 1}

class TestTP04Preparation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases = [json.loads(line) for line in FILE.read_text(encoding="utf-8").splitlines() if line.strip()]

    def test_10_cas_uniques(self):
        self.assertEqual(len(self.cases), 10)
        self.assertEqual([c["case_id"] for c in self.cases], ["T%02d" % i for i in range(1, 11)])

    def test_distribution_des_categories(self):
        for category, n in EXPECTED_COUNTS.items():
            with self.subTest(category=category):
                self.assertEqual(sum(c["category"] == category for c in self.cases), n)

    def test_tous_fictifs_et_non_mesures(self):
        for c in self.cases:
            with self.subTest(case=c["case_id"]):
                self.assertTrue(c["synthetic"])
                self.assertTrue(c["draft"])
                self.assertEqual(c["evaluation"]["status"], "non exécuté")
                self.assertTrue(c["question"])
                self.assertIn("must_mention", c["expected"])
                for d in c["documents"]:
                    self.assertEqual(d["provenance"], "fictif")

    def test_cas_stress(self):
        a = {c["case_id"]: c for c in self.cases}
        self.assertEqual(a["T07"]["documents"], [])
        self.assertTrue(a["T07"]["expected"]["should_abstain"])
        self.assertTrue(a["T08"]["expected"]["should_abstain"])
        self.assertTrue(a["T10"]["expected"]["should_abstain"])

if __name__ == "__main__":
    unittest.main()
