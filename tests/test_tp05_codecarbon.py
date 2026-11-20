"""Ces tests valident la lecture et la sécurité des chemins, PAS des mesures énergétiques."""
import csv
import pathlib
import tempfile
import unittest

from src.observability.codecarbon_local import read_local_metrics


class TestLocalCodeCarbonReader(unittest.TestCase):
    def test_absence_de_mesure_est_nd_pas_zero(self):
        with tempfile.TemporaryDirectory() as tmp:
            data = read_local_metrics("RCS-83-local", pathlib.Path(tmp))
            self.assertEqual(data["measurement_status"], "ND")
            self.assertIsNone(data["energy_kwh"])
            self.assertIsNone(data["co2e_kg"])

    def test_rejet_traversee_repertoire(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                read_local_metrics("../secret", pathlib.Path(tmp))

    def test_lecture_fichier_factice_isole(self):
        # Ligne 100 % fictive pour TESTER LE PARSEUR ; PAS un résultat RoboCare.
        with tempfile.TemporaryDirectory() as tmp:
            d = pathlib.Path(tmp) / "test"
            d.mkdir()
            with (d / "emissions.csv").open("w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=[
                    "energy_consumed", "emissions", "duration",
                    "tracking_mode", "codecarbon_version"
                ])
                writer.writeheader()
                writer.writerow({
                    "energy_consumed": "0.001", "emissions": "0.0001",
                    "duration": "15", "tracking_mode": "process",
                    "codecarbon_version": "test-fictif"
                })
            r = read_local_metrics("test", pathlib.Path(tmp))
            self.assertEqual(r["energy_kwh"], 0.001)
            self.assertEqual(r["co2e_kg"], 0.0001)
            self.assertEqual(r["measurement_status"], "estimation_codecarbon")


if __name__ == "__main__":
    unittest.main()
