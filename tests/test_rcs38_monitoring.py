"""Tests de contrat, aucun résultat réel de maintenance ou d'IA."""
import json
from pathlib import Path
import tempfile
import unittest
from tools.rcs38_contract import validate_fixture

ROOT=Path(__file__).resolve().parents[1]
class TestMonitoringDemo(unittest.TestCase):
    def test_fixture_validated(self):
        r=validate_fixture()
        self.assertEqual(r["devices"],4)
        self.assertEqual(r["runs"],2)

    def test_no_energy_claim_for_remote_api(self):
        data=json.loads((ROOT/"frontend/monitoring/demo.json").read_text(encoding="utf-8"))
        for run in data["runs"]:
            self.assertIsNone(run["energy_kwh"])
            self.assertIsNone(run["co2e_kg"])

    def test_four_monitoring_views(self):
        script=(ROOT/"frontend/monitoring/app.js").read_text(encoding="utf-8")
        for key in ('id:"equipment"','id:"data"','id:"maintenance"','id:"platform"'):
            self.assertIn(key,script)
        self.assertIn("chosenSite",script)
        self.assertIn("fictional_demo_only",script)

    def test_unverified_source_refused(self):
        data=json.loads((ROOT/"frontend/monitoring/demo.json").read_text(encoding="utf-8"))
        data["data_mode"]="real_hospital"
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/"bad.json"
            path.write_text(json.dumps(data),encoding="utf-8")
            with self.assertRaisesRegex(ValueError,"fictive"):
                validate_fixture(path)

if __name__=="__main__":
    unittest.main()
