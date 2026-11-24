"""Cross-branch RCS-38 ↔ Omar RCS-49/50/52 pipeline integration tests.

Uses Omar's actual versioned SQL migrations, CSV ingestion and anomaly scorer,
but all input rows are temporary fabricated industrial examples (no patient
data, no network download, no real medical records).
"""
from __future__ import annotations

from contextlib import closing
import csv
import hashlib
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from rcs.db import connect
from rcs.ingestion import import_csv, CONTRACT
from rcs.alerts import enregistrer_analyse
from tools.rcs38_ai4i_bridge import preview_ai4i, SOURCE_MODE


class RealSchemaIntegration(unittest.TestCase):
    def setUp(self):
        self.tdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tdir.cleanup)
        self.db = Path(self.tdir.name) / "actual-rcs-schema.sqlite"
        self.csv_path = Path(self.tdir.name) / "synthetic_rows.csv"
        with self.csv_path.open("w", encoding="utf-8", newline="") as output:
            writer = csv.DictWriter(output, fieldnames=list(CONTRACT))
            writer.writeheader()
            writer.writerow({
                "UDI": 1, "Type": "L", "Air temperature [K]": 298.2,
                "Process temperature [K]": 308.6, "Rotational speed [rpm]": 1400,
                "Torque [Nm]": 42.0, "Tool wear [min]": 15, "Machine failure": 0,
            })
            writer.writerow({
                "UDI": 2, "Type": "H", "Air temperature [K]": 301.1,
                "Process temperature [K]": 311.5, "Rotational speed [rpm]": 1250,
                "Torque [Nm]": 76.0, "Tool wear [min]": 35, "Machine failure": 1,
            })
        self.conn = connect(self.db)
        self.addCleanup(self.conn.close)

    def test_real_migrations_and_ingestion_readonly_adapter(self):
        expected_sha = hashlib.sha256(self.csv_path.read_bytes()).hexdigest()
        report = import_csv(self.conn, self.csv_path)
        self.assertEqual(report.statut, "importe")
        self.assertEqual(report.nb_acceptees, 2)
        self.assertEqual(report.nb_rejetees, 0)
        self.assertEqual(import_csv(self.conn, self.csv_path).statut, "deja_importe")
        n = self.conn.execute("SELECT count(*) FROM observation").fetchone()[0]
        self.assertEqual(n, 2)

        observation_id = self.conn.execute(
            "SELECT id FROM observation WHERE cle_source=?", ("2",)
        ).fetchone()[0]
        analysis_id, alert_id = enregistrer_analyse(
            self.conn, observation_id, "RCS-TEST-zscore@v1", 1.2, 0.8
        )
        self.assertIsNotNone(analysis_id)
        self.assertIsNotNone(alert_id)
        before = self.conn.execute("SELECT count(*) FROM audit").fetchone()[0]

        output = preview_ai4i(self.db, limit=20)
        self.assertEqual(output["source_mode"], SOURCE_MODE)
        self.assertTrue(output["read_only"])
        self.assertFalse(output["clinical_use"])
        self.assertFalse(output["control_enabled"])
        self.assertEqual(output["actions"], [])
        self.assertEqual(len(output["observations"]), 2)
        self.assertEqual({x["equipment_id"] for x in output["observations"]},
                         {"AI4I-L", "AI4I-H"})
        self.assertTrue(all(x["provenance"]["file_sha256"] == expected_sha
                            for x in output["observations"]))
        flagged = {x["source_record_id"]: x["anomaly"]["flag"] for x in output["observations"]}
        self.assertIsNone(flagged["1"])
        self.assertTrue(flagged["2"])
        self.assertEqual(self.conn.execute("SELECT count(*) FROM audit").fetchone()[0],
                         before)
        self.assertEqual(self.conn.execute("SELECT count(*) FROM observation").fetchone()[0], 2)

    def test_refuses_bad_medical_source_tag_on_real_schema(self):
        import_csv(self.conn, self.csv_path)
        self.conn.execute("UPDATE source_donnees SET categorie='Données patient' WHERE id='S04'")
        self.conn.commit()
        with self.assertRaises(ValueError):
            preview_ai4i(self.db)

    def test_readonly_mode_enforced(self):
        import_csv(self.conn, self.csv_path)
        self.assertTrue(preview_ai4i(self.db)["read_only"])
        with closing(sqlite3.connect(self.db)) as conn:
            self.assertEqual(conn.execute("SELECT count(*) FROM observation").fetchone()[0], 2)


if __name__ == "__main__":
    unittest.main()
