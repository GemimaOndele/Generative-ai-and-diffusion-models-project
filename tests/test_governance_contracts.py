"""Contrôles de gabarits. Ne certifient ni la performance IA ni la sécurité clinique."""
import csv
import json
from pathlib import Path
import unittest

BASE = Path(__file__).resolve().parents[1]

class TestGovernanceTemplates(unittest.TestCase):
    def test_registres_champs_obligatoires(self):
        checks = {
            "model_registry.csv": {"model_id","dataset_version","code_commit_sha","semantic_version","validation_metrics_ref","approval"},
            "templates/risk_register_template.csv": {"risk_id","likelihood_scale","impact_scale","owner","mitigation","review_date"},
            "cost_register.csv": {"cost_category","estimated_or_actual","hours_or_blank","amount_eur_or_blank","source_date"},
        }
        for name, must in checks.items():
            with self.subTest(name=name):
                with (BASE/"governance"/name).open(newline="",encoding="utf-8") as f:
                    rows=list(csv.reader(f))
                self.assertEqual(len(rows),1,"Données expérimentales fictives interdites")
                self.assertTrue(must.issubset(set(rows[0])))

    def test_schema_trace_valide_et_prive(self):
        d=json.loads((BASE/"governance"/"templates/trace_event_draft.schema.json").read_text(encoding="utf-8"))
        self.assertEqual(d["type"],"object")
        self.assertFalse(d["additionalProperties"])
        for field in ("trace_id","run_id","component","measurement_status","measurement_boundary"):
            self.assertIn(field,d["required"])
        banned={"patient_name","patient_id","api_key","raw_prompt","personal_data"}
        self.assertTrue(banned.isdisjoint(d["properties"]))

    def test_decision_template_not_parallel_register(self):
        root = BASE / "governance"
        template = root / "templates" / "decision_register_template.csv"
        self.assertTrue(template.is_file())
        self.assertEqual(len(template.read_text(encoding="utf-8").strip().splitlines()), 1)
        self.assertFalse((root / "decision_register.csv").exists())

if __name__=="__main__":
    unittest.main()
