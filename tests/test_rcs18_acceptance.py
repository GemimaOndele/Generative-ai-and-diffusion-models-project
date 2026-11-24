"""Preuve d'acceptation du ticket Jira RCS-18 (critères vérifiés sur pièces)."""

import csv
import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from src.governance import (
    DEFAULT_EXPORT_DIR,
    DEFAULT_REGISTER,
    acceptance_check,
    export_registers,
    main,
)


class Rcs18AcceptanceTest(unittest.TestCase):
    @staticmethod
    def _root() -> Path:
        return Path(__file__).resolve().parents[1]

    def _register(self) -> Path:
        return self._root() / DEFAULT_REGISTER

    def test_all_jira_criteria_are_met(self):
        result = acceptance_check(self._register(), self._root() / DEFAULT_EXPORT_DIR)
        self.assertTrue(result["ok"], result["criteria"])
        self.assertEqual(len(result["criteria"]), 9)
        self.assertTrue(all(item["ok"] for item in result["criteria"]))
        self.assertEqual(result["validation"], {"ok": True, "errors": [], "adrs": 10, "risks": 10})

    def test_committed_acceptance_evidence_matches_code(self):
        evidence = self._root() / "governance" / "acceptance_rcs18.json"
        self.assertTrue(evidence.exists())
        committed = json.loads(evidence.read_text(encoding="utf-8"))
        fresh = acceptance_check(self._register(), self._root() / DEFAULT_EXPORT_DIR)
        self.assertEqual(committed, fresh)

    def test_jira_risk_themes_are_all_covered(self):
        coverage = acceptance_check()["coverage"]
        self.assertEqual(
            set(coverage),
            {"projet", "IA", "biais", "sécurité", "RGPD", "usage biomédical",
             "fournisseur", "budget", "dette technique"},
        )
        self.assertTrue(all(coverage.values()), coverage)

    def test_delivered_csv_registers_contain_owner_and_mitigation(self):
        risk_csv = self._root() / DEFAULT_EXPORT_DIR / "risk_register.csv"
        with risk_csv.open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        self.assertEqual(len(rows), 10)
        self.assertTrue(all(row["owner"] and row["mitigation"] for row in rows))
        self.assertTrue(all(row["reviewer"] and row["ticket"] for row in rows))
        self.assertTrue(all(row["residual"] == "ND" for row in rows))

    def test_stale_register_is_detected(self):
        with tempfile.TemporaryDirectory() as directory:
            _, risk_path = export_registers(self._register(), directory)
            with risk_path.open("a", encoding="utf-8") as handle:
                handle.write("ligne obsolète\n")
            result = acceptance_check(self._register(), directory)
        self.assertFalse(result["ok"])
        stale = [item for item in result["criteria"] if item["id"] == "GENERATED_REGISTERS_UP_TO_DATE"]
        self.assertFalse(stale[0]["ok"])

    def test_cli_acceptance_exit_code(self):
        output = io.StringIO()
        with redirect_stdout(output):
            code = main([str(self._register()), "--acceptance", "--export-dir", str(self._root() / DEFAULT_EXPORT_DIR)])
        self.assertEqual(code, 0)
        self.assertTrue(json.loads(output.getvalue())["ok"])

        with tempfile.TemporaryDirectory() as directory:
            output = io.StringIO()
            with redirect_stdout(output):
                code = main([str(self._register()), "--acceptance", "--export-dir", directory])
            self.assertEqual(code, 1)
            self.assertFalse(json.loads(output.getvalue())["ok"])


if __name__ == "__main__":
    unittest.main()
