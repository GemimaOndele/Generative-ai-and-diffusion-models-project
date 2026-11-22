"""Read-only AI4I adapter tests using an isolated synthetic SQLite fixture."""
import sqlite3
import tempfile
import unittest
from pathlib import Path

from tools.rcs38_ai4i_bridge import preview_ai4i, SOURCE_MODE


DDL = """
CREATE TABLE source_donnees (id TEXT, nom TEXT, url TEXT, licence TEXT, categorie TEXT, date_verif TEXT);
CREATE TABLE equipement (id TEXT, type TEXT, site TEXT, criticite TEXT, est_fictif INTEGER);
CREATE TABLE lot_import (id INTEGER, source_id TEXT, fichier TEXT, sha256 TEXT, importe_le TEXT);
CREATE TABLE observation (
  id INTEGER, equipement_id TEXT, cle_source TEXT, lot_id INTEGER,
  air_temp_k REAL, process_temp_k REAL, rpm REAL, torque_nm REAL, tool_wear_min REAL
);
CREATE TABLE analyse_modele (id INTEGER, observation_id INTEGER, score REAL, seuil REAL, model_version TEXT);
"""


class TestAI4IReadOnlyAdapter(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.db = Path(self.tmp.name) / "proxy.sqlite3"
        with sqlite3.connect(self.db) as con:
            con.executescript(DDL)
            con.execute("INSERT INTO source_donnees VALUES (?,?,?,?,?,?)",
                        ("S04", "AI4I", "https://example.invalid/fixture", "test-only",
                         "Substitut synthétique NON médical", "2026-11-22"))
            con.execute("INSERT INTO equipement VALUES (?,?,?,?,?)",
                        ("AI4I-L", "substitut industriel", "simulé", "faible", 1))
            con.execute("INSERT INTO lot_import VALUES (?,?,?,?,?)",
                        (1, "S04", "fixture.csv", "a" * 64, "2026-11-22T12:00:00Z"))
            con.execute("INSERT INTO observation VALUES (?,?,?,?,?,?,?,?,?)",
                        (1, "AI4I-L", "42", 1, 300.0, 310.0, 1500, 40.0, 20))
            con.execute("INSERT INTO analyse_modele VALUES (?,?,?,?,?)",
                        (1, 1, 0.9, 0.8, "demo-zscore"))
            con.commit()

    def test_preview_retains_provenance_and_is_not_demo_fixture(self):
        result = preview_ai4i(self.db)
        self.assertEqual(result["source_mode"], SOURCE_MODE)
        self.assertNotIn("data_mode", result)
        self.assertTrue(result["read_only"])
        self.assertFalse(result["medical_data"])
        self.assertFalse(result["control_enabled"])
        self.assertEqual(result["actions"], [])
        self.assertEqual(result["x_axis"], "source_record_id_not_time")
        self.assertEqual(result["observations"][0]["provenance"]["file_sha256"], "a" * 64)
        self.assertEqual(result["observations"][0]["anomaly"]["flag"], True)
        self.assertNotIn("label", result["observations"][0])

    def test_no_scores_must_not_be_interpreted_as_no_anomaly(self):
        with sqlite3.connect(self.db) as con:
            con.execute("DELETE FROM analyse_modele")
        r = preview_ai4i(self.db)
        self.assertIsNone(r["observations"][0]["anomaly"]["flag"])
        self.assertIsNone(r["observations"][0]["anomaly"]["score"])

    def test_reject_non_medical_flag_missing(self):
        with sqlite3.connect(self.db) as con:
            con.execute("UPDATE source_donnees SET categorie = 'Dispositif patient'")
        with self.assertRaises(ValueError):
            preview_ai4i(self.db)

    def test_reject_real_equipment_even_if_id_prefix_matches(self):
        with sqlite3.connect(self.db) as con:
            con.execute("UPDATE equipement SET est_fictif = 0")
        with self.assertRaises(ValueError):
            preview_ai4i(self.db)

    def test_reject_invalid_limits(self):
        for limit in (0, 1001, -2, True, "20", 0.2):
            with self.subTest(limit=limit):
                with self.assertRaises(ValueError):
                    preview_ai4i(self.db, limit=limit)

    def test_read_only_no_database_mutation(self):
        with sqlite3.connect(self.db) as con:
            before = con.total_changes
            snapshot = con.execute("SELECT COUNT(*) FROM observation").fetchone()[0]
        preview_ai4i(self.db)
        with sqlite3.connect(self.db) as con:
            self.assertEqual(con.execute("SELECT COUNT(*) FROM observation").fetchone()[0],
                             snapshot)
            self.assertEqual(con.execute("SELECT COUNT(*) FROM audit").fetchone()[0]
                             if con.execute("SELECT name FROM sqlite_master WHERE name='audit'").fetchone()
                             else 0, 0)
        self.assertEqual(before, 0)


if __name__ == "__main__":
    unittest.main()
